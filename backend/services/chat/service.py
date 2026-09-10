"""Framework-agnostic entry points used by the Django view — kept free of
any Django/DRF import so this stays reusable (a management command, a
future Phase 2 consumer, tests) without dragging in the web layer.
"""
from __future__ import annotations

from typing import List

from .base import AnswerResult
from .engine import get_answer_engine


def answer_question(extracted_data: dict, question: str) -> AnswerResult:
    engine = get_answer_engine(extracted_data)
    return engine.answer(question)


def suggested_questions(extracted_data: dict) -> List[str]:
    engine = get_answer_engine(extracted_data)
    return engine.suggested_questions()
