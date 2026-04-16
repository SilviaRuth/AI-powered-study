"""Optional LLM-based reranker."""

from __future__ import annotations

import logging

from backend.core.config import get_settings
from backend.rag.embeddings import OpenAIService
from backend.rag.metadata import RetrievedChunk


LOGGER = logging.getLogger(__name__)


class Reranker:
    """Optional reranker that fails open."""

    def __init__(self, openai_service: OpenAIService) -> None:
        self.settings = get_settings()
        self.openai_service = openai_service

    def rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Rerank candidates or return the original order if reranking is disabled or fails."""
        if not candidates:
            return []
        if not self.settings.rerank_enabled:
            return candidates[: self.settings.rerank_top_n]

        prompt_lines = [
            "You are scoring retrieval relevance for a study assistant.",
            "Return strict JSON as {\"scores\": {\"S1\": 0.0, \"S2\": 0.0}} with scores between 0 and 1.",
            "Base the score only on how well the evidence answers the query.",
            f"QUERY: {query}",
            "",
        ]
        for index, candidate in enumerate(candidates, start=1):
            prompt_lines.append(f"S{index}: {candidate.chunk_text[:900]}")

        try:
            payload = self.openai_service.complete_json("\n".join(prompt_lines))
            scores = payload.get("scores", {})
            for index, candidate in enumerate(candidates, start=1):
                candidate.rerank_score = float(scores.get(f"S{index}", 0.0))
            ranked = sorted(
                candidates,
                key=lambda item: (item.rerank_score or 0.0, item.retrieval_score),
                reverse=True,
            )
            return ranked[: self.settings.rerank_top_n]
        except Exception as exc:  # pragma: no cover - fail-open path
            LOGGER.warning("Reranker failed; falling back to hybrid ranking: %s", exc)
            return candidates[: self.settings.rerank_top_n]
