"""Builds and stores a report's RAG chunks. ``index_report`` never raises:
an indexing failure is recorded on the report (``index_status='failed'``,
``index_error``) so it can never fail an upload or a chat request."""
from __future__ import annotations

import logging

from django.db import transaction
from reports.models import DocumentChunk, Report
from .chunking import build_chunks, chunk_texts
from .embeddings import embed_texts

logger = logging.getLogger(__name__)


def index_report(report: Report) -> bool:
    """(Re)indexes one report. Returns True on success."""
    try:
        chunks = build_chunks(report.extracted_data, report.original_filename)
        model_name, vectors = embed_texts(chunk_texts(chunks))

        with transaction.atomic():
            DocumentChunk.objects.filter(report=report).delete()
            DocumentChunk.objects.bulk_create([
                DocumentChunk(
                    report=report,
                    content=chunk['content'],
                    page_number=chunk['page_number'],
                    section=chunk['section'],
                    metadata=chunk['metadata'],
                    embedding=vector,
                    embedding_model=model_name,
                )
                for chunk, vector in zip(chunks, vectors)
            ])
            report.index_status = Report.IndexStatus.INDEXED
            report.index_error = ''
            report.save(update_fields=['index_status', 'index_error'])
        return True
    except Exception as exc:
        logger.exception('RAG indexing failed for report %s', report.pk)
        report.index_status = Report.IndexStatus.FAILED
        report.index_error = str(exc)[:2000]
        report.save(update_fields=['index_status', 'index_error'])
        return False


def ensure_indexed(report: Report) -> None:
    if report.status != Report.Status.COMPLETED or not report.extracted_data:
        return
    if report.index_status == Report.IndexStatus.PENDING:
        index_report(report)
