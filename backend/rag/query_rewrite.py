"""Conversational query rewriting."""

from __future__ import annotations

import logging
import re

from backend.core.config import get_settings
from backend.rag.embeddings import OpenAIService


LOGGER = logging.getLogger(__name__)
REFERENCE_TERMS = {
    "that",
    "this",
    "those",
    "these",
    "it",
    "they",
    "again",
    "compare",
    "next",
    "previous",
    "chapter",
    "section",
}


class QueryRewriter:
    """Rewrite follow-up questions into standalone retrieval queries."""

    def __init__(self, openai_service: OpenAIService) -> None:
        self.settings = get_settings()
        self.openai_service = openai_service

    def rewrite(self, question: str, history: list[dict]) -> str:
        """Rewrite a conversational query when useful."""
        if not self.settings.query_rewrite_enabled:
            return question
        if not history or not self.needs_rewrite(question):
            return question

        history_text = "\n".join(
            f"User: {entry['question']}\nAssistant: {entry['answer']}" for entry in history[-3:]
        )
        prompt = (
            "Rewrite the user's last question into a standalone search query for document retrieval.\n"
            "Keep the meaning, expand references, and return strict JSON as "
            "{\"query\": \"...\"}.\n\n"
            f"RECENT HISTORY:\n{history_text}\n\n"
            f"USER QUESTION:\n{question}"
        )
        try:
            payload = self.openai_service.complete_json(prompt)
            rewritten = str(payload.get("query", "")).strip()
            if rewritten:
                LOGGER.info("Query rewritten from %r to %r", question, rewritten)
                return rewritten
        except Exception as exc:  # pragma: no cover - fail-open path
            LOGGER.warning("Query rewrite failed; using original question: %s", exc)
        return question

    def needs_rewrite(self, question: str) -> bool:
        """Heuristic for follow-up questions that need more context."""
        lowered = question.lower()
        tokens = set(re.findall(r"\b\w+\b", lowered))
        return len(tokens) < 12 and bool(tokens & REFERENCE_TERMS)
