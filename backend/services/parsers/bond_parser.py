from __future__ import annotations

import re
from typing import List

from services.normalization.clean_data import clean_text, parse_date, parse_number

_NUM = r'[\d,]+\.?\d*'
_STATUS_RE = r'(?:Re-opened|Re-op(?:ened)?)'

_BOND_LINE_RE = re.compile(
    rf'^(?P<isin>[A-Z0-9]{{5,12}})\s+'
    rf'(?:(?P<status>{_STATUS_RE})\s+)?'
    rf'(?P<security>[A-Za-z0-9]+/\d{{4}}/\d{{1,2}}[A-Za-z]+)\s+'
    rf'(?P<maturity>\d{{1,2}}/\d{{1,2}}/\d{{4}})\s+'
    rf'(?P<coupon>[\d.]+)%\s+'
    rf'(?P<close>{_NUM})\s+'
    rf'(?P<prev>{_NUM})\s+'
    rf'(?P<bids>{_NUM})\s+'
    rf'(?P<offers>{_NUM})\s+'
    rf'(?P<traded>{_NUM})\s*$'
)

_GOV_HEADER_RE = re.compile(r'a\.\s*Government bonds', re.IGNORECASE)
_CORP_HEADER_RE = re.compile(r'b\.\s*Corporate bonds', re.IGNORECASE)


def _parse_bond_lines(text: str, category: str) -> List[dict]:
    bonds = []
    for line in text.splitlines():
        match = _BOND_LINE_RE.match(line.strip())
        if not match:
            continue
        status = match.group('status')
        is_reopened = bool(status)
        bonds.append({
            'isin': match.group('isin'),
            'status': 'Re-opened' if is_reopened else None,
            'security': match.group('security'),
            'label': f"{match.group('security')} (Re-opened)" if is_reopened else match.group('security'),
            'maturity_date': parse_date(match.group('maturity')),
            'coupon_rate': parse_number(match.group('coupon')),
            'closing_price': parse_number(match.group('close')),
            'previous_price': parse_number(match.group('prev')),
            'bids': parse_number(match.group('bids')),
            'offers': parse_number(match.group('offers')),
            'bond_traded': parse_number(match.group('traded')),
            'category': category,
            'issue_date': None,
            'yield_tm': None,
            't_bond_no': None,
        })
    return bonds


def parse_bonds_from_text(full_text: str) -> dict:
    gov_match = _GOV_HEADER_RE.search(full_text)
    corp_match = _CORP_HEADER_RE.search(full_text)

    government_bonds: List[dict] = []
    corporate_bonds: List[dict] = []

    if gov_match:
        end = corp_match.start() if corp_match else len(full_text)
        government_bonds = _parse_bond_lines(full_text[gov_match.end():end], 'TREASURY')

    if corp_match:
        corporate_bonds = _parse_bond_lines(full_text[corp_match.end():], 'CORPORATE')

    return {'government_bonds': government_bonds, 'corporate_bonds': corporate_bonds}


def derive_bond_trades(government_bonds: List[dict], corporate_bonds: List[dict]) -> List[dict]:
    """Build the bond-trades list from any bond row with a nonzero traded volume."""
    trades = []
    for bond in [*government_bonds, *corporate_bonds]:
        volume = bond.get('bond_traded')
        if not volume:
            continue
        closing = bond.get('closing_price')
        previous = bond.get('previous_price')
        change = (
            round(closing - previous, 6)
            if closing is not None and previous is not None
            else None
        )
        trades.append({
            'bond': bond.get('label') or bond.get('security'),
            'category': bond.get('category'),
            'volume': volume,
            'previous': previous,
            'closing': closing,
            'change': change,
        })
    return trades


def parse_bonds_from_excel(rows: List[list]) -> dict:
    if not rows:
        return {'government_bonds': [], 'corporate_bonds': []}

    header = [clean_text(cell) or '' for cell in rows[0]]
    header_lower = [h.lower() for h in header]

    def col(*names):
        for name in names:
            if name in header_lower:
                return header_lower.index(name)
        return None

    isin_col = col('isin-code', 'isin')
    tbond_col = col('t-bonds no', 't-bond no')
    issue_col = col('issue date')
    maturity_col = col('maturity date')
    coupon_col = col('coupon rate')
    yield_col = col('yield tm')
    category_col = col('bond category')
    close_col = col('closing price', 'close.', 'closing')

    government_bonds, corporate_bonds = [], []
    for row in rows[1:]:
        isin = clean_text(row[isin_col]) if isin_col is not None and isin_col < len(row) else None
        if not isin:
            continue
        category_raw = clean_text(row[category_col]) if category_col is not None and category_col < len(row) else None
        is_corporate = bool(category_raw and 'corp' in category_raw.lower())
        bond = {
            'isin': isin,
            'status': None,
            'security': isin,
            'label': isin,
            'maturity_date': parse_date(row[maturity_col]) if maturity_col is not None and maturity_col < len(row) else None,
            'coupon_rate': parse_number(row[coupon_col]) if coupon_col is not None and coupon_col < len(row) else None,
            'closing_price': parse_number(row[close_col]) if close_col is not None and close_col < len(row) else None,
            'previous_price': None,
            'bids': None,
            'offers': None,
            'bond_traded': None,
            'category': 'CORPORATE' if is_corporate else 'TREASURY',
            'issue_date': parse_date(row[issue_col]) if issue_col is not None and issue_col < len(row) else None,
            'yield_tm': parse_number(row[yield_col]) if yield_col is not None and yield_col < len(row) else None,
            't_bond_no': clean_text(row[tbond_col]) if tbond_col is not None and tbond_col < len(row) else None,
        }
        (corporate_bonds if is_corporate else government_bonds).append(bond)

    return {'government_bonds': government_bonds, 'corporate_bonds': corporate_bonds}


def parse_bond_trades_from_excel(rows: List[list]) -> List[dict]:
    """Parse the Excel "BONDS TRADES" sheet directly."""
    if not rows:
        return []

    header = [clean_text(cell) or '' for cell in rows[0]]
    header_lower = [h.lower() for h in header]

    def col(*names):
        for name in names:
            if name in header_lower:
                return header_lower.index(name)
        return None

    bond_col = col('bond')
    category_col = col('category')
    volume_col = col('volume')
    previous_col = col('previous')
    closing_col = col('closing')
    change_col = col('change')

    trades = []
    for row in rows[1:]:
        bond_name = clean_text(row[bond_col]) if bond_col is not None and bond_col < len(row) else None
        if not bond_name:
            continue
        trades.append({
            'bond': bond_name,
            'category': clean_text(row[category_col]) if category_col is not None and category_col < len(row) else None,
            'volume': parse_number(row[volume_col]) if volume_col is not None and volume_col < len(row) else None,
            'previous': parse_number(row[previous_col]) if previous_col is not None and previous_col < len(row) else None,
            'closing': parse_number(row[closing_col]) if closing_col is not None and closing_col < len(row) else None,
            'change': parse_number(row[change_col]) if change_col is not None and change_col < len(row) else None,
        })
    return trades
