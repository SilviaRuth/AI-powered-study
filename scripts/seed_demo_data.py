"""Create a few demo study notes and explain how to use them."""

from __future__ import annotations

from pathlib import Path


DEMO_DOCS = {
    "lecture_attention.txt": """Transformer Architecture

Self-attention lets a token attend to other relevant tokens in the same sequence. This helps the model capture long-range dependencies without relying on recurrence.

Multi-head attention projects the input into multiple subspaces so the model can learn several relationships in parallel.
""",
    "lecture_rnn.txt": """RNN Comparison

Recurrent neural networks process tokens sequentially and pass hidden state forward through time. They can model order, but long-range dependency learning is harder because gradients can vanish or explode.

LSTMs improve on vanilla RNNs by introducing gates that control memory updates.
""",
    "study_skills.txt": """Evidence-Based Studying

Active recall improves retention because it forces the learner to retrieve information rather than only re-read it.

Spaced repetition schedules reviews over increasing intervals to improve long-term memory.
""",
}


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    target_dir = base_dir / "data" / "eval"
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in DEMO_DOCS.items():
        (target_dir / filename).write_text(content, encoding="utf-8")

    print(f"Seeded {len(DEMO_DOCS)} demo documents in {target_dir}.")
    print("Upload them through the UI or copy them into data/uploads and re-index.")


if __name__ == "__main__":
    main()
