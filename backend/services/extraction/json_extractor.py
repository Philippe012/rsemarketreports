"""Extracts tabular records out of a JSON or JSON Lines file.

Real-world JSON exports rarely arrive as one flat array of flat objects, so
this module normalizes the common shapes into something
services.documents.generic_parser can turn into Dataset(s):

- a bare array of objects                          -> the primary table
- a single object                                   -> treated as one record
- a known API envelope (``data``/``results``/       -> that array wins,
  ``records``/``items``/``payload``)                   checked in that fixed
                                                        priority order
- multiple top-level arrays with no recognized      -> each becomes its own
  envelope key                                         dataset (never a
                                                        silent guess at
                                                        which is "the" data)
- JSON Lines / NDJSON (``.jsonl``, ``.ndjson``)     -> one record per line,
                                                        each tagged with its
                                                        line number
- nested objects                                    -> flattened with dotted
                                                        keys ("a.b.c")
- a nested array of objects (e.g. line items)       -> pulled out into its
  at any depth                                         own named table,
                                                        tagged with a
                                                        reference back to its
                                                        parent row, instead of
                                                        being dropped or
                                                        mangled
- a nested array of scalars                         -> joined into one cell
- records with missing fields                       -> left as a blank cell;
                                                        the union of every
                                                        key across records
                                                        becomes the header
- mixed object shapes                               -> same as above; a
                                                        field only some
                                                        records have is just
                                                        blank on the rest

Nothing here invents a value — a field that is genuinely absent from a
record stays absent (None), it is never defaulted or guessed. Every row also
carries a hidden ``_json_path`` (e.g. ``$.orders[2]``) and, for a nested
row, a ``_parent_ref`` back to whichever row it came from — the same
"bookkeeping key, not a real column" convention services.documents
.generic_parser already uses for ``_source_row`` (see that module's
``_records_to_table``, which strips any underscore-prefixed key back out of
the visible header before a table is built).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Known API-envelope keys, checked in this fixed priority order — a
# deterministic rule, never "whichever array happens to be longest".
_ENVELOPE_KEYS = ('data', 'results', 'records', 'items', 'payload')


class JsonExtractionError(Exception):
    """Raised when a JSON/JSON-Lines file cannot be read, parsed, or contains no usable records."""


@dataclass
class JsonExtractionResult:
    records: List[dict] = field(default_factory=list)
    # Every other table found — a nested array of objects at any depth, or
    # (when the root itself was ambiguous) another top-level array — keyed
    # by the dotted field path it was found under.
    nested_tables: Dict[str, List[dict]] = field(default_factory=dict)
    # Extraction-level warnings (e.g. an ambiguous top-level envelope) that
    # aren't about any one dataset yet, carried into document warnings by
    # services.documents.generic_parser.parse_json_document.
    warnings: List[str] = field(default_factory=list)


def _flatten_one(obj: Any) -> Tuple[Dict[str, Any], List[Tuple[str, List[Any]]]]:
    """Flattens a single JSON value's scalar/object fields into a flat dict
    (dotted keys). Any nested array-of-objects is *not* recursed into here —
    it's returned separately as (field_path, raw_list) so the caller
    (_process_records) can turn it into its own child table with proper
    JSONPath/parent-reference bookkeeping, rather than this function
    recursing blindly."""
    flat: Dict[str, Any] = {}
    nested_arrays: List[Tuple[str, List[Any]]] = []

    def walk(value: Any, prefix: str) -> None:
        if isinstance(value, dict):
            if not value:
                flat[prefix] = None
                return
            for key, sub_value in value.items():
                walk(sub_value, f'{prefix}.{key}' if prefix else str(key))
            return
        if isinstance(value, list):
            if not value:
                flat[prefix] = None
            elif all(isinstance(v, dict) for v in value):
                nested_arrays.append((prefix, value))
            else:
                flat[prefix] = '; '.join('' if v is None else str(v) for v in value)
            return
        flat[prefix] = value

    if not isinstance(obj, dict):
        flat['value'] = obj
    else:
        walk(obj, '')
    return flat, nested_arrays


def _parent_reference(flat_parent: Dict[str, Any], fallback: str) -> str:
    """The parent row's own natural identifier (its first field literally
    named/ending in "id"), falling back to its JSONPath when it has none —
    either way, a nested row can always be traced back to exactly one
    parent row, never left dangling."""
    for key, value in flat_parent.items():
        if key.startswith('_') or value in (None, ''):
            continue
        last_segment = key.rsplit('.', 1)[-1].lower()
        if last_segment == 'id' or last_segment.endswith('_id'):
            return str(value)
    return fallback


def _process_records(
    raw_records: List[Any],
    table_key: str,
    path_prefix: str,
    parent_refs: Optional[List[str]],
    line_numbers: Optional[List[int]],
    tables: Dict[str, List[dict]],
) -> None:
    """Flattens one list of raw JSON records into ``tables[table_key]``,
    recursing into any nested arrays-of-objects (at any depth) as their own
    child tables keyed by their dotted field path."""
    rows = tables.setdefault(table_key, [])
    for i, record in enumerate(raw_records):
        json_path = f'{path_prefix}[{i}]'
        flat, nested_arrays = _flatten_one(record)
        flat['_json_path'] = json_path
        if parent_refs is not None:
            flat['_parent_ref'] = parent_refs[i]
        if line_numbers is not None:
            flat['_jsonl_line'] = line_numbers[i]
        rows.append(flat)

        for field_path, raw_list in nested_arrays:
            child_key = f'{table_key}.{field_path}' if table_key else field_path
            own_ref = _parent_reference(flat, fallback=json_path)
            _process_records(
                raw_list, child_key, f'{json_path}.{field_path}',
                [own_ref] * len(raw_list), None, tables,
            )


def _select_root_tables(payload: Any) -> Tuple[Dict[str, List[Any]], List[str]]:
    """Decides which top-level array(s) become dataset(s).

    Returns ``{table_key: raw_records}`` — ``''`` means "the primary/unnamed
    table" (a bare top-level array, a single object, or the one recognized
    or only candidate array field); any other key names its own dataset
    directly, exactly like a nested array does. Also returns any warnings
    about how that decision was made (only non-empty when the choice was
    genuinely ambiguous).
    """
    if isinstance(payload, list):
        return {'': payload}, []
    if not isinstance(payload, dict):
        return {'': [payload]}, []

    for key in _ENVELOPE_KEYS:
        value = payload.get(key)
        if isinstance(value, list) and value:
            return {'': value}, []

    array_fields = {k: v for k, v in payload.items() if isinstance(v, list) and v}
    if len(array_fields) == 1:
        (_key, value), = array_fields.items()
        return {'': value}, []
    if len(array_fields) > 1:
        names = ', '.join(sorted(array_fields))
        warning = (
            f'This JSON object has {len(array_fields)} top-level arrays ({names}) and none use a '
            f'recognized envelope name (data/results/records/items/payload) — each was extracted as '
            f'its own dataset rather than guessing which one is "the" data.'
        )
        return dict(array_fields), [warning]

    # No array anywhere — the whole object is treated as a single record.
    return {'': [payload]}, []


def _decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def extract_json(file_path: str) -> JsonExtractionResult:
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
    except OSError as exc:
        raise JsonExtractionError(f'Unable to read the JSON file: {exc}') from exc

    if not raw.strip():
        raise JsonExtractionError('The JSON file is empty.')

    text = _decode(raw)
    is_jsonl = file_path.lower().endswith(('.jsonl', '.ndjson'))
    tables: Dict[str, List[dict]] = {}
    warnings: List[str] = []

    if is_jsonl:
        records: List[Any] = []
        line_numbers: List[int] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise JsonExtractionError(f'Invalid JSON on line {line_no}: {exc.msg}') from exc
            line_numbers.append(line_no)
        if not records:
            raise JsonExtractionError('The JSON file does not contain any records.')
        _process_records(records, '', '$', None, line_numbers, tables)
    else:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise JsonExtractionError(
                f'Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).'
            ) from exc
        root_tables, root_warnings = _select_root_tables(payload)
        warnings.extend(root_warnings)
        if not any(root_tables.values()):
            raise JsonExtractionError('The JSON file does not contain any records.')
        for key, records in root_tables.items():
            path_prefix = '$' if key == '' else f'$.{key}'
            _process_records(records, key, path_prefix, None, None, tables)

    primary = tables.pop('', [])
    return JsonExtractionResult(records=primary, nested_tables=tables, warnings=warnings)
