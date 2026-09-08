from __future__ import annotations

import datetime
import re
from typing import Optional

_THOUSANDS_RE = re.compile(r'(?<=\d),(?=\d{3}(\D|$))')
_NUMBER_RE = re.compile(r'^[+-]?\d+(\.\d+)?$')

_DATE_FORMATS = (
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%d/%m/%y',
    '%Y-%m-%d',
    '%d %B %Y',
    '%d %b %Y',
)


def clean_text(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).replace('\xa0', ' ').strip()
    text = re.sub(r'\s+', ' ', text)
    return text or None


def parse_number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text in {'-', '—', 'N/A', 'n/a', 'NA'}:
        return None

    text = text.replace('\xa0', ' ').strip()
    text = text.replace('%', '')
    text = re.sub(r'(?i)\b(frw|rwf|usd)\b', '', text).strip()
    text = text.replace(',', '')
    text = text.replace('+', '')

    if not _NUMBER_RE.match(text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_percent(value) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return parse_number(text.replace('%', ''))


def parse_int(value) -> Optional[int]:
    number = parse_number(value)
    if number is None:
        return None
    return int(round(number))


def parse_date(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def is_blank_row(row) -> bool:
    """True when every cell in a row is empty/None/whitespace."""
    return all(clean_text(cell) is None for cell in row)
