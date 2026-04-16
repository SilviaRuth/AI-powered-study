"""Context compression helpers."""

from __future__ import annotations

import re

from backend.core.config import get_settings
from backend.rag.metadata import RetrievedChunk


class ContextCompressor:
    """Filter evidence down to answer-relevant spans."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def compress(self, question: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Select the most relevant spans from retrieved chunks."""
        compressed: list[RetrievedChunk] = []
        keywords = set(re.findall(r"\b\w+\b", question.lower()))
        for candidate in candidates[: self.settings.max_context_chunks]:
            sentences = re.split(r"(?<=[.!?])\s+", candidate.chunk_text.strip())
            ranked = sorted(
                sentences,
                key=lambda sentence: self._sentence_overlap(sentence, keywords),
                reverse=True,
            )
            excerpt = " ".join(sentence for sentence in ranked[:2] if sentence).strip()
            if not excerpt:
                excerpt = candidate.chunk_text[: self.settings.max_excerpt_chars].strip()
            candidate.compressed_excerpt = excerpt[: self.settings.max_excerpt_chars].strip()
            compressed.append(candidate)
        return compressed

    @staticmethod
    def _sentence_overlap(sentence: str, keywords: set[str]) -> int:
        tokens = set(re.findall(r"\b\w+\b", sentence.lower()))
        return len(tokens & keywords)
