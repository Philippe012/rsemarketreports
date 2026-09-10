"""Builds the downloadable Excel workbook for an RSE market report from a
validated report dict. Only sections that actually have data become sheets —
nothing is invented to fill out an empty sheet.

(For a generic, non-RSE document, see services.export.generic_exporter —
services.pipeline.export_report_excel picks whichever one applies.)
"""
from datetime import datetime
from typing import List, Optional

from openpyxl import Workbook

from .xlsx_style import (
    FMT_DATE,
    FMT_DECIMAL,
    FMT_INTEGER,
    FMT_PERCENT,
    FMT_PRICE,
    LABEL_FONT,
    SUBTITLE_FONT,
    TITLE_FONT,
    write_table,
)


def _fmt_date(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return value


def _sheet_market_summary(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet('MARKET SUMMARY')
    ws['A1'] = data.get('report_title') or 'Rwanda Stock Exchange Market Report'
    ws['A1'].font = TITLE_FONT
    ws.merge_cells('A1:B1')

    report_date = _fmt_date(data.get('report_date'))
    ws['A2'] = f"Report date: {report_date if report_date else 'Unknown'}"
    ws['A2'].font = SUBTITLE_FONT
    ws.merge_cells('A2:B2')

    overview = data.get('market_overview') or {}
    rows = [
        ('Equity turnover (Frw)', overview.get('equity_turnover'), FMT_DECIMAL),
        ('Equity deals', overview.get('equity_deals'), FMT_INTEGER),
        ('Shares traded', overview.get('shares_traded'), FMT_DECIMAL),
        ('Bond market turnover (Frw)', overview.get('bond_turnover'), FMT_DECIMAL),
        ('Bond deals', overview.get('bond_deals'), FMT_INTEGER),
        ('Market capitalization (Frw)', overview.get('market_capitalization'), FMT_DECIMAL),
    ]
    row = 4
    ws.cell(row=row, column=1, value='MARKET OVERVIEW').font = LABEL_FONT
    row += 1
    for label, value, fmt in rows:
        ws.cell(row=row, column=1, value=label)
        cell = ws.cell(row=row, column=2, value=value)
        if isinstance(value, (int, float)):
            cell.number_format = fmt
        row += 1

    if any(overview.get(k) is not None for k in ('repo_deals', 'repo_turnover', 'repo_tenor', 'repo_rate')):
        row += 1
        ws.cell(row=row, column=1, value='REPO MARKET').font = LABEL_FONT
        row += 1
        repo_rows = [
            ('Repo deals', overview.get('repo_deals'), FMT_INTEGER),
            ('Repo turnover (Frw)', overview.get('repo_turnover'), FMT_DECIMAL),
            ('Repo tenor', overview.get('repo_tenor'), None),
            ('Repo average rate (%)', overview.get('repo_rate'), FMT_PERCENT),
        ]
        for label, value, fmt in repo_rows:
            ws.cell(row=row, column=1, value=label)
            cell = ws.cell(row=row, column=2, value=value)
            if fmt and isinstance(value, (int, float)):
                cell.number_format = fmt
            row += 1

    indices = data.get('indices') or []
    if indices:
        row += 1
        ws.cell(row=row, column=1, value='INDICES').font = LABEL_FONT
        row += 1
        for idx in indices:
            ws.cell(row=row, column=1, value=idx.get('name'))
            cell = ws.cell(row=row, column=2, value=idx.get('closing'))
            cell.number_format = FMT_DECIMAL
            row += 1

    insights = data.get('insights') or []
    if insights:
        row += 1
        ws.cell(row=row, column=1, value='INSIGHTS').font = LABEL_FONT
        row += 1
        for insight in insights:
            ws.cell(row=row, column=1, value=insight)
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            row += 1

    ws.column_dimensions['A'].width = 32
    ws.column_dimensions['B'].width = 22


def _sheet_stock(wb: Workbook, equities: List[dict]) -> None:
    if not equities:
        return
    ws = wb.create_sheet('STOCK')
    has_full_data = any(e.get('isin') for e in equities)
    if has_full_data:
        headers = ['ISIN-CODE', 'SECURITY', 'HIGH 12M', 'LOW 12M', 'HIGH TODAY',
                   'LOW TODAY', 'CLOSING', 'PREVIOUS', 'CHANGE', 'VOLUME', 'VALUE']
        rows = [[
            e.get('isin'), e.get('ticker'), e.get('high_12m'), e.get('low_12m'),
            e.get('high_today'), e.get('low_today'), e.get('closing'),
            e.get('previous'), e.get('change'), e.get('volume'), e.get('value'),
        ] for e in equities]
        formats = [None, None, FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL,
                   FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL, FMT_INTEGER, FMT_DECIMAL]
    else:
        headers = ['SECURITY', 'CLOSING', 'VOLUME', 'VALUE']
        rows = [[e.get('ticker'), e.get('closing'), e.get('volume'), e.get('value')] for e in equities]
        formats = [None, FMT_DECIMAL, FMT_INTEGER, FMT_DECIMAL]
    write_table(ws, 1, headers, rows, column_formats=formats)


def _sheet_market_stats(wb: Workbook, data: dict) -> None:
    overview = data.get('market_overview') or {}
    indices = data.get('indices') or []
    if not indices and not any(v is not None for v in overview.values()):
        return
    ws = wb.create_sheet('MARKET STATS')
    rows = [[idx.get('name'), idx.get('closing')] for idx in indices]
    label_map = [
        ('Equity turnover', overview.get('equity_turnover')),
        ('Bond market today (FRW)', overview.get('bond_turnover')),
        ('Market capitalization (FRW)', overview.get('market_capitalization')),
    ]
    for label, value in label_map:
        if value is not None:
            rows.append([label, value])
    write_table(ws, 1, ['INDICATORS', 'CLOSING'], rows, column_widths=[28, 20], column_formats=[None, FMT_DECIMAL])


def _sheet_bonds(wb: Workbook, government_bonds: List[dict], corporate_bonds: List[dict]) -> None:
    all_bonds = [*government_bonds, *corporate_bonds]
    if not all_bonds:
        return
    ws = wb.create_sheet('BONDS')
    headers = ['ISIN-CODE', 'STATUS', 'SECURITY', 'MATURITY DATE', 'COUPON RATE (%)',
               'CLOSING PRICE', 'PREVIOUS PRICE', 'BIDS', 'OFFERS', 'BOND TRADED', 'BOND CATEGORY']
    rows = [[
        b.get('isin'), b.get('status'), b.get('security'), _fmt_date(b.get('maturity_date')),
        b.get('coupon_rate'), b.get('closing_price'), b.get('previous_price'),
        b.get('bids'), b.get('offers'), b.get('bond_traded'), b.get('category'),
    ] for b in all_bonds]
    formats = [None, None, None, FMT_DATE, FMT_PERCENT, FMT_PRICE, FMT_PRICE,
               FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL, None]
    write_table(ws, 1, headers, rows, column_formats=formats)


def _sheet_bond_trades(wb: Workbook, trades: List[dict]) -> None:
    if not trades:
        return
    ws = wb.create_sheet('BONDS TRADES')
    headers = ['BOND', 'CATEGORY', 'VOLUME', 'PREVIOUS', 'CLOSING', 'CHANGE']
    rows = [[t.get('bond'), t.get('category'), t.get('volume'), t.get('previous'),
             t.get('closing'), t.get('change')] for t in trades]
    formats = [None, None, FMT_INTEGER, FMT_PRICE, FMT_PRICE, FMT_PRICE]
    write_table(ws, 1, headers, rows, column_formats=formats)


def _sheet_exchange_rate(wb: Workbook, rates: List[dict]) -> None:
    if not rates:
        return
    ws = wb.create_sheet('EXCHANGE RATE')
    headers = ['CURRENCY CODE', 'BUYING VALUE', 'SELLING VALUE', 'AVERAGE']
    rows = [[r.get('currency'), r.get('buying'), r.get('selling'), r.get('average')] for r in rates]
    formats = [None, FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL]
    write_table(ws, 1, headers, rows, column_widths=[16, 16, 16, 16], column_formats=formats)


def _sheet_indices(wb: Workbook, indices: List[dict], trading_stats: List[dict]) -> None:
    if not indices and not trading_stats:
        return
    ws = wb.create_sheet('INDICES')
    next_row = 1
    if indices:
        headers = ['INDEX', 'PREVIOUS', 'TODAY', 'POINTS CHANGE', '% CHANGE']
        rows = [[i.get('name'), i.get('previous'), i.get('today'),
                 i.get('points_change'), i.get('percent_change')] for i in indices]
        formats = [None, FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL, FMT_PERCENT]
        next_row = write_table(ws, next_row, headers, rows, column_widths=[14, 14, 14, 16, 12], column_formats=formats) + 1
    if trading_stats:
        headers = ['TRADING STAT', 'PREVIOUS', 'TODAY', 'CHANGE', '% CHANGE']
        rows = [[s.get('label'), s.get('previous'), s.get('today'),
                 s.get('change'), s.get('percent_change')] for s in trading_stats]
        formats = [None, FMT_DECIMAL, FMT_DECIMAL, FMT_DECIMAL, FMT_PERCENT]
        write_table(ws, next_row, headers, rows, column_widths=[20, 14, 14, 14, 12],
                    column_formats=formats, freeze_header=False)


def generate_excel(data: dict, output_path: str) -> str:
    """Generate the Excel workbook for a validated RSE report dict and save it to disk."""
    wb = Workbook()
    wb.remove(wb.active)

    _sheet_market_summary(wb, data)
    _sheet_stock(wb, data.get('equities') or [])
    _sheet_market_stats(wb, data)
    _sheet_bonds(wb, data.get('government_bonds') or [], data.get('corporate_bonds') or [])
    _sheet_bond_trades(wb, data.get('bond_trades') or [])
    _sheet_exchange_rate(wb, data.get('exchange_rates') or [])
    _sheet_indices(wb, data.get('indices') or [], data.get('trading_stats') or [])

    if not wb.sheetnames:
        wb.create_sheet('MARKET SUMMARY')

    wb.save(output_path)
    return output_path
