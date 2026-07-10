from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pdfplumber


class ExtractedPage:
    __slots__ = ("page_number", "text", "tables", "width", "height")

    def __init__(
        self,
        page_number: int,
        text: str = "",
        tables: list[list[list[str | None]]] | None = None,
        width: float = 0,
        height: float = 0,
    ):
        self.page_number = page_number
        self.text = text
        self.tables = tables or []
        self.width = width
        self.height = height


class ExtractionResult:
    __slots__ = ("file_name", "file_path", "file_hash", "page_count", "pages", "raw_text")

    def __init__(
        self,
        file_name: str = "",
        file_path: str = "",
        file_hash: str = "",
        page_count: int = 0,
        pages: list[ExtractedPage] | None = None,
        raw_text: str = "",
    ):
        self.file_name = file_name
        self.file_path = file_path
        self.file_hash = file_hash
        self.page_count = page_count
        self.pages = pages or []
        self.raw_text = raw_text


def compute_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_pdf(file_path: Path) -> ExtractionResult:
    result = ExtractionResult()
    result.file_name = file_path.name
    result.file_path = str(file_path)
    result.file_hash = compute_file_hash(file_path)

    with pdfplumber.open(file_path) as pdf:
        result.page_count = len(pdf.pages)
        raw_texts: list[str] = []

        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            page_text = page.extract_text() or ""
            raw_texts.append(page_text)

            tables_raw = page.extract_tables()
            tables: list[list[list[str | None]]] = []
            if tables_raw:
                for table in tables_raw:
                    if table:
                        tables.append(table)

            extracted_page = ExtractedPage(
                page_number=page_num,
                text=page_text,
                tables=tables,
                width=page.width or 0,
                height=page.height or 0,
            )
            result.pages.append(extracted_page)

        result.raw_text = "\n".join(raw_texts)

    return result
