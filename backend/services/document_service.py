"""Document ingestion and management service."""

from __future__ import annotations

from functools import lru_cache

from fastapi import UploadFile

from backend.models.schemas import DocumentSummary, DocumentsResponse, RebuildResponse, UploadResponse
from backend.rag.pipeline import get_assistant_pipeline


class DocumentService:
    """Document management workflows."""

    def __init__(self) -> None:
        self.pipeline = get_assistant_pipeline()

    async def ingest(self, upload: UploadFile) -> UploadResponse:
        """Ingest an uploaded file."""
        payload = await self.pipeline.ingest_upload(upload)
        return UploadResponse(**payload)

    def list_documents(self) -> DocumentsResponse:
        """List indexed documents."""
        documents = [DocumentSummary(**item) for item in self.pipeline.list_documents()]
        return DocumentsResponse(documents=documents)

    def delete_document(self, document_id: str) -> dict:
        """Delete a document and associated index data."""
        self.pipeline.delete_document(document_id)
        return {"message": "Document deleted successfully."}

    def rebuild_indexes(self) -> RebuildResponse:
        """Rebuild the local indexes from processed artifacts."""
        count = self.pipeline.rebuild_indexes()
        return RebuildResponse(message="Indexes rebuilt successfully.", indexed_documents=count)


@lru_cache(maxsize=1)
def get_document_service() -> DocumentService:
    """Return a shared document service."""
    return DocumentService()
