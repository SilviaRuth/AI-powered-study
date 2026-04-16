"""Persistent BM25 store."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


class BM25Store:
    """Persist sparse lexical retrieval data locally."""

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.docs_path = self.store_dir / "docs.json"
        self.stats_path = self.store_dir / "stats.json"
        self.documents: list[dict] = []
        self.stats: dict[str, float | int | dict[str, int]] = {}
        self._load()

    def _load(self) -> None:
        if self.docs_path.exists():
            self.documents = json.loads(self.docs_path.read_text(encoding="utf-8"))
        if self.stats_path.exists():
            self.stats = json.loads(self.stats_path.read_text(encoding="utf-8"))
        elif self.documents:
            self._recompute_stats()

    def _save(self) -> None:
        self.docs_path.write_text(
            json.dumps(self.documents, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        self.stats_path.write_text(
            json.dumps(self.stats, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        """Clear sparse data."""
        self.documents = []
        self.stats = {}
        self._save()

    def add_documents(self, chunks: list[dict]) -> None:
        """Add chunk documents to the sparse store."""
        for chunk in chunks:
            tokens = _tokenize(chunk["chunk_text"])
            self.documents.append(
                {
                    "metadata": chunk,
                    "tokens": tokens,
                    "term_freq": dict(Counter(tokens)),
                    "length": len(tokens),
                }
            )
        self._recompute_stats()
        self._save()

    def delete_document(self, document_id: str) -> None:
        """Delete all sparse entries for a document."""
        self.documents = [
            item for item in self.documents if item["metadata"].get("document_id") != document_id
        ]
        self._recompute_stats()
        self._save()

    def search(self, query: str, top_k: int) -> list[tuple[dict, float]]:
        """Search the sparse index with BM25."""
        if not self.documents:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        avgdl = float(self.stats.get("avgdl", 1.0)) or 1.0
        doc_count = int(self.stats.get("doc_count", 0))
        document_freqs = self.stats.get("document_freqs", {})
        k1 = 1.5
        b = 0.75
        results: list[tuple[dict, float]] = []

        for item in self.documents:
            score = 0.0
            doc_length = item["length"] or 1
            term_freq = item["term_freq"]
            for token in query_tokens:
                tf = term_freq.get(token, 0)
                if tf == 0:
                    continue
                df = int(document_freqs.get(token, 0))
                idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_length / avgdl)
                score += idf * (numerator / denominator)
            if score > 0:
                results.append((item["metadata"], score))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

    def _recompute_stats(self) -> None:
        if not self.documents:
            self.stats = {"doc_count": 0, "avgdl": 0.0, "document_freqs": {}}
            return

        document_freqs: Counter[str] = Counter()
        total_length = 0
        for item in self.documents:
            total_length += item["length"]
            document_freqs.update(set(item["tokens"]))

        self.stats = {
            "doc_count": len(self.documents),
            "avgdl": total_length / len(self.documents),
            "document_freqs": dict(document_freqs),
        }


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())
