"""Vector Store Port — abstract interface for vector databases."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from skos.m4.domain.vector_models import VectorQuery, VectorRecord, SearchResult


class VectorStorePort(ABC):
    """Abstract port for vector database operations."""

    @abstractmethod
    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        """Insert or update vector records in a collection."""
        pass

    @abstractmethod
    def search(self, collection_name: str, query: VectorQuery) -> SearchResult:
        """Search for similar vectors in a collection."""
        pass

    @abstractmethod
    def delete(self, collection_name: str, ids: list[str]) -> None:
        """Delete records by ID from a collection."""
        pass

    @abstractmethod
    def get_collection(self, collection_name: str) -> Any:
        """Get or create a collection handle."""
        pass

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all collection names."""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the vector store is reachable."""
        pass


class VectorStoreError(Exception):
    """Base error for vector store operations."""
    pass


class CollectionNotFoundError(VectorStoreError):
    """Raised when a collection does not exist."""
    pass
