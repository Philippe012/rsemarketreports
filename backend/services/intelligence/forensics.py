import re
from typing import List

from services.documents.schema_inference import parse_date_flexible
from services.normalization.clean_data import clean_text

MAX_ISSUES = 30

_CURRENCY_SYMBOL_RE = re.compile(r'[$€£¥]')
_CURRENCY_CODE_RE = re.compile(r'\b(USD|EUR|GBP|FRW|RWF|KES|KSH)\b', re.IGNORECASE)


def _currency_signatures(dataset: dict, column: dict) -> set:
    """Distinct currency symbols/codes actually written in this column's
    cells — more than one distinct signature means the column mixes units
    (e.g. some rows in "$" and others in "FRW")."""
    signatures = set()
    for row in dataset.get('rows', []):
        text = clean_text(row.get(column['name']))
        if text is None:
            continue
        symbols = frozenset(_CURRENCY_SYMBOL_RE.findall(text))
        codes = frozenset(m.upper() for m in _CURRENCY_CODE_RE.findall(text))
        signature = symbols | codes
        if signature:
            signatures.add(signature)
    return signatures


def _invalid_date_count(dataset: dict, column: dict) -> int:
    invalid = 0
    for row in dataset.get('rows', []):
        text = clean_text(row.get(column['name']))
        if text is None:
            continue
        if parse_date_flexible(text) is None:
            invalid += 1
    return invalid


def compute_forensics(datasets: List[dict]) -> dict:
    issues: List[dict] = []
    total_cells = 0
    missing_cells = 0
    total_rows = 0
    duplicate_rows = 0
    invalid_dates = 0
    inconsistent_unit_columns = 0

    for dataset in datasets:
        rows = dataset.get('rows', [])
        total_rows += len(rows)
        duplicate_rows += dataset.get('duplicate_row_count', 0) or 0

        if dataset.get('duplicate_row_count'):
            issues.append({
                'type': 'duplicates', 'severity': 'medium',
                'dataset': dataset['name'], 'column': None,
                'message': (
                    f'{dataset["duplicate_row_count"]} exact duplicate record(s) found in '
                    f'"{dataset["name"]}".'
                ),
            })

        for column in dataset.get('columns', []):
            column_total = column.get('total_count', 0) or 0
            non_null = column.get('non_null_count', 0) or 0
            total_cells += column_total
            missing = column_total - non_null
            missing_cells += missing

            if missing:
                severity = 'high' if column_total and missing / column_total >= 0.2 else 'medium'
                issues.append({
                    'type': 'missing_values', 'severity': severity,
                    'dataset': dataset['name'], 'column': column['display_name'],
                    'message': (
                        f'{missing} of {column_total} value(s) missing for '
                        f'"{column["display_name"]}" in "{dataset["name"]}".'
                    ),
                })

            if column.get('semantic_type') == 'date':
                invalid = _invalid_date_count(dataset, column)
                if invalid:
                    invalid_dates += invalid
                    issues.append({
                        'type': 'invalid_dates', 'severity': 'high',
                        'dataset': dataset['name'], 'column': column['display_name'],
                        'message': (
                            f'{invalid} value(s) in "{column["display_name"]}" ({dataset["name"]}) '
                            f'do not parse as a valid date.'
                        ),
                    })

            if column.get('semantic_type') == 'currency':
                signatures = _currency_signatures(dataset, column)
                if len(signatures) > 1:
                    inconsistent_unit_columns += 1
                    shown = ', '.join(''.join(sorted(s)) or '(none)' for s in list(signatures)[:4])
                    issues.append({
                        'type': 'inconsistent_units', 'severity': 'high',
                        'dataset': dataset['name'], 'column': column['display_name'],
                        'message': (
                            f'"{column["display_name"]}" in "{dataset["name"]}" mixes currency '
                            f'symbols/codes within the same column ({shown}).'
                        ),
                    })

    completeness = 1 - (missing_cells / total_cells) if total_cells else 1.0
    duplicate_penalty = min(duplicate_rows / total_rows, 0.3) if total_rows else 0.0
    invalid_date_penalty = min(invalid_dates / total_cells, 0.2) if total_cells else 0.0
    unit_penalty = min(inconsistent_unit_columns * 0.1, 0.3)
    score = round((completeness - duplicate_penalty - invalid_date_penalty - unit_penalty) * 100)
    score = max(0, min(100, score))

    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    issues.sort(key=lambda i: severity_order.get(i['severity'], 3))

    return {
        'quality_score': score,
        'total_rows': total_rows,
        'total_cells': total_cells,
        'missing_cells': missing_cells,
        'duplicate_rows': duplicate_rows,
        'invalid_dates': invalid_dates,
        'issues': issues[:MAX_ISSUES],
    }
