"""Builds the downloadable Excel workbook for a generic (non-RSE) Document —
one worksheet per extracted dataset, using the same styling as the RSE
exporter (see xlsx_style.py) so both pipelines produce a consistent-looking
workbook. Exports the full validated dataset, not just what happens to be
visible on screen.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment

from services.normalization.clean_data import parse_date, parse_number

from .xlsx_style import FMT_DATE, FMT_DECIMAL, FMT_INTEGER, FMT_PERCENT, LABEL_FONT, SUBTITLE_FONT, TITLE_FONT, safe_sheet_title, write_table

_NUMERIC_FORMATS = {
    'currency': FMT_DECIMAL,
    'quantity': FMT_INTEGER,
    'number': FMT_DECIMAL,
    'percentage': FMT_PERCENT,
}


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


def _sheet_for_dataset(wb: Workbook, dataset: dict, used_titles: set) -> None:
    columns = dataset.get('columns', [])
    rows = dataset.get('rows', [])
    if not columns or not rows:
        return

    title = safe_sheet_title(dataset.get('name') or 'Dataset', used_titles)
    ws = wb.create_sheet(title)

    headers = [c['display_name'] for c in columns]
    formats: List[Optional[str]] = []
    out_rows = []
    for row in rows:
        out_row = []
        row_formats = []
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

    widths = [max(12, min(40, len(h) + 2)) for h in headers]
    write_table(ws, 1, headers, out_rows, column_widths=widths, column_formats=formats)


def _sheet_overview(wb: Workbook, document: dict) -> None:
    ws = wb.create_sheet('OVERVIEW', 0)
    ws['A1'] = document.get('filename') or 'Document'
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:B1')

    ws['A2'] = f"Document type: {document.get('document_type') or 'General dataset'}"
    ws['A2'].font = SUBTITLE_FONT
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
            ws.cell(row=row, column=1, value=dataset.get('name'))
            ws.cell(row=row, column=2, value=dataset.get('row_count', 0))
            row += 1
        row += 1

    metrics = document.get('metrics', [])
    if metrics:
        ws.cell(row=row, column=1, value='KEY METRICS').font = LABEL_FONT
        row += 1
        for metric in metrics:
            ws.cell(row=row, column=1, value=metric.get('label'))
            cell = ws.cell(row=row, column=2, value=metric.get('value'))
            if isinstance(metric.get('value'), (int, float)) and metric.get('format_hint') != 'number':
                cell.number_format = _NUMERIC_FORMATS.get(metric.get('format_hint'), FMT_DECIMAL)
            row += 1
        row += 1

    insights = document.get('insights', [])
    if insights:
        ws.cell(row=row, column=1, value='INSIGHTS').font = LABEL_FONT
        row += 1
        for insight in insights:
            ws.cell(row=row, column=1, value=insight)
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
                ws.cell(row=row, column=2, value=', '.join(values))
                row += 1

    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 60


def _sheet_source(wb: Workbook, sections: List[dict]) -> None:
    if not sections:
        return
    ws = wb.create_sheet('SOURCE')
    headers = ['SECTION', 'CONTENT']
    rows = [[s.get('title') or '', s.get('content') or ''] for s in sections]
    write_table(ws, 1, headers, rows, column_widths=[28, 100])
    for row_idx in range(2, len(rows) + 2):
        ws.cell(row=row_idx, column=2).alignment = Alignment(wrap_text=True, vertical='top')


def generate_generic_excel(document: dict, output_path: str) -> str:
    """Generate the Excel workbook for a validated generic Document."""
    wb = Workbook()
    wb.remove(wb.active)

    _sheet_overview(wb, document)

    used_titles = {'overview'}
    for dataset in document.get('datasets', []):
        _sheet_for_dataset(wb, dataset, used_titles)

    _sheet_source(wb, document.get('sections', []))

    wb.save(output_path)
    return output_path
