from typing import List, Optional

from services.documents.model import make_dataset
from services.documents.schema_inference import infer_columns

_RSE_LIST_FIELDS = (
    ('Equities', 'equities'),
    ('Government Bonds', 'government_bonds'),
    ('Corporate Bonds', 'corporate_bonds'),
    ('Bond Trades', 'bond_trades'),
    ('Indices', 'indices'),
    ('Exchange Rates', 'exchange_rates'),
    ('Trading Statistics', 'trading_stats'),
)


def _dataset_from_rows(name: str, source: str, rows: List[dict]) -> Optional[dict]:
    if not rows:
        return None
    headers: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    columns = infer_columns(headers, rows)
    return make_dataset(name, source, columns, rows)


def to_analysis_datasets(extracted_data: Optional[dict]) -> List[dict]:
    """Returns a list of dataset dicts regardless of which pipeline produced
    ``extracted_data``. An unknown/empty payload returns an empty list
    rather than raising — analysis modules should degrade gracefully on a
    document that has nothing to analyze."""
    if not extracted_data:
        return []

    kind = extracted_data.get('kind')
    if kind == 'generic_document':
        return extracted_data.get('datasets') or []

    if kind == 'rse_market_report':
        datasets = []
        for name, field in _RSE_LIST_FIELDS:
            dataset = _dataset_from_rows(name, 'RSE market report', extracted_data.get(field) or [])
            if dataset:
                datasets.append(dataset)
        return datasets

    return []
