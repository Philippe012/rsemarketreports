"""Deterministic answer engine for RSE market reports (`kind ==
'rse_market_report'`). Indexes every figure already sitting in
`extracted_data` — market overview, indices, trading stats, equities,
bonds, bond trades, exchange rates — as facts a question can match against.
Nothing here parses the source document again or computes a new number;
every value is read straight from the already-validated extraction.
"""
from __future__ import annotations

from typing import List

from .base import AnswerEngine, AnswerResult, Source, not_found
from .fact_index import FactIndex
from .formatting import currency, num, percent
from .text_match import tokenize


def _words(*parts) -> set:
    words = set()
    for part in parts:
        if part:
            words.update(tokenize(str(part)))
    return words


class RseAnswerEngine(AnswerEngine):
    def __init__(self, data: dict):
        self._data = data
        self._index = FactIndex()
        self._build()

    # -- index construction -------------------------------------------------

    def _build(self) -> None:
        self._build_overview()
        self._build_indices()
        self._build_trading_stats()
        self._build_equities()
        self._build_bonds(self._data.get('government_bonds') or [], 'Government bonds')
        self._build_bonds(self._data.get('corporate_bonds') or [], 'Corporate bonds')
        self._build_bond_trades()
        self._build_exchange_rates()

    def _build_overview(self) -> None:
        o = self._data.get('market_overview') or {}
        src = Source('Market overview')
        fields = [
            (['equity', 'turnover'], f"Today's equity turnover was {currency(o.get('equity_turnover'))}."),
            (['equity', 'deals'], f"There were {num(o.get('equity_deals'))} equity deals today."),
            (['shares', 'traded'], f"{num(o.get('shares_traded'))} shares were traded today."),
            (['bond', 'turnover'], f"Today's bond turnover was {currency(o.get('bond_turnover'))}."),
            (['bond', 'deals'], f"There were {num(o.get('bond_deals'))} bond deals today."),
            (['market', 'capitalization', 'capitalisation', 'cap'],
             f"The market capitalization is {currency(o.get('market_capitalization'))}."),
            (['repo', 'deals'], f"There were {num(o.get('repo_deals'))} repo deals today."),
            (['repo', 'turnover'], f"Today's repo turnover was {currency(o.get('repo_turnover'))}."),
            (['repo', 'tenor'], f"The repo tenor was {o.get('repo_tenor') or 'not available in this document'}."),
            (['repo', 'rate'], f"The average repo rate was {percent(o.get('repo_rate'), signed=False)}."),
        ]
        for keywords, text in fields:
            self._index.add(keywords, text, src)

        self._index.add(
            ['market', 'overview', 'summary', 'session', 'today'],
            (
                f"Market overview: equity turnover {currency(o.get('equity_turnover'))} across "
                f"{num(o.get('equity_deals'))} deals ({num(o.get('shares_traded'))} shares traded); "
                f"bond turnover {currency(o.get('bond_turnover'))} across {num(o.get('bond_deals'))} deals; "
                f"market capitalization {currency(o.get('market_capitalization'))}."
            ),
            src,
        )

    def _build_indices(self) -> None:
        for idx in self._data.get('indices') or []:
            name = idx.get('name') or ''
            name_words = _words(name)
            src = Source('Indices', name)
            self._index.add(
                name_words | {'closing', 'today', 'value'},
                f"The {name} index closed at {num(idx.get('closing'), 2)} today (previous {num(idx.get('previous'), 2)}).",
                src,
            )
            self._index.add(
                name_words | {'change', 'points', 'percent', 'movement'},
                f"The {name} index changed by {num(idx.get('points_change'), 2)} points "
                f"({percent(idx.get('percent_change'))}) today.",
                src,
            )
            self._index.add(
                name_words,
                f"{name} index — closing {num(idx.get('closing'), 2)}, previous {num(idx.get('previous'), 2)}, "
                f"change {num(idx.get('points_change'), 2)} points ({percent(idx.get('percent_change'))}).",
                src,
            )

    def _build_trading_stats(self) -> None:
        for stat in self._data.get('trading_stats') or []:
            label = stat.get('label') or ''
            label_words = _words(label)
            if not label_words:
                continue
            src = Source('Trading statistics', label)
            self._index.add(
                label_words | {'today', 'value'},
                f"{label}: {num(stat.get('today'))} today (previous {num(stat.get('previous'))}).",
                src,
            )
            self._index.add(
                label_words | {'change', 'percent'},
                f"{label} changed by {num(stat.get('change'))} ({percent(stat.get('percent_change'))}).",
                src,
            )
            self._index.add(
                label_words,
                f"{label} — today {num(stat.get('today'))}, previous {num(stat.get('previous'))}, "
                f"change {num(stat.get('change'))} ({percent(stat.get('percent_change'))}).",
                src,
            )

    def _build_equities(self) -> None:
        for eq in self._data.get('equities') or []:
            ticker = eq.get('ticker') or ''
            entity_words = _words(ticker, eq.get('isin'))
            if not entity_words:
                continue
            src = Source('Equities', ticker)
            self._index.add(entity_words | {'closing', 'price', 'today'},
                             f"{ticker} closed at {num(eq.get('closing'))} today (previous {num(eq.get('previous'))}).", src)
            self._index.add(entity_words | {'previous', 'yesterday'},
                             f"{ticker}'s previous closing price was {num(eq.get('previous'))}.", src)
            self._index.add(entity_words | {'change', 'movement'},
                             f"{ticker} changed by {num(eq.get('change'))} today.", src)
            self._index.add(entity_words | {'volume', 'shares', 'traded'},
                             f"{num(eq.get('volume'))} shares of {ticker} were traded today.", src)
            self._index.add(entity_words | {'value', 'worth', 'turnover'},
                             f"The value traded for {ticker} today was {currency(eq.get('value'))}.", src)
            self._index.add(entity_words | {'12m', 'high', 'yearly', 'annual', 'year'},
                             f"{ticker}'s 12-month high is {num(eq.get('high_12m'))} and 12-month low is {num(eq.get('low_12m'))}.", src)
            self._index.add(entity_words,
                             f"{ticker} — closing {num(eq.get('closing'))}, previous {num(eq.get('previous'))}, "
                             f"change {num(eq.get('change'))}, volume {num(eq.get('volume'))}, value {currency(eq.get('value'))}.",
                             src)

    def _build_bonds(self, bonds: List[dict], category_label: str) -> None:
        for bond in bonds:
            security = bond.get('security') or bond.get('label') or ''
            entity_words = _words(security, bond.get('isin'), bond.get('label'))
            if not entity_words:
                continue
            src = Source(category_label, security)
            self._index.add(entity_words | {'coupon', 'rate'},
                             f"{security} has a coupon rate of {percent(bond.get('coupon_rate'), signed=False)}.", src)
            self._index.add(entity_words | {'closing', 'price'},
                             f"{security} closed at {num(bond.get('closing_price'), 2)} (previous {num(bond.get('previous_price'), 2)}).", src)
            self._index.add(entity_words | {'maturity', 'matures', 'due'},
                             f"{security} matures on {bond.get('maturity_date') or 'a date not available in this document'}.", src)
            self._index.add(entity_words | {'yield'},
                             f"{security}'s yield to maturity is {percent(bond.get('yield_tm'), signed=False)}.", src)
            self._index.add(entity_words | {'bids', 'offers'},
                             f"{security} had {num(bond.get('bids'))} bids and {num(bond.get('offers'))} offers.", src)
            self._index.add(entity_words,
                             f"{security} ({category_label.lower()}) — closing price {num(bond.get('closing_price'), 2)}, "
                             f"coupon {percent(bond.get('coupon_rate'), signed=False)}, maturity {bond.get('maturity_date') or 'not available'}.",
                             src)

    def _build_bond_trades(self) -> None:
        for trade in self._data.get('bond_trades') or []:
            bond = trade.get('bond') or ''
            entity_words = _words(bond)
            if not entity_words:
                continue
            src = Source('Bond trades', bond)
            self._index.add(entity_words | {'volume', 'traded'},
                             f"{num(trade.get('volume'))} of {bond} traded today.", src)
            self._index.add(entity_words | {'change'},
                             f"{bond} changed by {num(trade.get('change'), 2)} today.", src)
            self._index.add(entity_words,
                             f"{bond} traded — volume {num(trade.get('volume'))}, closing {num(trade.get('closing'), 2)}, "
                             f"previous {num(trade.get('previous'), 2)}, change {num(trade.get('change'), 2)}.", src)

        if self._data.get('bond_trades'):
            names = ', '.join(t.get('bond', '') for t in self._data['bond_trades'] if t.get('bond'))
            self._index.add(['which', 'bonds', 'traded', 'today'],
                             f"Bonds that traded today: {names}.", Source('Bond trades'))

    def _build_exchange_rates(self) -> None:
        for rate in self._data.get('exchange_rates') or []:
            currency_code = rate.get('currency') or ''
            entity_words = _words(currency_code)
            if not entity_words:
                continue
            src = Source('Exchange rates', currency_code)
            self._index.add(entity_words | {'buying', 'buy'},
                             f"The {currency_code} buying rate is {num(rate.get('buying'), 2)}.", src)
            self._index.add(entity_words | {'selling', 'sell'},
                             f"The {currency_code} selling rate is {num(rate.get('selling'), 2)}.", src)
            self._index.add(entity_words | {'average', 'mid', 'rate', 'exchange'},
                             f"The average {currency_code} exchange rate is {num(rate.get('average'), 2)}.", src)
            self._index.add(entity_words,
                             f"{currency_code} — buying {num(rate.get('buying'), 2)}, selling {num(rate.get('selling'), 2)}, "
                             f"average {num(rate.get('average'), 2)}.", src)

    # -- public interface -----------------------------------------------------

    def answer(self, question: str) -> AnswerResult:
        fact = self._index.best_match(question)
        if fact is None:
            return not_found()
        return AnswerResult(answer=fact.answer_text, sources=[fact.source], confidence=fact.confidence)

    def suggested_questions(self) -> List[str]:
        questions: List[str] = []
        equities = self._data.get('equities') or []
        indices = self._data.get('indices') or []
        overview = self._data.get('market_overview') or {}
        rates = self._data.get('exchange_rates') or []
        trades = self._data.get('bond_trades') or []
        gov_bonds = self._data.get('government_bonds') or []
        corp_bonds = self._data.get('corporate_bonds') or []

        if equities:
            questions.append(f"What was {equities[0].get('ticker')}'s closing price today?")
        if indices:
            questions.append(f"How did the {indices[0].get('name')} index perform today?")
        if overview.get('market_capitalization') is not None:
            questions.append('What is the total market capitalization?')
        if overview.get('equity_turnover') is not None:
            questions.append("What was today's equity turnover?")
        if rates:
            usd = next((r for r in rates if (r.get('currency') or '').upper() == 'USD'), rates[0])
            questions.append(f"What is the {usd.get('currency')} exchange rate today?")
        if trades:
            questions.append('Which bonds traded today?')
        elif gov_bonds or corp_bonds:
            questions.append(f"How many bonds are listed ({len(gov_bonds) + len(corp_bonds)} total)?")

        return questions[:6]
