"""Pydantic API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SourceCard(BaseModel):
    """Structured evidence card returned to the frontend."""

    document_id: str
    filename: str
    page_label: str | None = None
    section_title: str | None = None
    excerpt: str
    retrieval_score: float
    rerank_score: float | None = None
    match_origin: list[str] = Field(default_factory=list)
    chunk_id: int
    citation_label: str


class QueryRequest(BaseModel):
    """Question payload."""

    question: str


class QueryResponse(BaseModel):
    """Question answer response."""

    answer: str
    sources: list[SourceCard] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Upload response payload."""

    message: str
    filename: str
    document_id: str
    chunks_indexed: int


class HistoryEntry(BaseModel):
    """Saved chat message pair."""

    question: str
    answer: str
    sources: list[SourceCard] = Field(default_factory=list)


class HistoryResponse(BaseModel):
    """Chat history response."""

    history: list[HistoryEntry] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class DocumentSummary(BaseModel):
    """Indexed document metadata."""

    document_id: str
    original_filename: str
    stored_filename: str
    upload_timestamp: str
    source_type: str
    chunk_count: int
    status: str
    tags: list[str] = Field(default_factory=list)


class DocumentsResponse(BaseModel):
    """List of indexed documents."""

    documents: list[DocumentSummary] = Field(default_factory=list)


class RebuildResponse(BaseModel):
    """Index rebuild response."""

    message: str
    indexed_documents: int


class EvalRunResponse(BaseModel):
    """Evaluation API response."""

    results: dict[str, Any]
