"""End-to-end RAG pipeline for the AI Knowledge Assistant."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from backend.rag.chunking import chunk_text
from backend.rag.embeddings import OpenAIService
from backend.rag.retriever import VectorStore


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
VECTOR_DIR = BASE_DIR / "vector_store"
HISTORY_PATH = BASE_DIR / "data" / "history.json"
SUPPORTED_EXTENSIONS = {".pdf", ".txt"}
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.2"))


class KnowledgeAssistantPipeline:
    """Coordinates ingestion, retrieval, and answer generation."""

    def __init__(self) -> None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.vector_store = VectorStore(VECTOR_DIR)
        self.openai_service = OpenAIService()
        self.history = self._load_history()

    def _load_history(self) -> List[dict]:
        if HISTORY_PATH.exists():
            return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return []

    def _save_history(self) -> None:
        HISTORY_PATH.write_text(
            json.dumps(self.history, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    async def ingest_upload(self, upload: UploadFile) -> dict:
        """Save, parse, chunk, embed, and index an uploaded file."""
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError("Only PDF and TXT files are supported.")

        filename = f"{uuid.uuid4().hex}_{Path(upload.filename or 'document').name}"
        destination = UPLOAD_DIR / filename

        try:
            with destination.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)

            text = self._extract_text(destination)
            if not text.strip():
                raise ValueError("The uploaded document is empty or contains no extractable text.")

            chunks = chunk_text(text)
            if not chunks:
                raise ValueError("Unable to create chunks from the uploaded document.")

            embeddings = self.openai_service.embed_texts(chunks)
            metadata = [
                {
                    "filename": Path(upload.filename or filename).name,
                    "stored_filename": filename,
                    "chunk_id": chunk_id,
                    "text": chunk,
                }
                for chunk_id, chunk in enumerate(chunks)
            ]
            self.vector_store.add_embeddings(embeddings, metadata)
        except (PdfReadError, UnicodeDecodeError) as exc:
            destination.unlink(missing_ok=True)
            raise ValueError("The uploaded file could not be read as a valid document.") from exc
        except ValueError:
            destination.unlink(missing_ok=True)
            raise
        except Exception as exc:
            destination.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to process document: {exc}") from exc

        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": Path(upload.filename or filename).name,
            "chunks_indexed": len(chunks),
        }

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from a supported file."""
        if file_path.suffix.lower() == ".txt":
            return file_path.read_text(encoding="utf-8", errors="ignore")
        if file_path.suffix.lower() == ".pdf":
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError("Unsupported file type.")

    def answer_question(self, question: str) -> Tuple[str, List[dict]]:
        """Retrieve relevant chunks and generate a grounded answer."""
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")
        if not self.vector_store.metadata:
            raise ValueError("Upload at least one document before asking questions.")

        try:
            query_embedding = self.openai_service.embed_texts([cleaned_question])[0]
            retrieved = self.vector_store.search(query_embedding, top_k=4)
        except Exception as exc:
            raise RuntimeError(f"Failed to retrieve context: {exc}") from exc

        strong_matches = [item for item in retrieved if item[1] >= MIN_RELEVANCE_SCORE]
        if not strong_matches:
            answer = "I don't know"
            self._append_history(cleaned_question, answer, [])
            return answer, []

        context_parts = []
        sources = []
        for item, score in strong_matches:
            context_parts.append(
                f"[{item['filename']} | chunk {item['chunk_id']}]\n{item['text']}"
            )
            sources.append(
                {
                    "filename": item["filename"],
                    "chunk_id": item["chunk_id"],
                    "score": round(score, 4),
                    "excerpt": item["text"][:240],
                }
            )

        history_text = "\n".join(
            f"User: {entry['question']}\nAssistant: {entry['answer']}"
            for entry in self.history[-5:]
        )
        try:
            answer = self.openai_service.answer_with_context(
                question=cleaned_question,
                context="\n\n".join(context_parts),
                history=history_text,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to generate answer: {exc}") from exc

        if not answer:
            answer = "I don't know"

        self._append_history(cleaned_question, answer, sources)
        return answer, sources

    def _append_history(self, question: str, answer: str, sources: List[dict]) -> None:
        self.history.append(
            {
                "question": question,
                "answer": answer,
                "sources": sources,
            }
        )
        self._save_history()

    def get_history(self) -> List[dict]:
        """Return saved chat history."""
        return self.history

    def clear_history(self) -> None:
        """Remove saved chat history."""
        self.history = []
        self._save_history()


assistant_pipeline = KnowledgeAssistantPipeline()
