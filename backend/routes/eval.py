"""Evaluation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.evaluation.benchmark_runner import BenchmarkRunner
from backend.models.schemas import EvalRunResponse


router = APIRouter()


@router.post("/eval/run", response_model=EvalRunResponse)
async def run_eval() -> EvalRunResponse:
    """Run the local evaluation benchmark."""
    try:
        return EvalRunResponse(results=BenchmarkRunner().run())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run evaluation: {exc}") from exc
