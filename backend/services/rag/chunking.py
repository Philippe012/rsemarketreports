"""Turns a report's already-validated ``extracted_data`` into searchable
text chunks for RAG. Nothing here re-reads the source file: RSE reports are
chunked from their structured fields (so every figure becomes a plain
sentence that retrieval can find), and generic documents from their text
sections, dataset rows, metrics and insights.

Each chunk is a dict: ``{'content', 'page_number', 'section', 'metadata'}``.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional

from services.chat.formatting import currency, num, percent

MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
ROWS_PER_CHUNK = 20
MAX_ROWS_PER_DATASET = 2000
MAX_CHUNKS_PER_REPORT = 1500

_PAGE_RE = re.compile(r'\bpages?\s+(\d+)', re.IGNORECASE)


def _page_from(text: Optional[str]) -> Optional[int]:
    match = _PAGE_RE.search(text or '')
    return int(match.group(1)) if match else None


def _chunk(content: str, section: str, filename: str, page_number: Optional[int] = None, **extra) -> dict:
    return {
        'content': content.strip(),
        'page_number': page_number,
        'section': (section or '')[:255],
        'metadata': {'filename': filename, **extra},
    }


def split_text(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """Splits long text into overlapping windows, breaking on paragraph or
    sentence boundaries where possible so a chunk rarely cuts a sentence."""
    text = (text or '').strip()
    if len(text) <= max_chars:
        return [text] if text else []

    pieces: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind('\n'), window.rfind('. '))
            if cut > max_chars // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


# RSE market reports

def _rse_chunks(data: dict, filename: str) -> List[dict]:
    chunks: List[dict] = []
    date = data.get('report_date') or 'the report date'
    prefix = f'RSE market report for {date}.'

    o = data.get('market_overview') or {}
    if o:
        chunks.append(_chunk(
            f"{prefix} Market overview: equity turnover {currency(o.get('equity_turnover'))} across "
            f"{num(o.get('equity_deals'))} equity deals, {num(o.get('shares_traded'))} shares traded. "
            f"Bond turnover {currency(o.get('bond_turnover'))} across {num(o.get('bond_deals'))} bond deals. "
            f"Market capitalization {currency(o.get('market_capitalization'))}. "
            f"Repo deals {num(o.get('repo_deals'))}, repo turnover {currency(o.get('repo_turnover'))}, "
            f"repo rate {percent(o.get('repo_rate'), signed=False)}.",
            'Market Overview', filename,
        ))

    for idx in data.get('indices') or []:
        name = idx.get('name') or 'Index'
        chunks.append(_chunk(
            f"{prefix} The {name} index closed at {num(idx.get('closing'), 2)} (previous {num(idx.get('previous'), 2)}), "
            f"a change of {num(idx.get('points_change'), 2)} points ({percent(idx.get('percent_change'))}).",
            'Indices', filename, entity=name,
        ))

    for stat in data.get('trading_stats') or []:
        label = stat.get('label') or ''
        if label:
            chunks.append(_chunk(
                f"{prefix} {label}: today {num(stat.get('today'))}, previous {num(stat.get('previous'))}, "
                f"change {num(stat.get('change'))} ({percent(stat.get('percent_change'))}).",
                'Trading Statistics', filename, entity=label,
            ))

    for eq in data.get('equities') or []:
        ticker = eq.get('ticker') or ''
        if not ticker:
            continue
        isin = f" (ISIN {eq['isin']})" if eq.get('isin') else ''
        chunks.append(_chunk(
            f"{prefix} {ticker}{isin} closed at {num(eq.get('closing'))}. Previous price was {num(eq.get('previous'))}. "
            f"Change {num(eq.get('change'))}. {ticker} volume was {num(eq.get('volume'))} shares. "
            f"{ticker} traded value was {currency(eq.get('value'))}. "
            f"12-month high {num(eq.get('high_12m'))}, 12-month low {num(eq.get('low_12m'))}.",
            'Equities', filename, entity=ticker,
        ))

    for key, label in (('government_bonds', 'Government Bonds'), ('corporate_bonds', 'Corporate Bonds')):
        for bond in data.get(key) or []:
            security = bond.get('security') or bond.get('label') or ''
            if not security:
                continue
            chunks.append(_chunk(
                f"{prefix} {label[:-1]} {security}: closing price {num(bond.get('closing_price'), 2)} "
                f"(previous {num(bond.get('previous_price'), 2)}), coupon rate {percent(bond.get('coupon_rate'), signed=False)}, "
                f"yield to maturity {percent(bond.get('yield_tm'), signed=False)}, maturity date "
                f"{bond.get('maturity_date') or 'not available'}, {num(bond.get('bids'))} bids and {num(bond.get('offers'))} offers.",
                label, filename, entity=security,
            ))

    trades = data.get('bond_trades') or []
    for trade in trades:
        bond = trade.get('bond') or ''
        if bond:
            chunks.append(_chunk(
                f"{prefix} Bond trade {bond}: volume {num(trade.get('volume'))}, closing {num(trade.get('closing'), 2)}, "
                f"previous {num(trade.get('previous'), 2)}, change {num(trade.get('change'), 2)}.",
                'Bond Trades', filename, entity=bond,
            ))
    if trades:
        names = ', '.join(t.get('bond') for t in trades if t.get('bond'))
        chunks.append(_chunk(f'{prefix} {len(trades)} bond(s) traded: {names}.', 'Bond Trades', filename))

    for rate in data.get('exchange_rates') or []:
        code = rate.get('currency') or ''
        if code:
            chunks.append(_chunk(
                f"{prefix} {code} exchange rate: buying {num(rate.get('buying'), 2)}, selling {num(rate.get('selling'), 2)}, "
                f"average {num(rate.get('average'), 2)}.",
                'Exchange Rates', filename, entity=code,
            ))

    chunks.extend(_insight_chunks(data, filename, prefix))
    return chunks


# generic documents

def _section_chunks(data: dict, filename: str) -> List[dict]:
    chunks: List[dict] = []
    for section in data.get('sections') or []:
        title = section.get('title') or 'Untitled section'
        page = _page_from(title)
        for piece in split_text(section.get('content') or ''):
            chunks.append(_chunk(f'{title}\n{piece}', title, filename, page_number=page))
    return chunks


def _row_text(row: dict, columns: List[dict]) -> str:
    parts = []
    for column in columns:
        value = row.get(column.get('name'))
        if value not in (None, ''):
            parts.append(f"{column.get('display_name') or column.get('name')}: {value}")
    return '; '.join(parts)


def _dataset_chunks(data: dict, filename: str) -> List[dict]:
    chunks: List[dict] = []
    for dataset in data.get('datasets') or []:
        name = dataset.get('name') or 'Dataset'
        source = dataset.get('source') or ''
        page = _page_from(source)
        columns = dataset.get('columns') or []
        column_names = ', '.join(c.get('display_name') or c.get('name') or '' for c in columns)
        header = f'Dataset "{name}"' + (f' ({source})' if source else '')

        chunks.append(_chunk(
            f"{header} has {dataset.get('row_count', 0)} record(s) with columns: {column_names}.",
            f'Dataset: {name}', filename, page_number=page,
        ))

        rows = (dataset.get('rows') or [])[:MAX_ROWS_PER_DATASET]
        for start in range(0, len(rows), ROWS_PER_CHUNK):
            lines = [_row_text(r, columns) for r in rows[start:start + ROWS_PER_CHUNK]]
            lines = [line for line in lines if line]
            if lines:
                chunks.append(_chunk(
                    f'{header}, rows {start + 1}-{start + len(lines)}:\n' + '\n'.join(lines),
                    f'Dataset: {name}', filename, page_number=page,
                ))
    return chunks


def _metric_chunks(data: dict, filename: str) -> List[dict]:
    lines = []
    for metric in data.get('metrics') or []:
        label, value = metric.get('label'), metric.get('value')
        if label and value is not None:
            lines.append(f'{label}: {value}')
    if not lines:
        return []
    return [_chunk('Key metrics:\n' + '\n'.join(lines), 'Metrics', filename)]


def _insight_chunks(data: dict, filename: str, prefix: str = '') -> List[dict]:
    insights = [str(i) for i in (data.get('insights') or []) if i]
    if not insights:
        return []
    return [_chunk(f'{prefix} Insights: ' + ' '.join(insights), 'Insights', filename)]


# entry point

def build_chunks(extracted_data: Optional[dict], filename: str) -> List[dict]:
    data = extracted_data or {}
    if data.get('kind') == 'rse_market_report':
        chunks = _rse_chunks(data, filename)
    else:
        chunks = (
            _section_chunks(data, filename)
            + _metric_chunks(data, filename)
            + _insight_chunks(data, filename)
            + _dataset_chunks(data, filename)
        )
    return [c for c in chunks if c['content']][:MAX_CHUNKS_PER_REPORT]


def chunk_texts(chunks: Iterable[dict]) -> List[str]:
    return [c['content'] for c in chunks]
