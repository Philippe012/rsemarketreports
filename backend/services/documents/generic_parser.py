"""Turns the raw extraction results already produced by
services.extraction.{pdf_extractor,excel_extractor,csv_extractor,
docx_extractor,txt_extractor} into a generic Document (see model.py) for
documents that are not a recognized RSE market report.

This deliberately reuses the exact same low-level extraction as the RSE
pipeline — pdf_extractor/excel_extractor never assumed anything RSE-specific
in the first place, so both pipelines can consume their output. Only the
*interpretation* of that raw text/tables/sheets differs from here on.

A document with no tables at all is not a failure here — see validate.py.
Every document, table-shaped or not, gets sections/entities extracted from
its text, so a prose-only report still produces a real document overview.

Every Document returned here has already passed Pydantic structural
validation (schemas.validate_document_shape) — a bug in this module that
produces a malformed field surfaces immediately as a clear internal error
here, not as a broken dashboard downstream.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd
from django.conf import settings

from services.extraction.docx_extractor import DocxExtractionResult
from services.extraction.excel_extractor import ExcelExtractionResult
from services.extraction.json_extractor import JsonExtractionResult
from services.extraction.pdf_extractor import PdfExtractionResult
from services.normalization.clean_data import clean_text, is_blank_row
from services.normalization.validate_data import ReportValidationError

MAX_TABLE_ROWS = getattr(settings, 'MAX_TABLE_ROWS', 50_000)
MAX_TABLE_COLUMNS = getattr(settings, 'MAX_TABLE_COLUMNS', 200)
MAX_SHEETS_PER_WORKBOOK = getattr(settings, 'MAX_SHEETS_PER_WORKBOOK', 200)
MAX_PDF_PAGES = getattr(settings, 'MAX_PDF_PAGES', 1000)

from . import schema_inference
from .charts import suggest_charts
from .classification import classify_document
from .entities import extract_entities
from .figures import extract_docx_figures, extract_pdf_figures
from .insights import compute_insights
from .metrics import compute_metrics
from .model import make_dataset, make_document, make_section
from .schemas import validate_document_shape

MIN_DATA_ROWS_FOR_DATASET = 1
MIN_COLUMNS_FOR_DATASET = 2


def _dedupe_headers(raw_headers: List[Optional[str]]) -> List[str]:
    seen = {}
    headers = []
    for i, raw in enumerate(raw_headers):
        name = clean_text(raw) or f'Column {i + 1}'
        if name in seen:
            seen[name] += 1
            name = f'{name} ({seen[name]})'
        else:
            seen[name] = 1
        headers.append(name)
    return headers


def _table_to_dataset(name: str, source: str, table: List[List]) -> Optional[dict]:
    """Convert a raw 2D table (first row = header) into a Dataset, or None
    if it isn't shaped like real tabular data (too few columns/rows).

    Each row keeps a hidden ``_source_row`` key — its 1-based position in
    the *original* ``table`` (header included), before blank rows were
    dropped — so a value can always be traced back to where it sat in the
    extracted table (a spreadsheet row, a PDF table row, ...) without that
    bookkeeping key ever being treated as a real column (schema_inference
    and the frontend only ever look columns up by their declared names).
    """
    indexed_rows = [(i, r) for i, r in enumerate(table, start=1) if not is_blank_row(r)]
    blank_rows_skipped = len(table) - len(indexed_rows)
    if len(indexed_rows) < 1 + MIN_DATA_ROWS_FOR_DATASET:
        return None

    (_, header_row), *data_entries = indexed_rows
    headers = _dedupe_headers(header_row)
    if len([h for h in header_row if clean_text(h) is not None]) < MIN_COLUMNS_FOR_DATASET:
        return None

    if len(headers) > MAX_TABLE_COLUMNS:
        raise ReportValidationError(
            f'Dataset "{name}" has {len(headers)} columns, which is more than this system accepts '
            f'({MAX_TABLE_COLUMNS}) — it was rejected rather than silently truncated.'
        )
    if len(data_entries) > MAX_TABLE_ROWS:
        raise ReportValidationError(
            f'Dataset "{name}" has {len(data_entries)} rows, which is more than this system accepts '
            f'({MAX_TABLE_ROWS}) — it was rejected rather than silently truncated.'
        )

    row_dicts = []
    for source_row, raw_row in data_entries:
        row_dict = {
            headers[i]: raw_row[i] if i < len(raw_row) else None
            for i in range(len(headers))
        }
        row_dict['_source_row'] = source_row
        row_dicts.append(row_dict)
    if not row_dicts:
        return None

    columns = schema_inference.infer_columns(headers, row_dicts)

    # Whole-row duplicate detection: pandas' own duplicated() over the
    # dataframe of *cleaned* text values — cheap, vectorized, and exactly
    # the kind of table-wide check pandas exists for, rather than a
    # hand-rolled set-of-tuples loop.
    text_frame = pd.DataFrame(
        [[clean_text(row.get(h)) for h in headers] for row in row_dicts],
        columns=headers,
    )
    duplicate_row_count = int(text_frame.duplicated().sum())

    return make_dataset(
        name, source, columns, row_dicts,
        duplicate_row_count=duplicate_row_count, blank_rows_skipped=blank_rows_skipped,
    )


def _records_to_table(records: List[dict]) -> List[List]:
    """Builds a 2D table (header row + data rows) out of a list of flat
    record dicts whose key sets may differ record to record — the header
    is the union of every key, in first-seen order, so a record missing a
    field just leaves a blank cell rather than breaking the table shape.

    A key starting with "_" (e.g. json_extractor's ``_json_path``) is
    bookkeeping, not a real column, and is never included in the header —
    see ``_attach_json_provenance`` for how that same information reaches
    the finished dataset instead, as a hidden per-row key rather than a
    visible one."""
    headers: List[str] = []
    seen = set()
    for record in records:
        for key in record.keys():
            if key.startswith('_') or key in seen:
                continue
            seen.add(key)
            headers.append(key)
    return [headers] + [[record.get(h) for h in headers] for record in records]


def _attach_json_provenance(dataset: Optional[dict], records: List[dict]) -> None:
    """Copies json_extractor's per-record bookkeeping keys (``_json_path``,
    ``_parent_ref``, ``_jsonl_line``) from the original flat records onto
    the finished dataset's rows, matched back up via ``_source_row``
    (``_table_to_dataset`` numbers rows 1-based with the header as row 1, so
    row N of the table is ``records[N - 2]``) — a row that was skipped for
    being fully blank simply never receives (or needs) this bookkeeping."""
    if not dataset:
        return
    for row in dataset['rows']:
        index = row['_source_row'] - 2
        if 0 <= index < len(records):
            source = records[index]
            for key in ('_json_path', '_parent_ref', '_jsonl_line'):
                if key in source:
                    row[key] = source[key]


def _finalize(document: dict) -> dict:
    """Run the Pydantic structural-validation stage before handing the
    Document back to the pipeline."""
    return validate_document_shape(document)


def _sections_text(sections: List[dict]) -> str:
    return '\n'.join(s['content'] for s in sections if s.get('content'))


def _table_header_signature(table: List[List]) -> Optional[tuple]:
    for r in table:
        if not is_blank_row(r):
            return tuple(clean_text(c) for c in r)
    return None


def _merge_continued_pdf_tables(pages_tables: List[List[List[List]]]) -> List[Tuple[str, List[List]]]:
    """Groups the raw per-page PDF tables into ``(source_label, table)``
    pairs, merging a table into the group that precedes it only when it is
    the *first* table on the very next page and its header row matches the
    previous group's exactly — a narrow, high-confidence signal for "this
    is the same table continuing across a page break", not a guess. Any
    table that doesn't meet that bar simply starts its own group, which is
    exactly today's un-merged behavior — merging only ever happens when
    it's safe, never "when uncertain"."""
    groups: List[Tuple[List[Tuple[int, int]], List[List]]] = []
    for page_index, page_tables in enumerate(pages_tables, start=1):
        for table_index, table in enumerate(page_tables, start=1):
            header = _table_header_signature(table)
            merged = False
            if header is not None and len(header) > 1 and groups:
                last_locations, last_table = groups[-1]
                last_page, _ = last_locations[-1]
                if page_index == last_page + 1 and table_index == 1 and _table_header_signature(last_table) == header:
                    data_rows, seen_header = [], False
                    for r in table:
                        if not seen_header and not is_blank_row(r):
                            seen_header = True
                            continue
                        data_rows.append(r)
                    groups[-1] = (last_locations + [(page_index, table_index)], last_table + data_rows)
                    merged = True
            if not merged:
                groups.append(([(page_index, table_index)], table))

    result = []
    for locations, table in groups:
        first_page, first_table_index = locations[0]
        if len(locations) > 1:
            last_page = locations[-1][0]
            source = f'PDF pages {first_page}-{last_page}, table {first_table_index} (merged across page break)'
        else:
            source = f'PDF page {first_page}, table {first_table_index}'
        result.append((source, table))
    return result


def parse_pdf_document(extraction: PdfExtractionResult, filename: str, file_path: Optional[str] = None) -> dict:
    if len(extraction.pages_text) > MAX_PDF_PAGES:
        raise ReportValidationError(
            f'This PDF has {len(extraction.pages_text)} pages, which is more than this system accepts '
            f'({MAX_PDF_PAGES}) — it was rejected rather than only partially processed.'
        )
    datasets = []
    sections = []
    extraction_warnings: List[Tuple[str, str]] = []
    if extraction.used_ocr:
        extraction_warnings.append((
            'warning',
            'This PDF had no extractable text layer and was processed with OCR (optical character '
            'recognition) instead — OCR can misread characters, so every value here should be reviewed '
            'against the original document before being relied on.',
        ))

    for source, table in _merge_continued_pdf_tables(extraction.pages_tables):
        dataset_name = f'Table {len(datasets) + 1}'
        dataset = _table_to_dataset(dataset_name, source, table)
        if dataset:
            datasets.append(dataset)

    for page_index, page_text in enumerate(extraction.pages_text, start=1):
        stripped_page = page_text.strip()
        if stripped_page and len(stripped_page) > 40:
            lines = stripped_page.splitlines()
            first_line = lines[0].strip()
            # A short first line reads as a heading — pulled out as the
            # section's title rather than left duplicated at the top of its
            # own content. Each remaining line is cleaned individually
            # (not collapsed into one blob) so paragraph breaks survive.
            if first_line and len(first_line) < 90:
                title, body_lines = first_line, lines[1:]
            else:
                title, body_lines = f'Page {page_index}', lines
            body = '\n'.join(filter(None, (clean_text(line) for line in body_lines)))
            if body:
                sections.append(make_section(title, body))

    full_text = extraction.full_text
    document_type, confidence = classify_document(datasets, full_text)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)
    entities = extract_entities(full_text)
    figures = extract_pdf_figures(file_path) if file_path else []

    document = _finalize(make_document(
        filename, 'pdf', document_type, confidence, sections, datasets, metrics, charts,
        figures=figures, insights=insights, entities=entities,
    ))
    _attach_extraction_warnings(document, extraction_warnings)
    return document


def parse_excel_document(extraction: ExcelExtractionResult, filename: str) -> dict:
    if len(extraction.sheets) > MAX_SHEETS_PER_WORKBOOK:
        raise ReportValidationError(
            f'This workbook has {len(extraction.sheets)} sheets, which is more than this system accepts '
            f'({MAX_SHEETS_PER_WORKBOOK}) — it was rejected rather than only partially processed.'
        )
    datasets = []
    extraction_warnings: List[Tuple[str, str]] = []
    for sheet_name, rows in extraction.sheets.items():
        dataset = _table_to_dataset(sheet_name, f'Sheet: {sheet_name}', rows)
        if dataset:
            datasets.append(dataset)

        info = extraction.sheet_info.get(sheet_name)
        if not info:
            continue
        if info.hidden:
            # Not a data-quality problem by itself (plenty of legitimate
            # workbooks have a hidden "calculations" tab) — reported for
            # transparency (never silently processed-but-unmentioned)
            # without cluttering the main warnings panel over it.
            extraction_warnings.append(('info', f'Sheet "{sheet_name}" is hidden in the source workbook.'))
        if info.formula_without_cache_count:
            extraction_warnings.append(('warning', (
                f'Sheet "{sheet_name}": {info.formula_without_cache_count} formula cell(s) have no '
                f'cached value (the workbook was never recalculated/saved in Excel) and were treated '
                f'as blank rather than guessed — open the file in Excel, let it recalculate, and re-save '
                f'to fix this.'
            )))

    document_type, confidence = classify_document(datasets)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)

    document = _finalize(make_document(
        filename, 'excel', document_type, confidence, [], datasets, metrics, charts,
        insights=insights,
    ))
    _attach_extraction_warnings(document, extraction_warnings)
    return document


def parse_csv_document(rows: List[List], filename: str) -> dict:
    dataset = _table_to_dataset('Data', 'CSV file', rows)
    datasets = [dataset] if dataset else []

    document_type, confidence = classify_document(datasets)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)

    return _finalize(make_document(
        filename, 'csv', document_type, confidence, [], datasets, metrics, charts,
        insights=insights,
    ))


def _attach_extraction_warnings(document: dict, extraction_warnings: List[Tuple[str, str]]) -> None:
    """Attaches (severity, message) pairs raised by the extractor itself
    (an ambiguous JSON envelope, a hidden sheet, a formula with no cached
    value) *after* Pydantic validation already ran — see
    services.documents.validate, which pops this key back off and turns
    each pair into a proper structured validation issue."""
    document['_extraction_warnings'] = extraction_warnings


def parse_json_document(extraction: JsonExtractionResult, filename: str) -> dict:
    datasets = []
    primary = _table_to_dataset('Data', 'JSON records', _records_to_table(extraction.records))
    _attach_json_provenance(primary, extraction.records)
    if primary:
        datasets.append(primary)

    for field_path, records in extraction.nested_tables.items():
        nested = _table_to_dataset(field_path, f'JSON field: {field_path}', _records_to_table(records))
        _attach_json_provenance(nested, records)
        if nested:
            datasets.append(nested)

    document_type, confidence = classify_document(datasets)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)

    document = _finalize(make_document(
        filename, 'json', document_type, confidence, [], datasets, metrics, charts,
        insights=insights,
    ))
    _attach_extraction_warnings(document, [('warning', w) for w in extraction.warnings])
    return document


def parse_docx_document(extraction: DocxExtractionResult, filename: str, file_path: Optional[str] = None) -> dict:
    datasets = []
    for table_index, table in enumerate(extraction.tables, start=1):
        dataset = _table_to_dataset(f'Table {table_index}', f'Word table {table_index}', table)
        if dataset:
            datasets.append(dataset)

    sections = [make_section(s.get('heading'), s['content']) for s in extraction.sections if s.get('content')]

    full_text = _sections_text(sections)
    document_type, confidence = classify_document(datasets, full_text)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)
    entities = extract_entities(full_text)
    figures = extract_docx_figures(file_path) if file_path else []

    return _finalize(make_document(
        filename, 'docx', document_type, confidence, sections, datasets, metrics, charts,
        figures=figures, insights=insights, entities=entities,
    ))


def parse_txt_document(extraction, filename: str) -> dict:
    datasets = []
    for table_index, table in enumerate(extraction.tables, start=1):
        dataset = _table_to_dataset(f'Table {table_index}', f'Detected table {table_index}', table)
        if dataset:
            datasets.append(dataset)

    sections = [make_section(s.get('title'), s['content']) for s in extraction.sections if s.get('content')]

    document_type, confidence = classify_document(datasets, extraction.full_text)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)
    entities = extract_entities(extraction.full_text)

    return _finalize(make_document(
        filename, 'txt', document_type, confidence, sections, datasets, metrics, charts,
        insights=insights, entities=entities,
    ))
