from typing import List

import numpy as np

from services.normalization.clean_data import parse_number

MAX_NODES = 30
MAX_EDGES = 40
MIN_CORRELATION = 0.6
MIN_CORRELATION_ROWS = 5


def _node_id(dataset_name: str, column_name: str, value: str) -> str:
    return f'{dataset_name}::{column_name}::{value}'


def entity_relationship_graph(datasets: List[dict]) -> dict:
    nodes: dict = {}
    edges: dict = {}

    def add_node(node_id: str, label: str, node_type: str, dataset_name: str) -> None:
        node = nodes.setdefault(node_id, {
            'id': node_id, 'label': label, 'type': node_type, 'dataset': dataset_name, 'weight': 0,
        })
        node['weight'] += 1

    def add_edge(a: str, b: str, edge_type: str, weight: int = 1, extra: dict | None = None) -> None:
        key = tuple(sorted((a, b))) + (edge_type,)
        edge = edges.get(key)
        if edge is None:
            edge = {'source': key[0], 'target': key[1], 'type': edge_type, 'weight': 0}
            edges[key] = edge
        if extra:
            edge.update(extra)
        edge['weight'] += weight

    for dataset in datasets:
        columns = dataset.get('columns', [])
        rows = dataset.get('rows', [])
        categories = [c for c in columns if c.get('semantic_type') == 'category'][:2]
        measures = [c for c in columns if c.get('semantic_type') in ('currency', 'number', 'quantity')]

        if len(categories) == 2:
            col_a, col_b = categories
            for row in rows:
                value_a, value_b = row.get(col_a['name']), row.get(col_b['name'])
                if value_a in (None, '') or value_b in (None, ''):
                    continue
                node_a = _node_id(dataset['name'], col_a['name'], str(value_a))
                node_b = _node_id(dataset['name'], col_b['name'], str(value_b))
                add_node(node_a, str(value_a), 'category', dataset['name'])
                add_node(node_b, str(value_b), 'category', dataset['name'])
                add_edge(node_a, node_b, 'co_occurs')

        for i in range(len(measures)):
            for j in range(i + 1, len(measures)):
                col_a, col_b = measures[i], measures[j]
                pairs = []
                for row in rows:
                    a = parse_number(row.get(col_a['name']))
                    b = parse_number(row.get(col_b['name']))
                    if a is not None and b is not None:
                        pairs.append((a, b))
                if len(pairs) < MIN_CORRELATION_ROWS:
                    continue
                a_values = np.array([p[0] for p in pairs], dtype='float64')
                b_values = np.array([p[1] for p in pairs], dtype='float64')
                if np.std(a_values) == 0 or np.std(b_values) == 0:
                    continue
                correlation = float(np.corrcoef(a_values, b_values)[0, 1])
                if np.isnan(correlation) or abs(correlation) < MIN_CORRELATION:
                    continue
                node_a = _node_id(dataset['name'], col_a['name'], col_a['display_name'])
                node_b = _node_id(dataset['name'], col_b['name'], col_b['display_name'])
                add_node(node_a, col_a['display_name'], 'measure', dataset['name'])
                add_node(node_b, col_b['display_name'], 'measure', dataset['name'])
                add_edge(node_a, node_b, 'correlates', weight=len(pairs), extra={
                    'correlation': round(correlation, 2), 'evidence_count': len(pairs),
                })

    node_list = sorted(nodes.values(), key=lambda n: n['weight'], reverse=True)[:MAX_NODES]
    node_ids = {n['id'] for n in node_list}
    edge_list = [e for e in edges.values() if e['source'] in node_ids and e['target'] in node_ids]
    edge_list.sort(key=lambda e: e['weight'], reverse=True)

    return {'nodes': node_list, 'edges': edge_list[:MAX_EDGES]}
