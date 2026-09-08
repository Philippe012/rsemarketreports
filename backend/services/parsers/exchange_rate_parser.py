import re
from typing import List

from services.normalization.clean_data import clean_text, parse_number

_RATE_RE = re.compile(
    r'(?<![A-Za-z0-9])([A-Z]{3})\s+([\d,]+\.\d{2,4})\s+([\d,]+\.\d{2,4})\s+([\d,]+\.\d{2,4})(?![\d,.])'
)


def parse_exchange_rates_from_text(full_text: str) -> List[dict]:
    rates = []
    seen = set()
    for match in _RATE_RE.finditer(full_text):
        currency = match.group(1)
        if currency in seen:
            continue
        sell = parse_number(match.group(2))
        buy = parse_number(match.group(3))
        average = parse_number(match.group(4))
        if sell is None or buy is None:
            continue
        seen.add(currency)
        rates.append({
            'currency': currency,
            'buying': buy,
            'selling': sell,
            'average': average,
        })
    return rates


def parse_exchange_rates_from_excel(rows: List[list]) -> List[dict]:
    if not rows:
        return []

    header = [clean_text(cell) or '' for cell in rows[0]]
    header_lower = [h.lower() for h in header]

    def col(*names):
        for name in names:
            if name in header_lower:
                return header_lower.index(name)
        return None

    currency_col = col('currency code', 'currency')
    buying_col = col('buying value', 'buying')
    selling_col = col('selling value', 'selling')

    rates = []
    for row in rows[1:]:
        if currency_col is None or currency_col >= len(row):
            continue
        currency = clean_text(row[currency_col])
        if not currency:
            continue
        buying = parse_number(row[buying_col]) if buying_col is not None and buying_col < len(row) else None
        selling = parse_number(row[selling_col]) if selling_col is not None and selling_col < len(row) else None
        average = (
            round((buying + selling) / 2, 4)
            if buying is not None and selling is not None
            else None
        )
        rates.append({
            'currency': currency,
            'buying': buying,
            'selling': selling,
            'average': average,
        })
    return rates
