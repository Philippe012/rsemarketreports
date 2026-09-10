"""Suggests chart types for datasets — but only when a chart would actually
help. A dataset with no date/category axis to plot against just becomes a
table; that is the correct outcome, not a fallback to apologize for.
"""
from __future__ import annotations

from typing import List, Optional

from .model import make_chart

MAX_CATEGORY_CARDINALITY = 12
MAX_PIE_CARDINALITY = 6


def _first_column_of_type(columns: List[dict], semantic_types) -> Optional[dict]:
    for column in columns:
        if column.get('semantic_type') in semantic_types:
            return column
    return None


def suggest_charts(datasets: List[dict]) -> List[dict]:
    charts = []
    for dataset in datasets:
        columns = dataset.get('columns', [])
        rows = dataset.get('rows', [])
        if len(rows) < 2:
            continue

        measure = _first_column_of_type(columns, {'currency', 'number', 'quantity'})
        if not measure:
            continue

        date_col = _first_column_of_type(columns, {'date', 'datetime'})
        if date_col:
            charts.append(make_chart(
                dataset=dataset['name'], chart_type='line',
                x=date_col['name'], y=measure['name'],
                title=f'{measure["display_name"]} over {date_col["display_name"]}',
            ))
            continue

        category_col = next(
            (c for c in columns if c.get('semantic_type') == 'category'
             and 1 < len(set(str(r.get(c['name'])) for r in rows)) <= MAX_CATEGORY_CARDINALITY),
            None,
        )
        if category_col:
            unique_categories = len(set(str(r.get(category_col['name'])) for r in rows))
            chart_type = 'pie' if unique_categories <= MAX_PIE_CARDINALITY else 'bar'
            charts.append(make_chart(
                dataset=dataset['name'], chart_type=chart_type,
                x=category_col['name'], y=measure['name'],
                title=f'{measure["display_name"]} by {category_col["display_name"]}',
            ))

    return charts
