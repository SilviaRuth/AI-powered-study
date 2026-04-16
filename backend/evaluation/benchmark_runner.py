"""Local benchmark runner."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from backend.core.config import get_settings
from backend.evaluation.answer_eval import evaluate_answers
from backend.evaluation.dataset_loader import load_dataset
from backend.evaluation.retrieval_eval import evaluate_retrieval
from backend.rag.pipeline import get_assistant_pipeline


class BenchmarkRunner:
    """Run retrieval and answer evaluation against a local dataset."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pipeline = get_assistant_pipeline()

    def run(self, dataset_path: Path | None = None, output_path: Path | None = None) -> dict:
        """Execute the benchmark and write a JSON report."""
        dataset_path = dataset_path or (self.settings.eval_dir / "golden_set.json")
        output_path = output_path or (self.settings.eval_dir / "last_run.json")
        dataset = load_dataset(dataset_path)
        run_items: list[dict] = []

        for item in dataset:
            question = item["question"]
            _rewritten_query, retrieved = self.pipeline.retrieve_candidates(question, history=[])
            retrieved_sources = self.pipeline.citation_builder.build_sources(
                [candidate.citation_id for candidate in retrieved if candidate.citation_id],
                retrieved,
            )
            answer, sources, _ = self.pipeline.answer_question(question, history=[])
            run_items.append(
                {
                    **item,
                    "answer": answer,
                    "sources": sources,
                    "retrieved_sources": retrieved_sources,
                }
            )

        results = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "dataset_size": len(dataset),
            "retrieval": evaluate_retrieval(run_items, top_k=self.settings.top_k),
            "answers": evaluate_answers(run_items),
            "items": run_items,
        }
        output_path.write_text(json.dumps(results, ensure_ascii=True, indent=2), encoding="utf-8")
        return results
