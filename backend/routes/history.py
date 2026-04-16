"""History routes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import HistoryResponse, MessageResponse
from backend.services.history_service import get_history_service


router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def get_history() -> HistoryResponse:
    """Return chat history."""
    return HistoryResponse(history=get_history_service().get_history())


@router.post("/history/clear", response_model=MessageResponse)
async def clear_history() -> MessageResponse:
    """Clear the saved conversation history."""
    get_history_service().clear()
    return MessageResponse(message="History cleared.")
