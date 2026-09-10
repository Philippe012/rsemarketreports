import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from reports.models import Report
from reports.tests import AuthenticatedTestCase

User = get_user_model()

SAMPLE_DIR = os.path.join(settings.BASE_DIR.parent, 'sample_data')
SAMPLE_PDF = os.path.join(SAMPLE_DIR, 'RSE_sample.pdf')
SALES_CSV = os.path.join(SAMPLE_DIR, 'generic_sales_sample.csv')


class ReportRenameAndDeleteTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            self.report_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']

    def test_rename_updates_filename(self):
        response = self.client.patch(
            f'/api/reports/{self.report_id}/', {'original_filename': 'renamed.pdf'}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['original_filename'], 'renamed.pdf')

    def test_rename_rejects_blank_filename(self):
        response = self.client.patch(
            f'/api/reports/{self.report_id}/', {'original_filename': '   '}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_removes_report(self):
        response = self.client.delete(f'/api/reports/{self.report_id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Report.objects.filter(pk=self.report_id).exists())
        self.assertEqual(self.client.get(f'/api/reports/{self.report_id}/').status_code, 404)


class ReportListFilteringTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            self.rse_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']
        with open(SALES_CSV, 'rb') as f:
            self.csv_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']

    def test_list_returns_paginated_envelope_with_facets(self):
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ('results', 'count', 'page', 'page_size', 'total_pages', 'facets'):
            self.assertIn(key, body)
        self.assertEqual(body['count'], 2)
        self.assertIn('pdf', body['facets']['source_types'])
        self.assertIn('csv', body['facets']['source_types'])

    def test_filter_by_source_type(self):
        response = self.client.get('/api/reports/', {'source_type': 'csv'})
        results = response.json()['results']
        self.assertEqual([r['id'] for r in results], [self.csv_id])

    def test_filter_by_document_type_is_dynamic_not_rse_hardcoded(self):
        response = self.client.get('/api/reports/', {'document_type': 'sales'})
        results = response.json()['results']
        self.assertEqual([r['id'] for r in results], [self.csv_id])
        self.assertEqual(results[0]['document_type'], 'Sales')

        rse_response = self.client.get('/api/reports/', {'document_type': 'rse'})
        self.assertEqual([r['id'] for r in rse_response.json()['results']], [self.rse_id])

    def test_search_matches_filename(self):
        response = self.client.get('/api/reports/', {'search': 'generic_sales'})
        self.assertEqual([r['id'] for r in response.json()['results']], [self.csv_id])

    def test_sort_by_headline_value_descending(self):
        response = self.client.get('/api/reports/', {'sort': '-value'})
        results = response.json()['results']
        # The RSE report's market capitalization dwarfs the CSV's revenue total.
        self.assertEqual(results[0]['id'], self.rse_id)

    def test_pagination_page_size(self):
        response = self.client.get('/api/reports/', {'page_size': 1, 'page': 2})
        body = response.json()
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['page'], 2)
        self.assertEqual(body['total_pages'], 2)

    def test_rse_report_has_headline_metric_and_insights(self):
        report = Report.objects.get(pk=self.rse_id)
        self.assertEqual(report.headline_metric_label, 'Market capitalization')
        self.assertIsNotNone(report.headline_metric_value)
        self.assertGreater(len(report.extracted_data['insights']), 0)


class ReportBulkDeleteTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            self.report_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']
        self.other = User.objects.create_user(username='someone-else@example.com', email='someone-else@example.com', password='pw12345678')
        self.others_report = Report.objects.create(
            user=self.other, original_filename='not-mine.pdf', source_type=Report.SourceType.PDF,
            status=Report.Status.COMPLETED,
        )

    def test_user_can_only_bulk_delete_their_own(self):
        response = self.client.post(
            '/api/reports/bulk-delete/', {'ids': [self.report_id, str(self.others_report.id)]}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['deleted'], [self.report_id])
        self.assertFalse(Report.objects.filter(pk=self.report_id).exists())
        self.assertTrue(Report.objects.filter(pk=self.others_report.id).exists())

    def test_empty_ids_rejected(self):
        response = self.client.post('/api/reports/bulk-delete/', {'ids': []}, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class ReportAdminAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff@example.com', email='staff@example.com', password='staff-pass-123', is_staff=True)
        self.regular = User.objects.create_user(username='regular@example.com', email='regular@example.com', password='regular-pass-123')
        self.regulars_report = Report.objects.create(
            user=self.regular, original_filename='mine.pdf', source_type=Report.SourceType.PDF,
            status=Report.Status.COMPLETED,
        )

    def test_regular_user_cannot_access_admin_list(self):
        self.client.login(username='regular@example.com', password='regular-pass-123')
        self.assertEqual(self.client.get('/api/reports/admin/').status_code, 403)

    def test_staff_sees_every_users_documents_with_owner_email(self):
        self.client.login(username='staff@example.com', password='staff-pass-123')
        response = self.client.get('/api/reports/admin/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['owner_email'], 'regular@example.com')

    def test_staff_can_delete_another_users_document(self):
        self.client.login(username='staff@example.com', password='staff-pass-123')
        response = self.client.post(
            '/api/reports/bulk-delete/', {'ids': [str(self.regulars_report.id)]}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Report.objects.filter(pk=self.regulars_report.id).exists())

    def test_me_endpoint_exposes_is_staff(self):
        self.client.login(username='staff@example.com', password='staff-pass-123')
        response = self.client.get('/api/auth/me/')
        self.assertTrue(response.json()['is_staff'])
