"""User-scoped hybrid retrieval over DocumentChunk.

Security: every query is filtered by ``report__user=user`` — there is no
code path that searches chunks without an owner filter, so one user can
never retrieve another user's documents.

Ranking is a blend of cosine similarity (embeddings) and keyword overlap,
computed with numpy in Python. That is fine for a per-user corpus; if the
database gains the pgvector extension later, this is the one place to swap
in a ``CosineDistance`` ORM query.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from reports.models import DocumentChunk, Report
from services.chat.text_match import significant_words

from .embeddings import embed_question

VECTOR_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
MIN_SCORE = 0.15


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float

    @property
    def filename(self) -> str:
        return self.chunk.report.original_filename

    @property
    def location(self) -> str:
        parts = []
        if self.chunk.page_number:
            parts.append(f'Page {self.chunk.page_number}')
        if self.chunk.section:
            parts.append(self.chunk.section)
        return ', '.join(parts)


def _keyword_scores(question: str, contents: List[str]) -> np.ndarray:
    q_words = significant_words(question)
    if not q_words:
        return np.zeros(len(contents))
    return np.array([len(q_words & significant_words(c)) / len(q_words) for c in contents])


def retrieve_chunks(user, question: str, report: Optional[Report] = None, limit: int = 8,
                    min_score: float = MIN_SCORE) -> List[RetrievedChunk]:
    if user is None or not getattr(user, 'is_authenticated', False):
        return []

    queryset = DocumentChunk.objects.filter(
        report__user=user,
        report__status=Report.Status.COMPLETED,
    ).select_related('report')
    if report is not None:
        queryset = queryset.filter(report=report)

    chunks = list(queryset)
    if not chunks:
        return []

    cosine = _cosine_scores(question, chunks)
    scores = VECTOR_WEIGHT * cosine + KEYWORD_WEIGHT * _keyword_scores(question, [c.content for c in chunks])
    order = np.argsort(-scores)[:limit]
    return [RetrievedChunk(chunks[i], float(scores[i])) for i in order if scores[i] >= min_score]


def _cosine_scores(question: str, chunks: List[DocumentChunk]) -> np.ndarray:
    """Chunks may come from different embedders (e.g. some indexed before
    an API key was added), so the question is embedded once per model and
    only compared with chunks from that same model. If a model is
    unavailable its chunks get 0 here and rank on keywords alone."""
    scores = np.zeros(len(chunks))
    groups: Dict[str, List[int]] = defaultdict(list)
    for i, chunk in enumerate(chunks):
        groups[chunk.embedding_model].append(i)

    for model_name, indices in groups.items():
        query = embed_question(question, model_name)
        if query is None:
            continue
        query_vec = np.array(query, dtype=float)
        rows = [i for i in indices if len(chunks[i].embedding) == len(query_vec)]
        if not rows:
            continue
        matrix = np.array([chunks[i].embedding for i in rows], dtype=float)
        norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(query_vec) or 1.0)
        scores[rows] = np.divide(matrix @ query_vec, norms, out=np.zeros(len(rows)), where=norms > 0)
    return scores
