"""FTS5-based implementation of the Knowledge Engine.

This is the v1 implementation using SQLite FTS5.
Future implementations may use:
    - Qdrant/Milvus for vector search
    - ChromaDB for embeddings
    - Hybrid FTS5 + vector search
"""

import warnings
from typing import List

from .engine import KnowledgeEngine
from ..domain.models import SearchResult, SemanticQuery
from ..database.repositories.search_index_repository import SearchIndexRepository


class FTS5Engine(KnowledgeEngine):
    """Knowledge Engine implementation using SQLite FTS5.

    If FTS5 is not available in the SQLite build, falls back
    to basic LIKE-based search with a warning.
    """

    def __init__(self, search_repo: SearchIndexRepository) -> None:
        self._repo = search_repo
        self._check_fts5()

    def _check_fts5(self) -> None:
        """Check if FTS5 is available and warn if not."""
        try:
            self._repo._db.execute("SELECT 1 FROM search_index LIMIT 0")
        except Exception:
            warnings.warn(
                "FTS5 is not available in this SQLite build. "
                "Search will use fallback LIKE queries. "
                "For better performance, use a SQLite build with FTS5 enabled.",
                RuntimeWarning
            )

    def index(self, entity_type: str, entity_id: int, title: str, body: str,
              project_names: str = "", tags: str = "", source_name: str = "", path: str = "") -> None:
        self._repo.index_conversation(entity_type, entity_id, title, body,
                                      project_names, tags, source_name, path)

    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        return self._repo.search(query, limit)

    def semantic_search(self, query: SemanticQuery) -> List[SearchResult]:
        """Placeholder for semantic search.

        In the future, this will:
        1. Generate embeddings for the query text
        2. Query a vector database
        3. Return results ordered by cosine similarity

        For now, falls back to full-text search.
        """
        warnings.warn(
            "Semantic search is not yet implemented. Falling back to full-text search.",
            UserWarning
        )
        return self.search(query.query_text, query.top_k)

    def delete(self, entity_type: str, entity_id: int) -> None:
        self._repo.delete_by_entity(entity_type, entity_id)

    def clear(self) -> None:
        self._repo.clear_all()
