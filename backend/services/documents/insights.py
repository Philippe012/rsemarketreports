"""Generates a small set of plain-language observations about the extracted
datasets — a range, a leader, a trend — each one a direct readout of a
number already computed (schema_inference's stats, or a plain pandas
groupby/aggregate here), never a claim invented beyond what the data shows.

Insights are deliberately capped and only generated when the underlying
comparison is meaningful (e.g. a "highest by category" insight needs more
than one category to say anything) — an empty list is the right answer for
a dataset too small or too uniform to say anything useful about.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from services.normalization.clean_data import parse_date, parse_number

MAX_INSIGHTS = 6


def _format_number(value: float) -> str:
    if value == int(value):
        return f'{int(value):,}'
    return f'{value:,.2f}'


def _range_insight(dataset: dict, column: dict) -> Optional[str]:
    stats = column.get('stats')
    if not stats or stats.get('min') is None or stats.get('max') is None:
        return None
    if stats['min'] == stats['max']:
        return None
    return (
        f'"{column["display_name"]}" in {dataset["name"]} ranges from '
        f'{_format_number(stats["min"])} to {_format_number(stats["max"])} '
        f'(average {_format_number(stats["mean"])}) across {dataset["row_count"]} records.'
    )


def _leader_insight(dataset: dict, category_column: dict, measure_column: dict) -> Optional[str]:
    rows = dataset.get('rows', [])
    totals: dict = {}
    for row in rows:
        category = row.get(category_column['name'])
        if category is None or category == '':
            continue
        value = parse_number(row.get(measure_column['name']))
        if value is None:
            continue
        totals[category] = totals.get(category, 0) + value
    if len(totals) < 2:
        return None
    leader = max(totals, key=totals.get)
    trailer = min(totals, key=totals.get)
    if leader == trailer:
        return None
    return (
        f'By total {measure_column["display_name"]}, "{leader}" leads '
        f'({_format_number(totals[leader])}) and "{trailer}" trails '
        f'({_format_number(totals[trailer])}) among {measure_column["display_name"].lower()} in {dataset["name"]}.'
    )


def _outlier_insight(dataset: dict, column: dict) -> Optional[str]:
    stats = column.get('stats')
    if not stats or not stats.get('std') or stats.get('mean') is None:
        return None
    mean, std = stats['mean'], stats['std']
    outlier_count = 0
    for row in dataset.get('rows', []):
        value = parse_number(row.get(column['name']))
        if value is not None and abs(value - mean) > 2 * std:
            outlier_count += 1
    if not outlier_count:
        return None
    plural = 'value' if outlier_count == 1 else 'values'
    return (
        f'"{column["display_name"]}" in {dataset["name"]} has {outlier_count} {plural} more than 2 standard '
        f'deviations from the mean ({_format_number(mean)}) — worth reviewing as potential outliers.'
    )


def _correlation_insight(dataset: dict, column_a: dict, column_b: dict) -> Optional[str]:
    pairs = []
    for row in dataset.get('rows', []):
        a = parse_number(row.get(column_a['name']))
        b = parse_number(row.get(column_b['name']))
        if a is not None and b is not None:
            pairs.append((a, b))
    if len(pairs) < 5:
        return None
    a_values = np.array([p[0] for p in pairs], dtype='float64')
    b_values = np.array([p[1] for p in pairs], dtype='float64')
    if np.std(a_values) == 0 or np.std(b_values) == 0:
        return None
    correlation = float(np.corrcoef(a_values, b_values)[0, 1])
    if np.isnan(correlation) or abs(correlation) < 0.6:
        return None
    direction = 'positively' if correlation > 0 else 'negatively'
    return (
        f'"{column_a["display_name"]}" and "{column_b["display_name"]}" in {dataset["name"]} are strongly '
        f'{direction} correlated (r={correlation:.2f}) across {len(pairs)} records with both values present.'
    )


def _trend_insight(dataset: dict, date_column: dict, measure_column: dict) -> Optional[str]:
    rows = dataset.get('rows', [])
    points = []
    for row in rows:
        date_str = parse_date(row.get(date_column['name']))
        value = parse_number(row.get(measure_column['name']))
        if date_str is None or value is None:
            continue
        points.append((date_str, value))
    if len(points) < 3:
        return None
    points.sort(key=lambda p: p[0])
    series = pd.Series([v for _, v in points])
    x = np.arange(len(series))
    slope = float(np.polyfit(x, series.to_numpy(dtype='float64'), 1)[0])
    relative_slope = slope * len(series) / (series.mean() or 1)
    if relative_slope > 0.08:
        direction = 'increased'
    elif relative_slope < -0.08:
        direction = 'decreased'
    else:
        return None
    return (
        f'"{measure_column["display_name"]}" in {dataset["name"]} {direction} over the period '
        f'covered ({points[0][0]} to {points[-1][0]}).'
    )


def compute_insights(datasets: List[dict]) -> List[str]:
    insights: List[str] = []

    for dataset in datasets:
        columns = dataset.get('columns', [])
        measures = [c for c in columns if c.get('semantic_type') in ('currency', 'number', 'quantity')]
        categories = [c for c in columns if c.get('semantic_type') == 'category']
        dates = [c for c in columns if c.get('semantic_type') in ('date', 'datetime')]

        if measures:
            range_text = _range_insight(dataset, measures[0])
            if range_text:
                insights.append(range_text)

        if categories and measures:
            leader_text = _leader_insight(dataset, categories[0], measures[0])
            if leader_text:
                insights.append(leader_text)

        if dates and measures:
            trend_text = _trend_insight(dataset, dates[0], measures[0])
            if trend_text:
                insights.append(trend_text)

        if measures:
            outlier_text = _outlier_insight(dataset, measures[0])
            if outlier_text:
                insights.append(outlier_text)

        if len(measures) >= 2:
            correlation_text = _correlation_insight(dataset, measures[0], measures[1])
            if correlation_text:
                insights.append(correlation_text)

        if dataset.get('duplicate_row_count'):
            insights.append(
                f'{dataset["name"]} contains {dataset["duplicate_row_count"]} exact duplicate '
                f'record(s) — see Data Quality for details.'
            )

        if len(insights) >= MAX_INSIGHTS:
            break

    return insights[:MAX_INSIGHTS]
