"""Tests for the Advanced Intelligence layer (services.intelligence):
unit tests against synthetic data for the individual modules, plus
end-to-end tests hitting the new API endpoints with the same real sample
files the rest of the suite already trusts (backend/reports/tests.py,
test_generic_documents.py) — one full upload -> /analysis/ round trip per
pipeline kind.
"""
import os

from django.conf import settings
from django.test import SimpleTestCase

from reports.models import Report
from reports.tests import AuthenticatedTestCase
from services.intelligence.adapter import to_analysis_datasets
from services.intelligence.alerts import evaluate_alerts
from services.intelligence.anomalies import detect_anomalies
from services.intelligence.dashboard_builder import suggest_visualization
from services.intelligence.forensics import compute_forensics
from services.intelligence.ranking import what_matters_most
from services.intelligence.timeline import compare_reports

SAMPLE_DIR = os.path.join(settings.BASE_DIR.parent, 'sample_data')
SAMPLE_PDF = os.path.join(SAMPLE_DIR, 'RSE_sample.pdf')
SALES_CSV = os.path.join(SAMPLE_DIR, 'generic_sales_sample.csv')


def _column(name, display_name, semantic_type, non_null_count, total_count, stats=None):
    return {
        'name': name, 'display_name': display_name, 'semantic_type': semantic_type,
        'data_type': 'number' if semantic_type in ('currency', 'number', 'quantity', 'percentage') else 'string',
        'nullable': non_null_count < total_count, 'non_null_count': non_null_count, 'total_count': total_count,
        'confidence': 'high', 'sample_values': [], 'stats': stats,
    }


class ForensicsTests(SimpleTestCase):
    def test_perfect_dataset_scores_100(self):
        dataset = {
            'name': 'Clean', 'row_count': 3, 'duplicate_row_count': 0,
            'rows': [{'Amount': 10}, {'Amount': 20}, {'Amount': 30}],
            'columns': [_column('Amount', 'Amount', 'currency', 3, 3, {'mean': 20, 'std': 8.16, 'min': 10, 'max': 30})],
        }
        report = compute_forensics([dataset])
        self.assertEqual(report['quality_score'], 100)
        self.assertEqual(report['issues'], [])

    def test_missing_values_and_duplicates_lower_the_score(self):
        dataset = {
            'name': 'Dirty', 'row_count': 4, 'duplicate_row_count': 2,
            'rows': [{'Amount': 10}, {'Amount': None}, {'Amount': 30}, {'Amount': 30}],
            'columns': [_column('Amount', 'Amount', 'currency', 2, 4, {'mean': 20, 'std': 10, 'min': 10, 'max': 30})],
        }
        report = compute_forensics([dataset])
        self.assertLess(report['quality_score'], 100)
        self.assertEqual(report['missing_cells'], 2)
        self.assertEqual(report['duplicate_rows'], 2)
        types = {issue['type'] for issue in report['issues']}
        self.assertIn('missing_values', types)
        self.assertIn('duplicates', types)

    def test_mixed_currency_symbols_flagged_as_inconsistent(self):
        dataset = {
            'name': 'Mixed', 'row_count': 2, 'duplicate_row_count': 0,
            'rows': [{'Price': '$10'}, {'Price': 'FRW 5000'}],
            'columns': [_column('Price', 'Price', 'currency', 2, 2, {'mean': 2505, 'std': 2495, 'min': 10, 'max': 5000})],
        }
        report = compute_forensics([dataset])
        types = {issue['type'] for issue in report['issues']}
        self.assertIn('inconsistent_units', types)


class AnomalyRadarTests(SimpleTestCase):
    def test_zscore_outlier_detected(self):
        values = [100] * 9 + [1000]
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        dataset = {
            'name': 'Readings', 'row_count': len(values),
            'rows': [{'Value': v} for v in values],
            'columns': [_column('Value', 'Value', 'number', len(values), len(values), {
                'mean': mean, 'std': std, 'min': min(values), 'max': max(values),
            })],
        }
        anomalies = detect_anomalies([dataset])
        self.assertTrue(any(a['type'] == 'outlier' and a['value'] == 1000 for a in anomalies))

    def test_mismatched_total_detected(self):
        dataset = {
            'name': 'Ledger', 'row_count': 3,
            'rows': [
                {'Category': 'North', 'Amount': 100},
                {'Category': 'South', 'Amount': 100},
                {'Category': 'Total', 'Amount': 500},
            ],
            'columns': [
                _column('Category', 'Category', 'category', 3, 3),
                _column('Amount', 'Amount', 'currency', 3, 3, {'mean': 233.3, 'std': 188.6, 'min': 100, 'max': 500}),
            ],
        }
        anomalies = detect_anomalies([dataset])
        self.assertTrue(any(a['type'] == 'mismatched_total' for a in anomalies))

    def test_no_anomalies_on_uniform_data(self):
        dataset = {
            'name': 'Flat', 'row_count': 4,
            'rows': [{'Value': 10}, {'Value': 10}, {'Value': 10}, {'Value': 10}],
            'columns': [_column('Value', 'Value', 'number', 4, 4, {'mean': 10, 'std': 0, 'min': 10, 'max': 10})],
        }
        self.assertEqual(detect_anomalies([dataset]), [])


class RankingTests(SimpleTestCase):
    def test_high_severity_findings_rank_first(self):
        forensics = {'issues': [{'severity': 'low', 'message': 'minor', 'dataset': 'D', 'column': 'C'}]}
        anomalies = [{'severity': 'high', 'message': 'big outlier', 'dataset': 'D', 'column': 'C'}]
        discoveries = ['A plain discovery.']
        ranked = what_matters_most(discoveries, anomalies, forensics)
        self.assertEqual(ranked[0]['text'], 'big outlier')
        self.assertEqual(ranked[0]['category'], 'anomaly')


class AlertsTests(SimpleTestCase):
    def test_alert_triggers_when_threshold_crossed(self):
        extracted_data = {
            'kind': 'generic_document',
            'datasets': [{
                'name': 'Sales', 'row_count': 2, 'duplicate_row_count': 0,
                'rows': [{'Revenue': 100}, {'Revenue': 200}],
                'columns': [_column('Revenue', 'Revenue', 'currency', 2, 2)],
            }],
        }
        rules = [{'id': 1, 'metric_label': 'Total revenue', 'dataset': 'Sales', 'column': 'Revenue', 'operator': 'gt', 'threshold': 250}]
        results = evaluate_alerts(rules, extracted_data)
        self.assertTrue(results[0]['triggered'])
        self.assertEqual(results[0]['current_value'], 300)

    def test_alert_not_triggered_when_below_threshold(self):
        extracted_data = {
            'kind': 'generic_document',
            'datasets': [{
                'name': 'Sales', 'row_count': 1, 'duplicate_row_count': 0,
                'rows': [{'Revenue': 100}],
                'columns': [_column('Revenue', 'Revenue', 'currency', 1, 1)],
            }],
        }
        rules = [{'id': 1, 'metric_label': 'Total revenue', 'dataset': 'Sales', 'column': 'Revenue', 'operator': 'gt', 'threshold': 250}]
        results = evaluate_alerts(rules, extracted_data)
        self.assertFalse(results[0]['triggered'])


class DashboardBuilderTests(SimpleTestCase):
    def test_matches_measure_and_category_from_query(self):
        datasets = [{
            'name': 'Sales', 'row_count': 4,
            'rows': [
                {'Region': 'East', 'Revenue': 100}, {'Region': 'West', 'Revenue': 200},
                {'Region': 'East', 'Revenue': 150}, {'Region': 'North', 'Revenue': 50},
            ],
            'columns': [
                _column('Region', 'Region', 'category', 4, 4),
                _column('Revenue', 'Revenue', 'currency', 4, 4),
            ],
        }]
        result = suggest_visualization(datasets, 'show revenue by region')
        self.assertEqual(result['dataset'], 'Sales')
        self.assertIsNotNone(result['chart'])
        self.assertEqual(result['chart']['x'], 'Region')
        self.assertEqual(result['chart']['y'], 'Revenue')

    def test_no_match_returns_honest_reason(self):
        result = suggest_visualization([], 'show me profit by planet')
        self.assertIsNone(result['dataset'])
        self.assertIsNone(result['chart'])


class TimelineTests(SimpleTestCase):
    def test_different_kinds_are_not_comparable(self):
        result = compare_reports({'kind': 'generic_document'}, {'kind': 'rse_market_report'})
        self.assertFalse(result['comparable'])

    def test_dataset_row_changes_are_detected(self):
        base = {'kind': 'generic_document', 'metrics': [], 'datasets': [{
            'name': 'Sales', 'row_count': 1, 'duplicate_row_count': 0,
            'rows': [{'Revenue': 100}], 'columns': [_column('Revenue', 'Revenue', 'currency', 1, 1)],
        }]}
        other = {'kind': 'generic_document', 'metrics': [], 'datasets': [{
            'name': 'Sales', 'row_count': 2, 'duplicate_row_count': 0,
            'rows': [{'Revenue': 100}, {'Revenue': 300}], 'columns': [_column('Revenue', 'Revenue', 'currency', 2, 2)],
        }]}
        result = compare_reports(base, other)
        self.assertTrue(result['comparable'])
        diff = result['dataset_diffs'][0]
        self.assertEqual(diff['status'], 'changed')
        self.assertEqual(diff['rows_added'], 1)


class RseAdapterTests(SimpleTestCase):
    def test_rse_lists_become_datasets_with_inferred_columns(self):
        extracted_data = {
            'kind': 'rse_market_report',
            'equities': [
                {'ticker': 'BOK', 'isin': 'RW001', 'closing': 660, 'previous': 650, 'change': 10, 'volume': 21600, 'value': 14256000},
                {'ticker': 'BLR', 'isin': 'RW002', 'closing': 120, 'previous': 130, 'change': -10, 'volume': 500, 'value': 60000},
            ],
        }
        datasets = to_analysis_datasets(extracted_data)
        equities_dataset = next(d for d in datasets if d['name'] == 'Equities')
        self.assertEqual(equities_dataset['row_count'], 2)
        semantic_types = {c['name']: c['semantic_type'] for c in equities_dataset['columns']}
        self.assertEqual(semantic_types['closing'], 'number')
        # "isin" is a recognized identifier-name hint; "ticker" isn't, so with
        # only two rows it reads as a (correctly) low-cardinality category —
        # the same schema_inference behavior generic documents already rely on.
        self.assertEqual(semantic_types['isin'], 'identifier')
        self.assertEqual(semantic_types['ticker'], 'category')


class GenericDocumentAnalysisEndpointTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SALES_CSV, 'rb') as f:
            upload = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')
        self.report_id = upload.json()['id']

    def test_analysis_endpoint_returns_full_bundle(self):
        response = self.client.get(f'/api/reports/{self.report_id}/analysis/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ('investigate', 'forensics', 'anomalies', 'discoveries', 'what_matters_most',
                    'relationships', 'geography', 'vision', 'alerts'):
            self.assertIn(key, body)
        self.assertIsNone(body['trading'])
        self.assertGreaterEqual(body['forensics']['quality_score'], 0)

    def test_explain_metric_returns_source_rows(self):
        response = self.client.post(f'/api/reports/{self.report_id}/explain/', {
            'dataset': 'Data', 'column': 'Revenue', 'kind': 'sum',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('calculation', body)
        self.assertGreater(len(body['source_rows']), 0)

    def test_dashboard_builder_endpoint(self):
        response = self.client.post(f'/api/reports/{self.report_id}/dashboard-builder/', {
            'query': 'revenue by region',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()['dataset'])

    def test_alerts_crud(self):
        create = self.client.post(f'/api/reports/{self.report_id}/alerts/', {
            'metric_label': 'High revenue', 'dataset': 'Sales data', 'column': 'Revenue',
            'operator': 'gt', 'threshold': 1,
        }, content_type='application/json')
        self.assertEqual(create.status_code, 201)
        alert_id = create.json()['id']

        listing = self.client.get(f'/api/reports/{self.report_id}/alerts/')
        self.assertEqual(len(listing.json()), 1)

        delete = self.client.delete(f'/api/reports/{self.report_id}/alerts/{alert_id}/')
        self.assertEqual(delete.status_code, 204)
        self.assertEqual(len(self.client.get(f'/api/reports/{self.report_id}/alerts/').json()), 0)


class RseAnalysisEndpointTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            upload = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')
        self.report_id = upload.json()['id']

    def test_analysis_endpoint_includes_trading_view(self):
        response = self.client.get(f'/api/reports/{self.report_id}/analysis/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNotNone(body['trading'])
        self.assertIn('top_gainers', body['trading'])

    def test_compare_against_itself_is_comparable(self):
        response = self.client.get(f'/api/reports/{self.report_id}/compare/', {'with': self.report_id})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['comparable'])
        for diff in body['dataset_diffs']:
            self.assertEqual(diff['status'], 'unchanged')


class ChatIntelligenceExtensionTests(AuthenticatedTestCase):
    def test_generic_chat_answers_what_matters_most(self):
        with open(SALES_CSV, 'rb') as f:
            upload = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')
        report_id = upload.json()['id']
        response = self.client.post(f'/api/reports/{report_id}/chat/', {'message': 'What matters most in this document?'},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 201)
        answer = response.json()['assistant_message']['content']
        self.assertNotIn("couldn't find", answer.lower())

    def test_rse_chat_answers_data_quality_question(self):
        with open(SAMPLE_PDF, 'rb') as f:
            upload = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')
        report_id = upload.json()['id']
        response = self.client.post(f'/api/reports/{report_id}/chat/', {'message': 'How clean and reliable is this data?'},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('quality score', response.json()['assistant_message']['content'].lower())
