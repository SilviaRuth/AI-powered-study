"""Shared RAG dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ParsedBlock:
    """A natural text block extracted from a document."""

    text: str
    block_type: str
    page_number: int | None = None
    section_title: str | None = None


@dataclass
class ParsedPage:
    """Page-level parsed document data."""

    page_number: int | None
    text: str
    blocks: list[ParsedBlock] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """Document representation created during parsing."""

    document_id: str
    filename: str
    stored_filename: str
    source_type: str
    pages: list[ParsedPage]
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChunkRecord:
    """Chunk metadata stored and retrieved by the system."""

    document_id: str
    filename: str
    stored_filename: str
    chunk_id: int
    page_start: int | None
    page_end: int | None
    section_title: str | None
    chunk_text: str
    token_count: int
    source_type: str
    tags: list[str] = field(default_factory=list)

    def key(self) -> str:
        return f"{self.document_id}:{self.chunk_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievedChunk(ChunkRecord):
    """Chunk plus retrieval metadata."""

    retrieval_score: float = 0.0
    rerank_score: float | None = None
    dense_score: float | None = None
    sparse_score: float | None = None
    match_origin: list[str] = field(default_factory=list)
    compressed_excerpt: str | None = None
    citation_id: str | None = None
    citation_label: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RetrievedChunk":
        return cls(**payload)


def chunk_from_dict(payload: dict[str, Any]) -> ChunkRecord:
    """Create a chunk record from serialized data."""
    return ChunkRecord(**payload)
