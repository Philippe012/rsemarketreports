import os

import openpyxl
from django.conf import settings
from django.test import SimpleTestCase, TestCase

from reports.models import Report
from reports.tests import AuthenticatedTestCase
from services.documents.classification import classify_document
from services.documents.schema_inference import infer_column

SAMPLE_DIR = os.path.join(settings.BASE_DIR.parent, 'sample_data')
SALES_CSV = os.path.join(SAMPLE_DIR, 'generic_sales_sample.csv')
HR_XLSX = os.path.join(SAMPLE_DIR, 'generic_hr_sample.xlsx')
OPERATIONS_DOCX = os.path.join(SAMPLE_DIR, 'generic_operations_sample.docx')
NOTES_TXT = os.path.join(SAMPLE_DIR, 'generic_notes_sample.txt')
PROSE_ONLY_TXT = os.path.join(SAMPLE_DIR, 'generic_prose_only_sample.txt')
OPERATIONS_PDF = os.path.join(SAMPLE_DIR, 'generic_operations_sample.pdf')


class SchemaInferenceTests(SimpleTestCase):
    def test_infers_currency_from_name_and_values(self):
        column = infer_column('Revenue', [4800000, 3400000, 5600000])
        self.assertEqual(column['semantic_type'], 'currency')

    def test_infers_percentage_from_percent_sign(self):
        column = infer_column('Discount', ['5%', '0%', '10%'])
        self.assertEqual(column['semantic_type'], 'percentage')

    def test_infers_date_column(self):
        column = infer_column('Date', ['2025-01-15', '2025-02-10', '2025-03-05'])
        self.assertEqual(column['semantic_type'], 'date')

    def test_infers_category_for_low_cardinality_text(self):
        column = infer_column('Region', ['East Africa', 'West Africa', 'East Africa', 'Central Africa'] * 3)
        self.assertEqual(column['semantic_type'], 'category')

    def test_infers_identifier_for_high_cardinality_coded_column(self):
        column = infer_column('Employee ID', [f'E{i:03d}' for i in range(20)])
        self.assertEqual(column['semantic_type'], 'identifier')

    def test_never_invents_a_type_for_an_empty_column(self):
        column = infer_column('Notes', [])
        self.assertEqual(column['non_null_count'], 0)
        self.assertEqual(column['confidence'], 'low')


class EntityExtractionTests(SimpleTestCase):
    def test_extracts_currency_and_percent_mentions(self):
        from services.documents.entities import extract_entities

        text = "Revenue grew 12% to reach $4.5 million, with costs up 3%."
        entities = extract_entities(text)
        self.assertIn('$4.5 million', entities['numbers'])
        self.assertIn('12%', entities['numbers'])

    def test_extracts_dates(self):
        from services.documents.entities import extract_entities

        entities = extract_entities("The program launched in March 2024 and ended on 12/05/2025.")
        self.assertIn('March 2024', entities['dates'])
        self.assertIn('12/05/2025', entities['dates'])

    def test_keywords_require_repetition(self):
        from services.documents.entities import extract_entities

        entities = extract_entities("The clinic served patients. The clinic was busy. One clinic visit only.")
        self.assertIn('clinic', entities['keywords'])
        # "patients" appears once — not a "frequently mentioned" term.
        self.assertNotIn('patients', entities['keywords'])

    def test_no_entities_in_empty_text(self):
        from services.documents.entities import extract_entities

        entities = extract_entities('')
        self.assertEqual(entities, {'numbers': [], 'dates': [], 'keywords': []})


class InsightsComputationTests(SimpleTestCase):
    def test_range_insight_for_numeric_column(self):
        from services.documents.insights import compute_insights

        datasets = [{
            'name': 'Sales', 'row_count': 3, 'duplicate_row_count': 0,
            'rows': [{'Revenue': 100}, {'Revenue': 300}, {'Revenue': 200}],
            'columns': [{
                'name': 'Revenue', 'display_name': 'Revenue', 'semantic_type': 'currency',
                'stats': {'min': 100, 'max': 300, 'mean': 200, 'std': 100, 'unique_count': 3, 'missing_count': 0},
            }],
        }]
        insights = compute_insights(datasets)
        self.assertTrue(any('100' in i and '300' in i for i in insights))

    def test_no_insight_when_column_is_constant(self):
        from services.documents.insights import compute_insights

        datasets = [{
            'name': 'Flat', 'row_count': 3, 'duplicate_row_count': 0,
            'rows': [{'Value': 5}, {'Value': 5}, {'Value': 5}],
            'columns': [{
                'name': 'Value', 'display_name': 'Value', 'semantic_type': 'number',
                'stats': {'min': 5, 'max': 5, 'mean': 5, 'std': 0, 'unique_count': 1, 'missing_count': 0},
            }],
        }]
        self.assertEqual(compute_insights(datasets), [])

    def test_no_insights_for_empty_dataset_list(self):
        from services.documents.insights import compute_insights

        self.assertEqual(compute_insights([]), [])


class DuplicateRowDetectionTests(TestCase):

    def test_duplicate_rows_are_counted(self):
        from services.pipeline import process_report_file

        csv_content = 'Name,City\nAda,Kigali\nBob,Musanze\nAda,Kigali\n'
        tmp_path = os.path.join(settings.BASE_DIR, 'uploads', 'tmp_dup_test.csv')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        try:
            result = process_report_file(tmp_path, 'tmp_dup_test.csv')
            dataset = result['data']['datasets'][0]
            self.assertEqual(dataset['duplicate_row_count'], 1)
        finally:
            os.remove(tmp_path)


class DocumentClassificationTests(SimpleTestCase):
    def test_classifies_sales_dataset(self):
        datasets = [{'columns': [
            {'name': 'Region', 'display_name': 'Region'},
            {'name': 'Product', 'display_name': 'Product'},
            {'name': 'Revenue', 'display_name': 'Revenue'},
            {'name': 'Units Sold', 'display_name': 'Units Sold'},
        ]}]
        label, confidence = classify_document(datasets)
        self.assertEqual(label, 'Sales')
        self.assertIn(confidence, ('high', 'medium'))

    def test_falls_back_to_general_dataset_when_unrecognized(self):
        datasets = [{'columns': [{'name': 'Foo', 'display_name': 'Foo'}, {'name': 'Bar', 'display_name': 'Bar'}]}]
        label, confidence = classify_document(datasets)
        self.assertEqual(label, 'General dataset')
        self.assertEqual(confidence, 'low')


class GenericCsvUploadTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SALES_CSV, 'rb') as f:
            self.response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')

    def test_upload_succeeds_and_is_routed_generically(self):
        self.assertEqual(self.response.status_code, 201)
        data = self.response.json()
        self.assertEqual(data['status'], Report.Status.COMPLETED)
        self.assertEqual(data['source_type'], 'csv')
        self.assertEqual(data['extracted_data']['kind'], 'generic_document')

    def test_dataset_and_columns_extracted_correctly(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(len(document['datasets']), 1)
        dataset = document['datasets'][0]
        self.assertEqual(dataset['row_count'], 12)
        semantic_types = {c['name']: c['semantic_type'] for c in dataset['columns']}
        self.assertEqual(semantic_types['Date'], 'date')
        self.assertEqual(semantic_types['Region'], 'category')
        self.assertEqual(semantic_types['Revenue'], 'currency')
        self.assertEqual(semantic_types['Discount %'], 'percentage')

    def test_document_classified_as_sales(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(document['document_type'], 'Sales')

    def test_metrics_are_real_aggregates_not_invented(self):
        document = self.response.json()['extracted_data']
        revenue_metric = next(m for m in document['metrics'] if m['column'] == 'Revenue')
        self.assertAlmostEqual(revenue_metric['value'], 40875000.0)

    def test_download_returns_workbook_with_dataset_sheet(self):
        
        report_id = self.response.json()['id']
        download = self.client.get(f'/api/reports/{report_id}/download/')
        self.assertEqual(download.status_code, 200)
        workbook = openpyxl.load_workbook(__import__('io').BytesIO(b''.join(download.streaming_content)))
        self.assertIn('OVERVIEW', workbook.sheetnames)
        self.assertIn('Data', workbook.sheetnames)
        rows = list(workbook['Data'].iter_rows(min_row=2, values_only=True))
        self.assertEqual(len(rows), 12)


class GenericExcelUploadTests(AuthenticatedTestCase):
    def test_multi_sheet_excel_produces_multiple_datasets(self):
        with open(HR_XLSX, 'rb') as f:
            response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')
        self.assertEqual(response.status_code, 201)
        document = response.json()['extracted_data']
        self.assertEqual(document['kind'], 'generic_document')
        dataset_names = {d['name'] for d in document['datasets']}
        self.assertEqual(dataset_names, {'Employees', 'Departments'})
        self.assertEqual(document['document_type'], 'HR')


class GenericDocxUploadTests(AuthenticatedTestCase):

    def setUp(self):
        super().setUp()
        with open(OPERATIONS_DOCX, 'rb') as f:
            self.response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')

    def test_upload_succeeds(self):
        self.assertEqual(self.response.status_code, 201)
        data = self.response.json()
        self.assertEqual(data['source_type'], 'docx')
        self.assertEqual(data['extracted_data']['kind'], 'generic_document')

    def test_both_tables_extracted_as_separate_datasets(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(len(document['datasets']), 2)
        row_counts = sorted(d['row_count'] for d in document['datasets'])
        self.assertEqual(row_counts, [3, 3])

    def test_narrative_text_preserved_as_sections_with_headings(self):
        document = self.response.json()['extracted_data']
        headings = [s['title'] for s in document['sections']]
        self.assertIn('Quarterly Operations Report', headings)
        self.assertIn('Outlook', headings)

    def test_table_values_are_not_invented(self):
        document = self.response.json()['extracted_data']
        throughput = next(d for d in document['datasets'] if 'Shipments' in {c['name'] for c in d['columns']})
        kigali = next(r for r in throughput['rows'] if r['Center'] == 'Kigali Hub')
        self.assertEqual(kigali['Shipments'], '4820')
        self.assertEqual(kigali['On-Time %'], '96.5')


class GenericTxtUploadTests(AuthenticatedTestCase):

    def setUp(self):
        super().setUp()
        with open(NOTES_TXT, 'rb') as f:
            self.response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')

    def test_upload_succeeds(self):
        self.assertEqual(self.response.status_code, 201)
        data = self.response.json()
        self.assertEqual(data['source_type'], 'txt')
        self.assertEqual(data['extracted_data']['kind'], 'generic_document')

    def test_embedded_table_detected(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(len(document['datasets']), 1)
        dataset = document['datasets'][0]
        self.assertEqual(dataset['row_count'], 5)
        semantic_types = {c['name']: c['semantic_type'] for c in dataset['columns']}
        self.assertEqual(semantic_types['Cost (USD)'], 'currency')

    def test_headings_recognised_around_the_table(self):
        document = self.response.json()['extracted_data']
        headings = [s['title'] for s in document['sections']]
        self.assertIn('Monthly Fuel Consumption Log', headings)
        self.assertIn('Notes', headings)


class ProseOnlyDocumentTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(PROSE_ONLY_TXT, 'rb') as f:
            self.response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')

    def test_upload_succeeds_with_no_datasets(self):
        self.assertEqual(self.response.status_code, 201)
        self.assertEqual(self.response.json()['status'], Report.Status.COMPLETED)
        document = self.response.json()['extracted_data']
        self.assertEqual(document['datasets'], [])
        self.assertGreater(len(document['sections']), 0)

    def test_entities_extracted_from_prose(self):
        document = self.response.json()['extracted_data']
        entities = document['entities']
        self.assertIn('88%', entities['numbers'])
        self.assertIn('$2.4 million', entities['numbers'])
        self.assertTrue(any('2026' in d for d in entities['dates']))
        self.assertIn('program', entities['keywords'])

    def test_no_insights_or_charts_invented_without_data(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(document['insights'], [])
        self.assertEqual(document['charts'], [])

    def test_download_returns_a_workbook_even_with_no_datasets(self):
        report_id = self.response.json()['id']
        download = self.client.get(f'/api/reports/{report_id}/download/')
        self.assertEqual(download.status_code, 200)


class PdfWithFiguresAndInsightsTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(OPERATIONS_PDF, 'rb') as f:
            self.response = self.client.post('/api/reports/upload/', {'file': f}, format='multipart')

    def test_upload_succeeds(self):
        self.assertEqual(self.response.status_code, 201)
        data = self.response.json()
        self.assertEqual(data['source_type'], 'pdf')
        self.assertEqual(data['extracted_data']['kind'], 'generic_document')

    def test_table_extracted_correctly(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(len(document['datasets']), 1)
        dataset = document['datasets'][0]
        self.assertEqual(dataset['row_count'], 3)
        kigali = next(r for r in dataset['rows'] if r['Center'] == 'Kigali Hub')
        self.assertEqual(kigali['Shipments'], '4820')

    def test_embedded_figure_extracted(self):
        document = self.response.json()['extracted_data']
        self.assertEqual(len(document['figures']), 1)
        figure = document['figures'][0]
        self.assertEqual(figure['source'], 'Page 1')
        self.assertTrue(figure['thumbnail'].startswith('data:image/png;base64,'))

    def test_insights_are_real_aggregates(self):
        document = self.response.json()['extracted_data']
        insight_text = ' '.join(document['insights'])
        self.assertIn('4,820', insight_text)
        self.assertIn('Kigali Hub', insight_text)

    def test_prose_section_preserved(self):
        document = self.response.json()['extracted_data']
        self.assertTrue(any('Regional Distribution Center Review' == s['title'] for s in document['sections']))
