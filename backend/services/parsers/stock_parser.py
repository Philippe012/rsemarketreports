import re
from typing import List

from services.normalization.clean_data import clean_text, parse_number

_NUM = r'[+-]?[\d,]+\.?\d*'

_STOCK_LINE_RE = re.compile(
    r'^([A-Z0-9]{10,12})\s+([A-Z]{2,6})\s+'
    rf'({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s*$'
)


def parse_stocks_from_text(full_text: str) -> List[dict]:
    equities = []
    seen = set()
    for line in full_text.splitlines():
        match = _STOCK_LINE_RE.match(line.strip())
        if not match:
            continue
        isin = match.group(1)
        ticker = match.group(2)
        if ticker in seen:
            continue
        seen.add(ticker)
        numbers = [parse_number(match.group(i)) for i in range(3, 12)]
        high_12m, low_12m, high_today, low_today, closing, previous, change, volume, value = numbers
        equities.append({
            'isin': isin,
            'ticker': ticker,
            'high_12m': high_12m,
            'low_12m': low_12m,
            'high_today': high_today,
            'low_today': low_today,
            'closing': closing,
            'previous': previous,
            'change': change,
            'volume': int(volume) if volume is not None else None,
            'value': value,
        })
    return equities


def parse_stocks_from_excel(rows: List[list]) -> List[dict]:
    if not rows:
        return []

    header = [clean_text(cell) or '' for cell in rows[0]]
    header_lower = [h.lower() for h in header]

    def col(*names):
        for name in names:
            if name in header_lower:
                return header_lower.index(name)
        return None

    ticker_col = col('security', 'stock', 'ticker')
    closing_col = col('closing', 'close', 'closing price')
    volume_col = col('volume')
    value_col = col('value')

    equities = []
    for row in rows[1:]:
        if ticker_col is None or ticker_col >= len(row):
            continue
        ticker = clean_text(row[ticker_col])
        if not ticker:
            continue
        equities.append({
            'isin': None,
            'ticker': ticker,
            'high_12m': None,
            'low_12m': None,
            'high_today': None,
            'low_today': None,
            'closing': parse_number(row[closing_col]) if closing_col is not None and closing_col < len(row) else None,
            'previous': None,
            'change': None,
            'volume': int(v) if volume_col is not None and volume_col < len(row) and (v := parse_number(row[volume_col])) is not None else None,
            'value': parse_number(row[value_col]) if value_col is not None and value_col < len(row) else None,
        })
    return equities
