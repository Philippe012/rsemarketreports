"""Plain-text extraction. TXT files are the least structured input this
platform accepts, so this module does two modest, honest things rather than
guessing aggressively:

1. Looks for blocks of consecutive lines that are consistently delimiter-
   separated (comma/tab/semicolon/pipe) with the same field count — those
   are lifted out as tables, in the same shape every other extractor uses.
2. Groups the remaining text into sections, treating a short line with no
   sentence-ending punctuation as a heading for the paragraph that follows
   it (a common convention in plain-text reports and README-style files).

Anything that doesn't fit either pattern still ends up in a section as
plain paragraph text — never dropped.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import List, Optional

TableRows = List[List[str]]

_DELIMITERS = (',', '\t', ';', '|')
MIN_TABLE_ROWS = 3
HEADING_MAX_LENGTH = 80


class TxtExtractionError(Exception):
    """Raised when a text file cannot be read or is empty."""


@dataclass
class TxtExtractionResult:
    sections: List[dict] = field(default_factory=list)  # [{title, content}]
    tables: List[TableRows] = field(default_factory=list)
    full_text: str = ''


def _decode(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def _detect_delimiter(line: str) -> Optional[str]:
    for delimiter in _DELIMITERS:
        if line.count(delimiter) >= 1:
            return delimiter
    return None


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > HEADING_MAX_LENGTH:
        return False
    if stripped.endswith(('.', '?', '!', ',', ':', ';')):
        return False
    return True


def _extract_tables_and_text(lines: List[str]) -> tuple[List[TableRows], List[str]]:
    """Scans line-by-line for runs of consistently-delimited rows; returns
    the tables found and the remaining lines (table runs removed, replaced
    with nothing so surrounding paragraphs still join up correctly)."""
    tables: List[TableRows] = []
    remaining: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        delimiter = _detect_delimiter(line) if line.strip() else None
        if delimiter:
            field_count = len(next(csv.reader([line], delimiter=delimiter)))
            run = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip():
                candidate_delim = _detect_delimiter(lines[j])
                if candidate_delim != delimiter:
                    break
                candidate_fields = len(next(csv.reader([lines[j]], delimiter=delimiter)))
                if candidate_fields != field_count:
                    break
                run.append(lines[j])
                j += 1
            if len(run) >= MIN_TABLE_ROWS and field_count >= 2:
                reader = csv.reader(run, delimiter=delimiter)
                tables.append([list(row) for row in reader])
                i = j
                continue
        remaining.append(line)
        i += 1
    return tables, remaining


def _stands_alone(lines: List[str], index: int) -> bool:
    """True when the line at ``index`` has blank lines (or a file boundary)
    on both sides — the shape of a heading, as opposed to a hard-wrapped
    fragment of a longer sentence (which is only blank-bounded on one side,
    if any)."""
    before_blank = index == 0 or not lines[index - 1].strip()
    after_blank = index == len(lines) - 1 or not lines[index + 1].strip()
    return before_blank and after_blank


def _lines_to_sections(lines: List[str]) -> List[dict]:
    sections: List[dict] = []
    current_title: Optional[str] = None
    current_paragraph: List[str] = []

    def flush():
        content = '\n'.join(current_paragraph).strip()
        if content:
            sections.append({'title': current_title, 'content': content})

    # The start of the file counts as preceded by a blank line, so a title
    # on the very first line is still recognised as a heading.
    blank_streak = 1
    for i, line in enumerate(lines):
        if not line.strip():
            blank_streak += 1
            continue
        # A blank gap ends whatever paragraph was accumulating.
        if blank_streak > 0 and current_paragraph:
            flush()
            current_title = None
            current_paragraph = []
        # A short, punctuation-free line standing alone (blank on both
        # sides) reads as a heading for the paragraph that follows it — a
        # hard-wrapped sentence fragment only ever has a blank on one side,
        # so this rejects those without needing to guess at grammar.
        if blank_streak > 0 and not current_paragraph and _looks_like_heading(line) and _stands_alone(lines, i):
            current_title = line.strip()
        else:
            current_paragraph.append(line.strip())
        blank_streak = 0
    flush()
    return sections


def extract_txt(file_path: str) -> TxtExtractionResult:
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
    except OSError as exc:
        raise TxtExtractionError(f'Unable to read the text file: {exc}') from exc

    if not raw.strip():
        raise TxtExtractionError('The text file is empty.')

    text = _decode(raw)
    lines = text.splitlines()

    tables, remaining_lines = _extract_tables_and_text(lines)
    sections = _lines_to_sections(remaining_lines)

    if not sections and not tables:
        raise TxtExtractionError('The text file does not contain any readable content.')

    return TxtExtractionResult(sections=sections, tables=tables, full_text=text)
