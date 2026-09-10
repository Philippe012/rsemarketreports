
from dataclasses import dataclass, field
from typing import List


@dataclass
class Source:
    label: str
    detail: str = ''

    def to_dict(self) -> dict:
        return {'label': self.label, 'detail': self.detail}


@dataclass
class AnswerResult:
    answer: str
    sources: List[Source] = field(default_factory=list)
    confidence: str = 'medium'

    def to_dict(self) -> dict:
        return {
            'answer': self.answer,
            'sources': [s.to_dict() for s in self.sources],
            'confidence': self.confidence,
        }


NOT_FOUND = "I couldn't find anything in this document that answers that. Try asking about a specific figure, section, or dataset."


def not_found() -> AnswerResult:
    return AnswerResult(answer=NOT_FOUND, sources=[], confidence='low')


class AnswerEngine:

    def answer(self, question: str) -> AnswerResult:
        raise NotImplementedError

    def suggested_questions(self) -> List[str]:
        raise NotImplementedError


class CompositeAnswerEngine(AnswerEngine):
    def __init__(self, engines: List[AnswerEngine]):
        if not engines:
            raise ValueError('CompositeAnswerEngine needs at least one engine')
        self._engines = engines

    def answer(self, question: str) -> AnswerResult:
        last = None
        for engine in self._engines:
            result = engine.answer(question)
            if result.confidence != 'low':
                return result
            last = result
        return last

    def suggested_questions(self) -> List[str]:
        questions: List[str] = []
        for engine in self._engines:
            for q in engine.suggested_questions():
                if q not in questions:
                    questions.append(q)
        return questions
