"""Sparse lexical retrieval abstraction."""

from __future__ import annotations

from backend.rag.metadata import ChunkRecord, RetrievedChunk
from backend.rag.storage.bm25_store import BM25Store


class BM25Retriever:
    """BM25 retriever with local persistence."""

    def __init__(self, store: BM25Store) -> None:
        self.store = store

    def index_chunks(self, chunks: list[ChunkRecord]) -> None:
        """Store sparse documents."""
        if not chunks:
            return
        self.store.add_documents([chunk.to_dict() for chunk in chunks])

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Retrieve top sparse matches."""
        results = self.store.search(query, top_k=top_k)
        return [
            RetrievedChunk(**metadata, retrieval_score=score, sparse_score=score, match_origin=["sparse"])
            for metadata, score in results
        ]

    def delete_document(self, document_id: str) -> None:
        """Remove a document from the sparse index."""
        self.store.delete_document(document_id)

    def clear(self) -> None:
        """Clear the sparse index."""
        self.store.clear()
