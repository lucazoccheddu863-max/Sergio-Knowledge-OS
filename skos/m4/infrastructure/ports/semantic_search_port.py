"""Semantic Search Port — abstract interface for semantic search engines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from skos.m4.domain.search_models import SemanticQuery, SemanticSearchResult


class SemanticSearchPort(ABC):
    """Abstract port for semantic search operations.

    Hides the underlying vector store implementation (ChromaDB, Qdrant, etc.)
    from the application layer.
    """

    @abstractmethod
    def search(self, query: SemanticQuery) -> SemanticSearchResult:
        """Execute a semantic search query."""
        pass

    @abstractmethod
    def index_document(self, doc_id: str, text: str, metadata: dict[str, Any], source_id: str = "") -> None:
        """Index a single document for semantic search."""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """Delete a document from the semantic search index."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the semantic search engine is operational."""
        pass


class SemanticSearchError(Exception):
    """Base error for semantic search operations."""
    pass
