"""Automated, deterministic insights for RSE market reports — the same
"never claim more than the numbers show" principle as
services.documents.insights (generic documents), reading the RSE-specific
schema (services.parsers.rse_parser) instead of the generic dataset/column
model. Every sentence is a direct readout of a value already sitting in
extracted_data; nothing is recomputed or estimated.
"""
from __future__ import annotations

from typing import List, Optional

MAX_INSIGHTS = 6


def _fmt(value, decimals: int = 0) -> str:
    if value is None:
        return 'not available'
    v = float(value)
    if decimals == 0 and v == int(v):
        return f'{int(v):,}'
    return f'{v:,.{decimals}f}'


def compute_rse_insights(data: dict) -> List[str]:
    insights: List[str] = []

    equities = [e for e in data.get('equities') or [] if e.get('change') is not None]
    if len(equities) >= 2:
        gainer = max(equities, key=lambda e: e['change'])
        loser = min(equities, key=lambda e: e['change'])
        if gainer['change'] > 0:
            insights.append(
                f"{gainer['ticker']} was today's top gainer, up {_fmt(gainer['change'], 2)} to close at {_fmt(gainer['closing'], 2)}."
            )
        if loser['change'] < 0 and loser['ticker'] != gainer['ticker']:
            insights.append(
                f"{loser['ticker']} was today's top decliner, down {_fmt(abs(loser['change']), 2)} to close at {_fmt(loser['closing'], 2)}."
            )

    traded = [e for e in data.get('equities') or [] if e.get('volume')]
    if traded:
        most_active = max(traded, key=lambda e: e['volume'])
        insights.append(
            f"{most_active['ticker']} was the most actively traded equity, with {_fmt(most_active['volume'])} shares changing hands."
        )

    for idx in data.get('indices') or []:
        pct = idx.get('percent_change')
        if pct:
            direction = 'gained' if pct > 0 else 'lost'
            insights.append(
                f"The {idx['name']} index {direction} {_fmt(abs(pct), 2)}% today, closing at {_fmt(idx.get('closing'), 2)}."
            )

    all_bonds = (data.get('government_bonds') or []) + (data.get('corporate_bonds') or [])
    bonds_with_yield = [b for b in all_bonds if b.get('yield_tm') is not None]
    if bonds_with_yield:
        top_yield = max(bonds_with_yield, key=lambda b: b['yield_tm'])
        insights.append(
            f"{top_yield.get('security')} carries the highest yield to maturity among listed bonds, at {_fmt(top_yield['yield_tm'], 2)}%."
        )

    overview = data.get('market_overview') or {}
    if overview.get('market_capitalization') is not None:
        insights.append(f"Total market capitalization stood at FRW {_fmt(overview['market_capitalization'])}.")
    if overview.get('equity_deals') is not None and overview.get('equity_turnover') is not None:
        insights.append(
            f"Equity turnover reached FRW {_fmt(overview['equity_turnover'])} across {_fmt(overview['equity_deals'])} deal(s)."
        )

    return insights[:MAX_INSIGHTS]
