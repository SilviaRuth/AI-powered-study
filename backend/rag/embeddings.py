"""OpenAI embedding and answer generation helpers."""

from __future__ import annotations

import os
from typing import Iterable, List

from openai import OpenAI


DEFAULT_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")


class OpenAIService:
    """Thin wrapper around OpenAI API calls used by the RAG pipeline."""

    def __init__(
        self,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        chat_model: str = DEFAULT_CHAT_MODEL,
    ) -> None:
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """Lazily create the API client so imports work without env vars set."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        prepared = list(texts)
        if not prepared:
            return []
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=prepared,
        )
        return [item.embedding for item in response.data]

    def answer_with_context(self, question: str, context: str, history: str) -> str:
        """Generate a grounded answer that only uses retrieved context."""
        prompt = (
            "You are an AI assistant.\n"
            "Answer ONLY using the provided context.\n"
            "If the answer is not in the context, say \"I don't know\".\n\n"
            f"CHAT HISTORY:\n{history or 'No previous conversation.'}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}"
        )
        response = self.client.responses.create(
            model=self.chat_model,
            input=prompt,
        )
        return response.output_text.strip()
