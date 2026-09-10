from services.extraction.excel_extractor import ExcelExtractionResult
from services.extraction.pdf_extractor import PdfExtractionResult
from services.parsers import bond_parser, exchange_rate_parser, index_parser, market_parser, stock_parser
from services.normalization.validate_data import validate_report

EMPTY_MARKET_OVERVIEW = {
    'equity_turnover': None,
    'equity_deals': None,
    'shares_traded': None,
    'bond_turnover': None,
    'bond_deals': None,
    'market_capitalization': None,
    'repo_deals': None,
    'repo_turnover': None,
    'repo_tenor': None,
    'repo_rate': None,
}


RSE_EXCEL_SHEET_SIGNALS = {'STOCK', 'MARKET STATS', 'BONDS', 'BONDS TRADES', 'EXCHANGE RATE'}


def is_rse_report(source_type: str, extraction) -> bool:
    """Cheap, deterministic check for whether a document is an RSE market
    report — used by services.pipeline to route PDFs/Excel workbooks to this
    specialized parser instead of the generic document-intelligence engine
    (services.documents). CSVs never route here; RSE never ships as CSV.
    """
    if source_type == 'pdf':
        return 'RWANDA STOCK EXCHANGE' in extraction.full_text.upper()
    if source_type == 'excel':
        sheet_names = {name.strip().upper() for name in extraction.sheets.keys()}
        return len(sheet_names & RSE_EXCEL_SHEET_SIGNALS) >= 2
    return False


def _empty_schema(source_type: str) -> dict:
    return {
        'kind': 'rse_market_report',
        'report_title': None,
        'report_date': None,
        'source_type': source_type,
        'market_overview': dict(EMPTY_MARKET_OVERVIEW),
        'indices': [],
        'trading_stats': [],
        'equities': [],
        'government_bonds': [],
        'corporate_bonds': [],
        'bond_trades': [],
        'exchange_rates': [],
    }


def parse_pdf_report(extraction: PdfExtractionResult, filename: str) -> dict:
    full_text = extraction.full_text
    data = _empty_schema('pdf')

    data['report_title'] = market_parser.parse_report_title(full_text)
    data['report_date'] = (
        market_parser.parse_report_date_from_text(full_text)
        or market_parser.parse_report_date_from_filename(filename)
    )
    data['market_overview'] = market_parser.parse_market_overview_from_text(full_text)
    data['trading_stats'] = market_parser.parse_trading_stats_from_text(full_text)
    data['indices'] = index_parser.parse_indices_from_text(full_text)
    data['equities'] = stock_parser.parse_stocks_from_text(full_text)

    bonds = bond_parser.parse_bonds_from_text(full_text)
    data['government_bonds'] = bonds['government_bonds']
    data['corporate_bonds'] = bonds['corporate_bonds']
    data['bond_trades'] = bond_parser.derive_bond_trades(
        data['government_bonds'], data['corporate_bonds']
    )

    data['exchange_rates'] = exchange_rate_parser.parse_exchange_rates_from_text(full_text)

    return data


def parse_excel_report(extraction: ExcelExtractionResult, filename: str) -> dict:
    sheets = extraction.sheets
    data = _empty_schema('excel')

    data['report_date'] = market_parser.parse_report_date_from_filename(filename)
    data['report_title'] = 'Rwanda Stock Exchange Market Report'

    market_stats_rows = _find_sheet(sheets, 'MARKET STATS')
    if market_stats_rows:
        data['market_overview'] = market_parser.parse_market_overview_from_market_stats(market_stats_rows)
        data['indices'] = index_parser.parse_indices_from_market_stats(market_stats_rows)

    stock_rows = _find_sheet(sheets, 'STOCK')
    if stock_rows:
        data['equities'] = stock_parser.parse_stocks_from_excel(stock_rows)

    bonds_rows = _find_sheet(sheets, 'BONDS')
    if bonds_rows:
        bonds = bond_parser.parse_bonds_from_excel(bonds_rows)
        data['government_bonds'] = bonds['government_bonds']
        data['corporate_bonds'] = bonds['corporate_bonds']

    bond_trades_rows = _find_sheet(sheets, 'BONDS TRADES')
    if bond_trades_rows:
        data['bond_trades'] = bond_parser.parse_bond_trades_from_excel(bond_trades_rows)

    exchange_rows = _find_sheet(sheets, 'EXCHANGE RATE')
    if exchange_rows:
        data['exchange_rates'] = exchange_rate_parser.parse_exchange_rates_from_excel(exchange_rows)

    return data


def _find_sheet(sheets: dict, name: str):
    normalized = {k.strip().upper(): v for k, v in sheets.items()}
    return normalized.get(name.strip().upper())


def build_report(source_type: str, extraction, filename: str):
    if source_type == 'pdf':
        data = parse_pdf_report(extraction, filename)
    else:
        data = parse_excel_report(extraction, filename)
    return validate_report(data)
