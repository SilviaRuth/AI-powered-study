"""Query routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.core.exceptions import RetrievalError
from backend.models.schemas import QueryRequest, QueryResponse
from backend.services.query_service import get_query_service


router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(payload: QueryRequest) -> QueryResponse:
    """Answer a question using retrieved document context."""
    try:
        return get_query_service().answer(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RetrievalError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
