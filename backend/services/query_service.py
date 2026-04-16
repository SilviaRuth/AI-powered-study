"""Question answering service."""

from __future__ import annotations

from functools import lru_cache

from backend.models.schemas import QueryResponse
from backend.rag.pipeline import get_assistant_pipeline
from backend.services.history_service import get_history_service


class QueryService:
    """Handle grounded QA requests."""

    def __init__(self) -> None:
        self.pipeline = get_assistant_pipeline()
        self.history_service = get_history_service()

    def answer(self, question: str) -> QueryResponse:
        """Answer a question and persist the result to history."""
        history = self.history_service.get_history()
        answer, sources, _rewritten_query = self.pipeline.answer_question(question, history)
        self.history_service.append_entry(question=question, answer=answer, sources=sources)
        return QueryResponse(answer=answer, sources=sources)


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    """Return a shared query service."""
    return QueryService()
