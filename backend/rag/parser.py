"""Document parsing utilities."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from backend.rag.metadata import ParsedBlock, ParsedDocument, ParsedPage


def _split_blocks(text: str, page_number: int | None) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    raw_blocks = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    for raw_block in raw_blocks:
        block_type = "heading" if _looks_like_heading(raw_block) else "paragraph"
        blocks.append(
            ParsedBlock(
                text=_normalize_whitespace(raw_block),
                block_type=block_type,
                page_number=page_number,
            )
        )
    return blocks


def _looks_like_heading(text: str) -> bool:
    cleaned = " ".join(text.split())
    if not cleaned:
        return False
    words = cleaned.split()
    if len(words) > 12:
        return False
    if cleaned.endswith((".", "!", "?", ";", ":")):
        return False
    return cleaned.isupper() or cleaned.istitle() or bool(re.match(r"^\d+(\.\d+)*\s+\S+", cleaned))


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_document(
    file_path: Path,
    *,
    filename: str,
    stored_filename: str,
    document_id: str,
    tags: list[str] | None = None,
) -> ParsedDocument:
    """Parse a PDF or TXT file into page-aware blocks."""
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        page = ParsedPage(page_number=None, text=text, blocks=_split_blocks(text, page_number=None))
        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            stored_filename=stored_filename,
            source_type="txt",
            pages=[page],
            tags=tags or [],
        )

    if suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
        except PdfReadError as exc:
            raise ValueError("The uploaded file could not be read as a valid PDF.") from exc

        pages: list[ParsedPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(
                ParsedPage(
                    page_number=index,
                    text=text,
                    blocks=_split_blocks(text, page_number=index),
                )
            )
        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            stored_filename=stored_filename,
            source_type="pdf",
            pages=pages,
            tags=tags or [],
        )

    raise ValueError("Only PDF and TXT files are supported.")
