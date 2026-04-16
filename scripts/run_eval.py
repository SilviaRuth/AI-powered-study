"""Run the local benchmark suite."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.evaluation.benchmark_runner import BenchmarkRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local RAG evaluation benchmark.")
    parser.add_argument("--dataset", type=Path, default=None, help="Path to the benchmark dataset JSON.")
    parser.add_argument("--output", type=Path, default=None, help="Where to write the JSON results.")
    args = parser.parse_args()

    results = BenchmarkRunner().run(dataset_path=args.dataset, output_path=args.output)
    print(f"Evaluated {results['dataset_size']} benchmark items.")
    print(f"Retrieval metrics: {results['retrieval']}")
    print(f"Answer metrics: {results['answers']}")


if __name__ == "__main__":
    main()
