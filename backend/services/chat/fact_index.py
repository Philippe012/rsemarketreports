from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from .text_match import significant_words


@dataclass
class Fact:
    keywords: Set[str]
    answer_text: str
    source: 'Source'
    confidence: str = 'high'


class FactIndex:
    def __init__(self) -> None:
        self._facts: List[Fact] = []

    def add(self, keywords: Iterable[str], answer_text: str, source, confidence: str = 'high') -> None:
        words = {str(w).lower() for w in keywords if w}
        if words and answer_text:
            self._facts.append(Fact(words, answer_text, source, confidence))

    def __len__(self) -> int:
        return len(self._facts)

    def best_match(self, question: str, min_score: float = 0.3) -> Optional[Fact]:
        q_words = significant_words(question)
        if not q_words:
            return None

        best: Optional[Fact] = None
        best_key = (0.0, 0)
        for fact in self._facts:
            matched = fact.keywords & q_words
            if not matched:
                continue
            score = len(matched) / len(fact.keywords)
            key = (score, len(matched))
            if key > best_key:
                best_key, best = key, fact

        if best is None or best_key[0] < min_score:
            return None
        return best
