"""Chat history persistence."""

from __future__ import annotations

import json
from functools import lru_cache

from backend.core.config import get_settings


class HistoryService:
    """Store conversation history in a local JSON file."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.ensure_directories()

    def get_history(self) -> list[dict]:
        """Return saved chat history."""
        if not self.settings.history_path.exists():
            return []
        raw_history = json.loads(self.settings.history_path.read_text(encoding="utf-8"))
        normalized_history = self._normalize_history(raw_history)
        if normalized_history != raw_history:
            self._save(normalized_history)
        return normalized_history

    def append_entry(self, question: str, answer: str, sources: list[dict]) -> None:
        """Append a chat entry."""
        history = self.get_history()
        history.append({"question": question, "answer": answer, "sources": sources})
        self._save(history)

    def clear(self) -> None:
        """Clear saved chat history."""
        self._save([])

    def _save(self, history: list[dict]) -> None:
        self.settings.history_path.write_text(
            json.dumps(history, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _normalize_history(self, history: list[dict]) -> list[dict]:
        """Normalize persisted history so older saved entries remain readable."""
        normalized: list[dict] = []
        for entry in history:
            sources = entry.get("sources") or []
            normalized.append(
                {
                    "question": entry.get("question", ""),
                    "answer": entry.get("answer", ""),
                    "sources": [self._normalize_source(source) for source in sources if isinstance(source, dict)],
                }
            )
        return normalized

    def _normalize_source(self, source: dict) -> dict:
        """Backfill fields for legacy source cards saved before the schema upgrade."""
        filename = str(source.get("filename", "Unknown source"))
        chunk_id = int(source.get("chunk_id", -1))
        page_label = source.get("page_label")
        citation_label = source.get("citation_label")
        if not citation_label:
            citation_label = page_label and f"[{filename} {page_label}]" or f"[{filename} chunk {chunk_id}]"

        return {
            "document_id": source.get("document_id") or f"legacy:{filename}",
            "filename": filename,
            "page_label": page_label,
            "section_title": source.get("section_title"),
            "excerpt": str(source.get("excerpt", "")),
            "retrieval_score": float(source.get("retrieval_score", source.get("score", 0.0)) or 0.0),
            "rerank_score": source.get("rerank_score"),
            "match_origin": list(source.get("match_origin", [])),
            "chunk_id": chunk_id,
            "citation_label": citation_label,
        }


@lru_cache(maxsize=1)
def get_history_service() -> HistoryService:
    """Return a shared history service."""
    return HistoryService()
