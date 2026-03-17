"""FAISS-backed vector retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np


class VectorStore:
    """Persist document chunk metadata alongside a FAISS index."""

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store_dir / "index.faiss"
        self.metadata_path = self.store_dir / "metadata.json"
        self.dimension: int | None = None
        self.index: faiss.Index | None = None
        self.metadata: List[dict] = []
        self._load()

    def _load(self) -> None:
        """Load saved FAISS index and metadata if present."""
        if self.metadata_path.exists():
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.dimension = self.index.d

    def _save(self) -> None:
        """Persist the vector store to disk."""
        self.metadata_path.write_text(
            json.dumps(self.metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))

    def add_embeddings(self, embeddings: List[List[float]], metadata: List[dict]) -> None:
        """Add new chunk embeddings and metadata to the store."""
        if not embeddings:
            return

        vectors = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(vectors)

        if self.index is None:
            self.dimension = vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)

        if vectors.shape[1] != self.dimension:
            raise ValueError("Embedding dimension does not match existing vector store.")

        self.index.add(vectors)
        self.metadata.extend(metadata)
        self._save()

    def search(self, embedding: List[float], top_k: int = 4) -> List[Tuple[dict, float]]:
        """Return the most relevant chunks for a query embedding."""
        if self.index is None or not self.metadata:
            return []

        query = np.array([embedding], dtype="float32")
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, top_k)

        results: List[Tuple[dict, float]] = []
        for index, score in zip(indices[0], scores[0]):
            if index < 0 or index >= len(self.metadata):
                continue
            results.append((self.metadata[index], float(score)))
        return results
