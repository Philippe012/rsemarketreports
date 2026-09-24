from typing import List

from services.normalization.clean_data import parse_date, parse_number

Z_THRESHOLD = 2.5
Z_HIGH_SEVERITY = 4.0
JUMP_THRESHOLD = 0.5
JUMP_HIGH_SEVERITY = 1.0
TOTAL_LABELS = {'total', 'grand total', 'subtotal', 'sum', 'overall'}
MAX_ANOMALIES = 40


def _zscore_outliers(dataset: dict, column: dict) -> List[dict]:
    stats = column.get('stats')
    if not stats or not stats.get('std'):
        return []
    mean, std = stats['mean'], stats['std']
    found = []
    for index, row in enumerate(dataset.get('rows', [])):
        value = parse_number(row.get(column['name']))
        if value is None:
            continue
        z = abs(value - mean) / std
        if z <= Z_THRESHOLD:
            continue
        severity = 'high' if z >= Z_HIGH_SEVERITY else 'medium'
        found.append({
            'type': 'outlier', 'severity': severity,
            'dataset': dataset['name'], 'column': column['display_name'],
            'row_index': index, 'value': value,
            'message': (
                f'"{column["display_name"]}" value {value:,.2f} in row {index + 1} of '
                f'"{dataset["name"]}" is {z:.1f} standard deviations from the mean ({mean:,.2f}).'
            ),
        })
    return found


def _period_jumps(dataset: dict, date_column: dict, measure_column: dict) -> List[dict]:
    points = []
    for index, row in enumerate(dataset.get('rows', [])):
        date_str = parse_date(row.get(date_column['name']))
        value = parse_number(row.get(measure_column['name']))
        if date_str is None or value is None:
            continue
        points.append((date_str, value, index))
    if len(points) < 2:
        return []
    points.sort(key=lambda p: p[0])

    found = []
    for i in range(1, len(points)):
        prev_date, prev_value, _ = points[i - 1]
        cur_date, cur_value, row_index = points[i]
        
        if prev_value == 0:
            continue
        change = (cur_value - prev_value) / abs(prev_value)
        
        if abs(change) < JUMP_THRESHOLD:
            continue
        severity = 'high' if abs(change) >= JUMP_HIGH_SEVERITY else 'medium'
        found.append({
            'type': 'sudden_change', 'severity': severity,
            'dataset': dataset['name'], 'column': measure_column['display_name'],
            'row_index': row_index, 'value': cur_value,
            'message': (
                f'"{measure_column["display_name"]}" in "{dataset["name"]}" moved {change * 100:+.0f}% '
                f'from {prev_date} ({prev_value:,.2f}) to {cur_date} ({cur_value:,.2f}).'
            ),
        })
    return found


def _mismatched_totals(dataset: dict, category_column: dict, measure_column: dict) -> List[dict]:
    total_declared = None
    parts_sum = 0.0
    parts_seen = False
    for row in dataset.get('rows', []):
        label = str(row.get(category_column['name']) or '').strip().lower()
        value = parse_number(row.get(measure_column['name']))
        if value is None:
            continue
        if label in TOTAL_LABELS:
            total_declared = value
        else:
            parts_sum += value
            parts_seen = True

    if total_declared is None or not parts_seen:
        return []
    tolerance = max(abs(total_declared) * 0.01, 0.01)
    if abs(total_declared - parts_sum) <= tolerance:
        return []
    return [{
        'type': 'mismatched_total', 'severity': 'high',
        'dataset': dataset['name'], 'column': measure_column['display_name'], 'row_index': None,
        'value': total_declared,
        'message': (
            f'The declared total for "{measure_column["display_name"]}" in "{dataset["name"]}" is '
            f'{total_declared:,.2f}, but the individual rows sum to {parts_sum:,.2f}.'
        ),
    }]


def detect_anomalies(datasets: List[dict]) -> List[dict]:
    anomalies: List[dict] = []
    for dataset in datasets:
        columns = dataset.get('columns', [])
        measures = [c for c in columns if c.get('semantic_type') in ('currency', 'number', 'quantity')]
        categories = [c for c in columns if c.get('semantic_type') == 'category']
        dates = [c for c in columns if c.get('semantic_type') in ('date', 'datetime')]

        for measure in measures:
            anomalies.extend(_zscore_outliers(dataset, measure))
            for category in categories[:1]:
                anomalies.extend(_mismatched_totals(dataset, category, measure))
            for date_column in dates[:1]:
                anomalies.extend(_period_jumps(dataset, date_column, measure))

    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    anomalies.sort(key=lambda a: severity_order.get(a['severity'], 3))
    return anomalies[:MAX_ANOMALIES]
