from fastapi.testclient import TestClient

from backend.app import create_app
from backend.models.schemas import QueryResponse


class _StubHistoryService:
    def get_history(self):
        return [{"question": "Q1", "answer": "A1", "sources": []}]

    def clear(self):
        return None


class _StubQueryService:
    def answer(self, question: str):
        return QueryResponse(answer=f"Echo: {question}", sources=[])


class _StubDocumentService:
    async def ingest(self, upload):
        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": upload.filename,
            "document_id": "doc_test",
            "chunks_indexed": 2,
        }

    def list_documents(self):
        return {
            "documents": [
                {
                    "document_id": "doc_test",
                    "original_filename": "notes.txt",
                    "stored_filename": "stored_notes.txt",
                    "upload_timestamp": "2026-04-14T00:00:00+00:00",
                    "source_type": "txt",
                    "chunk_count": 2,
                    "status": "indexed",
                    "tags": [],
                }
            ]
        }

    def delete_document(self, document_id: str):
        return {"message": "Document deleted successfully."}

    def rebuild_indexes(self):
        return {"message": "Indexes rebuilt successfully.", "indexed_documents": 1}


def test_api_routes(monkeypatch) -> None:
    from backend.routes import docs as docs_routes
    from backend.routes import history as history_routes
    from backend.routes import query as query_routes
    from backend.routes import upload as upload_routes

    monkeypatch.setattr(history_routes, "get_history_service", lambda: _StubHistoryService())
    monkeypatch.setattr(query_routes, "get_query_service", lambda: _StubQueryService())
    monkeypatch.setattr(upload_routes, "get_document_service", lambda: _StubDocumentService())
    monkeypatch.setattr(docs_routes, "get_document_service", lambda: _StubDocumentService())

    client = TestClient(create_app())

    history_response = client.get("/api/history")
    query_response = client.post("/api/query", json={"question": "What is self-attention?"})
    docs_response = client.get("/api/documents")

    assert history_response.status_code == 200
    assert query_response.status_code == 200
    assert docs_response.status_code == 200
    assert query_response.json()["answer"] == "Echo: What is self-attention?"
