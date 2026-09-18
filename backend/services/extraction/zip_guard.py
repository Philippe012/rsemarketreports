"""A cheap pre-flight check shared by every extractor whose format is a zip
archive under the hood (.xlsx/.xlsm, .docx) — inspects the archive's own
size metadata (no decompression needed) before any parsing library gets a
chance to expand a maliciously crafted archive fully into memory.
"""
from __future__ import annotations

import zipfile
from typing import Type

MAX_ZIP_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # a generous ceiling for a real spreadsheet/document
MAX_ZIP_COMPRESSION_RATIO = 200  # a legitimate xlsx/docx rarely compresses much beyond ~50x


def check_zip_bomb(
    file_path: str, error_cls: Type[Exception], *,
    max_ratio: int = MAX_ZIP_COMPRESSION_RATIO, max_uncompressed: int = MAX_ZIP_UNCOMPRESSED_BYTES,
) -> None:
    """Raises ``error_cls`` (the caller's own extraction-error type, so it's
    handled exactly like any other extraction failure) if the archive would
    decompress to an unreasonable size, or has an unreasonable compression
    ratio for its format. Never raises for a file that isn't a zip archive
    at all, or one that's simply corrupt — those are left to the real parser
    to report with a clearer, format-specific error."""
    try:
        if not zipfile.is_zipfile(file_path):
            return
        with zipfile.ZipFile(file_path) as archive:
            infos = archive.infolist()
            total_uncompressed = sum(info.file_size for info in infos)
            total_compressed = sum(max(info.compress_size, 1) for info in infos)
    except zipfile.BadZipFile:
        return

    if total_uncompressed > max_uncompressed:
        raise error_cls(
            f'This file would decompress to more than {max_uncompressed // (1024 * 1024)}MB, which is '
            f'larger than this system accepts — it was rejected before being fully loaded into memory.'
        )
    if total_compressed and total_uncompressed / total_compressed > max_ratio:
        raise error_cls(
            'This file\'s compression ratio is unusually high for its format and was rejected as a '
            'possible decompression bomb rather than risk loading it fully into memory.'
        )
