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

from typing import List, Optional

import pandas as pd

from services.extraction.docx_extractor import DocxExtractionResult
from services.extraction.excel_extractor import ExcelExtractionResult
from services.extraction.pdf_extractor import PdfExtractionResult
from services.normalization.clean_data import clean_text, is_blank_row

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
    if it isn't shaped like real tabular data (too few columns/rows)."""
    rows = [r for r in table if not is_blank_row(r)]
    if len(rows) < 1 + MIN_DATA_ROWS_FOR_DATASET:
        return None

    header_row, *data_rows = rows
    headers = _dedupe_headers(header_row)
    if len([h for h in header_row if clean_text(h) is not None]) < MIN_COLUMNS_FOR_DATASET:
        return None

    row_dicts = []
    for raw_row in data_rows:
        if is_blank_row(raw_row):
            continue
        row_dicts.append({
            headers[i]: raw_row[i] if i < len(raw_row) else None
            for i in range(len(headers))
        })
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

    return make_dataset(name, source, columns, row_dicts, duplicate_row_count=duplicate_row_count)


def _finalize(document: dict) -> dict:
    """Run the Pydantic structural-validation stage before handing the
    Document back to the pipeline."""
    return validate_document_shape(document)


def _sections_text(sections: List[dict]) -> str:
    return '\n'.join(s['content'] for s in sections if s.get('content'))


def parse_pdf_document(extraction: PdfExtractionResult, filename: str, file_path: Optional[str] = None) -> dict:
    datasets = []
    sections = []

    for page_index, (page_text, page_tables) in enumerate(zip(extraction.pages_text, extraction.pages_tables), start=1):
        for table_index, table in enumerate(page_tables, start=1):
            dataset_name = f'Table {len(datasets) + 1} (page {page_index})'
            dataset = _table_to_dataset(dataset_name, f'PDF page {page_index}, table {table_index}', table)
            if dataset:
                datasets.append(dataset)

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

    return _finalize(make_document(
        filename, 'pdf', document_type, confidence, sections, datasets, metrics, charts,
        figures=figures, insights=insights, entities=entities,
    ))


def parse_excel_document(extraction: ExcelExtractionResult, filename: str) -> dict:
    datasets = []
    for sheet_name, rows in extraction.sheets.items():
        dataset = _table_to_dataset(sheet_name, f'Sheet: {sheet_name}', rows)
        if dataset:
            datasets.append(dataset)

    document_type, confidence = classify_document(datasets)
    metrics = compute_metrics(datasets)
    charts = suggest_charts(datasets)
    insights = compute_insights(datasets)

    return _finalize(make_document(
        filename, 'excel', document_type, confidence, [], datasets, metrics, charts,
        insights=insights,
    ))


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
