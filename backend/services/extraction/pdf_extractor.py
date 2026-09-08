from dataclasses import dataclass, field
from typing import List

import pdfplumber

from services.extraction.table_extractor import TableRows, extract_page_tables
from services.extraction.text_extractor import extract_page_text, extract_text_with_fitz


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be opened or contains no extractable text."""


@dataclass
class PdfExtractionResult:
    pages_text: List[str] = field(default_factory=list)
    pages_tables: List[List[TableRows]] = field(default_factory=list)
    used_fallback: bool = False

    @property
    def full_text(self) -> str:
        return '\f'.join(self.pages_text)


def extract_pdf(file_path: str) -> PdfExtractionResult:
    try:
        pages_text: List[str] = []
        pages_tables: List[List[TableRows]] = []
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                raise PdfExtractionError('The PDF file has no pages.')
            for page in pdf.pages:
                pages_text.append(extract_page_text(page))
                pages_tables.append(extract_page_tables(page))

        if not any(text.strip() for text in pages_text):
            raise PdfExtractionError('No extractable text found via pdfplumber.')

        return PdfExtractionResult(pages_text=pages_text, pages_tables=pages_tables)

    except Exception as exc: 
        try:
            fallback_text = extract_text_with_fitz(file_path)
        except Exception:
            raise PdfExtractionError(
                f'Unable to read the PDF file: {exc}'
            ) from exc

        pages = fallback_text.split('\f')
        if not any(page.strip() for page in pages):
            raise PdfExtractionError(
                'The PDF could not be parsed and contains no readable text.'
            ) from exc

        return PdfExtractionResult(
            pages_text=pages,
            pages_tables=[[] for _ in pages],
            used_fallback=True,
        )
