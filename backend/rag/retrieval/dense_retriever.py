"""Dense retrieval abstraction."""

from __future__ import annotations

from backend.rag.embeddings import OpenAIService
from backend.rag.metadata import ChunkRecord, RetrievedChunk
from backend.rag.storage.faiss_store import FaissStore


class DenseRetriever:
    """FAISS-based dense retriever."""

    def __init__(self, store: FaissStore, openai_service: OpenAIService) -> None:
        self.store = store
        self.openai_service = openai_service

    def index_chunks(self, chunks: list[ChunkRecord]) -> None:
        """Embed and store chunks."""
        if not chunks:
            return
        embeddings = self.openai_service.embed_texts(chunk.chunk_text for chunk in chunks)
        self.store.add_embeddings(embeddings, [chunk.to_dict() for chunk in chunks])

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Retrieve top dense matches."""
        if not query.strip():
            return []
        query_embedding = self.openai_service.embed_texts([query])[0]
        results = self.store.search(query_embedding, top_k=top_k)
        return [
            RetrievedChunk(**metadata, retrieval_score=score, dense_score=score, match_origin=["dense"])
            for metadata, score in results
        ]

    def delete_document(self, document_id: str) -> None:
        """Remove a document from the dense index."""
        self.store.delete_document(document_id)

    def clear(self) -> None:
        """Clear the dense index."""
        self.store.clear()
