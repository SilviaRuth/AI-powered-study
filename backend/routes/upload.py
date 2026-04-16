"""Upload routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.exceptions import IngestionError
from backend.models.schemas import UploadResponse
from backend.services.document_service import get_document_service


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Upload and index a supported document."""
    try:
        return await get_document_service().ingest(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IngestionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
