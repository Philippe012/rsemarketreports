"""Explain This: for a metric or chart already shown on the dashboard,
returns the literal calculation performed and the exact source rows used —
reusing the same aggregation semantics as
``services.documents.metrics.compute_metrics`` rather than re-deriving new
math, so the explanation can never drift from what is on screen.
"""
from __future__ import annotations

from typing import List, Optional

from services.normalization.clean_data import parse_number

MAX_SOURCE_ROWS = 20
_VERB = {'sum': 'Sum', 'average': 'Average', 'count': 'Count'}


def _find_dataset(datasets: List[dict], name: str) -> Optional[dict]:
    return next((d for d in datasets if d.get('name') == name), None)


def _find_column(dataset: dict, name: str) -> Optional[dict]:
    return next((c for c in (dataset.get('columns') or []) if c.get('name') == name), None)


def explain_metric(datasets: List[dict], dataset_name: str, column_name: str, kind: str) -> dict:
    dataset = _find_dataset(datasets, dataset_name)
    if dataset is None:
        return {'explanation': f'Dataset "{dataset_name}" was not found.', 'calculation': '', 'source_rows': []}

    if kind == 'count' or not column_name:
        rows = dataset.get('rows', [])
        return {
            'explanation': f'{len(rows)} record(s) in "{dataset_name}".',
            'calculation': f'count(rows) over "{dataset_name}".',
            'source_rows': rows[:MAX_SOURCE_ROWS],
        }

    column = _find_column(dataset, column_name)
    display_name = column.get('display_name') if column else column_name
    values_with_rows = []
    for row in dataset.get('rows', []):
        value = parse_number(row.get(column_name))
        if value is not None:
            values_with_rows.append((value, row))

    if not values_with_rows:
        return {
            'explanation': f'No numeric values were found for "{display_name}" in "{dataset_name}".',
            'calculation': '', 'source_rows': [],
        }

    verb = _VERB.get(kind, 'Aggregate')
    total = sum(v for v, _ in values_with_rows)
    aggregate = total / len(values_with_rows) if kind == 'average' else total

    return {
        'explanation': (
            f'{verb} of {len(values_with_rows)} non-null value(s) in "{display_name}" across '
            f'"{dataset_name}" = {aggregate:,.2f}.'
        ),
        'calculation': (
            f'{verb.lower()}({display_name}) over {len(values_with_rows)} of '
            f'{dataset.get("row_count", 0)} row(s) with a numeric value present.'
        ),
        'source_rows': [row for _, row in values_with_rows[:MAX_SOURCE_ROWS]],
    }


def explain_chart(datasets: List[dict], chart: dict) -> dict:
    dataset = _find_dataset(datasets, chart.get('dataset'))
    if dataset is None:
        return {'explanation': f'Dataset "{chart.get("dataset")}" was not found.', 'calculation': '', 'source_rows': []}

    x_name, y_name = chart.get('x'), chart.get('y')
    rows = [
        row for row in dataset.get('rows', [])
        if row.get(x_name) not in (None, '') and row.get(y_name) not in (None, '')
    ]
    return {
        'explanation': (
            f'"{chart.get("title")}" plots "{y_name}" against "{x_name}" using {len(rows)} of '
            f'{dataset.get("row_count", 0)} row(s) in "{dataset["name"]}" that have both values present.'
        ),
        'calculation': f'{chart.get("chart_type")} chart of {y_name} vs {x_name}.',
        'source_rows': rows[:MAX_SOURCE_ROWS],
    }
