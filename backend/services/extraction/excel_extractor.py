from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import openpyxl

from services.normalization.clean_data import is_blank_row

SheetRows = List[List]


class ExcelExtractionError(Exception):
    """Raised when a workbook cannot be opened or contains no sheets/data."""


@dataclass
class ExcelExtractionResult:
    sheets: Dict[str, SheetRows] = field(default_factory=dict)


def extract_excel(file_path: str) -> ExcelExtractionResult:
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    except Exception as exc:  # noqa: BLE001
        raise ExcelExtractionError(f'Unable to read the Excel file: {exc}') from exc

    if not workbook.sheetnames:
        raise ExcelExtractionError('The workbook contains no worksheets.')

    sheets: Dict[str, SheetRows] = {}
    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
        rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
        while rows and is_blank_row(rows[-1]):
            rows.pop()
        sheets[sheet_name] = rows

    if not any(sheets.values()):
        raise ExcelExtractionError('The workbook does not contain any data.')

    return ExcelExtractionResult(sheets=sheets)
