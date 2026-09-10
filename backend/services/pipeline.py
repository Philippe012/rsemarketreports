"""Wires extraction -> parsing -> validation together for a single uploaded
document. Kept outside of Django views/models so the processing logic stays
framework-agnostic and unit-testable on its own.

Routing: a PDF or Excel file is first checked against a cheap, deterministic
RSE-market-report signature (services.parsers.rse_parser.is_rse_report). If
it matches, it runs through the specialized RSE pipeline that has existed
from the start of this project — full RSE domain knowledge, unchanged. If it
doesn't match — or the file is CSV/DOCX/TXT, none of which ever carry an RSE
report — it runs through the generic document-intelligence pipeline
(services.documents), which builds a Document of arbitrary datasets/
columns/metrics/charts instead of the RSE-shaped schema. Both pipelines are
validated with the same ReportValidationError, so the view layer needs no
branching, and neither one ever fails simply because a document "isn't RSE".
"""
from __future__ import annotations

import os

from services.documents.generic_parser import (
    parse_csv_document,
    parse_docx_document,
    parse_excel_document,
    parse_pdf_document,
    parse_txt_document,
)
from services.documents.rse_insights import compute_rse_insights
from services.documents.validate import validate_document
from services.export.excel_exporter import generate_excel
from services.export.generic_exporter import generate_generic_excel
from services.extraction.csv_extractor import CsvExtractionError, extract_csv
from services.extraction.docx_extractor import DocxExtractionError, extract_docx
from services.extraction.excel_extractor import ExcelExtractionError, extract_excel
from services.extraction.pdf_extractor import PdfExtractionError, extract_pdf
from services.extraction.txt_extractor import TxtExtractionError, extract_txt
from services.normalization.validate_data import ReportValidationError
from services.parsers.rse_parser import build_report, is_rse_report

SOURCE_TYPE_PDF = 'pdf'
SOURCE_TYPE_EXCEL = 'excel'
SOURCE_TYPE_CSV = 'csv'
SOURCE_TYPE_DOCX = 'docx'
SOURCE_TYPE_TXT = 'txt'

# Formats that can never be an RSE report (RSE always ships as PDF or Excel)
# and always route straight to the generic pipeline.
GENERIC_ONLY_TYPES = {SOURCE_TYPE_CSV, SOURCE_TYPE_DOCX, SOURCE_TYPE_TXT}

PDF_EXTENSIONS = {'.pdf'}
EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}
CSV_EXTENSIONS = {'.csv'}
DOCX_EXTENSIONS = {'.docx'}
TXT_EXTENSIONS = {'.txt'}

_EXTRACTORS = {
    SOURCE_TYPE_CSV: (extract_csv, lambda extraction, name, path: parse_csv_document(extraction.rows, name)),
    SOURCE_TYPE_DOCX: (extract_docx, lambda extraction, name, path: parse_docx_document(extraction, name, path)),
    SOURCE_TYPE_TXT: (extract_txt, lambda extraction, name, path: parse_txt_document(extraction, name)),
}


class UnsupportedFileType(Exception):
    pass


def detect_source_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in PDF_EXTENSIONS:
        return SOURCE_TYPE_PDF
    if ext in EXCEL_EXTENSIONS:
        return SOURCE_TYPE_EXCEL
    if ext in CSV_EXTENSIONS:
        return SOURCE_TYPE_CSV
    if ext in DOCX_EXTENSIONS:
        return SOURCE_TYPE_DOCX
    if ext in TXT_EXTENSIONS:
        return SOURCE_TYPE_TXT
    raise UnsupportedFileType(
        f'Unsupported file type "{ext}". Please upload a PDF, Excel (.xlsx), Word (.docx), CSV or TXT document.'
    )


def process_report_file(file_path: str, original_filename: str) -> dict:
    source_type = detect_source_type(original_filename)

    if source_type in GENERIC_ONLY_TYPES:
        extract_fn, parse_fn = _EXTRACTORS[source_type]
        extraction = extract_fn(file_path)
        document = parse_fn(extraction, original_filename, file_path)
        document, warnings = validate_document(document)
        return {'source_type': source_type, 'data': document, 'warnings': warnings}

    if source_type == SOURCE_TYPE_PDF:
        extraction = extract_pdf(file_path)
    else:
        extraction = extract_excel(file_path)

    if is_rse_report(source_type, extraction):
        data, warnings = build_report(source_type, extraction, original_filename)
        data['insights'] = compute_rse_insights(data)
        return {'source_type': source_type, 'data': data, 'warnings': warnings}

    if source_type == SOURCE_TYPE_PDF:
        document = parse_pdf_document(extraction, original_filename, file_path)
    else:
        document = parse_excel_document(extraction, original_filename)
    document, warnings = validate_document(document)
    return {'source_type': source_type, 'data': document, 'warnings': warnings}


def export_report_excel(data: dict, output_path: str) -> str:
    if data.get('kind') == 'generic_document':
        return generate_generic_excel(data, output_path)
    return generate_excel(data, output_path)


# Re-exported for convenience so views only need to import this module.
__all__ = [
    'process_report_file',
    'export_report_excel',
    'detect_source_type',
    'UnsupportedFileType',
    'PdfExtractionError',
    'ExcelExtractionError',
    'CsvExtractionError',
    'DocxExtractionError',
    'TxtExtractionError',
    'ReportValidationError',
]
