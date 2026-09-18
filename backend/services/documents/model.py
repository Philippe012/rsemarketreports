"""The universal data model for the generic document-intelligence pipeline.

Every non-RSE document (and, conceptually, RSE ones too — they just use a
more specific schema built by services.parsers.rse_parser instead) is
represented as a plain JSON-serializable ``Document`` dict built from these
constructors:

    Document
    ├── sections   [{title, content}]            free-text narrative found in the doc
    └── datasets   [Dataset]                      every table-shaped block found
            ├── columns [Column]                  semantic metadata per column
            └── rows    [{column_name: value}]

Everything here is plain dicts rather than classes, matching the style
already used by the RSE schema (services.parsers.rse_parser) — there is
no behavioural reason to introduce a second modelling paradigm.
"""
from __future__ import annotations

from typing import List, Optional

# Semantic types a column can be classified as. Deliberately small and
# concrete — see services.documents.schema_inference for how a column is
# assigned one of these.
SEMANTIC_TYPES = (
    'identifier', 'category', 'date', 'datetime', 'number',
    'currency', 'percentage', 'quantity', 'text', 'boolean',
)


def make_column(
    name: str,
    display_name: str,
    semantic_type: str,
    data_type: str,
    non_null_count: int,
    total_count: int,
    sample_values: List,
    confidence: str = 'medium',
) -> dict:
    return {
        'name': name,
        'display_name': display_name,
        'semantic_type': semantic_type,
        'data_type': data_type,
        'nullable': non_null_count < total_count,
        'non_null_count': non_null_count,
        'total_count': total_count,
        'confidence': confidence,
        'sample_values': sample_values[:5],
        'stats': None,
    }


def make_dataset(
    name: str, source: str, columns: List[dict], rows: List[dict], duplicate_row_count: int = 0,
    blank_rows_skipped: int = 0,
) -> dict:
    return {
        'name': name,
        'source': source,
        'columns': columns,
        'rows': rows,
        'row_count': len(rows),
        'duplicate_row_count': duplicate_row_count,
        # Rows present in the originally extracted table but skipped because
        # every cell in them was blank — never a *data* loss (there was
        # nothing to keep), but reported so "raw rows in vs. rows out" always
        # reconciles instead of quietly shrinking.
        'blank_rows_skipped': blank_rows_skipped,
    }


def make_metric(
    label: str, value, dataset: str, column: str, kind: str, format_hint: str = 'number',
    calculation_method: str = 'row_count', included_count: int = 0, excluded_count: int = 0,
) -> dict:
    return {
        'label': label,
        'value': value,
        'dataset': dataset,
        'column': column,
        'kind': kind,
        'format_hint': format_hint,  # 'number' | 'currency' | 'percentage' | 'quantity'
        # How the value was actually derived, and over how many of the
        # dataset's rows — e.g. a "Total Revenue" of 40,875,000 computed
        # over 11 of 12 rows (one had an unparseable value) is a different,
        # more auditable claim than a bare number with no accounting for
        # the row that didn't count.
        'calculation_method': calculation_method,
        'included_row_count': included_count,
        'excluded_row_count': excluded_count,
        'validation_status': 'ok' if excluded_count == 0 else 'partial',
    }


def make_chart(dataset: str, chart_type: str, x: str, y: str, title: str) -> dict:
    return {
        'dataset': dataset,
        'chart_type': chart_type,  # 'line' | 'bar' | 'pie'
        'x': x,
        'y': y,
        'title': title,
    }


def make_document(
    filename: str,
    source_type: str,
    document_type: str,
    document_type_confidence: str,
    sections: List[dict],
    datasets: List[dict],
    metrics: List[dict],
    charts: List[dict],
    figures: Optional[List[dict]] = None,
    insights: Optional[List[str]] = None,
    entities: Optional[dict] = None,
) -> dict:
    return {
        'kind': 'generic_document',
        'filename': filename,
        'source_type': source_type,
        'document_type': document_type,
        'document_type_confidence': document_type_confidence,
        'sections': sections,
        'datasets': datasets,
        'metrics': metrics,
        'charts': charts,
        'figures': figures or [],
        'insights': insights or [],
        'entities': entities or make_entities([], [], []),
    }


def make_section(title: Optional[str], content: str) -> dict:
    return {'title': title, 'content': content}


def make_figure(source: str, width: Optional[int], height: Optional[int], image_format: str, thumbnail: Optional[str]) -> dict:
    """An embedded image found in the document (a chart, a photo, a diagram).
    Never interpreted — no chart values are read out of the pixels — just
    surfaced with a small thumbnail and where it came from."""
    return {
        'source': source,
        'width': width,
        'height': height,
        'format': image_format,
        'thumbnail': thumbnail,
    }


def make_entities(numbers: List[str], dates: List[str], keywords: List[str]) -> dict:
    """Numbers, dates, and frequently-mentioned terms lifted verbatim from
    the document's prose — see services.documents.entities."""
    return {'numbers': numbers, 'dates': dates, 'keywords': keywords}
