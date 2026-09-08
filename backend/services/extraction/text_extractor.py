import pymupdf as fitz
from typing import List


def extract_page_text(page) -> str:
    return page.extract_text() or ''


def extract_pages_text(pdf) -> List[str]:
    return [extract_page_text(page) for page in pdf.pages]


def extract_full_text(pdf) -> str:
    return '\f'.join(extract_pages_text(pdf))


def extract_text_with_fitz(path: str) -> str:

    text_parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return '\f'.join(text_parts)
