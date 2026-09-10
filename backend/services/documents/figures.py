"""Extracts embedded images (figures/charts) from PDF and Word documents.

This never tries to interpret *what* a chart shows — reading the actual
data series out of a chart image is outside what a deterministic pipeline
can do honestly. It surfaces the figure (a small thumbnail, its size, and
where it came from) so the user can see it, and stops there; no chart
values are invented from an image.
"""
from __future__ import annotations

import base64
import io
from typing import List, Optional

from PIL import Image

from .model import make_figure

MAX_FIGURES = 6
THUMBNAIL_MAX_DIM = 320


def _thumbnail_data_uri(image_bytes: bytes) -> Optional[str]:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((THUMBNAIL_MAX_DIM, THUMBNAIL_MAX_DIM))
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:  # noqa: BLE001 - a figure we can't thumbnail is skipped, not a pipeline failure
        return None


def extract_pdf_figures(file_path: str, max_figures: int = MAX_FIGURES) -> List[dict]:
    import pymupdf as fitz

    figures: List[dict] = []
    try:
        with fitz.open(file_path) as doc:
            for page_index, page in enumerate(doc, start=1):
                for image_info in page.get_images(full=True):
                    if len(figures) >= max_figures:
                        return figures
                    xref = image_info[0]
                    try:
                        extracted = doc.extract_image(xref)
                    except Exception:  # noqa: BLE001
                        continue
                    thumbnail = _thumbnail_data_uri(extracted['image'])
                    if thumbnail is None:
                        continue
                    figures.append(make_figure(
                        source=f'Page {page_index}',
                        width=extracted.get('width'),
                        height=extracted.get('height'),
                        image_format=extracted.get('ext', 'png'),
                        thumbnail=thumbnail,
                    ))
    except Exception:  # noqa: BLE001 - figures are a bonus, never worth failing the whole upload over
        return figures
    return figures


def extract_docx_figures(file_path: str, max_figures: int = MAX_FIGURES) -> List[dict]:
    from docx import Document as DocxDocument

    figures: List[dict] = []
    try:
        document = DocxDocument(file_path)
        image_parts = [
            part for part in document.part.related_parts.values()
            if getattr(part, 'content_type', '').startswith('image/')
        ]
        for part in image_parts[:max_figures]:
            thumbnail = _thumbnail_data_uri(part.blob)
            if thumbnail is None:
                continue
            try:
                with Image.open(io.BytesIO(part.blob)) as img:
                    width, height = img.size
            except Exception:  # noqa: BLE001
                width = height = None
            content_type = getattr(part, 'content_type', 'image/png')
            figures.append(make_figure(
                source='Word document',
                width=width,
                height=height,
                image_format=content_type.split('/')[-1],
                thumbnail=thumbnail,
            ))
    except Exception:  # noqa: BLE001
        return figures
    return figures
