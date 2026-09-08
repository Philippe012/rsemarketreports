
import re
from typing import List, Optional

from services.normalization.clean_data import clean_text, parse_number

_INDEX_LINE_RE = re.compile(
    r'^([A-Z][A-Z0-9]{1,9})\s+'
    r'([+-]?[\d,]+\.\d+)\s+'
    r'([+-]?[\d,]+\.\d+)\s+'
    r'([+-]?[\d,]+\.\d+)\s+'
    r'([+-]?[\d,]+\.\d+)(?:\s|$)'
)

_KNOWN_INDEX_NAMES = {'RSI', 'ALSI', 'EAE20', 'EAE'}


def parse_indices_from_text(full_text: str) -> List[dict]:
    indices = []
    seen = set()
    for line in full_text.splitlines():
        match = _INDEX_LINE_RE.match(line.strip())
        if not match:
            continue
        name = match.group(1)
        if name not in _KNOWN_INDEX_NAMES:
            continue
        if name in seen:
            continue
        seen.add(name)
        previous = parse_number(match.group(2))
        today = parse_number(match.group(3))
        indices.append({
            'name': name,
            'previous': previous,
            'today': today,
            'closing': today if today is not None else previous,
            'points_change': parse_number(match.group(4)),
            'percent_change': parse_number(match.group(5)),
        })
    return indices


def parse_indices_from_market_stats(rows: List[list]) -> List[dict]:
    indices = []
    for row in rows:
        if not row:
            continue
        name = clean_text(row[0]) if len(row) > 0 else None
        if not name:
            continue
        
        if not re.match(r'^[A-Z0-9]{2,10}$', name):
            continue
        closing = parse_number(row[1]) if len(row) > 1 else None
        if closing is None:
            continue
        indices.append({
            'name': name,
            'previous': None,
            'today': None,
            'closing': closing,
            'points_change': None,
            'percent_change': None,
        })
    return indices


def find_index(indices: List[dict], name: str) -> Optional[dict]:
    return next((idx for idx in indices if idx['name'].upper() == name.upper()), None)
