"""OpenAI integration helpers."""

from __future__ import annotations

import json
import os
import re
from typing import Iterable

from openai import OpenAI

from backend.core.config import get_settings


class OpenAIService:
    """Thin wrapper around the OpenAI APIs used by the RAG stack."""

    def __init__(self) -> None:
        settings = get_settings()
        self.embedding_model = settings.openai_embedding_model
        self.chat_model = settings.openai_chat_model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """Lazily construct the client."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        prepared = [text for text in texts if text.strip()]
        if not prepared:
            return []
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=prepared,
        )
        return [item.embedding for item in response.data]

    def complete_text(self, prompt: str) -> str:
        """Generate plain text output."""
        response = self.client.responses.create(
            model=self.chat_model,
            input=prompt,
        )
        return response.output_text.strip()

    def complete_json(self, prompt: str) -> dict:
        """Generate a JSON object and parse it defensively."""
        raw = self.complete_text(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)
