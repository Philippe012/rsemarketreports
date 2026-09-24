import re
from typing import Iterable, List, Set

_WORD_RE = re.compile(r"[a-z0-9%]+(?:['.][a-z0-9]+)*")

_STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but', 'with', 'this',
    'that', 'it', 'its', 'as', 'by', 'from', 'what', 'which', 'who', 'whom',
    'how', 'do', 'does', 'did', 'has', 'have', 'had', 'i', 'you', 'me',
    'my', 'we', 'our', 'please', 'tell', 'show', 'give', 'about', 'can',
}


def tokenize(text: str) -> List[str]:
    return _WORD_RE.findall((text or '').lower())


def significant_words(text: str) -> Set[str]:
    """Tokens with stopwords removed — used to score relevance rather than
    exact-match a whole sentence."""
    return {w for w in tokenize(text) if w not in _STOPWORDS and len(w) > 1}


def overlap_score(question_words: Set[str], candidate_words: Iterable[str]) -> float:
    """Fraction of `candidate_words` (e.g. a section's keywords, or a
    field's synonym list) that also appear in the question — 0 if either
    side is empty. Simple, explainable, and good enough for keyword-scale
    matching over a single document's already-extracted content."""
    candidate = set(candidate_words)
    if not candidate or not question_words:
        return 0.0
    return len(candidate & question_words) / len(candidate)


def contains_any(question_words: Set[str], words: Iterable[str]) -> bool:
    return any(w in question_words for w in words)


def best_matching_text(question: str, candidates: List[str], min_score: float = 0.12) -> int:
    """Returns the index of the candidate string with the highest word
    overlap with `question`, or -1 if nothing clears `min_score`. Used for
    narrative fallback search over section/paragraph text."""
    q_words = significant_words(question)
    if not q_words:
        return -1
    best_index, best_score = -1, 0.0
    for i, candidate in enumerate(candidates):
        c_words = significant_words(candidate)
        if not c_words:
            continue
        score = len(q_words & c_words) / len(q_words)
        if score > best_score:
            best_index, best_score = i, score
    return best_index if best_score >= min_score else -1
