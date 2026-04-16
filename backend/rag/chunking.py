"""Structure-aware chunking helpers."""

from __future__ import annotations

import re

from backend.core.config import get_settings
from backend.rag.metadata import ChunkRecord, ParsedBlock, ParsedDocument


def chunk_document(parsed_document: ParsedDocument) -> list[ChunkRecord]:
    """Chunk a parsed document while preserving structure and metadata."""
    settings = get_settings()
    chunk_size = settings.chunk_size_words
    overlap = settings.chunk_overlap_words
    min_chunk = settings.min_chunk_words

    all_blocks: list[ParsedBlock] = []
    for page in parsed_document.pages:
        all_blocks.extend(page.blocks)

    chunks: list[ChunkRecord] = []
    buffer: list[ParsedBlock] = []
    current_section: str | None = None
    chunk_id = 0

    def flush_buffer() -> None:
        nonlocal buffer, chunk_id
        if not buffer:
            return
        chunk = _build_chunk(parsed_document, buffer, chunk_id, current_section)
        if chunk is not None:
            chunks.append(chunk)
            chunk_id += 1
        buffer = []

    for block in all_blocks:
        block_words = _word_count(block.text)
        if block.block_type == "heading":
            flush_buffer()
            current_section = block.text
            continue

        if block_words > chunk_size:
            flush_buffer()
            split_chunks = _split_large_block(
                parsed_document=parsed_document,
                block=block,
                chunk_size=chunk_size,
                overlap=overlap,
                start_chunk_id=chunk_id,
                section_title=current_section,
            )
            chunks.extend(split_chunks)
            chunk_id += len(split_chunks)
            continue

        if buffer and _word_count(" ".join(item.text for item in buffer)) + block_words > chunk_size:
            flush_buffer()
        buffer.append(block)

    flush_buffer()
    return _merge_tiny_chunks(chunks, min_chunk_words=min_chunk)


def chunk_text(text: str, chunk_size: int = 280, overlap: int = 40) -> list[str]:
    """Backwards-compatible plain-text chunker used by tests and legacy imports."""
    if not text.strip():
        return []
    words = text.split()
    step = max(chunk_size - overlap, 1)
    results: list[str] = []
    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size]
        if piece:
            results.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
    return results


def _build_chunk(
    parsed_document: ParsedDocument,
    blocks: list[ParsedBlock],
    chunk_id: int,
    section_title: str | None,
) -> ChunkRecord | None:
    text = "\n\n".join(block.text for block in blocks if block.text.strip())
    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not normalized:
        return None
    pages = [block.page_number for block in blocks if block.page_number is not None]
    if section_title and not normalized.startswith(section_title):
        normalized = f"{section_title}\n\n{normalized}"
    return ChunkRecord(
        document_id=parsed_document.document_id,
        filename=parsed_document.filename,
        stored_filename=parsed_document.stored_filename,
        chunk_id=chunk_id,
        page_start=min(pages) if pages else None,
        page_end=max(pages) if pages else None,
        section_title=section_title,
        chunk_text=normalized,
        token_count=_word_count(normalized),
        source_type=parsed_document.source_type,
        tags=list(parsed_document.tags),
    )


def _split_large_block(
    *,
    parsed_document: ParsedDocument,
    block: ParsedBlock,
    chunk_size: int,
    overlap: int,
    start_chunk_id: int,
    section_title: str | None,
) -> list[ChunkRecord]:
    sentences = re.split(r"(?<=[.!?])\s+", block.text.strip())
    pieces: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        if not sentence:
            continue
        candidate = " ".join(current + [sentence]).strip()
        if current and _word_count(candidate) > chunk_size:
            pieces.append(" ".join(current).strip())
            trailing_words = " ".join(current).split()[-overlap:] if overlap else []
            current = [" ".join(trailing_words), sentence] if trailing_words else [sentence]
        else:
            current.append(sentence)
    if current:
        pieces.append(" ".join(current).strip())

    if not pieces:
        pieces = chunk_text(block.text, chunk_size=chunk_size, overlap=overlap)

    results: list[ChunkRecord] = []
    for index, piece in enumerate(pieces):
        chunk = _build_chunk(
            parsed_document,
            [ParsedBlock(text=piece, block_type="paragraph", page_number=block.page_number)],
            start_chunk_id + index,
            section_title,
        )
        if chunk is not None:
            results.append(chunk)
    return results


def _merge_tiny_chunks(chunks: list[ChunkRecord], *, min_chunk_words: int) -> list[ChunkRecord]:
    merged: list[ChunkRecord] = []
    for chunk in chunks:
        if merged and chunk.token_count < min_chunk_words:
            previous = merged[-1]
            previous.chunk_text = f"{previous.chunk_text}\n\n{chunk.chunk_text}".strip()
            previous.token_count = _word_count(previous.chunk_text)
            previous.page_end = chunk.page_end or previous.page_end
            continue
        merged.append(chunk)

    for index, chunk in enumerate(merged):
        chunk.chunk_id = index
    return merged


def _word_count(text: str) -> int:
    return len(text.split())
