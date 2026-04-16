"""Retrieval metrics."""

from __future__ import annotations


def evaluate_retrieval(run_items: list[dict], *, top_k: int) -> dict[str, float]:
    """Compute hit@k, recall@k, and MRR from retrieval outputs."""
    hits = 0
    recalls = []
    reciprocal_ranks = []

    for item in run_items:
        expected_docs = set(item.get("expected_documents", []))
        retrieved_docs = [source["filename"] for source in item.get("retrieved_sources", [])[:top_k]]
        if not expected_docs:
            reciprocal_ranks.append(0.0)
            recalls.append(1.0)
            continue

        matched = [doc for doc in retrieved_docs if doc in expected_docs]
        if matched:
            hits += 1
            first_rank = retrieved_docs.index(matched[0]) + 1
            reciprocal_ranks.append(1 / first_rank)
        else:
            reciprocal_ranks.append(0.0)

        recalls.append(len(set(matched)) / len(expected_docs))

    total = len(run_items) or 1
    return {
        "hit_at_k": hits / total,
        "recall_at_k": sum(recalls) / total,
        "mrr": sum(reciprocal_ranks) / total,
    }
