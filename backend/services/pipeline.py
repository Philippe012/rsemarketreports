from __future__ import annotations

import hashlib
import os
from typing import Optional

from services.documents.generic_parser import (
    parse_csv_document,
    parse_docx_document,
    parse_excel_document,
    parse_json_document,
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
from services.extraction.json_extractor import JsonExtractionError, extract_json
from services.extraction.pdf_extractor import PdfExtractionError, extract_pdf
from services.extraction.txt_extractor import TxtExtractionError, extract_txt
from services.normalization.validate_data import ReportValidationError
from services.parsers.rse_parser import build_report, is_rse_report

SOURCE_TYPE_PDF = 'pdf'
SOURCE_TYPE_EXCEL = 'excel'
SOURCE_TYPE_CSV = 'csv'
SOURCE_TYPE_DOCX = 'docx'
SOURCE_TYPE_TXT = 'txt'
SOURCE_TYPE_JSON = 'json'

GENERIC_ONLY_TYPES = {SOURCE_TYPE_CSV, SOURCE_TYPE_DOCX, SOURCE_TYPE_TXT, SOURCE_TYPE_JSON}

PDF_EXTENSIONS = {'.pdf'}
EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}
CSV_EXTENSIONS = {'.csv'}
DOCX_EXTENSIONS = {'.docx'}
TXT_EXTENSIONS = {'.txt'}
JSON_EXTENSIONS = {'.json', '.jsonl', '.ndjson'}

_EXTRACTORS = {
    SOURCE_TYPE_CSV: (extract_csv, lambda extraction, name, path: parse_csv_document(extraction.rows, name)),
    SOURCE_TYPE_DOCX: (extract_docx, lambda extraction, name, path: parse_docx_document(extraction, name, path)),
    SOURCE_TYPE_TXT: (extract_txt, lambda extraction, name, path: parse_txt_document(extraction, name)),
    SOURCE_TYPE_JSON: (extract_json, lambda extraction, name, path: parse_json_document(extraction, name)),
}


class UnsupportedFileType(Exception):
    pass


def compute_upload_hash(upload) -> str:
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return digest.hexdigest()


_ZIP_OR_OLE_SIGNATURES = (b'PK\x03\x04', b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
_SIGNATURE_CHECKS = {
    SOURCE_TYPE_PDF: lambda head: head.startswith(b'%PDF-'),
    SOURCE_TYPE_EXCEL: lambda head: head.startswith(_ZIP_OR_OLE_SIGNATURES),
    SOURCE_TYPE_DOCX: lambda head: head.startswith(b'PK\x03\x04'),
}


def verify_upload_signature(source_type: str, upload) -> Optional[str]:
    check = _SIGNATURE_CHECKS.get(source_type)
    if not check:
        return None
    head = upload.read(8)
    upload.seek(0)
    if not check(head):
        return (
            f'This file\'s content doesn\'t match a {source_type.upper()} file, even though its name '
            f'suggests one — it may have been renamed, corrupted, or is a different format entirely.'
        )
    return None


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
    if ext in JSON_EXTENSIONS:
        return SOURCE_TYPE_JSON
    raise UnsupportedFileType(
        f'Unsupported file type "{ext}". Please upload a PDF, Excel (.xlsx/.xls), Word (.docx), '
        f'CSV, TXT, or JSON (.json/.jsonl) document.'
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


def export_report_excel(data: dict, output_path: str, report_meta: Optional[dict] = None) -> str:
    if data.get('kind') == 'generic_document':
        return generate_generic_excel(data, output_path, report_meta=report_meta)
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
    'JsonExtractionError',
    'ReportValidationError',
]
