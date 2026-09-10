"""Picks one representative "headline" figure out of a processed
document's extracted_data — used only so the documents list can sort/
filter by "financial value" across every document kind without querying
arbitrary JSON shapes per kind in the database. Never invents a number:
if nothing suitable is present, returns (``''``, ``None``).
"""
from __future__ import annotations

from typing import Optional, Tuple


def compute_headline_metric(data: Optional[dict]) -> Tuple[str, Optional[float]]:
    if not data:
        return '', None

    if data.get('kind') == 'rse_market_report':
        overview = data.get('market_overview') or {}
        for label, key in (
            ('Market capitalization', 'market_capitalization'),
            ('Equity turnover', 'equity_turnover'),
            ('Bond turnover', 'bond_turnover'),
        ):
            value = overview.get(key)
            if value is not None:
                return label, float(value)
        return '', None

    metrics = data.get('metrics') or []
    for metric in metrics:
        value = metric.get('value')
        if metric.get('kind') == 'sum' and metric.get('format_hint') == 'currency' and isinstance(value, (int, float)):
            return metric.get('label', ''), float(value)
    for metric in metrics:
        value = metric.get('value')
        if isinstance(value, (int, float)):
            return metric.get('label', ''), float(value)
    return '', None
