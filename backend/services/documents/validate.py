"""Validates a generic Document before it's shown to the user or exported.

Mirrors services.normalization.validate_data's philosophy: flag genuine
problems in plain language, never invent values, and only raise when there
is truly nothing usable to show — reuses the same exception class so the
view layer needs no branching between the RSE and generic pipelines.

Every check is recorded twice:

- as a structured issue (``document['validation_issues']``) carrying a
  stable ``rule_id``, a ``severity``, and — where it applies — the exact
  dataset/column/row it's about, so a UI or export can group, filter, or
  color-code issues instead of pattern-matching prose.
- as the existing plain-English ``warnings`` list, unchanged in shape
  (``List[str]``) so the frontend, the Report model, and every existing test
  asserting on warning text keep working exactly as before. ``info``-level
  issues (e.g. "N blank rows were skipped") are recorded in
  ``validation_issues`` but deliberately left out of ``warnings`` — they are
  not something the user needs reviewing, just something that must never be
  silently unaccounted for.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from services.normalization.clean_data import clean_text, parse_number
from services.normalization.validate_data import ReportValidationError

# Row labels that mark a row as a declared total/subtotal rather than an
# individual record — used to reconcile a source-provided total against the
# sum of the other rows without ever assuming which row (if any) is a total.
TOTAL_ROW_LABELS = {'total', 'grand total', 'subtotal', 'sum', 'overall'}
_RECONCILIATION_TOLERANCE_RATIO = 0.01
_RECONCILIATION_TOLERANCE_ABS = 0.01
_NUMERIC_SEMANTIC_TYPES = ('currency', 'quantity', 'number')
_LABEL_SEMANTIC_TYPES = ('category', 'text', 'identifier')


def _issue(
    rule_id: str, severity: str, message: str, *, dataset: Optional[str] = None,
    column: Optional[str] = None, row: Optional[int] = None, source: Optional[dict] = None,
    value: Any = None, suggested_action: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        'rule_id': rule_id, 'severity': severity, 'message': message,
        'dataset': dataset, 'column': column, 'row': row, 'source': source,
        'value': value, 'suggested_action': suggested_action,
    }


def _record(issues: List[dict], warnings: List[str], issue: dict) -> None:
    issues.append(issue)
    if issue['severity'] != 'info':
        warnings.append(issue['message'])


def _check_low_confidence_columns(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    low_confidence = [c['display_name'] for c in dataset.get('columns', []) if c.get('confidence') == 'low']
    if not low_confidence:
        return
    name = dataset['name']
    _record(issues, warnings, _issue(
        'low_confidence_column', 'warning',
        f'Dataset "{name}": could not confidently determine the type of '
        f'{"column" if len(low_confidence) == 1 else "columns"} {", ".join(low_confidence)}.',
        dataset=name, suggested_action='Review these columns\' values; the inferred type may not fit.',
    ))


def _check_missing_values(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    """One issue per incomplete column (not just the single worst one, as an
    earlier version of this check did) — a document with three sparse
    columns deserves three reviewable findings, not one that hides the rest."""
    name = dataset['name']
    for column in dataset.get('columns', []):
        total, non_null = column.get('total_count', 0), column.get('non_null_count', 0)
        missing = total - non_null
        if total == 0 or missing == 0:
            continue
        display = column['display_name']
        if missing == total:
            message = f'Dataset "{name}": every record is missing a value for "{display}".'
            action = 'This column may have failed to extract at all — check the source.'
        else:
            message = f'Dataset "{name}": {missing} record(s) are missing a value for "{display}".'
            action = 'Confirm whether these should genuinely be blank.'
        _record(issues, warnings, _issue(
            'missing_values', 'warning', message, dataset=name, column=display, suggested_action=action,
        ))


def _check_duplicate_rows(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    duplicate_count = dataset.get('duplicate_row_count', 0)
    if duplicate_count:
        name = dataset['name']
        _record(issues, warnings, _issue(
            'duplicate_rows', 'warning',
            f'Dataset "{name}": {duplicate_count} record(s) appear to be exact duplicates of another row.',
            dataset=name, suggested_action='Check the source for accidental repeats before relying on totals.',
        ))


def _check_blank_rows_skipped(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    skipped = dataset.get('blank_rows_skipped', 0)
    if skipped:
        name = dataset['name']
        _record(issues, warnings, _issue(
            'blank_rows_skipped', 'info',
            f'Dataset "{name}": {skipped} fully blank row(s) in the source table were skipped '
            f'(there was nothing in them to extract).',
            dataset=name,
        ))


def _check_column_stats(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    name = dataset['name']
    for column in dataset.get('columns', []):
        stats = column.get('stats')
        if not stats:
            continue
        display = column['display_name']
        semantic_type = column.get('semantic_type')

        unparsed = stats.get('unparsed_count') or 0
        if unparsed:
            kind = 'date' if semantic_type == 'date' else 'number'
            _record(issues, warnings, _issue(
                'unparsed_value', 'warning',
                f'Dataset "{name}": {unparsed} value(s) in "{display}" did not look like a valid {kind} '
                f'and were treated as missing rather than guessed.',
                dataset=name, column=display,
                suggested_action='Review the source cells and correct or remove them.',
            ))

        negative = stats.get('negative_count') or 0
        if negative and semantic_type in ('currency', 'quantity'):
            _record(issues, warnings, _issue(
                'negative_value', 'warning',
                f'Dataset "{name}": "{display}" has {negative} negative value(s), which is unusual for a '
                f'{semantic_type} field — verify against the source.',
                dataset=name, column=display,
                suggested_action='Confirm whether negative values are expected here (e.g. refunds, adjustments).',
            ))

        unique_count = stats.get('unique_count')
        if semantic_type == 'identifier' and unique_count is not None:
            duplicate_values = column.get('non_null_count', 0) - unique_count
            if duplicate_values > 0:
                _record(issues, warnings, _issue(
                    'duplicate_identifier', 'warning',
                    f'Dataset "{name}": "{display}" has {duplicate_values} duplicate value(s) in a column '
                    f'that normally identifies each record uniquely.',
                    dataset=name, column=display,
                    suggested_action='Check for repeated, merged, or re-used identifiers.',
                ))

        ambiguous = stats.get('ambiguous_date_count') or 0
        if ambiguous:
            _record(issues, warnings, _issue(
                'ambiguous_date', 'warning',
                f'Dataset "{name}": {ambiguous} date value(s) in "{display}" have both a day and month '
                f'part of 12 or below (e.g. "03/04/2026"), which is ambiguous — they were read as '
                f'day-first (3 April 2026).',
                dataset=name, column=display,
                suggested_action='Confirm the source document\'s date convention (day-first vs. month-first).',
            ))


def _check_total_row_reconciliation(dataset: dict, issues: List[dict], warnings: List[str]) -> None:
    """If a row's label reads as a declared total (see TOTAL_ROW_LABELS),
    its numeric columns are checked against the sum of every other row —
    catching the common real-world case where a source spreadsheet's own
    "Total" row doesn't actually match its line items."""
    rows = dataset.get('rows', [])
    columns = dataset.get('columns', [])
    if len(rows) < 2:
        return
    label_columns = [c for c in columns if c.get('semantic_type') in _LABEL_SEMANTIC_TYPES]
    numeric_columns = [c for c in columns if c.get('semantic_type') in _NUMERIC_SEMANTIC_TYPES]
    if not label_columns or not numeric_columns:
        return

    name = dataset['name']
    for row in rows:
        label = next(
            (clean_text(row.get(c['name'])) for c in label_columns
             if (clean_text(row.get(c['name'])) or '').strip().lower() in TOTAL_ROW_LABELS),
            None,
        )
        if label is None:
            continue
        other_rows = [r for r in rows if r is not row]
        for column in numeric_columns:
            claimed = parse_number(row.get(column['name']))
            if claimed is None:
                continue
            computed = sum(
                v for v in (parse_number(r.get(column['name'])) for r in other_rows) if v is not None
            )
            tolerance = max(_RECONCILIATION_TOLERANCE_ABS, abs(computed) * _RECONCILIATION_TOLERANCE_RATIO)
            if abs(claimed - computed) > tolerance:
                _record(issues, warnings, _issue(
                    'total_mismatch', 'error',
                    f'Dataset "{name}": the "{label}" row\'s "{column["display_name"]}" value '
                    f'({claimed:g}) does not match the sum of the other rows ({computed:g}).',
                    dataset=name, column=column['display_name'], value=claimed,
                    suggested_action='Re-check the source total against its itemized rows.',
                ))


def validate_document(document: dict) -> Tuple[dict, List[str]]:
    """A document with no tables is not a failure — most real documents
    (a policy memo, a narrative report, a letter) have no table at all, and
    still deserve a document overview built from their text. This only
    raises when literally nothing readable came out of extraction (no text,
    no tables, no figures) — that is a genuine extraction failure."""
    warnings: List[str] = []
    issues: List[dict] = []
    datasets = document.get('datasets', [])
    sections = document.get('sections', [])
    figures = document.get('figures', [])

    if not datasets and not sections and not figures:
        raise ReportValidationError(
            'We couldn\'t extract any readable content from this document — no text, '
            'tables, or figures were found. The file may be empty, corrupted, or a scanned '
            'image without a text layer.'
        )

    # Any extraction-level warning already raised by the extractor/parser
    # itself (e.g. an ambiguous JSON envelope, a hidden sheet, a formula
    # cell with no cached value) is carried through with its own severity
    # rather than re-derived here — see generic_parser._attach_extraction_warnings.
    for severity, message in document.pop('_extraction_warnings', []):
        _record(issues, warnings, _issue('extraction_warning', severity, message))

    for dataset in datasets:
        _check_low_confidence_columns(dataset, issues, warnings)
        _check_missing_values(dataset, issues, warnings)
        _check_duplicate_rows(dataset, issues, warnings)
        _check_blank_rows_skipped(dataset, issues, warnings)
        _check_column_stats(dataset, issues, warnings)
        _check_total_row_reconciliation(dataset, issues, warnings)

    document['validation_issues'] = issues
    return document, warnings
