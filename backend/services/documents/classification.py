"""Best-effort classification of what *kind* of document this is, based on
the semantic types and names of the columns actually extracted (never on
guesswork about content that wasn't extracted). Low-confidence guesses are
reported as "General dataset" rather than a forced, potentially wrong label
— see the module docstring in schema_inference.py for the same principle.
"""
from __future__ import annotations

from typing import List, Tuple

_CATEGORY_KEYWORDS = {
    'Financial': ('revenue', 'expense', 'profit', 'margin', 'income', 'balance', 'asset',
                  'liability', 'equity', 'cash flow', 'turnover', 'budget'),
    'Market data': ('isin', 'ticker', 'bond', 'coupon', 'exchange rate', 'index', 'equity',
                     'stock', 'yield', 'closing price', 'trading'),
    'Sales': ('product', 'region', 'customer', 'order', 'units sold', 'sales', 'discount'),
    'HR': ('employee', 'department', 'salary', 'hire date', 'headcount', 'payroll', 'staff'),
    'Operations': ('inventory', 'warehouse', 'shipment', 'supplier', 'sku', 'stock level'),
    'Education': ('student', 'grade', 'course', 'enrollment', 'gpa', 'semester'),
    'Government': ('budget allocation', 'ministry', 'district', 'census', 'public'),
}

MIN_SCORE_FOR_CONFIDENT_LABEL = 2


def classify_document(datasets: List[dict], full_text: str = '') -> Tuple[str, str]:
    """Returns (label, confidence). Confidence is 'high', 'medium', or 'low'
    (low means "General dataset" — the label is a genuine best guess, not a
    forced classification the caller should treat as certain)."""
    haystack_parts = [full_text.lower()]
    for dataset in datasets:
        for column in dataset.get('columns', []):
            haystack_parts.append(str(column.get('name', '')).lower())
            haystack_parts.append(str(column.get('display_name', '')).lower())
    haystack = ' '.join(haystack_parts)

    scores = {}
    for label, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in haystack)
        if score:
            scores[label] = score

    if not scores:
        return 'General dataset', 'low'

    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]

    if best_score >= MIN_SCORE_FOR_CONFIDENT_LABEL:
        # A clear runner-up within 1 point of the leader means the signal is
        # genuinely ambiguous between two categories — don't pick one.
        runner_up = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
        if best_score - runner_up <= 0 and len(scores) > 1:
            return 'General business', 'medium'
        return best_label, 'high'

    return best_label, 'medium'
