"""Citation helpers."""

from __future__ import annotations

from backend.core.config import get_settings
from backend.rag.metadata import RetrievedChunk


class CitationBuilder:
    """Attach readable evidence citations to results."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def assign_labels(self, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Assign stable prompt-facing and user-facing citation labels."""
        for index, candidate in enumerate(candidates, start=1):
            candidate.citation_id = f"S{index}"
            candidate.citation_label = self.display_label(candidate)
        return candidates

    def display_label(self, candidate: RetrievedChunk) -> str:
        """Build a compact citation label."""
        if candidate.page_start is None:
            return f"[{candidate.filename} chunk {candidate.chunk_id}]"
        if candidate.page_end and candidate.page_end != candidate.page_start:
            return f"[{candidate.filename} pp.{candidate.page_start}-{candidate.page_end}]"
        return f"[{candidate.filename} p.{candidate.page_start}]"

    def build_answer(
        self,
        answer: str,
        cited_ids: list[str],
        candidates: list[RetrievedChunk],
    ) -> str:
        """Append human-readable citations to the final answer."""
        if answer.strip() == "I don't know":
            return "I don't know"
        cited = [candidate.citation_label for candidate in candidates if candidate.citation_id in cited_ids]
        unique_labels = []
        for label in cited:
            if label and label not in unique_labels:
                unique_labels.append(label)
        if not unique_labels:
            return "I don't know"
        return f"{answer.strip()} {' '.join(unique_labels)}".strip()

    def build_sources(self, cited_ids: list[str], candidates: list[RetrievedChunk]) -> list[dict]:
        """Build structured evidence cards for cited chunks."""
        sources = []
        for candidate in candidates:
            if candidate.citation_id not in cited_ids:
                continue
            sources.append(
                {
                    "document_id": candidate.document_id,
                    "filename": candidate.filename,
                    "page_label": self._page_label(candidate),
                    "section_title": candidate.section_title,
                    "excerpt": (candidate.compressed_excerpt or candidate.chunk_text)[
                        : self.settings.max_excerpt_chars
                    ],
                    "retrieval_score": round(candidate.retrieval_score, 4),
                    "rerank_score": round(candidate.rerank_score, 4)
                    if candidate.rerank_score is not None
                    else None,
                    "match_origin": candidate.match_origin,
                    "chunk_id": candidate.chunk_id,
                    "citation_label": candidate.citation_label or self.display_label(candidate),
                }
            )
        return sources

    def _page_label(self, candidate: RetrievedChunk) -> str | None:
        if candidate.page_start is None:
            return None
        if candidate.page_end and candidate.page_end != candidate.page_start:
            return f"pp.{candidate.page_start}-{candidate.page_end}"
        return f"p.{candidate.page_start}"
