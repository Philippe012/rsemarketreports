"""Validates a generic Document before it's shown to the user or exported.

Mirrors services.normalization.validate_data's philosophy: flag genuine
problems in plain language, never invent values, and only raise when there
is truly nothing usable to show — reuses the same exception class so the
view layer needs no branching between the RSE and generic pipelines.
"""
from __future__ import annotations

from typing import List, Tuple

from services.normalization.validate_data import ReportValidationError


def validate_document(document: dict) -> Tuple[dict, List[str]]:
    """A document with no tables is not a failure — most real documents
    (a policy memo, a narrative report, a letter) have no table at all, and
    still deserve a document overview built from their text. This only
    raises when literally nothing readable came out of extraction (no text,
    no tables, no figures) — that is a genuine extraction failure."""
    warnings: List[str] = []
    datasets = document.get('datasets', [])
    sections = document.get('sections', [])
    figures = document.get('figures', [])

    if not datasets and not sections and not figures:
        raise ReportValidationError(
            'We couldn\'t extract any readable content from this document — no text, '
            'tables, or figures were found. The file may be empty, corrupted, or a scanned '
            'image without a text layer.'
        )

    for dataset in datasets:
        low_confidence_columns = [c['display_name'] for c in dataset.get('columns', []) if c.get('confidence') == 'low']
        if low_confidence_columns:
            warnings.append(
                f'Dataset "{dataset["name"]}": could not confidently determine the type of '
                f'{"column" if len(low_confidence_columns) == 1 else "columns"} '
                f'{", ".join(low_confidence_columns)}.'
            )
        incomplete_columns = [
            c['display_name'] for c in dataset.get('columns', [])
            if c.get('total_count', 0) > 0 and c.get('non_null_count', 0) < c.get('total_count', 0)
        ]
        if incomplete_columns:
            missing_counts = {
                c['display_name']: c['total_count'] - c['non_null_count']
                for c in dataset.get('columns', []) if c['display_name'] in incomplete_columns
            }
            worst = max(missing_counts.values())
            worst_col = max(missing_counts, key=missing_counts.get)
            warnings.append(
                f'Dataset "{dataset["name"]}": {worst} record(s) are missing a value for "{worst_col}".'
            )

        duplicate_count = dataset.get('duplicate_row_count', 0)
        if duplicate_count:
            warnings.append(
                f'Dataset "{dataset["name"]}": {duplicate_count} record(s) appear to be exact '
                f'duplicates of another row.'
            )

    return document, warnings
