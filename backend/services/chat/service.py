"""Framework-agnostic entry points used by the Django view — kept free of
any Django/DRF import so this stays reusable (a management command, a
future Phase 2 consumer, tests) without dragging in the web layer.
The RAG path (``answer_chat``) imports its Django-backed modules lazily.
"""
from __future__ import annotations

from typing import List, Optional

from .base import AnswerResult
from .engine import get_answer_engine

SCOPE_DOCUMENT = 'document'
SCOPE_ALL = 'all'
CHAT_SCOPES = (SCOPE_DOCUMENT, SCOPE_ALL)
MAX_LAZY_INDEX_PER_REQUEST = 10


def answer_question(extracted_data: dict, question: str) -> AnswerResult:
    engine = get_answer_engine(extracted_data)
    return engine.answer(question)


def suggested_questions(extracted_data: dict) -> List[str]:
    engine = get_answer_engine(extracted_data)
    return engine.suggested_questions()


def answer_chat(user, report, question: str, scope: str = SCOPE_DOCUMENT,
                history: Optional[List[dict]] = None) -> AnswerResult:
    """Hybrid, conversational answer. The deterministic engine keeps exact
    structured figures authoritative; RAG covers everything else.

    ``history`` is the earlier conversation (``[{'role', 'content'}, …]``,
    oldest first). With an LLM configured, a follow-up ("and its volume?")
    is first rewritten into a standalone question, and the LLM writes the
    answer from the retrieved passages — grounded by any exact figure the
    deterministic engine found, which it must quote as-is.

    * ``document`` — searches this report only.
    * ``all`` — searches every completed document ``user`` owns.

    Without an LLM (or if the API fails): a high-confidence deterministic
    answer wins; otherwise the best retrieved passage is quoted.
    """
    from services.rag.indexing import ensure_indexed

    from .rag_engine import condense_question, llm_available, rag_answer

    standalone = condense_question(question, history)
    structured = answer_question(report.extracted_data, standalone)
    verified = structured if structured.confidence == 'high' else None
    search_report = None if scope == SCOPE_ALL else report

    if scope == SCOPE_ALL:
        _index_pending_reports(user)
    else:
        ensure_indexed(report)

    if llm_available():
        outcome = rag_answer(user, question, report=search_report, history=history, verified=verified,
                             search_question=standalone, verified_label=f'"{report.original_filename}"')
        if outcome.generated:
            return outcome.result
        if verified is not None:
            return verified
        rag = outcome.result
        return rag if rag.confidence != 'low' else structured

    if scope == SCOPE_ALL:
        rag = rag_answer(user, standalone, report=None).result
        return rag if rag.confidence != 'low' else structured

    if verified is not None:
        return verified
    rag = rag_answer(user, standalone, report=report).result
    replaceable = structured.confidence == 'low' or _is_keyword_section_match(structured)
    if rag.confidence != 'low' and replaceable:
        return rag
    return structured


def _is_keyword_section_match(result: AnswerResult) -> bool:
    """The generic engine's narrative fallback (a plain keyword match over
    section text) — the one medium-confidence answer RAG strictly improves
    on, since RAG ranks the same passages and cites file and page."""
    return any(s.label == 'Section' for s in result.sources)


def _index_pending_reports(user) -> None:
    from reports.models import Report
    from services.rag.indexing import index_report

    pending = Report.objects.filter(
        user=user, status=Report.Status.COMPLETED, index_status=Report.IndexStatus.PENDING,
    )[:MAX_LAZY_INDEX_PER_REQUEST]
    for report in pending:
        index_report(report)
