"""Heuristic answer evaluation."""

from __future__ import annotations


def evaluate_answers(run_items: list[dict]) -> dict[str, float]:
    """Compute lightweight answer quality metrics."""
    citation_correct = 0
    unsupported_answers = 0
    correct_idk = 0

    for item in run_items:
        expected_docs = set(item.get("expected_documents", []))
        answer = item.get("answer", "")
        source_docs = {source["filename"] for source in item.get("sources", [])}
        is_idk = answer.strip() == "I don't know"

        if source_docs and (not expected_docs or source_docs & expected_docs):
            citation_correct += 1
        if not expected_docs and not is_idk:
            unsupported_answers += 1
        if not expected_docs and is_idk:
            correct_idk += 1

    total = len(run_items) or 1
    no_answer_expected = sum(1 for item in run_items if not item.get("expected_documents")) or 1
    return {
        "citation_correctness": citation_correct / total,
        "unsupported_answer_rate": unsupported_answers / no_answer_expected,
        "correct_i_dont_know_rate": correct_idk / no_answer_expected,
    }
