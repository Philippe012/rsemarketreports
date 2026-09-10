from typing import List, Optional

from services.normalization.clean_data import parse_number

from .adapter import to_analysis_datasets

_OPERATORS = {
    'gt': lambda value, threshold: value > threshold,
    'gte': lambda value, threshold: value >= threshold,
    'lt': lambda value, threshold: value < threshold,
    'lte': lambda value, threshold: value <= threshold,
}


def _dataset_total(datasets: List[dict], dataset_name: str, column_name: str) -> Optional[float]:
    dataset = next((d for d in datasets if d['name'] == dataset_name), None)
    if dataset is None:
        return None
    values = [parse_number(row.get(column_name)) for row in dataset.get('rows', [])]
    values = [v for v in values if v is not None]
    return sum(values) if values else None


def evaluate_alerts(rules: List[dict], extracted_data: dict) -> List[dict]:
    datasets = to_analysis_datasets(extracted_data)
    results = []
    for rule in rules:
        current_value = _dataset_total(datasets, rule['dataset'], rule['column'])
        triggered = False
        if current_value is not None:
            operator = _OPERATORS.get(rule['operator'])
            if operator:
                triggered = operator(current_value, rule['threshold'])
        results.append({
            'id': rule.get('id'),
            'metric_label': rule.get('metric_label'),
            'dataset': rule.get('dataset'),
            'column': rule.get('column'),
            'operator': rule.get('operator'),
            'threshold': rule.get('threshold'),
            'current_value': current_value,
            'triggered': triggered,
        })
    return results
