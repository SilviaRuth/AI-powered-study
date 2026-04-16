"""End-to-end RAG pipeline orchestration."""

from __future__ import annotations

import logging
import shutil
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import UploadFile

from backend.core.config import Settings, get_settings
from backend.core.exceptions import DocumentNotFoundError, IngestionError, RetrievalError
from backend.rag.chunking import chunk_document
from backend.rag.embeddings import OpenAIService
from backend.rag.generation.answer_generator import AnswerGenerator
from backend.rag.generation.citation_builder import CitationBuilder
from backend.rag.generation.context_compressor import ContextCompressor
from backend.rag.generation.prompt_builder import PromptBuilder
from backend.rag.ingest import load_processed_chunks, save_processed_document
from backend.rag.metadata import RetrievedChunk
from backend.rag.parser import parse_document
from backend.rag.query_rewrite import QueryRewriter
from backend.rag.retrieval.bm25_retriever import BM25Retriever
from backend.rag.retrieval.dedupe import dedupe_candidates
from backend.rag.retrieval.dense_retriever import DenseRetriever
from backend.rag.retrieval.hybrid_retriever import HybridRetriever
from backend.rag.retrieval.reranker import Reranker
from backend.rag.storage.bm25_store import BM25Store
from backend.rag.storage.doc_registry import DocumentRegistry
from backend.rag.storage.faiss_store import FaissStore


LOGGER = logging.getLogger(__name__)


class AssistantPipeline:
    """Coordinates ingestion, retrieval, and answer generation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_directories()
        self.openai_service = OpenAIService()
        self.registry = DocumentRegistry(self.settings.registry_path)
        self.dense_retriever = DenseRetriever(FaissStore(self.settings.dense_store_dir), self.openai_service)
        self.sparse_retriever = BM25Retriever(BM25Store(self.settings.sparse_store_dir))
        self.hybrid_retriever = HybridRetriever(self.dense_retriever, self.sparse_retriever)
        self.reranker = Reranker(self.openai_service)
        self.query_rewriter = QueryRewriter(self.openai_service)
        self.context_compressor = ContextCompressor()
        self.citation_builder = CitationBuilder()
        self.answer_generator = AnswerGenerator(self.openai_service, PromptBuilder())

    async def ingest_upload(self, upload: UploadFile) -> dict:
        """Save, parse, chunk, index, and register an uploaded document."""
        original_filename = Path(upload.filename or "document").name
        suffix = Path(original_filename).suffix.lower()
        if suffix not in self.settings.supported_extensions:
            raise ValueError("Only PDF and TXT files are supported.")

        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
        destination = self.settings.upload_dir / stored_filename

        try:
            with destination.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)

            parsed_document = parse_document(
                destination,
                filename=original_filename,
                stored_filename=stored_filename,
                document_id=document_id,
            )
            if not any(page.text.strip() for page in parsed_document.pages):
                raise ValueError("The uploaded document is empty or contains no extractable text.")

            chunks = chunk_document(parsed_document)
            if not chunks:
                raise ValueError("Unable to create chunks from the uploaded document.")

            save_processed_document(
                self.settings.processed_dir,
                document_id=document_id,
                parsed_document=parsed_document.to_dict(),
                chunks=chunks,
            )
            self.dense_retriever.index_chunks(chunks)
            self.sparse_retriever.index_chunks(chunks)
            self.registry.upsert(
                {
                    "document_id": document_id,
                    "original_filename": original_filename,
                    "stored_filename": stored_filename,
                    "upload_timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_type": parsed_document.source_type,
                    "chunk_count": len(chunks),
                    "status": "indexed",
                    "tags": [],
                }
            )
        except Exception as exc:
            self._cleanup_failed_document(document_id, destination)
            if isinstance(exc, (IngestionError, ValueError)):
                raise
            raise IngestionError(f"Failed to process document: {exc}") from exc

        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": original_filename,
            "document_id": document_id,
            "chunks_indexed": len(chunks),
        }

    def answer_question(self, question: str, history: list[dict]) -> tuple[str, list[dict], str]:
        """Retrieve context, generate a grounded answer, and return cited sources."""
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")
        if not self.registry.list_documents():
            raise ValueError("Upload at least one document before asking questions.")

        try:
            rewritten_query, evidence = self.retrieve_candidates(cleaned_question, history)
            answer, cited_ids = self.answer_generator.generate(cleaned_question, history, evidence)
            final_answer = self.citation_builder.build_answer(answer, cited_ids, evidence)
            sources = self.citation_builder.build_sources(cited_ids, evidence)
            return final_answer, sources, rewritten_query
        except ValueError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Failed to answer question: {exc}") from exc

    def retrieve_candidates(self, question: str, history: list[dict]) -> tuple[str, list[RetrievedChunk]]:
        """Run retrieval, dedupe, reranking, compression, and citation labeling."""
        rewritten_query = self.query_rewriter.rewrite(question, history)
        candidates = self.hybrid_retriever.search(rewritten_query)
        filtered = [
            candidate
            for candidate in candidates
            if candidate.retrieval_score >= self.settings.min_relevance_score
        ]
        deduped = dedupe_candidates(filtered)
        reranked = self.reranker.rerank(question, deduped)
        compressed = self.context_compressor.compress(question, reranked[: self.settings.top_k])
        labeled = self.citation_builder.assign_labels(compressed)
        return rewritten_query, labeled

    def list_documents(self) -> list[dict]:
        """List indexed documents."""
        return self.registry.list_documents()

    def delete_document(self, document_id: str) -> None:
        """Delete a document's registry entry and index data."""
        record = self.registry.get(document_id)
        if record is None:
            raise DocumentNotFoundError(f"Document {document_id} was not found.")

        self.dense_retriever.delete_document(document_id)
        self.sparse_retriever.delete_document(document_id)
        self.registry.delete(document_id)

        upload_path = self.settings.upload_dir / record["stored_filename"]
        processed_path = self.settings.processed_dir / f"{document_id}.json"
        upload_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)

    def rebuild_indexes(self) -> int:
        """Rebuild dense and sparse indexes from processed artifacts."""
        self.dense_retriever.clear()
        self.sparse_retriever.clear()
        count = 0
        for processed_path in sorted(self.settings.processed_dir.glob("doc_*.json")):
            chunks = load_processed_chunks(processed_path)
            if not chunks:
                continue
            self.dense_retriever.index_chunks(chunks)
            self.sparse_retriever.index_chunks(chunks)
            count += 1
        LOGGER.info("Rebuilt indexes for %s processed documents", count)
        return count

    def _cleanup_failed_document(self, document_id: str, upload_path: Path) -> None:
        upload_path.unlink(missing_ok=True)
        processed_path = self.settings.processed_dir / f"{document_id}.json"
        processed_path.unlink(missing_ok=True)
        self.dense_retriever.delete_document(document_id)
        self.sparse_retriever.delete_document(document_id)
        self.registry.delete(document_id)


@lru_cache(maxsize=1)
def get_assistant_pipeline() -> AssistantPipeline:
    """Return a shared pipeline instance."""
    return AssistantPipeline()


assistant_pipeline = get_assistant_pipeline()
