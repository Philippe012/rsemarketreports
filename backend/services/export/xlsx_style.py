"""Shared openpyxl styling primitives used by every Excel export (the RSE
exporter and the generic-document exporter alike), so both pipelines produce
visually consistent, professionally formatted workbooks from one place.
"""
from __future__ import annotations

from typing import List, Optional, Set

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

# A string cell whose content starts with one of these is at risk of being
# evaluated as a formula (or, if the sheet is later re-exported as CSV and
# reopened, of classic "CSV/formula injection") — since every cell here can
# ultimately come from attacker-controlled uploaded-document content (a
# category value, a sample value, a filename), every such cell written
# anywhere in this module is neutralized. openpyxl itself only *writes* a
# leading "=" as an evaluated formula (confirmed: assigning a string that
# starts with "=" to Cell.value sets data_type to "f" automatically), so
# without this, an uploaded document containing e.g. a cell that reads
# ``=HYPERLINK("http://evil","click")`` would become a live, evaluated
# formula in the workbook this system hands back to the user.
_FORMULA_TRIGGER_CHARS = ('=', '+', '-', '@')


def neutralize_formula_injection(cell) -> None:
    """Forces a cell holding attacker-controlled text back to a plain
    string type if openpyxl would otherwise treat it as a formula — see the
    module-level note above. Safe to call on every cell unconditionally."""
    if isinstance(cell.value, str) and cell.value.startswith(_FORMULA_TRIGGER_CHARS):
        cell.data_type = 's'


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
        neutralize_formula_injection(cell)
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
    as_excel_table: bool = False,
    table_name_hint: Optional[str] = None,
    used_table_names: Optional[Set[str]] = None,
) -> int:
    """Write a header row + data rows starting at ``start_row``.

    ``freeze_header`` should be left ``True`` only for the first (or only)
    table on a sheet — freeze panes are a sheet-level setting, so a second
    call on the same sheet would otherwise silently move the freeze down to
    that table's header instead of the top of the sheet.

    ``as_excel_table=True`` additionally registers the range as a real
    openpyxl/Excel ``Table`` object (banded rows, a named range Excel's own
    UI recognizes as "a table") rather than just an autofilter — reserved
    for callers that control a whole, single-table sheet (multi-table
    sheets, like the RSE exporter's, keep the plain autofilter behavior
    instead, since Excel Tables cannot overlap and this helper has no view
    of the other tables sharing that sheet). Skipped automatically when
    there are zero data rows, since Excel requires a table to have at least
    one.
    """
    write_header_row(ws, start_row, headers)
    for i, row_values in enumerate(rows):
        row_idx = start_row + 1 + i
        for col, value in enumerate(row_values, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            neutralize_formula_injection(cell)
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

    end_row = start_row + len(rows)
    last_col_letter = get_column_letter(len(headers))
    table_ref = f'A{start_row}:{last_col_letter}{end_row}'

    if as_excel_table and rows:
        table = Table(displayName=_safe_table_name(table_name_hint or ws.title, used_table_names), ref=table_ref)
        table.tableStyleInfo = TableStyleInfo(
            name='TableStyleMedium2', showRowStripes=True, showFirstColumn=False,
        )
        ws.add_table(table)
        if freeze_header:
            ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    elif freeze_header:
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
        ws.auto_filter.ref = table_ref
    return start_row + 1 + len(rows)


def _safe_table_name(hint: str, used: Optional[Set[str]]) -> str:
    """Excel Table names must be unique per workbook, start with a letter or
    underscore, and contain only letters/digits/underscores."""
    cleaned = ''.join(c if c.isalnum() else '_' for c in hint) or 'Table'
    if cleaned[0].isdigit():
        cleaned = f'T_{cleaned}'
    cleaned = cleaned[:200]
    if used is None:
        return cleaned
    candidate, suffix = cleaned, 2
    while candidate in used:
        candidate = f'{cleaned}_{suffix}'
        suffix += 1
    used.add(candidate)
    return candidate


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
