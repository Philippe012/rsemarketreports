from dataclasses import dataclass, field
from typing import List

from docx import Document as _DocxDocument
from docx.oxml.ns import qn
from docx.table import Table as _DocxTable
from docx.text.paragraph import Paragraph as _DocxParagraph

from .zip_guard import check_zip_bomb

TableRows = List[List[str]]


class DocxExtractionError(Exception):
    """Raised when a .docx file cannot be opened or has no readable content."""


@dataclass
class DocxExtractionResult:
    sections: List[dict] = field(default_factory=list)  # [{heading, content}]
    tables: List[TableRows] = field(default_factory=list)


def _iter_block_items(document):
    """Yield each paragraph/table in the document body in document order."""
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield _DocxParagraph(child, document)
        elif child.tag == qn('w:tbl'):
            yield _DocxTable(child, document)


def _is_heading(paragraph: _DocxParagraph) -> bool:
    style_name = (paragraph.style.name or '') if paragraph.style else ''
    return style_name.lower().startswith('heading') or style_name.lower() == 'title'


def _table_to_rows(table: _DocxTable) -> TableRows:
    return [[cell.text.strip() for cell in row.cells] for row in table.rows]


def extract_docx(file_path: str) -> DocxExtractionResult:
    check_zip_bomb(file_path, DocxExtractionError)
    try:
        document = _DocxDocument(file_path)
    except Exception as exc:  # noqa: BLE001
        raise DocxExtractionError(f'Unable to read the Word document: {exc}') from exc

    sections: List[dict] = []
    tables: List[TableRows] = []

    current_heading = None
    current_paragraphs: List[str] = []

    def flush_section():
        content = '\n'.join(p for p in current_paragraphs if p.strip())
        if content.strip():
            sections.append({'heading': current_heading, 'content': content})

    for block in _iter_block_items(document):
        if isinstance(block, _DocxParagraph):
            text = block.text.strip()
            if not text:
                continue
            if _is_heading(block):
                flush_section()
                current_heading = text
                current_paragraphs = []
            else:
                current_paragraphs.append(text)
        elif isinstance(block, _DocxTable):
            rows = _table_to_rows(block)
            if rows:
                tables.append(rows)

    flush_section()

    if not sections and not tables:
        raise DocxExtractionError('The Word document contains no readable text or tables.')

    return DocxExtractionResult(sections=sections, tables=tables)
