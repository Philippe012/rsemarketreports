"""Discoveries: a thin, honest wrapper that surfaces the same
plain-language observations already computed at ingest time
(``services.documents.insights.compute_insights`` for generic documents,
``services.documents.rse_insights.compute_rse_insights`` for RSE reports —
both already stored on ``extracted_data['insights']`` by
``services.pipeline``). Recomputes from scratch only as a fallback for a
report stored before this field existed, so the Advanced Intelligence
bundle never depends on a field that might be missing.
"""
from __future__ import annotations

from typing import List

from services.documents.insights import compute_insights
from services.documents.rse_insights import compute_rse_insights

from .adapter import to_analysis_datasets


def compute_discoveries(extracted_data: dict) -> List[str]:
    if not extracted_data:
        return []

    stored = extracted_data.get('insights')
    if stored:
        return stored

    if extracted_data.get('kind') == 'rse_market_report':
        return compute_rse_insights(extracted_data)
    return compute_insights(to_analysis_datasets(extracted_data))
