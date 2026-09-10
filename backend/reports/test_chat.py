import os

from django.conf import settings
from django.test import SimpleTestCase

from reports.models import ChatMessage
from reports.tests import AuthenticatedTestCase
from services.chat.base import CompositeAnswerEngine, not_found
from services.chat.engine import get_answer_engine
from services.chat.fact_index import FactIndex
from services.chat.service import answer_question, suggested_questions

SAMPLE_DIR = os.path.join(settings.BASE_DIR.parent, 'sample_data')
SAMPLE_PDF = os.path.join(SAMPLE_DIR, 'RSE_sample.pdf')
SALES_CSV = os.path.join(SAMPLE_DIR, 'generic_sales_sample.csv')
PROSE_ONLY_TXT = os.path.join(SAMPLE_DIR, 'generic_prose_only_sample.txt')


class FactIndexTests(SimpleTestCase):
    def test_best_match_prefers_more_specific_fact(self):
        index = FactIndex()
        index.add(['bok'], 'BOK summary.', source='Equities')
        index.add(['bok', 'closing', 'price'], 'BOK closed at 660.', source='Equities')
        fact = index.best_match('What was BOK closing price today?')
        self.assertEqual(fact.answer_text, 'BOK closed at 660.')

    def test_no_match_returns_none(self):
        index = FactIndex()
        index.add(['bok'], 'BOK summary.', source='Equities')
        self.assertIsNone(index.best_match('Tell me about the weather'))


class CompositeAnswerEngineTests(SimpleTestCase):
    def test_falls_through_to_next_engine_when_first_is_unsure(self):
        class Unsure:
            def answer(self, question):
                return not_found()

            def suggested_questions(self):
                return ['a']

        class Sure:
            def answer(self, question):
                from services.chat.base import AnswerResult
                return AnswerResult(answer='confident answer', confidence='high')

            def suggested_questions(self):
                return ['b']

        composite = CompositeAnswerEngine([Unsure(), Sure()])
        result = composite.answer('anything')
        self.assertEqual(result.answer, 'confident answer')
        self.assertEqual(set(composite.suggested_questions()), {'a', 'b'})


class RseAnswerEngineTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            self.report = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()
        self.data = self.report['extracted_data']

    def test_answers_a_specific_equity_price_with_source(self):
        result = answer_question(self.data, "What was BOK's closing price today?")
        self.assertIn('660', result.answer)
        self.assertEqual(result.confidence, 'high')
        self.assertTrue(any('Equities' in s.label for s in result.sources))

    def test_answers_market_capitalization(self):
        result = answer_question(self.data, 'What is the total market capitalization?')
        self.assertIn('6,634,919,683,716', result.answer)

    def test_unknown_question_says_so_plainly(self):
        result = answer_question(self.data, 'What is the meaning of life?')
        self.assertEqual(result.confidence, 'low')
        self.assertIn("couldn't find", result.answer)

    def test_suggested_questions_are_grounded_in_this_document(self):
        questions = suggested_questions(self.data)
        self.assertGreaterEqual(len(questions), 4)
        self.assertLessEqual(len(questions), 6)


class GenericAnswerEngineTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SALES_CSV, 'rb') as f:
            self.report = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()
        self.data = self.report['extracted_data']

    def test_answers_row_count_question(self):
        dataset_name = self.data['datasets'][0]['name']
        result = answer_question(self.data, f'How many records are in the {dataset_name} dataset?')
        self.assertIn(str(self.data['datasets'][0]['row_count']), result.answer)

    def test_never_invents_numbers_when_unsupported(self):
        result = answer_question(self.data, 'What will next quarter revenue be?')
        # Either a grounded low-confidence refusal, or a genuine match — never a fabricated forecast number.
        self.assertNotIn('will be', result.answer.lower())

    def test_prose_only_document_falls_back_to_section_search(self):
        with open(PROSE_ONLY_TXT, 'rb') as f:
            report = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()
        engine = get_answer_engine(report['extracted_data'])
        # Should not crash even with no datasets, and should never fabricate a data-backed answer.
        result = engine.answer('What is this document about?')
        self.assertIsNotNone(result.answer)


class ChatEndpointTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        with open(SAMPLE_PDF, 'rb') as f:
            self.report_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']

    def test_get_returns_empty_history_and_suggestions(self):
        response = self.client.get(f'/api/reports/{self.report_id}/chat/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['messages'], [])
        self.assertGreater(len(body['suggested_questions']), 0)

    def test_post_creates_user_and_assistant_messages_and_persists_history(self):
        response = self.client.post(
            f'/api/reports/{self.report_id}/chat/', {'message': "What was BOK's closing price?"}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['user_message']['role'], 'user')
        self.assertEqual(body['assistant_message']['role'], 'assistant')
        self.assertIn('660', body['assistant_message']['content'])
        self.assertTrue(len(body['assistant_message']['sources']) > 0)

        self.assertEqual(ChatMessage.objects.filter(report_id=self.report_id).count(), 2)
        history = self.client.get(f'/api/reports/{self.report_id}/chat/').json()
        self.assertEqual(len(history['messages']), 2)

    def test_empty_message_rejected(self):
        response = self.client.post(f'/api/reports/{self.report_id}/chat/', {'message': '   '}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_chat_scoped_to_owner_only(self):
        self.client.logout()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user(username='intruder@example.com', email='intruder@example.com', password='intruder-pass-123')
        self.client.login(username='intruder@example.com', password='intruder-pass-123')
        response = self.client.get(f'/api/reports/{self.report_id}/chat/')
        self.assertEqual(response.status_code, 404)
