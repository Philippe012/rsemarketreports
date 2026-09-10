"""Deterministic entity extraction from free-form text: the numbers, dates,
and frequently-mentioned terms actually written in the document's prose.

This exists for documents that have no table at all — a policy memo, a
narrative report — so they still get something concrete out of the
platform besides "here is your text back". Every entity here is a literal
substring lifted from the source text via regex, not a model's guess at
what the text means; nothing is paraphrased or inferred.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import List

MAX_NUMBERS = 12
MAX_DATES = 8
MAX_KEYWORDS = 10

_MONTHS = (
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
)

_CURRENCY_MENTION_RE = re.compile(
    r'(?:[$€£¥]\s?[\d,]+(?:\.\d+)?(?:\s?(?:million|billion|thousand))?)'
    r'|(?:\b(?:USD|EUR|GBP|Frw|FRW|RWF|KES|Ksh)\s?[\d,]+(?:\.\d+)?(?:\s?(?:million|billion|thousand))?)',
)
_PERCENT_MENTION_RE = re.compile(r'\b\d+(?:\.\d+)?\s?%')
_LARGE_NUMBER_RE = re.compile(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b')

_MONTH_YEAR_RE = re.compile(rf'\b(?:{"|".join(_MONTHS)})\s+\d{{4}}\b')
_FULL_DATE_RE = re.compile(rf'\b(?:{"|".join(_MONTHS)})\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b')
_NUMERIC_DATE_RE = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
_QUARTER_RE = re.compile(r'\bQ[1-4]\s+\d{4}\b')

_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'of', 'in', 'on', 'at', 'to', 'for',
    'with', 'by', 'from', 'as', 'is', 'was', 'were', 'are', 'be', 'been',
    'this', 'that', 'these', 'those', 'it', 'its', 'their', 'there', 'which',
    'has', 'have', 'had', 'will', 'would', 'could', 'should', 'than', 'over',
    'into', 'about', 'across', 'during', 'per', 'each', 'all', 'also', 'not',
    'more', 'most', 'such', 'other', 'between', 'both', 'while', 'after',
    'before', 'up', 'down', 'out', 'if', 'so', 'no', 'yes', 'they', 'we',
}
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{2,}")


def extract_numbers(text: str) -> List[str]:
    """Currency amounts and percentages first (most meaningful), then plain
    large numbers, in the order they appear — deduplicated, capped."""
    found: List[str] = []
    seen = set()
    for pattern in (_CURRENCY_MENTION_RE, _PERCENT_MENTION_RE, _LARGE_NUMBER_RE):
        for match in pattern.finditer(text):
            value = match.group().strip()
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(value)
            if len(found) >= MAX_NUMBERS:
                return found
    return found


def extract_dates(text: str) -> List[str]:
    found: List[str] = []
    seen = set()
    for pattern in (_FULL_DATE_RE, _MONTH_YEAR_RE, _NUMERIC_DATE_RE, _QUARTER_RE):
        for match in pattern.finditer(text):
            value = match.group().strip()
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(value)
            if len(found) >= MAX_DATES:
                return found
    return found


def extract_keywords(text: str) -> List[str]:
    """The most frequently repeated significant words — a plain word-frequency
    count, not topic modeling. Reported honestly as "frequently mentioned
    terms" by the UI, not as inferred topics."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    significant = [w for w in words if w not in _STOPWORDS]
    if not significant:
        return []
    counts = Counter(significant)
    # A word that only appears once across the whole document isn't a
    # "frequently mentioned" term worth surfacing.
    ranked = [word for word, count in counts.most_common(MAX_KEYWORDS * 3) if count > 1]
    return ranked[:MAX_KEYWORDS]


def extract_entities(text: str) -> dict:
    return {
        'numbers': extract_numbers(text),
        'dates': extract_dates(text),
        'keywords': extract_keywords(text),
    }
