"""Infers what a table column actually *is* — not just its raw data type,
but its semantic role (an amount of money, a percentage, a category people
will want to filter by, an identifier, a date, ...).

Nothing here invents values: it only classifies columns that already exist
in the extracted rows, using both the column's name and the shape of its
actual values (never name alone — a column literally named "Total" still
has to look numeric before it is trusted as one).

The heavy lifting on "how many of these values are numeric/dates" and "what
does the numeric distribution look like" is delegated to pandas/NumPy
(vectorized over the whole column) rather than hand-rolled per-value loops —
this module supplies the *domain* rules (what counts as a percentage vs. a
plain number vs. a quantity), pandas supplies the aggregation.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from dateutil import parser as dateutil_parser

from services.normalization.clean_data import clean_text, parse_date, parse_number

from .model import make_column

_DATEUTIL_DEFAULT = datetime(2000, 1, 1)

_CURRENCY_SYMBOL_RE = re.compile(r'[$€£¥]')
_CURRENCY_NAME_HINTS = (
    'price', 'cost', 'revenue', 'expense', 'salary', 'income', 'amount',
    'turnover', 'value', 'total', 'budget', 'fee', 'payment', 'profit', 'margin',
)
_PERCENT_NAME_HINTS = ('percent', 'pct', '%', 'rate', 'growth', 'margin', 'ratio')
_IDENTIFIER_NAME_HINTS = ('id', 'isin', 'code', 'sku', 'ref', 'number', 'no.')
_QUANTITY_NAME_HINTS = ('quantity', 'qty', 'volume', 'units', 'count', 'stock', 'headcount')
_DATE_NAME_HINTS = ('date', 'year', 'month', 'period', 'day', 'time')
_BOOLEAN_VALUES = {'true', 'false', 'yes', 'no', 'y', 'n', '0', '1', 'active', 'inactive'}
# A loose guard for the dateutil fallback below: only worth trying on text
# that actually looks date-shaped (has a separator or a month name), so a
# column of plain numeric IDs never gets fed through a free-form date parser.
_DATE_LIKE_RE = re.compile(
    r'[/\-]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec', re.IGNORECASE
)
# A numeric date whose day and month parts are both <=12 (e.g. "03/04/2026")
# is genuinely ambiguous — "3 April" under day-first reading (what parse_date
# assumes) vs. "March 4th" under month-first reading — and no amount of
# clever parsing resolves that without knowing the source locale, so this is
# only ever used to *flag* the ambiguity, never to silently pick a side.
_AMBIGUOUS_NUMERIC_DATE_RE = re.compile(r'^(\d{1,2})[/\-](\d{1,2})[/\-]\d{2,4}$')


def _is_structurally_ambiguous_date(text: str) -> bool:
    match = _AMBIGUOUS_NUMERIC_DATE_RE.match(text.strip())
    if not match:
        return False
    first, second = int(match.group(1)), int(match.group(2))
    return first <= 12 and second <= 12 and first != second

# Non-numeric columns still carry a uniqueness/completeness stats block (so
# duplicate-identifier detection has something to check) but never a
# parse-failure or negative count — those only mean something for numbers.
_NON_NUMERIC_STATS_BASE = {
    'min': None, 'max': None, 'mean': None, 'std': None,
    'unparsed_count': 0, 'negative_count': 0, 'ambiguous_date_count': 0,
}


def _text_stats(unique_count: int, missing_count: int) -> dict:
    return {**_NON_NUMERIC_STATS_BASE, 'unique_count': unique_count, 'missing_count': missing_count}


def _name_has_any(name: str, hints: Tuple[str, ...]) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in hints)


def _looks_like_percent_text(text: str) -> bool:
    return text.strip().endswith('%')


def _looks_like_currency_text(text: str) -> bool:
    return bool(_CURRENCY_SYMBOL_RE.search(text))


def parse_date_flexible(text: str) -> Optional[str]:
    """Strict formats first (parse_date); dateutil as a wider fallback for
    generic documents whose date formatting we can't predict in advance —
    guarded so it's only ever tried on text that already looks date-shaped."""
    strict = parse_date(text)
    if strict is not None:
        return strict
    if not _DATE_LIKE_RE.search(text):
        return None
    try:
        dt = dateutil_parser.parse(text, fuzzy=False, default=_DATEUTIL_DEFAULT)
    except (ValueError, OverflowError, TypeError):
        return None
    if not (1900 <= dt.year <= 2100):
        return None
    return dt.date().isoformat()


def _numeric_series(texts: List[str]) -> pd.Series:
    """Vectorized numeric coercion: our own parse_number (handles $, commas,
    %, accounting parens) per cell, aggregated as a pandas Series so the
    caller gets real statistics (mean/std/min/max) via pandas/NumPy rather
    than a hand-rolled sum-and-divide."""
    return pd.Series([parse_number(t) for t in texts], dtype='float64')


def infer_column(name: str, raw_values: List, total_count: Optional[int] = None) -> dict:
    """Classify one column from its name and the values actually present.

    ``raw_values`` should be every non-blank cell seen for this column
    (already stripped of fully-empty rows by the caller). ``total_count``
    lets the caller pass the dataset's full row count when it differs from
    ``len(raw_values)`` (i.e. some rows had this cell blank).
    """
    total = total_count if total_count is not None else len(raw_values)
    texts = [clean_text(v) for v in raw_values]
    texts = [t for t in texts if t is not None]
    non_null_count = len(texts)
    sample_values = texts[:5]

    display_name = name.strip() if name else 'Column'

    if non_null_count == 0:
        return make_column(name, display_name, 'text', 'string', 0, total, [], confidence='low')

    percent_hits = sum(1 for t in texts if _looks_like_percent_text(t))
    currency_hits = sum(1 for t in texts if _looks_like_currency_text(t))
    numeric_series = _numeric_series(texts)
    numeric_hits = int(numeric_series.notna().sum())
    date_hits = sum(1 for t in texts if parse_date_flexible(t) is not None)
    boolean_hits = sum(1 for t in texts if t.lower() in _BOOLEAN_VALUES)

    unique_values = set(t.lower() for t in texts)
    uniqueness_ratio = len(unique_values) / non_null_count

    numeric_ratio = numeric_hits / non_null_count
    date_ratio = date_hits / non_null_count
    boolean_ratio = boolean_hits / non_null_count

    stats = None
    if numeric_hits > 0:
        clean_numeric = numeric_series.dropna()
        stats = {
            'min': float(np.min(clean_numeric)),
            'max': float(np.max(clean_numeric)),
            'mean': float(np.mean(clean_numeric)),
            'std': float(np.std(clean_numeric)) if len(clean_numeric) > 1 else 0.0,
            'unique_count': int(clean_numeric.nunique()),
            'missing_count': total - numeric_hits,
            # Present-but-unparsable text, distinct from genuinely blank
            # cells — e.g. "N/A" in a revenue column — so validation can
            # tell the two apart instead of lumping them into one count.
            'unparsed_count': non_null_count - numeric_hits,
            'negative_count': int((clean_numeric < 0).sum()),
            'ambiguous_date_count': 0,
        }

    # Dates: most values parse as a date and it's a plausible date-shaped column.
    if date_ratio >= 0.8 and (numeric_ratio < 0.8 or _name_has_any(display_name, _DATE_NAME_HINTS)):
        column = make_column(name, display_name, 'date', 'date', non_null_count, total, sample_values, 'high')
        column['stats'] = {
            **_NON_NUMERIC_STATS_BASE,
            'unique_count': None,
            'missing_count': total - date_hits,
            # Present-but-unparsable text (e.g. a stray "TBD" in a date
            # column), distinct from a genuinely blank cell.
            'unparsed_count': non_null_count - date_hits,
            'ambiguous_date_count': sum(1 for t in texts if _is_structurally_ambiguous_date(t)),
        }
        return column

    # Booleans: a tiny, fixed vocabulary of yes/no-shaped values.
    if boolean_ratio == 1.0 and len(unique_values) <= 2:
        column = make_column(name, display_name, 'boolean', 'boolean', non_null_count, total, sample_values, 'high')
        column['stats'] = None
        return column

    if numeric_ratio >= 0.8:
        # Numeric — now decide *which kind* of number this is.
        if percent_hits / non_null_count >= 0.5 or _name_has_any(display_name, _PERCENT_NAME_HINTS):
            semantic_type, confidence = 'percentage', 'high'
        elif currency_hits / non_null_count >= 0.3 or _name_has_any(display_name, _CURRENCY_NAME_HINTS):
            semantic_type, confidence = 'currency', 'medium'
        elif _name_has_any(display_name, _QUANTITY_NAME_HINTS):
            semantic_type, confidence = 'quantity', 'medium'
        elif _name_has_any(display_name, _IDENTIFIER_NAME_HINTS) and uniqueness_ratio > 0.9:
            semantic_type, confidence = 'identifier', 'medium'
            stats = _text_stats(len(unique_values), total - non_null_count)
        else:
            semantic_type, confidence = 'number', 'high'
        column = make_column(name, display_name, semantic_type, 'number', non_null_count, total, sample_values, confidence)
        column['stats'] = stats
        return column

    # Non-numeric text: identifier vs. category vs. free text.
    if _name_has_any(display_name, _IDENTIFIER_NAME_HINTS) and uniqueness_ratio > 0.9:
        column = make_column(name, display_name, 'identifier', 'string', non_null_count, total, sample_values, 'medium')
        column['stats'] = _text_stats(len(unique_values), total - non_null_count)
        return column
    if uniqueness_ratio > 0.95 and non_null_count > 5:
        # Nearly every value is unique with no identifier-style name — still
        # behaves like an identifier (e.g. a name or reference column).
        column = make_column(name, display_name, 'identifier', 'string', non_null_count, total, sample_values, 'low')
        column['stats'] = _text_stats(len(unique_values), total - non_null_count)
        return column
    # Low cardinality relative to row count reads as a dimension to group/filter by.
    if len(unique_values) <= max(20, non_null_count * 0.5):
        avg_len = sum(len(t) for t in texts) / non_null_count
        if avg_len <= 40:
            column = make_column(name, display_name, 'category', 'string', non_null_count, total, sample_values, 'medium')
            column['stats'] = _text_stats(len(unique_values), total - non_null_count)
            return column

    column = make_column(name, display_name, 'text', 'string', non_null_count, total, sample_values, 'medium')
    column['stats'] = None
    return column


def infer_columns(headers: List[str], rows: List[dict]) -> List[dict]:
    """Infer every column in a dataset given its header names and row dicts."""
    total = len(rows)
    columns = []
    for header in headers:
        values = [row.get(header) for row in rows]
        non_blank = [v for v in values if clean_text(v) is not None]
        columns.append(infer_column(header, non_blank, total_count=total))
    return columns
