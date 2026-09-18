"""Builds the downloadable Excel workbook for a generic (non-RSE) Document —
one worksheet per extracted dataset, using the same styling as the RSE
exporter (see xlsx_style.py) so both pipelines produce a consistent-looking
workbook. Exports the full validated dataset, not just what happens to be
visible on screen.

Beyond the raw data sheets, the workbook also carries the metadata a real
production consumer needs to trust and audit it: where each value came from
(SOURCE METADATA, and a "Source Row" column on every dataset sheet), what
every column was inferred to mean (DATA DICTIONARY), every data-quality
concern raised during validation with its severity (VALIDATION ISSUES), how
each dataset's row count reconciles against its source table
(RECONCILIATION), and the un-normalized values exactly as extracted, side by
side with the typed/normalized dataset sheets (RAW EXTRACTED DATA) — never
silently dropped once the dashboard has moved on.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill

from services.normalization.clean_data import clean_text, parse_date, parse_number

from .xlsx_style import (
    FMT_DATE, FMT_DECIMAL, FMT_INTEGER, FMT_PERCENT, LABEL_FONT, SUBTITLE_FONT, TITLE_FONT,
    neutralize_formula_injection, safe_sheet_title, write_table,
)

# validate.py always prefixes a dataset-scoped warning with `Dataset "name": `
# — this module owns that convention (see services.documents.validate), so
# parsing it back out here to group issues by dataset is reading our own
# format, not guessing at someone else's.
_DATASET_PREFIX_RE = re.compile(r'^Dataset "([^"]+)":\s*(.*)$')

_NUMERIC_FORMATS = {
    'currency': FMT_DECIMAL,
    'quantity': FMT_INTEGER,
    'number': FMT_DECIMAL,
    'percentage': FMT_PERCENT,
}

_SEVERITY_FILL = {
    'error': PatternFill(start_color='FBE1E1', end_color='FBE1E1', fill_type='solid'),
    'warning': PatternFill(start_color='FDF3D6', end_color='FDF3D6', fill_type='solid'),
    'info': PatternFill(start_color='E7EEF7', end_color='E7EEF7', fill_type='solid'),
}
_SEVERITY_FONT = {
    'error': Font(color='9C1F1F', bold=True),
    'warning': Font(color='8A6300'),
    'info': Font(color='2E5A88'),
}
_NEGATIVE_FILL = PatternFill(start_color='FBE1E1', end_color='FBE1E1', fill_type='solid')


def _safe_cell(ws, row: int, column: int, value):
    cell = ws.cell(row=row, column=column, value=value)
    neutralize_formula_injection(cell)
    return cell


def _cell_value_and_format(value, semantic_type: str):
    """Convert one raw cell value for a given semantic type into the
    (value, number_format) pair to write — dates become real Excel dates,
    numeric semantic types become real numbers, everything else stays text."""
    if value is None or value == '':
        return None, None

    if semantic_type in ('date', 'datetime'):
        iso = parse_date(value)
        if iso:
            try:
                return datetime.strptime(iso, '%Y-%m-%d').date(), FMT_DATE
            except ValueError:
                pass
        return value, None

    if semantic_type in _NUMERIC_FORMATS:
        number = parse_number(value)
        if number is not None:
            return number, _NUMERIC_FORMATS[semantic_type]
        return value, None

    return value, None


def _sheet_for_dataset(wb: Workbook, dataset: dict, used_titles: set, used_table_names: set) -> None:
    columns = dataset.get('columns', [])
    rows = dataset.get('rows', [])
    if not columns or not rows:
        return

    title = safe_sheet_title(dataset.get('name') or 'Dataset', used_titles)
    ws = wb.create_sheet(title)

    # "Source Row" traces every exported value back to its position in the
    # originally extracted table (a spreadsheet row, a PDF/Word table row,
    # a JSON record — see generic_parser._table_to_dataset) so a
    # wrong-looking number can always be checked against the source
    # document, not just trusted blind.
    has_source_row = any(row.get('_source_row') is not None for row in rows)
    headers = (['Source Row'] if has_source_row else []) + [c['display_name'] for c in columns]
    formats: List[Optional[str]] = []
    out_rows = []
    for row in rows:
        out_row = [row.get('_source_row')] if has_source_row else []
        row_formats = [None] if has_source_row else []
        for column in columns:
            value, fmt = _cell_value_and_format(row.get(column['name']), column.get('semantic_type'))
            out_row.append(value)
            row_formats.append(fmt)
        out_rows.append(out_row)
        # Column formats are consistent per column (same semantic type for
        # every row), so the last row's formats are representative — but to
        # stay correct even with mixed/blank cells, take the first non-None
        # format seen per column across all rows.
        if not formats:
            formats = list(row_formats)
        else:
            formats = [f or existing for f, existing in zip(row_formats, formats)]

    widths = [10 if h == 'Source Row' else max(12, min(40, len(h) + 2)) for h in headers]
    write_table(
        ws, 1, headers, out_rows, column_widths=widths, column_formats=formats,
        as_excel_table=True, table_name_hint=title, used_table_names=used_table_names,
    )

    # Highlight negative values in currency/quantity columns — the same
    # condition services.documents.validate flags as a warning, made
    # visible directly on the data instead of only in prose elsewhere.
    offset = 1 if has_source_row else 0
    for i, column in enumerate(columns):
        if column.get('semantic_type') not in ('currency', 'quantity'):
            continue
        col_letter = ws.cell(row=1, column=offset + i + 1).column_letter
        cell_range = f'{col_letter}2:{col_letter}{1 + len(out_rows)}'
        ws.conditional_formatting.add(
            cell_range, CellIsRule(operator='lessThan', formula=['0'], fill=_NEGATIVE_FILL),
        )


def _sheet_overview(wb: Workbook, document: dict) -> None:
    ws = wb.create_sheet('OVERVIEW', 0)
    _safe_cell(ws, 1, 1, document.get('filename') or 'Document').font = TITLE_FONT
    ws.merge_cells('A1:B1')

    _safe_cell(ws, 2, 1, f"Document type: {document.get('document_type') or 'General dataset'}").font = SUBTITLE_FONT
    ws.merge_cells('A2:B2')

    row = 4
    datasets = document.get('datasets', [])
    if datasets:
        ws.cell(row=row, column=1, value='DATASETS').font = LABEL_FONT
        row += 1
        ws.cell(row=row, column=1, value='Name')
        ws.cell(row=row, column=2, value='Records')
        row += 1
        for dataset in datasets:
            _safe_cell(ws, row, 1, dataset.get('name'))
            ws.cell(row=row, column=2, value=dataset.get('row_count', 0))
            row += 1
        row += 1

    metrics = document.get('metrics', [])
    if metrics:
        ws.cell(row=row, column=1, value='KEY METRICS').font = LABEL_FONT
        row += 1
        for metric in metrics:
            _safe_cell(ws, row, 1, metric.get('label'))
            cell = ws.cell(row=row, column=2, value=metric.get('value'))
            if isinstance(metric.get('value'), (int, float)) and metric.get('format_hint') != 'number':
                cell.number_format = _NUMERIC_FORMATS.get(metric.get('format_hint'), FMT_DECIMAL)
            if metric.get('validation_status') == 'partial':
                note = ws.cell(row=row, column=3, value=(
                    f"{metric.get('excluded_row_count', 0)} row(s) excluded (unparseable/missing value)"
                ))
                note.font = Font(italic=True, color='8A6300')
            row += 1
        row += 1

    insights = document.get('insights', [])
    if insights:
        ws.cell(row=row, column=1, value='INSIGHTS').font = LABEL_FONT
        row += 1
        for insight in insights:
            _safe_cell(ws, row, 1, insight)
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            row += 1
        row += 1

    entities = document.get('entities') or {}
    if any(entities.get(k) for k in ('numbers', 'dates', 'keywords')):
        ws.cell(row=row, column=1, value='FOUND IN TEXT').font = LABEL_FONT
        row += 1
        for label, key in (('Numbers mentioned', 'numbers'), ('Dates mentioned', 'dates'), ('Frequent terms', 'keywords')):
            values = entities.get(key) or []
            if values:
                ws.cell(row=row, column=1, value=label)
                _safe_cell(ws, row, 2, ', '.join(values))
                row += 1

    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 60


def _sheet_source(wb: Workbook, sections: List[dict]) -> None:
    if not sections:
        return
    ws = wb.create_sheet('SOURCE TEXT')
    headers = ['SECTION', 'CONTENT']
    rows = [[s.get('title') or '', s.get('content') or ''] for s in sections]
    write_table(ws, 1, headers, rows, column_widths=[28, 100])
    for row_idx in range(2, len(rows) + 2):
        ws.cell(row=row_idx, column=2).alignment = Alignment(wrap_text=True, vertical='top')


def _fmt_datetime(value) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M:%S UTC')
    return str(value)


def _sheet_source_metadata(wb: Workbook, document: dict, report_meta: Optional[dict]) -> None:
    """A single place answering "where did this workbook come from, and
    when" — the original file, when it was uploaded/processed/exported, and
    which source location backs each dataset — so the workbook stands on
    its own as an audit record, not just a snapshot of the dashboard."""
    report_meta = report_meta or {}
    ws = wb.create_sheet('SOURCE METADATA')
    ws['A1'] = 'SOURCE METADATA'
    ws['A1'].font = TITLE_FONT

    issue_count = len(document.get('validation_issues') or report_meta.get('warnings') or [])
    fields = [
        ('Original filename', document.get('filename')),
        ('Source format', (document.get('source_type') or '').upper()),
        ('Detected document type', document.get('document_type')),
        ('Document type confidence', document.get('document_type_confidence')),
        ('Report ID', report_meta.get('report_id')),
        ('Uploaded at', _fmt_datetime(report_meta.get('created_at'))),
        ('Processed at', _fmt_datetime(report_meta.get('processed_at'))),
        ('Workbook generated at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('Datasets extracted', len(document.get('datasets', []))),
        ('Total records (all datasets)', sum(d.get('row_count', 0) for d in document.get('datasets', []))),
        ('Validation issues raised', issue_count),
    ]
    row = 3
    for label, value in fields:
        ws.cell(row=row, column=1, value=label).font = LABEL_FONT
        _safe_cell(ws, row, 2, value)
        row += 1

    datasets = document.get('datasets', [])
    if datasets:
        row += 1
        ws.cell(row=row, column=1, value='DATASET SOURCES').font = LABEL_FONT
        row += 1
        ws.cell(row=row, column=1, value='Dataset').font = LABEL_FONT
        ws.cell(row=row, column=2, value='Source location').font = LABEL_FONT
        row += 1
        for dataset in datasets:
            _safe_cell(ws, row, 1, dataset.get('name'))
            _safe_cell(ws, row, 2, dataset.get('source'))
            row += 1

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 50


def _sheet_data_dictionary(wb: Workbook, document: dict, used_table_names: set) -> None:
    """What every extracted column was inferred to *mean* — semantic type,
    confidence, and completeness — so a value's format on a dataset sheet
    (a date, a currency amount, a percentage) can always be explained
    rather than taken on faith."""
    datasets = document.get('datasets', [])
    if not datasets:
        return
    ws = wb.create_sheet('DATA DICTIONARY')
    headers = ['Dataset', 'Column', 'Semantic Type', 'Data Type', 'Confidence', 'Non-Null', 'Total', 'Sample Values']
    rows = []
    for dataset in datasets:
        for column in dataset.get('columns', []):
            rows.append([
                dataset.get('name'),
                column.get('display_name'),
                column.get('semantic_type'),
                column.get('data_type'),
                column.get('confidence'),
                column.get('non_null_count'),
                column.get('total_count'),
                ', '.join(str(v) for v in (column.get('sample_values') or [])),
            ])
    write_table(
        ws, 1, headers, rows, column_widths=[22, 24, 16, 12, 12, 10, 10, 44],
        as_excel_table=True, table_name_hint='DataDictionary', used_table_names=used_table_names,
    )


def _sheet_validation_issues(wb: Workbook, issues: List[dict]) -> None:
    """Every data-quality concern raised while validating this document,
    with its severity — kept alongside the data itself, not just shown once
    on the dashboard, so a reviewer working from the spreadsheet alone still
    sees them, color-coded by how serious each one is."""
    if not issues:
        return
    ws = wb.create_sheet('VALIDATION ISSUES')
    headers = ['#', 'Severity', 'Dataset', 'Column', 'Rule', 'Issue', 'Suggested action']
    rows = [
        [i, issue.get('severity'), issue.get('dataset') or '', issue.get('column') or '',
         issue.get('rule_id'), issue.get('message'), issue.get('suggested_action') or '']
        for i, issue in enumerate(issues, start=1)
    ]
    write_table(ws, 1, headers, rows, column_widths=[5, 10, 22, 20, 20, 70, 45])
    for row_idx, issue in enumerate(issues, start=2):
        severity = issue.get('severity')
        fill = _SEVERITY_FILL.get(severity)
        font = _SEVERITY_FONT.get(severity)
        if fill:
            ws.cell(row=row_idx, column=2).fill = fill
        if font:
            ws.cell(row=row_idx, column=2).font = font
        ws.cell(row=row_idx, column=6).alignment = Alignment(wrap_text=True, vertical='top')
        ws.cell(row=row_idx, column=7).alignment = Alignment(wrap_text=True, vertical='top')


def _sheet_reconciliation(wb: Workbook, document: dict) -> None:
    """Per-dataset accounting of raw rows in vs. rows out (never a
    black box: blank rows skipped and exact-duplicate rows are both
    reported, not just silently absorbed) plus any total-vs-itemized
    mismatch findings raised during validation."""
    datasets = document.get('datasets', [])
    issues = document.get('validation_issues') or []
    if not datasets:
        return
    ws = wb.create_sheet('RECONCILIATION')

    ws.cell(row=1, column=1, value='ROW COUNT RECONCILIATION').font = LABEL_FONT
    headers = ['Dataset', 'Raw rows (incl. header)', 'Blank rows skipped', 'Records extracted', 'Of which exact duplicates (kept)']
    rows = [
        [
            d.get('name'),
            d.get('row_count', 0) + d.get('blank_rows_skipped', 0) + 1,
            d.get('blank_rows_skipped', 0),
            d.get('row_count', 0),
            d.get('duplicate_row_count', 0),
        ]
        for d in datasets
    ]
    next_row = write_table(ws, 2, headers, rows, column_widths=[24, 22, 18, 18, 18])

    total_issues = [i for i in issues if i.get('rule_id') == 'total_mismatch']
    if total_issues:
        next_row += 2
        ws.cell(row=next_row, column=1, value='TOTAL RECONCILIATION').font = LABEL_FONT
        next_row += 1
        t_headers = ['Dataset', 'Column', 'Reported total', 'Finding']
        t_rows = [
            [i.get('dataset'), i.get('column'), i.get('value'), i.get('message')]
            for i in total_issues
        ]
        write_table(ws, next_row, t_headers, t_rows, column_widths=[22, 20, 18, 90], freeze_header=False)


def _sheet_raw_extracted_data(wb: Workbook, datasets: List[dict]) -> None:
    """Every dataset's values exactly as extracted — cleaned of surrounding
    whitespace only, never coerced to a number/date/None the way the
    per-dataset normalized sheets are — stacked one table per dataset on a
    single sheet so the normalized and raw views can be compared side by
    side without hunting across many sheets."""
    datasets_with_rows = [d for d in datasets if d.get('columns') and d.get('rows')]
    if not datasets_with_rows:
        return
    ws = wb.create_sheet('RAW EXTRACTED DATA')
    row = 1
    for dataset in datasets_with_rows:
        columns = dataset['columns']
        rows = dataset['rows']
        ws.cell(row=row, column=1, value=dataset.get('name')).font = LABEL_FONT
        row += 1
        headers = [c['display_name'] for c in columns]
        raw_rows = [[clean_text(r.get(c['name'])) for c in columns] for r in rows]
        widths = [max(12, min(40, len(h) + 2)) for h in headers]
        row = write_table(ws, row, headers, raw_rows, column_widths=widths, freeze_header=False) + 1


def generate_generic_excel(document: dict, output_path: str, report_meta: Optional[dict] = None) -> str:
    """Generate the Excel workbook for a validated generic Document.

    ``report_meta`` — an optional ``{report_id, created_at, processed_at,
    warnings}`` dict supplied by the caller (see reports.views) — is purely
    additive context for the SOURCE METADATA sheet; the workbook is still
    fully generated without it.
    """
    wb = Workbook()
    wb.remove(wb.active)
    used_table_names: set = set()

    _sheet_overview(wb, document)
    _sheet_source_metadata(wb, document, report_meta)
    _sheet_data_dictionary(wb, document, used_table_names)
    _sheet_validation_issues(wb, document.get('validation_issues') or [])
    _sheet_reconciliation(wb, document)

    used_titles = {'overview', 'source metadata', 'data dictionary', 'validation issues', 'reconciliation'}
    for dataset in document.get('datasets', []):
        _sheet_for_dataset(wb, dataset, used_titles, used_table_names)

    _sheet_raw_extracted_data(wb, document.get('datasets', []))
    _sheet_source(wb, document.get('sections', []))

    wb.save(output_path)
    return output_path
