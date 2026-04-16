"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    """Local-first settings for the application."""

    base_dir: Path
    upload_dir: Path
    processed_dir: Path
    history_path: Path
    eval_dir: Path
    dense_store_dir: Path
    sparse_store_dir: Path
    registry_path: Path
    openai_chat_model: str
    openai_embedding_model: str
    supported_extensions: tuple[str, ...]
    chunk_size_words: int
    chunk_overlap_words: int
    min_chunk_words: int
    top_k: int
    dense_candidate_count: int
    sparse_candidate_count: int
    hybrid_candidate_count: int
    hybrid_rrf_k: int
    hybrid_dense_weight: float
    hybrid_sparse_weight: float
    rerank_enabled: bool
    rerank_top_n: int
    query_rewrite_enabled: bool
    logging_level: str
    history_window: int
    max_context_chunks: int
    max_excerpt_chars: int
    min_relevance_score: float

    def ensure_directories(self) -> None:
        """Create the local directories used by the app."""
        for path in (
            self.upload_dir,
            self.processed_dir,
            self.eval_dir,
            self.dense_store_dir,
            self.sparse_store_dir,
            self.history_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached app settings."""
    base_dir = Path(__file__).resolve().parents[2]
    return Settings(
        base_dir=base_dir,
        upload_dir=base_dir / "data" / "uploads",
        processed_dir=base_dir / "data" / "processed",
        history_path=base_dir / "data" / "history.json",
        eval_dir=base_dir / "data" / "eval",
        dense_store_dir=base_dir / "vector_store" / "dense",
        sparse_store_dir=base_dir / "vector_store" / "sparse",
        registry_path=base_dir / "data" / "processed" / "document_registry.json",
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        supported_extensions=(".pdf", ".txt"),
        chunk_size_words=_get_int("RAG_CHUNK_SIZE_WORDS", 280),
        chunk_overlap_words=_get_int("RAG_CHUNK_OVERLAP_WORDS", 40),
        min_chunk_words=_get_int("RAG_MIN_CHUNK_WORDS", 80),
        top_k=_get_int("RAG_TOP_K", 5),
        dense_candidate_count=_get_int("RAG_DENSE_CANDIDATES", 8),
        sparse_candidate_count=_get_int("RAG_SPARSE_CANDIDATES", 8),
        hybrid_candidate_count=_get_int("RAG_HYBRID_PRE_RERANK_K", 12),
        hybrid_rrf_k=_get_int("RAG_HYBRID_RRF_K", 60),
        hybrid_dense_weight=_get_float("RAG_HYBRID_DENSE_WEIGHT", 0.6),
        hybrid_sparse_weight=_get_float("RAG_HYBRID_SPARSE_WEIGHT", 0.4),
        rerank_enabled=_get_bool("RAG_RERANK_ENABLED", False),
        rerank_top_n=_get_int("RAG_RERANK_TOP_N", 5),
        query_rewrite_enabled=_get_bool("RAG_QUERY_REWRITE_ENABLED", False),
        logging_level=os.getenv("LOG_LEVEL", "INFO"),
        history_window=_get_int("RAG_HISTORY_WINDOW", 5),
        max_context_chunks=_get_int("RAG_MAX_CONTEXT_CHUNKS", 5),
        max_excerpt_chars=_get_int("RAG_MAX_EXCERPT_CHARS", 420),
        min_relevance_score=_get_float("RAG_MIN_RELEVANCE_SCORE", 0.0),
    )
