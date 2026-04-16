"""Evaluation dataset loading."""

from __future__ import annotations

import json
from pathlib import Path


def load_dataset(dataset_path: Path) -> list[dict]:
    """Load the benchmark dataset from JSON."""
    return json.loads(dataset_path.read_text(encoding="utf-8"))
