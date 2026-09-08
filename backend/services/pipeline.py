import os

from services.export.excel_exporter import generate_excel
from services.extraction.excel_extractor import ExcelExtractionError, extract_excel
from services.extraction.pdf_extractor import PdfExtractionError, extract_pdf
from services.normalization.validate_data import ReportValidationError
from services.parsers.rse_parser import build_report

SOURCE_TYPE_PDF = 'pdf'
SOURCE_TYPE_EXCEL = 'excel'

PDF_EXTENSIONS = {'.pdf'}
EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}


class UnsupportedFileType(Exception):
    pass


def detect_source_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in PDF_EXTENSIONS:
        return SOURCE_TYPE_PDF
    if ext in EXCEL_EXTENSIONS:
        return SOURCE_TYPE_EXCEL
    raise UnsupportedFileType(
        f'Unsupported file type "{ext}". Please upload a PDF or Excel (.xlsx) RSE report.'
    )


def process_report_file(file_path: str, original_filename: str) -> dict:
    source_type = detect_source_type(original_filename)

    if source_type == SOURCE_TYPE_PDF:
        extraction = extract_pdf(file_path)
    else:
        extraction = extract_excel(file_path)

    data, warnings = build_report(source_type, extraction, original_filename)

    return {'source_type': source_type, 'data': data, 'warnings': warnings}


def export_report_excel(data: dict, output_path: str) -> str:
    return generate_excel(data, output_path)


__all__ = [
    'process_report_file',
    'export_report_excel',
    'detect_source_type',
    'UnsupportedFileType',
    'PdfExtractionError',
    'ExcelExtractionError',
    'ReportValidationError',
]
