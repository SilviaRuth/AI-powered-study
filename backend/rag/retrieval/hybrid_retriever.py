"""Hybrid retrieval with reciprocal rank fusion."""

from __future__ import annotations

from backend.core.config import get_settings
from backend.rag.metadata import RetrievedChunk
from backend.rag.retrieval.bm25_retriever import BM25Retriever
from backend.rag.retrieval.dense_retriever import DenseRetriever


class HybridRetriever:
    """Combine dense and sparse results into a single ranked list."""

    def __init__(self, dense_retriever: DenseRetriever, sparse_retriever: BM25Retriever) -> None:
        self.settings = get_settings()
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

    def search(self, query: str) -> list[RetrievedChunk]:
        """Search both retrievers and fuse their rankings."""
        dense_results = self.dense_retriever.search(query, self.settings.dense_candidate_count)
        sparse_results = self.sparse_retriever.search(query, self.settings.sparse_candidate_count)
        candidates: dict[str, RetrievedChunk] = {}

        self._merge_results(
            candidates,
            dense_results,
            weight=self.settings.hybrid_dense_weight,
            origin="dense",
        )
        self._merge_results(
            candidates,
            sparse_results,
            weight=self.settings.hybrid_sparse_weight,
            origin="sparse",
        )

        merged = list(candidates.values())
        merged.sort(key=lambda item: item.retrieval_score, reverse=True)
        return merged[: self.settings.hybrid_candidate_count]

    def _merge_results(
        self,
        candidates: dict[str, RetrievedChunk],
        results: list[RetrievedChunk],
        *,
        weight: float,
        origin: str,
    ) -> None:
        for rank, result in enumerate(results, start=1):
            key = result.key()
            fused_increment = weight / (self.settings.hybrid_rrf_k + rank)
            if key not in candidates:
                result.retrieval_score = fused_increment
                result.match_origin = [origin]
                candidates[key] = result
                continue

            candidate = candidates[key]
            candidate.retrieval_score += fused_increment
            if origin not in candidate.match_origin:
                candidate.match_origin.append(origin)
            if result.dense_score is not None:
                candidate.dense_score = result.dense_score
            if result.sparse_score is not None:
                candidate.sparse_score = result.sparse_score
