"""API router assembly."""

from __future__ import annotations

from fastapi import APIRouter

from backend.routes.docs import router as docs_router
from backend.routes.eval import router as eval_router
from backend.routes.history import router as history_router
from backend.routes.query import router as query_router
from backend.routes.upload import router as upload_router


api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(query_router)
api_router.include_router(history_router)
api_router.include_router(docs_router)
api_router.include_router(eval_router)
