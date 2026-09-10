import re
from typing import List, Optional

from services.documents.charts import MAX_CATEGORY_CARDINALITY, MAX_PIE_CARDINALITY
from services.documents.model import make_chart

_WORD_RE = re.compile(r'[a-z0-9]+')


def _tokens(text: str) -> set:
    return set(_WORD_RE.findall((text or '').lower()))


def suggest_visualization(datasets: List[dict], query: str) -> dict:
    query_tokens = _tokens(query)
    best_dataset, best_measure, best_score = None, None, -1

    for dataset in datasets:
        dataset_score = len(query_tokens & _tokens(dataset.get('name', '')))
        for column in dataset.get('columns', []):
            if column.get('semantic_type') not in ('currency', 'number', 'quantity'):
                continue
            score = dataset_score + len(query_tokens & _tokens(column.get('display_name', ''))) * 2
            if score > best_score:
                best_dataset, best_measure, best_score = dataset, column, score

    if best_dataset is None or best_measure is None:
        return {
            'dataset': None, 'chart': None,
            'reason': 'No dataset in this document matched that request.',
        }

    columns = best_dataset.get('columns', [])
    rows = best_dataset.get('rows', [])
    date_column = next((c for c in columns if c.get('semantic_type') in ('date', 'datetime')), None)
    category_column = next(
        (c for c in columns if c.get('semantic_type') == 'category'
         and 1 < len(set(str(row.get(c['name'])) for row in rows)) <= MAX_CATEGORY_CARDINALITY),
        None,
    )

    # If the query itself names a specific axis column, prefer that over the
    # pipeline's automatic pick.
    named_axis = next(
        (c for c in columns if c is not best_measure and _tokens(c.get('display_name', '')) & query_tokens),
        None,
    )
    if named_axis is not None:
        if named_axis.get('semantic_type') in ('date', 'datetime'):
            date_column, category_column = named_axis, None
        elif named_axis.get('semantic_type') == 'category':
            category_column = named_axis

    if date_column:
        chart = make_chart(
            best_dataset['name'], 'line', date_column['name'], best_measure['name'],
            f'{best_measure["display_name"]} over {date_column["display_name"]}',
        )
        reason = (
            f'Matched "{best_measure["display_name"]}" in "{best_dataset["name"]}"; plotted over time '
            f'since a date column is available.'
        )
    elif category_column:
        unique_count = len(set(str(row.get(category_column['name'])) for row in rows))
        chart_type = 'pie' if unique_count <= MAX_PIE_CARDINALITY else 'bar'
        chart = make_chart(
            best_dataset['name'], chart_type, category_column['name'], best_measure['name'],
            f'{best_measure["display_name"]} by {category_column["display_name"]}',
        )
        reason = (
            f'Matched "{best_measure["display_name"]}" in "{best_dataset["name"]}"; grouped by '
            f'"{category_column["display_name"]}".'
        )
    else:
        chart = None
        reason = (
            f'Found "{best_measure["display_name"]}" in "{best_dataset["name"]}" but no category or date '
            f'column to chart it against — showing the table instead.'
        )

    return {'dataset': best_dataset['name'], 'chart': chart, 'reason': reason}
