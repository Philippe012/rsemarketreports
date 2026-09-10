"""CSV extraction. Returns raw rows (list of lists) exactly like
excel_extractor's single-sheet output — deliberately the same shape so the
generic document parser can treat a CSV file as "a workbook with one sheet"
without any special-casing.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import List

from services.normalization.clean_data import is_blank_row

RowList = List[List]


class CsvExtractionError(Exception):
    """Raised when a CSV file cannot be read or contains no data."""


@dataclass
class CsvExtractionResult:
    rows: RowList = field(default_factory=list)


def _decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def extract_csv(file_path: str) -> CsvExtractionResult:
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
    except OSError as exc:
        raise CsvExtractionError(f'Unable to read the CSV file: {exc}') from exc

    if not raw.strip():
        raise CsvExtractionError('The CSV file is empty.')

    text = _decode(raw)

    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t|')
    except csv.Error:
        dialect = csv.excel  # default comma-separated

    reader = csv.reader(io.StringIO(text), dialect)
    rows: RowList = [list(row) for row in reader]

    while rows and is_blank_row(rows[-1]):
        rows.pop()

    if not rows:
        raise CsvExtractionError('The CSV file does not contain any data.')

    return CsvExtractionResult(rows=rows)
