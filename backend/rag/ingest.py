"""Helpers for processed document artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from backend.rag.metadata import ChunkRecord, chunk_from_dict


def save_processed_document(
    processed_dir: Path,
    *,
    document_id: str,
    parsed_document: dict,
    chunks: list[ChunkRecord],
) -> Path:
    """Persist parsed pages and chunk metadata for rebuilds and debugging."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / f"{document_id}.json"
    payload = {
        "document": parsed_document,
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return output_path


def load_processed_chunks(processed_path: Path) -> list[ChunkRecord]:
    """Load serialized chunk records from disk."""
    payload = json.loads(processed_path.read_text(encoding="utf-8"))
    return [chunk_from_dict(item) for item in payload.get("chunks", [])]
