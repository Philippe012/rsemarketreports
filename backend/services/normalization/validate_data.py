from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple, Union

import pandas as pd


class ReportValidationError(Exception):
    """Raised when a document yields no meaningful structured data at all."""


def _warn(warnings: List[str], message: str) -> None:
    warnings.append(message)


def _warn_duplicates(
    rows: List[dict],
    keys: Union[str, Sequence[str]],
    label: str,
    warnings: List[str],
    describe: Optional[Callable[[dict], str]] = None,
) -> None:
    if not rows:
        return
    key_list = [keys] if isinstance(keys, str) else list(keys)
    frame = pd.DataFrame(rows)
    if not all(k in frame.columns for k in key_list):
        return

    present = frame[key_list].notna().all(axis=1)
    duplicated = present & frame.duplicated(subset=key_list, keep=False)
    if not duplicated.any():
        return

    seen = set()
    for _, row in frame.loc[duplicated].iterrows():
        record = row.to_dict()
        identity = tuple(record[k] for k in key_list)
        if identity in seen:
            continue
        seen.add(identity)
        text = describe(record) if describe else str(record[key_list[0]])
        _warn(warnings, f'Duplicate {label} "{text}" appears more than once in the source table.')


def validate_equities(equities: List[dict], warnings: List[str]) -> List[dict]:
    valid = []
    for row in equities:
        ticker = row.get('ticker')
        if not ticker:
            _warn(warnings, 'Dropped an equity row with no ticker symbol.')
            continue
        if row.get('closing') is None:
            _warn(warnings, f'Equity "{ticker}" has no closing price.')
        if row.get('volume') is not None and row['volume'] < 0:
            _warn(warnings, f'Equity "{ticker}" has a negative volume; treating as unknown.')
            row['volume'] = None
        valid.append(row)
    _warn_duplicates(valid, 'ticker', 'ticker', warnings)
    return valid


def validate_indices(indices: List[dict], warnings: List[str]) -> List[dict]:
    valid = []
    for row in indices:
        if not row.get('name'):
            continue
        if row.get('closing') is None:
            _warn(warnings, f'Index "{row.get("name")}" has no closing value.')
            continue
        valid.append(row)
    return valid


def _validate_bond_list(bonds: List[dict], warnings: List[str], label: str) -> List[dict]:
    valid = []
    for row in bonds:
        security = row.get('security') or row.get('isin')
        if not security:
            _warn(warnings, f'Dropped a {label} bond row with no security identifier.')
            continue
        coupon = row.get('coupon_rate')
        if coupon is not None and not (0 <= coupon <= 100):
            _warn(warnings, f'{label.capitalize()} bond "{security}" has an implausible coupon rate ({coupon}%); treating as unknown.')
            row['coupon_rate'] = None
        if row.get('closing_price') is None:
            _warn(warnings, f'{label.capitalize()} bond "{security}" has no closing price.')
        valid.append(row)
        
    _warn_duplicates(
        valid,
        ['isin', 'security', 'maturity_date', 'coupon_rate'],
        f'{label} bond record',
        warnings,
        describe=lambda r: f"{r.get('isin')} ({r.get('security')}, matures {r.get('maturity_date')})",
    )
    return valid


def validate_bonds(government_bonds: List[dict], corporate_bonds: List[dict], warnings: List[str]) -> Tuple[List[dict], List[dict]]:
    return (
        _validate_bond_list(government_bonds, warnings, 'government'),
        _validate_bond_list(corporate_bonds, warnings, 'corporate'),
    )


def validate_bond_trades(trades: List[dict], warnings: List[str]) -> List[dict]:
    valid = []
    for row in trades:
        if not row.get('bond'):
            continue
        if row.get('volume') is None or row.get('volume') <= 0:
            _warn(warnings, f'Bond trade "{row.get("bond")}" has no positive traded volume.')
            continue
        valid.append(row)
    return valid


def validate_exchange_rates(rates: List[dict], warnings: List[str]) -> List[dict]:
    valid = []
    for row in rates:
        currency = row.get('currency')
        if not currency:
            continue
        buying, selling = row.get('buying'), row.get('selling')
        if buying is None or selling is None:
            _warn(warnings, f'Exchange rate for {currency} is incomplete.')
        elif buying <= 0 or selling <= 0:
            _warn(warnings, f'Exchange rate for {currency} has a non-positive value; treating as unknown.')
            row['buying'], row['selling'], row['average'] = None, None, None
        elif buying > selling:
            _warn(warnings, f'Exchange rate for {currency}: buying rate is higher than selling rate — check the source document.')
        valid.append(row)
    _warn_duplicates(valid, 'currency', 'currency', warnings)
    return valid


def validate_market_overview(overview: dict, warnings: List[str]) -> dict:
    for field in ('equity_turnover', 'shares_traded', 'bond_turnover', 'market_capitalization', 'repo_turnover'):
        value = overview.get(field)
        if value is not None and value < 0:
            _warn(warnings, f'Market overview field "{field}" is negative; treating as unknown.')
            overview[field] = None
    rate = overview.get('repo_rate')
    if rate is not None and not (0 <= rate <= 100):
        _warn(warnings, f'Repo market average rate ({rate}%) is out of a plausible range; treating as unknown.')
        overview['repo_rate'] = None
    return overview


def validate_report(data: dict) -> Tuple[dict, List[str]]:
    warnings: List[str] = []

    if not data.get('report_date'):
        _warn(warnings, 'Could not determine the report date from the document.')

    data['market_overview'] = validate_market_overview(data.get('market_overview', {}), warnings)
    data['equities'] = validate_equities(data.get('equities', []), warnings)
    data['indices'] = validate_indices(data.get('indices', []), warnings)
    data['government_bonds'], data['corporate_bonds'] = validate_bonds(
        data.get('government_bonds', []), data.get('corporate_bonds', []), warnings
    )
    data['bond_trades'] = validate_bond_trades(data.get('bond_trades', []), warnings)
    data['exchange_rates'] = validate_exchange_rates(data.get('exchange_rates', []), warnings)

    has_any_data = any([
        data['equities'],
        data['indices'],
        data['government_bonds'],
        data['corporate_bonds'],
        data['bond_trades'],
        data['exchange_rates'],
        any(v is not None for v in data.get('market_overview', {}).values()),
        data.get('trading_stats'),
    ])
    if not has_any_data:
        raise ReportValidationError(
            'No recognizable RSE market data (equities, bonds, indices, '
            'exchange rates or market stats) could be extracted from this document.'
        )

    return data, warnings
