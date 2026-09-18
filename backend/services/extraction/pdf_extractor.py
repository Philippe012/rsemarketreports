from dataclasses import dataclass, field
from typing import Callable, List, Optional

import pdfplumber

from services.extraction.table_extractor import TableRows, extract_page_tables
from services.extraction.text_extractor import extract_page_text, extract_text_with_fitz

# Extension point for a future OCR engine (Tesseract, a cloud OCR API, ...).
# When None (the default — no OCR dependency is installed by this project),
# a PDF with no extractable text layer fails extraction with a clear,
# specific error rather than silently returning an empty/partial document —
# see `extract_pdf` below. To wire one in: assign a callable here that takes
# a file path and returns the OCR'd text per page (joined with "\f", same
# convention as PdfExtractionResult.full_text), or None if OCR itself found
# nothing.
OCR_ENGINE: Optional[Callable[[str], Optional[str]]] = None


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be opened or contains no extractable text."""


@dataclass
class PdfExtractionResult:
    pages_text: List[str] = field(default_factory=list)
    pages_tables: List[List[TableRows]] = field(default_factory=list)
    used_fallback: bool = False
    # True only when OCR_ENGINE was actually used to recover this text — a
    # signal to downstream validation that the content is a machine guess
    # at pixels, not a text layer, and deserves a "needs review" flag rather
    # than being trusted exactly like a native text extraction.
    used_ocr: bool = False

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
            fallback_text = ''

        pages = fallback_text.split('\f') if fallback_text else []
        if any(page.strip() for page in pages):
            return PdfExtractionResult(
                pages_text=pages,
                pages_tables=[[] for _ in pages],
                used_fallback=True,
            )

        # Neither pdfplumber nor the fitz fallback found any text layer at
        # all — this is very likely a scanned/image-only PDF. Try the OCR
        # extension point (see OCR_ENGINE above) before giving up; if none
        # is configured, fail with a specific, honest message instead of a
        # generic "couldn't read the file" — this is a different, well
        # understood failure mode, not a corrupt or unsupported file.
        if OCR_ENGINE is not None:
            try:
                ocr_text = OCR_ENGINE(file_path)
            except Exception:
                ocr_text = None
            if ocr_text and ocr_text.strip():
                ocr_pages = ocr_text.split('\f')
                return PdfExtractionResult(
                    pages_text=ocr_pages,
                    pages_tables=[[] for _ in ocr_pages],
                    used_fallback=True,
                    used_ocr=True,
                )

        raise PdfExtractionError(
            'This PDF has no extractable text layer, which usually means it is a scanned image rather '
            'than a text-based document. OCR is not enabled on this system, so it cannot be processed '
            'automatically — try re-exporting or re-scanning it with a text layer, or use an OCR tool '
            'before uploading.'
        ) from exc
