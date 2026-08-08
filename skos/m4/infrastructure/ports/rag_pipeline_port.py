"""RAG Pipeline Port — abstract interface for RAG implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.domain.rag_models import RAGQuery, RAGResult


class RAGPipelinePort(ABC):
    """Abstract port for Retrieval Augmented Generation pipelines."""

    @abstractmethod
    def answer(self, query: RAGQuery) -> RAGResult:
        """Execute the full RAG pipeline: retrieve → augment → generate."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the RAG pipeline is operational."""
        pass


class RAGError(Exception):
    """Base error for RAG operations."""
    pass
