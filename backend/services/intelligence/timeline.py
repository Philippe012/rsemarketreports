from typing import List

from .adapter import to_analysis_datasets


def _metrics_by_label(data: dict) -> dict:
    return {m['label']: m for m in (data.get('metrics') or [])}


def _row_key(row: dict) -> tuple:
    return tuple(sorted((str(k), str(v)) for k, v in row.items()))


def compare_reports(base_data: dict, other_data: dict) -> dict:
    base_kind, other_kind = base_data.get('kind'), other_data.get('kind')
    if base_kind != other_kind:
        return {
            'comparable': False,
            'reason': 'These two documents are different kinds of reports and cannot be compared directly.',
        }

    metric_diffs: List[dict] = []
    base_metrics, other_metrics = _metrics_by_label(base_data), _metrics_by_label(other_data)
    for label in sorted(set(base_metrics) | set(other_metrics)):
        before = base_metrics.get(label, {}).get('value')
        after = other_metrics.get(label, {}).get('value')
        delta = percent_delta = None
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            delta = after - before
            percent_delta = (delta / before * 100) if before else None
        metric_diffs.append({'label': label, 'before': before, 'after': after, 'delta': delta, 'percent_delta': percent_delta})

    base_datasets = {d['name']: d for d in to_analysis_datasets(base_data)}
    other_datasets = {d['name']: d for d in to_analysis_datasets(other_data)}
    dataset_diffs: List[dict] = []
    for name in sorted(set(base_datasets) | set(other_datasets)):
        base_dataset, other_dataset = base_datasets.get(name), other_datasets.get(name)
        if base_dataset is None or other_dataset is None:
            dataset_diffs.append({
                'dataset': name, 'status': 'added' if base_dataset is None else 'removed',
                'row_count_before': base_dataset['row_count'] if base_dataset else 0,
                'row_count_after': other_dataset['row_count'] if other_dataset else 0,
                'rows_added': 0, 'rows_removed': 0,
            })
            continue
        base_keys = {_row_key(row) for row in base_dataset.get('rows', [])}
        other_keys = {_row_key(row) for row in other_dataset.get('rows', [])}
        dataset_diffs.append({
            'dataset': name,
            'status': 'unchanged' if base_keys == other_keys else 'changed',
            'row_count_before': base_dataset['row_count'],
            'row_count_after': other_dataset['row_count'],
            'rows_added': len(other_keys - base_keys),
            'rows_removed': len(base_keys - other_keys),
        })

    return {'comparable': True, 'metric_diffs': metric_diffs, 'dataset_diffs': dataset_diffs}
