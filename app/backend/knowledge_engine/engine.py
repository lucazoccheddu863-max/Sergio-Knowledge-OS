"""Abstract Knowledge Engine interface.

The Knowledge Engine is the central search and retrieval subsystem
of Sergio Knowledge OS. Today it implements FTS5 full-text search.
Tomorrow it will support:
    - Semantic search via embeddings
    - Vector search (Qdrant, Milvus, ChromaDB)
    - RAG (Retrieval-Augmented Generation)
    - AI-powered query understanding
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.models import SearchResult, SemanticQuery


class KnowledgeEngine(ABC):
    """Abstract interface for the Knowledge Engine.

    All search implementations must conform to this interface.
    This allows seamless swapping between FTS5, vector DB, or hybrid search.
    """

    @abstractmethod
    def index(self, entity_type: str, entity_id: int, title: str, body: str,
              project_names: str = "", tags: str = "", source_name: str = "", path: str = "") -> None:
        """Index content for search.

        Args:
            entity_type: Type of entity ("conversation", "message", "file")
            entity_id: Database ID of the entity
            title: Title or heading
            body: Full text content
            project_names: Comma-separated project names
            tags: Comma-separated tags
            source_name: Source name (e.g., "ChatGPT", "Gemini")
            path: File path or URL
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Full-text search.

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            List of SearchResult ordered by relevance
        """
        pass

    @abstractmethod
    def semantic_search(self, query: SemanticQuery) -> List[SearchResult]:
        """Semantic search via embeddings.

        Placeholder for future implementation.
        Will use vector embeddings to find semantically similar content.

        Args:
            query: SemanticQuery with text and optional embedding vector

        Returns:
            List of SearchResult ordered by semantic similarity
        """
        pass

    @abstractmethod
    def delete(self, entity_type: str, entity_id: int) -> None:
        """Remove an entity from the search index."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed content."""
        pass
