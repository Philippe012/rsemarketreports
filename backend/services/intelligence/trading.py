from typing import List

MAX_ROWS = 10


def _ranked(items: List[dict], key: str, reverse: bool) -> List[dict]:
    present = [item for item in items if item.get(key) is not None]
    return sorted(present, key=lambda item: item[key], reverse=reverse)[:MAX_ROWS]


def trading_analytics(data: dict) -> dict:
    equities = data.get('equities') or []
    indices = data.get('indices') or []
    bonds = (data.get('government_bonds') or []) + (data.get('corporate_bonds') or [])

    return {
        'top_gainers': _ranked(equities, 'change', reverse=True),
        'top_losers': _ranked(equities, 'change', reverse=False),
        'volume_leaders': _ranked(equities, 'volume', reverse=True),
        'value_leaders': _ranked(equities, 'value', reverse=True),
        'index_performance': sorted(indices, key=lambda i: i.get('percent_change') or 0, reverse=True),
        'bond_yield_ranking': _ranked(bonds, 'yield_tm', reverse=True),
        'exchange_rates': data.get('exchange_rates') or [],
        'market_overview': data.get('market_overview') or {},
    }
