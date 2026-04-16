"""Document management routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.core.exceptions import DocumentNotFoundError
from backend.models.schemas import DocumentsResponse, MessageResponse, RebuildResponse
from backend.services.document_service import get_document_service


router = APIRouter()


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents() -> DocumentsResponse:
    """List indexed documents."""
    return get_document_service().list_documents()


@router.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(document_id: str) -> MessageResponse:
    """Delete a document from the registry and indexes."""
    try:
        payload = get_document_service().delete_document(document_id)
        return MessageResponse(**payload)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/rebuild", response_model=RebuildResponse)
async def rebuild_documents() -> RebuildResponse:
    """Rebuild all local indexes from processed artifacts."""
    return get_document_service().rebuild_indexes()
