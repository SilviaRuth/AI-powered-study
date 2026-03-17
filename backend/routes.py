"""API routes for document upload, querying, and history."""

from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.rag.pipeline import assistant_pipeline


router = APIRouter()


class QueryRequest(BaseModel):
    """User question payload."""

    question: str


class QueryResponse(BaseModel):
    """Question answer response."""

    answer: str
    sources: List[dict]


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    """Upload and index a supported document."""
    try:
        result = await assistant_pipeline.ingest_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@router.post("/query", response_model=QueryResponse)
async def query_documents(payload: QueryRequest) -> QueryResponse:
    """Answer a question using retrieved document context."""
    try:
        answer, sources = assistant_pipeline.answer_question(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return QueryResponse(answer=answer, sources=sources)


@router.get("/history")
async def get_history() -> dict:
    """Return chat history."""
    return {"history": assistant_pipeline.get_history()}


@router.post("/history/clear")
async def clear_history() -> dict:
    """Clear the saved conversation history."""
    assistant_pipeline.clear_history()
    return {"message": "History cleared."}
