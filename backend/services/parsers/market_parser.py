import re
from typing import List, Optional

from services.normalization.clean_data import clean_text, parse_date, parse_number

_MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11,
    'december': 12,
}

_TITLE_DATE_RE = re.compile(
    r'(\d{1,2})(?:ST|ND|RD|TH)?\s+([A-Za-z]+)\s+(\d{4})', re.IGNORECASE
)


_BOND_TURNOVER_RE = re.compile(
    r'turnover\s+of\s+Frw\s*([\d,]+)\s+worth\s+of\s+bonds\s+traded\s+in\s+(\d+)\s+deals',
    re.IGNORECASE,
)

_TRADING_STAT_LABELS = ('Shares traded', 'Equity Turnover', 'Number of deals')
_TRADING_STAT_RE = re.compile(
    r'^(' + '|'.join(_TRADING_STAT_LABELS) + r')\s+'
    r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
    re.IGNORECASE,
)

_MARKET_CAP_RE = re.compile(r'Market\s+Capitalization\s+\(Frw\)\s*([\d,]+)', re.IGNORECASE)

_REPO_DEALS_RE = re.compile(
    r'Repo\s+Market,\s*(\d+)\s+deals?\s+worth\s+Frw\s*([\d,.]+)\s*(billion|million|thousand)?\s+'
    r'were\s+traded\s+for\s+a\s+([\w-]+)',
    re.IGNORECASE,
)
_REPO_RATE_RE = re.compile(r'tenor\s+with\s+average\s+rate\s+of\s+([\d.]+)%', re.IGNORECASE)

_UNIT_MULTIPLIERS = {'thousand': 1_000, 'million': 1_000_000, 'billion': 1_000_000_000}


def parse_report_title(full_text: str) -> Optional[str]:
    for line in full_text.splitlines():
        text = clean_text(line)
        if text and 'RWANDA STOCK EXCHANGE' in text.upper():
            return text
    return None


def parse_report_date_from_text(full_text: str) -> Optional[str]:
    match = _TITLE_DATE_RE.search(full_text)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = _MONTHS.get(month_name.lower())
    if not month:
        return None
    return parse_date(f'{int(day):02d}/{month:02d}/{year}')


def parse_report_date_from_filename(filename: str) -> Optional[str]:
    match = re.search(r'(\d{2})[-_](\d{2})[-_](\d{4})', filename)
    if not match:
        return None
    day, month, year = match.groups()
    return parse_date(f'{day}/{month}/{year}')


def parse_trading_stats_from_text(full_text: str) -> List[dict]:
    stats = []
    seen = set()
    for line in full_text.splitlines():
        match = _TRADING_STAT_RE.match(line.strip())
        if not match:
            continue
        label = match.group(1)
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        stats.append({
            'label': label,
            'previous': parse_number(match.group(2)),
            'today': parse_number(match.group(3)),
            'change': parse_number(match.group(4)),
            'percent_change': parse_number(match.group(5)),
        })
    return stats


def parse_repo_activity_from_text(full_text: str) -> dict:
    repo = {'repo_deals': None, 'repo_turnover': None, 'repo_tenor': None, 'repo_rate': None}

    deals_match = _REPO_DEALS_RE.search(full_text)
    if deals_match:
        deals = parse_number(deals_match.group(1))
        amount = parse_number(deals_match.group(2))
        unit = (deals_match.group(3) or '').lower()
        multiplier = _UNIT_MULTIPLIERS.get(unit, 1)
        repo['repo_deals'] = int(deals) if deals is not None else None
        repo['repo_turnover'] = amount * multiplier if amount is not None else None
        repo['repo_tenor'] = clean_text(deals_match.group(4))

    rate_match = _REPO_RATE_RE.search(full_text)
    if rate_match:
        repo['repo_rate'] = parse_number(rate_match.group(1))

    return repo


def parse_market_overview_from_text(full_text: str) -> dict:
    stats = {s['label'].lower(): s for s in parse_trading_stats_from_text(full_text)}

    equity_turnover = None
    if 'equity turnover' in stats:
        equity_turnover = stats['equity turnover']['today']

    shares_traded = None
    if 'shares traded' in stats:
        shares_traded = stats['shares traded']['today']

    equity_deals = None
    if 'number of deals' in stats:
        equity_deals = stats['number of deals']['today']

    bond_turnover = None
    bond_deals = None
    bond_match = _BOND_TURNOVER_RE.search(full_text)
    if bond_match:
        bond_turnover = parse_number(bond_match.group(1))
        bond_deals = parse_number(bond_match.group(2))

    market_cap = None
    cap_match = _MARKET_CAP_RE.search(full_text)
    if cap_match:
        market_cap = parse_number(cap_match.group(1))

    return {
        'equity_turnover': equity_turnover,
        'equity_deals': int(equity_deals) if equity_deals is not None else None,
        'shares_traded': shares_traded,
        'bond_turnover': bond_turnover,
        'bond_deals': int(bond_deals) if bond_deals is not None else None,
        'market_capitalization': market_cap,
        **parse_repo_activity_from_text(full_text),
    }


_MARKET_STATS_FIELD_MAP = {
    'equity turnover': 'equity_turnover',
    'bond market today (frw)': 'bond_turnover',
    'bond market today': 'bond_turnover',
    'market capitalization (frw)': 'market_capitalization',
    'market capitalization': 'market_capitalization',
    'shares traded': 'shares_traded',
    'number of deals': 'equity_deals',
    'bond deals': 'bond_deals',
}


def parse_market_overview_from_market_stats(rows: List[list]) -> dict:
    overview = {field: None for field in (
        'equity_turnover', 'equity_deals', 'shares_traded',
        'bond_turnover', 'bond_deals', 'market_capitalization',
        'repo_deals', 'repo_turnover', 'repo_tenor', 'repo_rate',
    )}
    for row in rows:
        if not row:
            continue
        label = clean_text(row[0]) if len(row) > 0 else None
        if not label:
            continue
        field = _MARKET_STATS_FIELD_MAP.get(label.lower())
        if not field:
            continue
        value = parse_number(row[1]) if len(row) > 1 else None
        if field == 'equity_deals' or field == 'bond_deals':
            overview[field] = int(value) if value is not None else None
        else:
            overview[field] = value
    return overview
