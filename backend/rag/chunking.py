"""Document chunking helpers."""

from __future__ import annotations

from typing import List


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
    """Split text into overlapping word chunks.

    The spec calls for roughly 500-1000 token chunks. Using word counts keeps the
    implementation lightweight while staying in the requested range.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    words = cleaned.split(" ")
    chunks: List[str] = []
    step = max(chunk_size - overlap, 1)

    for start in range(0, len(words), step):
        segment = words[start : start + chunk_size]
        if not segment:
            continue
        chunks.append(" ".join(segment))
        if start + chunk_size >= len(words):
            break

    return chunks
