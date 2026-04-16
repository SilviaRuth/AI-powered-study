"""Deduplicate highly overlapping retrieval results."""

from __future__ import annotations

import re

from backend.rag.metadata import RetrievedChunk


def dedupe_candidates(candidates: list[RetrievedChunk], overlap_threshold: float = 0.8) -> list[RetrievedChunk]:
    """Remove duplicates while keeping the strongest-scoring candidate."""
    accepted: list[RetrievedChunk] = []
    seen_texts: set[str] = set()
    ordered = sorted(
        candidates,
        key=lambda item: (item.rerank_score or item.retrieval_score),
        reverse=True,
    )
    for candidate in ordered:
        normalized = _normalize(candidate.chunk_text)
        if normalized in seen_texts:
            continue

        if any(_is_overlapping(candidate, existing, overlap_threshold) for existing in accepted):
            continue

        seen_texts.add(normalized)
        accepted.append(candidate)

    accepted.sort(key=lambda item: item.rerank_score or item.retrieval_score, reverse=True)
    return accepted


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def _is_overlapping(left: RetrievedChunk, right: RetrievedChunk, threshold: float) -> bool:
    if left.document_id != right.document_id:
        return False
    if abs(left.chunk_id - right.chunk_id) > 1:
        return False
    left_tokens = set(_normalize(left.chunk_text).split())
    right_tokens = set(_normalize(right.chunk_text).split())
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
    return overlap >= threshold
