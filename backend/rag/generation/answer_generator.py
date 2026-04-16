"""Grounded answer generation."""

from __future__ import annotations

from backend.rag.embeddings import OpenAIService
from backend.rag.generation.prompt_builder import PromptBuilder
from backend.rag.metadata import RetrievedChunk


class AnswerGenerator:
    """Generate grounded answers with cited evidence ids."""

    def __init__(self, openai_service: OpenAIService, prompt_builder: PromptBuilder) -> None:
        self.openai_service = openai_service
        self.prompt_builder = prompt_builder

    def generate(
        self,
        question: str,
        history: list[dict],
        evidence: list[RetrievedChunk],
    ) -> tuple[str, list[str]]:
        """Return a grounded answer and the citation ids actually used."""
        if not evidence:
            return "I don't know", []

        payload = self.openai_service.complete_json(
            self.prompt_builder.build(question=question, history=history, evidence=evidence)
        )
        answer = str(payload.get("answer", "")).strip() or "I don't know"
        citations = [str(item).strip() for item in payload.get("citations", []) if str(item).strip()]
        if answer.lower() in {"i don't know", "idk", "unknown"}:
            return "I don't know", []
        return answer, citations
