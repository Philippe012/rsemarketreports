import os
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model

from reports.models import DocumentChunk, Report
from reports.tests import AuthenticatedTestCase
from services.chat.service import answer_chat
from services.rag.chunking import build_chunks
from services.rag.indexing import index_report
from services.rag.retrieval import retrieve_chunks

PROSE_ONLY_TXT = os.path.join(settings.BASE_DIR.parent, 'sample_data', 'generic_prose_only_sample.txt')

RSE_DATA = {
    'kind': 'rse_market_report',
    'report_date': '2024-05-02',
    'market_overview': {'equity_turnover': 14256000, 'equity_deals': 12, 'market_capitalization': 1000},
    'equities': [{'ticker': 'BOK', 'closing': 660, 'previous': 660, 'change': 0, 'volume': 21600, 'value': 14256000}],
}


def _generic(text, title='Page 2'):
    return {'kind': 'generic_document', 'sections': [{'title': title, 'content': text}]}


class RagTestCase(AuthenticatedTestCase):
    """Forces the offline embedder/answerer so tests never call an API."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {'OPENAI_API_KEY': ''})
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def make_report(self, data, filename, user=None):
        report = Report.objects.create(
            user=user or self.user, original_filename=filename, source_type='txt',
            status=Report.Status.COMPLETED, extracted_data=data,
        )
        self.assertTrue(index_report(report))
        return report


class ChunkingTests(RagTestCase):
    def test_rse_structured_facts_become_searchable_sentences(self):
        text = '\n'.join(c['content'] for c in build_chunks(RSE_DATA, 'rse.pdf'))
        self.assertIn('BOK closed at 660', text)
        self.assertIn('BOK volume was 21,600 shares', text)
        self.assertIn('FRW 14,256,000', text)

    def test_generic_section_keeps_page_and_filename(self):
        chunk = build_chunks(_generic('Some long enough section text.'), 'doc.pdf')[0]
        self.assertEqual(chunk['page_number'], 2)
        self.assertEqual(chunk['metadata']['filename'], 'doc.pdf')


class IndexingTests(RagTestCase):
    def test_upload_creates_chunks_and_marks_indexed(self):
        with open(PROSE_ONLY_TXT, 'rb') as f:
            report_id = self.client.post('/api/reports/upload/', {'file': f}, format='multipart').json()['id']
        report = Report.objects.get(pk=report_id)
        self.assertEqual(report.index_status, Report.IndexStatus.INDEXED)
        self.assertGreater(report.chunks.count(), 0)

    def test_indexing_failure_is_recorded_not_raised(self):
        report = Report.objects.create(user=self.user, original_filename='x.txt', source_type='txt',
                                       status=Report.Status.COMPLETED, extracted_data=_generic('text here'))
        with mock.patch('services.rag.indexing.embed_texts', side_effect=RuntimeError('boom')):
            self.assertFalse(index_report(report))
        report.refresh_from_db()
        self.assertEqual(report.index_status, Report.IndexStatus.FAILED)
        self.assertIn('boom', report.index_error)

    def test_deleting_report_deletes_its_chunks(self):
        report = self.make_report(_generic('Warehouse expansion approved.'), 'a.txt')
        report.delete()
        self.assertEqual(DocumentChunk.objects.count(), 0)


class RetrievalTests(RagTestCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.make_report(_generic('The Kigali warehouse expansion was approved by the board.'), 'warehouse.txt')
        self.payroll = self.make_report(_generic('Payroll costs rose because of new hires in Musanze.'), 'payroll.txt')
        other = get_user_model().objects.create_user(username='b@example.com', email='b@example.com', password='pw-12345678')
        self.secret = self.make_report(_generic('Secret warehouse acquisition plan for Kigali.'), 'secret.txt', user=other)

    def test_user_never_retrieves_another_users_chunks(self):
        hits = retrieve_chunks(self.user, 'Kigali warehouse')
        self.assertTrue(hits)
        self.assertTrue(all(h.chunk.report.user_id == self.user.id for h in hits))

    def test_document_scope_only_searches_that_report(self):
        hits = retrieve_chunks(self.user, 'Kigali warehouse expansion', report=self.payroll)
        self.assertTrue(all(h.chunk.report_id == self.payroll.id for h in hits))

    def test_all_scope_searches_every_owned_report(self):
        result = answer_chat(self.user, self.warehouse, 'Why did payroll costs rise?', scope='all')
        self.assertIn('new hires', result.answer)
        self.assertEqual(result.sources[0].label, 'payroll.txt')

    def test_citation_includes_filename_and_page(self):
        result = answer_chat(self.user, self.warehouse, 'Who approved the warehouse expansion?')
        self.assertEqual(result.sources[0].label, 'warehouse.txt')
        self.assertIn('Page 2', result.sources[0].detail)

    def test_unsupported_question_returns_not_found(self):
        result = answer_chat(self.user, self.warehouse, 'What is the capital of Peru?')
        self.assertEqual(result.confidence, 'low')
        self.assertIn("couldn't find", result.answer)


class HybridAnswerTests(RagTestCase):
    def test_exact_rse_figures_still_come_from_structured_engine(self):
        report = self.make_report(RSE_DATA, 'rse.pdf')
        result = answer_chat(self.user, report, "What was BOK's closing price today?")
        self.assertEqual(result.confidence, 'high')
        self.assertIn('660', result.answer)
        self.assertTrue(any('Equities' in s.label for s in result.sources))


def _completion(text):
    message = mock.Mock(content=text)
    return mock.Mock(choices=[mock.Mock(message=message)])


LLM_ENV = {'OPENAI_API_KEY': 'test-key', 'RAG_LLM': 'on', 'RAG_EMBEDDINGS': 'local'}


class ConversationalLlmTests(RagTestCase):
    """The OpenAI client is mocked — these check the wiring, not the model."""

    def setUp(self):
        super().setUp()
        self.report = self.make_report(RSE_DATA, 'rse.pdf')
        self.history = [
            {'role': 'user', 'content': "What was BOK's closing price?"},
            {'role': 'assistant', 'content': 'BOK closed at 660 today (previous 660).'},
        ]
        env = mock.patch.dict(os.environ, LLM_ENV)
        env.start()
        self.addCleanup(env.stop)
        self.client = mock.Mock()
        patcher = mock.patch('services.chat.rag_engine._client', return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_follow_up_is_rewritten_and_answered_with_history_and_citations(self):
        self.client.chat.completions.create.side_effect = [
            _completion('What was the BOK trading volume?'),
            _completion('BOK traded 21,600 shares on 2 May 2024 [2].'),
        ]
        result = answer_chat(self.user, self.report, 'and its volume?', history=self.history)

        self.assertIn('21,600', result.answer)
        self.assertEqual(result.sources[0].label, 'rse.pdf')
        generate_messages = self.client.chat.completions.create.call_args_list[1].kwargs['messages']
        self.assertIn("What was BOK's closing price?", [m['content'] for m in generate_messages])
        self.assertIn('Question: and its volume?', generate_messages[-1]['content'])

    def test_verified_structured_figure_is_given_to_the_llm(self):
        self.client.chat.completions.create.return_value = _completion('BOK closed at 660 [1].')
        result = answer_chat(self.user, self.report, "What was BOK's closing price today?")
        context = self.client.chat.completions.create.call_args.kwargs['messages'][-1]['content']
        self.assertIn('VERIFIED', context)
        self.assertEqual(result.confidence, 'high')
        self.assertTrue(any('Equities' in s.label for s in result.sources))

    def test_api_failure_falls_back_to_exact_structured_answer(self):
        self.client.chat.completions.create.side_effect = RuntimeError('401 invalid_api_key')
        result = answer_chat(self.user, self.report, "What was BOK's closing price today?")
        self.assertEqual(result.answer, 'BOK closed at 660 today (previous 660).')

    def test_llm_not_found_returns_controlled_not_found(self):
        self.client.chat.completions.create.return_value = _completion('NOT_FOUND')
        result = answer_chat(self.user, self.report, 'What is the capital of Peru?')
        self.assertEqual(result.confidence, 'low')

    def test_embedding_api_failure_falls_back_to_local_embedder(self):
        with mock.patch.dict(os.environ, {'RAG_EMBEDDINGS': ''}), \
                mock.patch('services.rag.embeddings._openai_embed_many', side_effect=RuntimeError('401')):
            self.assertTrue(index_report(self.report))
        self.assertEqual(set(self.report.chunks.values_list('embedding_model', flat=True)), {'local-hash-v1'})


class ChatScopeEndpointTests(RagTestCase):
    def setUp(self):
        super().setUp()
        self.report = self.make_report(_generic('The Kigali warehouse expansion was approved.'), 'warehouse.txt')

    def test_invalid_scope_rejected(self):
        response = self.client.post(f'/api/reports/{self.report.id}/chat/',
                                    {'message': 'hi', 'scope': 'everyone'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_all_scope_accepted(self):
        response = self.client.post(f'/api/reports/{self.report.id}/chat/',
                                    {'message': 'Was the warehouse expansion approved?', 'scope': 'all'},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['assistant_message']['sources'][0]['label'], 'warehouse.txt')
