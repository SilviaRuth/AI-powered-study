"""Rebuild dense and sparse indexes from processed document artifacts."""

from __future__ import annotations

from backend.rag.pipeline import get_assistant_pipeline


def main() -> None:
    count = get_assistant_pipeline().rebuild_indexes()
    print(f"Rebuilt indexes for {count} processed documents.")


if __name__ == "__main__":
    main()
