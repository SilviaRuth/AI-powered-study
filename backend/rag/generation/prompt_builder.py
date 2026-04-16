"""Prompt construction for grounded answer generation."""

from __future__ import annotations

from backend.rag.metadata import RetrievedChunk


class PromptBuilder:
    """Build prompts for answer generation."""

    def build(self, question: str, history: list[dict], evidence: list[RetrievedChunk]) -> str:
        """Create a concise grounded-answer prompt."""
        history_text = "\n".join(
            f"User: {entry['question']}\nAssistant: {entry['answer']}" for entry in history[-4:]
        )
        evidence_blocks = []
        for candidate in evidence:
            evidence_blocks.append(
                "\n".join(
                    [
                        f"{candidate.citation_id} {candidate.citation_label}",
                        f"Section: {candidate.section_title or 'Unknown'}",
                        candidate.compressed_excerpt or candidate.chunk_text,
                    ]
                )
            )
        return (
            "You are an AI study assistant.\n"
            "Use only the supplied evidence.\n"
            "If the evidence does not support the answer, answer exactly with \"I don't know\".\n"
            "Do not invent citations. Keep answers concise unless the user asks for more detail.\n"
            "Return strict JSON as {\"answer\": \"...\", \"citations\": [\"S1\"]}.\n\n"
            f"RECENT HISTORY:\n{history_text or 'No previous conversation.'}\n\n"
            f"EVIDENCE:\n{chr(10).join(evidence_blocks)}\n\n"
            f"QUESTION:\n{question}"
        )
