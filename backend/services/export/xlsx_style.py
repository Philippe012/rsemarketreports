"""Shared openpyxl styling primitives used by every Excel export (the RSE
exporter and the generic-document exporter alike), so both pipelines produce
visually consistent, professionally formatted workbooks from one place.
"""
from __future__ import annotations

from typing import List, Optional

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

HEADER_FILL = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
HEADER_FONT = Font(color='FFFFFF', bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color='1E3A5F')
SUBTITLE_FONT = Font(italic=True, size=10, color='666666')
LABEL_FONT = Font(bold=True)
THIN_BORDER = Border(bottom=Side(style='thin', color='D9D9D9'))
ALT_FILL = PatternFill(start_color='F4F7FB', end_color='F4F7FB', fill_type='solid')

# Coupon/yield/percent-change values are stored as percentage points (13.5
# meaning "13.5%"), not fractions, so a literal "%" suffix format is used
# instead of Excel's native percentage format (which would multiply by 100
# and show "1350%").
FMT_INTEGER = '#,##0'
FMT_DECIMAL = '#,##0.00'
FMT_PRICE = '#,##0.000'
FMT_PERCENT = '0.00"%"'
FMT_DATE = 'dd-mmm-yyyy'


def write_header_row(ws: Worksheet, row: int, headers: List[str]) -> None:
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[row].height = 22


def write_table(
    ws: Worksheet,
    start_row: int,
    headers: List[str],
    rows: List[list],
    column_widths: Optional[List[int]] = None,
    column_formats: Optional[List[Optional[str]]] = None,
    freeze_header: bool = True,
) -> int:
    """Write a header row + data rows starting at ``start_row``.

    ``freeze_header`` should be left ``True`` only for the first (or only)
    table on a sheet — freeze panes are a sheet-level setting, so a second
    call on the same sheet would otherwise silently move the freeze down to
    that table's header instead of the top of the sheet.
    """
    write_header_row(ws, start_row, headers)
    for i, row_values in enumerate(rows):
        row_idx = start_row + 1 + i
        for col, value in enumerate(row_values, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.border = THIN_BORDER
            if i % 2 == 1:
                cell.fill = ALT_FILL
            fmt = column_formats[col - 1] if column_formats and col - 1 < len(column_formats) else None
            if fmt and isinstance(value, (int, float)):
                cell.number_format = fmt
            elif fmt == FMT_DATE and value is not None:
                cell.number_format = fmt
    widths = column_widths or [max(14, len(h) + 2) for h in headers]
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width
    if freeze_header:
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    return start_row + 1 + len(rows)


def safe_sheet_title(name: str, used: set) -> str:
    """Excel sheet names: max 31 chars, no []:*?/\\, and must be unique."""
    cleaned = ''.join(c for c in name if c not in '[]:*?/\\') or 'Sheet'
    cleaned = cleaned[:31]
    candidate = cleaned
    suffix = 2
    while candidate.lower() in used:
        candidate = f'{cleaned[:28]} {suffix}'
        suffix += 1
    used.add(candidate.lower())
    return candidate
