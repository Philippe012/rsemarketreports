"""Generates a small set of headline metrics (KPIs) from the extracted
datasets — sums for money/quantity columns, an average for percentage
columns. Every metric is a plain aggregate over real extracted values
(reusing the per-column stats schema_inference already computed with
NumPy); nothing is invented, and the count is capped so the dashboard shows
a handful of meaningful numbers rather than one for every column.
"""
from __future__ import annotations

from typing import List

from .model import make_metric

MAX_METRICS = 6
_AGGREGATABLE_TYPES = {'currency': 'sum', 'quantity': 'sum', 'number': 'sum', 'percentage': 'average'}
_FORMAT_HINT = {'currency': 'currency', 'quantity': 'quantity', 'number': 'number', 'percentage': 'percentage'}


def compute_metrics(datasets: List[dict]) -> List[dict]:
    metrics = []
    for dataset in datasets:
        rows = dataset.get('rows', [])
        if not rows:
            continue
        for column in dataset.get('columns', []):
            semantic_type = column.get('semantic_type')
            kind = _AGGREGATABLE_TYPES.get(semantic_type)
            stats = column.get('stats')
            if not kind or not stats or stats.get('mean') is None:
                continue
            # `mean` was already computed by schema_inference over only the
            # values that actually parsed as numbers — never over blanks or
            # unparsed text — so `non_null_numeric` is both "how many values
            # the aggregate covers" and the correct sum multiplier.
            non_null_numeric = dataset['row_count'] - stats.get('missing_count', 0)
            excluded = dataset['row_count'] - non_null_numeric
            if kind == 'average':
                aggregate = stats['mean']
                method = 'average_of_parsed_values'
            else:
                # A column's sum is mean * count-of-non-null-numeric-values —
                # the per-column stats block only keeps the aggregates
                # (mean/min/max), not the raw series, so the total is
                # reconstructed from them rather than re-parsing every row.
                aggregate = stats['mean'] * non_null_numeric
                method = 'sum_of_parsed_values'
            label_prefix = 'Average' if kind == 'average' else 'Total'
            metrics.append(make_metric(
                label=f'{label_prefix} {column["display_name"]}',
                value=round(aggregate, 4),
                dataset=dataset['name'],
                column=column['name'],
                kind=kind,
                format_hint=_FORMAT_HINT[semantic_type],
                calculation_method=method,
                included_count=non_null_numeric,
                excluded_count=excluded,
            ))
        # A record-count metric per dataset is genuinely useful context and
        # costs nothing to compute.
        metrics.append(make_metric(
            label=f'{dataset["name"]} records',
            value=len(rows),
            dataset=dataset['name'],
            column='',
            kind='count',
            format_hint='number',
            calculation_method='row_count',
            included_count=len(rows),
            excluded_count=0,
        ))

    return metrics[:MAX_METRICS]
