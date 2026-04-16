"""FAISS-backed dense store with local metadata persistence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import faiss
import numpy as np


class FaissStore:
    """Persist normalized embeddings and chunk metadata locally."""

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store_dir / "index.faiss"
        self.metadata_path = self.store_dir / "metadata.json"
        self.vectors_path = self.store_dir / "vectors.npy"
        self.index: faiss.Index | None = None
        self.dimension: int | None = None
        self.metadata: list[dict] = []
        self.vectors = np.empty((0, 0), dtype="float32")
        self._migrate_legacy_store()
        self._load()

    def _migrate_legacy_store(self) -> None:
        legacy_dir = self.store_dir.parent
        legacy_index = legacy_dir / "index.faiss"
        legacy_metadata = legacy_dir / "metadata.json"
        if self.index_path.exists() or not legacy_index.exists() or not legacy_metadata.exists():
            return
        shutil.copy2(legacy_index, self.index_path)
        shutil.copy2(legacy_metadata, self.metadata_path)

    def _load(self) -> None:
        if self.metadata_path.exists():
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if self.vectors_path.exists():
            loaded = np.load(self.vectors_path)
            self.vectors = loaded.astype("float32")
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.dimension = self.index.d
        elif self.vectors.size:
            self.dimension = self.vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(self.vectors)

    def _save(self) -> None:
        self.metadata_path.write_text(
            json.dumps(self.metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        if self.vectors.size:
            np.save(self.vectors_path, self.vectors)
        elif self.vectors_path.exists():
            self.vectors_path.unlink()

        if self.index is not None and self.metadata:
            faiss.write_index(self.index, str(self.index_path))
        elif self.index_path.exists():
            self.index_path.unlink()

    def clear(self) -> None:
        """Clear the dense store."""
        self.index = None
        self.dimension = None
        self.metadata = []
        self.vectors = np.empty((0, 0), dtype="float32")
        self._save()

    def add_embeddings(self, embeddings: list[list[float]], metadata: list[dict]) -> None:
        """Append embeddings and metadata."""
        if not embeddings:
            return
        vectors = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(vectors)
        if self.index is None:
            self.dimension = vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)
            self.vectors = np.empty((0, self.dimension), dtype="float32")
        if vectors.shape[1] != self.dimension:
            raise ValueError("Embedding dimension does not match existing dense index.")

        self.index.add(vectors)
        self.vectors = np.vstack([self.vectors, vectors]) if self.vectors.size else vectors
        self.metadata.extend(metadata)
        self._save()

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to a document and rebuild the index."""
        if not self.metadata:
            return
        keep_indices = [
            index for index, item in enumerate(self.metadata) if item.get("document_id") != document_id
        ]
        self.metadata = [self.metadata[index] for index in keep_indices]
        if self.vectors.size and keep_indices:
            self.vectors = self.vectors[keep_indices]
        else:
            self.vectors = np.empty((0, self.dimension or 0), dtype="float32")

        if not self.metadata:
            self.clear()
            return

        self.index = faiss.IndexFlatIP(self.vectors.shape[1])
        self.index.add(self.vectors)
        self.dimension = self.vectors.shape[1]
        self._save()

    def search(self, embedding: list[float], top_k: int) -> list[tuple[dict, float]]:
        """Search the dense index."""
        if self.index is None or not self.metadata:
            return []
        query = np.array([embedding], dtype="float32")
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, top_k)
        results: list[tuple[dict, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            results.append((self.metadata[idx], float(score)))
        return results
