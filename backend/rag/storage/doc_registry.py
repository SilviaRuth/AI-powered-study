"""Document registry stored on disk as JSON."""

from __future__ import annotations

import json
from pathlib import Path


class DocumentRegistry:
    """Lightweight document registry."""

    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._documents = self._load()

    def _load(self) -> dict[str, dict]:
        if not self.registry_path.exists():
            return {}
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.registry_path.write_text(
            json.dumps(self._documents, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def upsert(self, payload: dict) -> None:
        """Insert or update a document record."""
        self._documents[payload["document_id"]] = payload
        self._save()

    def list_documents(self) -> list[dict]:
        """Return registry entries sorted by upload time descending."""
        return sorted(
            self._documents.values(),
            key=lambda item: item.get("upload_timestamp", ""),
            reverse=True,
        )

    def get(self, document_id: str) -> dict | None:
        """Fetch a document entry."""
        return self._documents.get(document_id)

    def delete(self, document_id: str) -> dict | None:
        """Delete a document entry and return it."""
        removed = self._documents.pop(document_id, None)
        self._save()
        return removed

    def all(self) -> dict[str, dict]:
        """Return the raw registry mapping."""
        return dict(self._documents)
