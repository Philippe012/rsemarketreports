from typing import Optional

MISSING = 'not available in this document'


def num(value, decimals: int = 0) -> str:
    if value is None:
        return MISSING
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals == 0 and v == int(v):
        return f'{int(v):,}'
    return f'{v:,.{decimals}f}'


def currency(value, code: str = 'FRW', decimals: int = 2) -> str:
    if value is None:
        return MISSING
    return f'{code} {num(value, decimals)}'


def percent(value, decimals: int = 2, signed: bool = True) -> str:
    if value is None:
        return MISSING
    sign = '+' if signed and value > 0 else ''
    return f'{sign}{value:.{decimals}f}%'


def date_str(value: Optional[str]) -> str:
    return value if value else MISSING
