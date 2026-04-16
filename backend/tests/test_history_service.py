import json

from backend.services.history_service import HistoryService


def test_history_service_normalizes_legacy_sources(tmp_path, monkeypatch) -> None:
    history_path = tmp_path / "history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "question": "What do you think of this resume?",
                    "answer": "Looks solid.",
                    "sources": [
                        {
                            "filename": "resume.pdf",
                            "chunk_id": 0,
                            "score": 0.42,
                            "excerpt": "Project management and Microsoft Office skills.",
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    class _Settings:
        def __init__(self):
            self.history_path = history_path

        def ensure_directories(self):
            history_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.services.history_service.get_settings", lambda: _Settings())

    service = HistoryService()
    history = service.get_history()

    assert history[0]["sources"][0]["document_id"] == "legacy:resume.pdf"
    assert history[0]["sources"][0]["retrieval_score"] == 0.42
    assert history[0]["sources"][0]["citation_label"] == "[resume.pdf chunk 0]"
