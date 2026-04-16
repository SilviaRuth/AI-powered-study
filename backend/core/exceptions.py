"""Application exceptions."""

from __future__ import annotations


class AppError(Exception):
    """Base application exception."""


class IngestionError(AppError):
    """Raised when document ingestion fails."""


class RetrievalError(AppError):
    """Raised when retrieval fails."""


class GenerationError(AppError):
    """Raised when answer generation fails."""


class DocumentNotFoundError(AppError):
    """Raised when a document does not exist."""
