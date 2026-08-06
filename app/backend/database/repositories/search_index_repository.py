"""Repository for FTS5 search_index virtual table."""

from typing import List, Tuple, Any
from ...domain.models import SearchResult
from .base_repository import BaseRepository


class SearchIndexRepository(BaseRepository):
    """Repository for full-text search via FTS5.

    Note: FTS5 is a virtual table in SQLite. If FTS5 is not available,
    falls back to basic LIKE queries.
    """

    def __init__(self, db: Any) -> None:
        super().__init__(db)
        self._fts5_available = self._check_fts5()

    def _check_fts5(self) -> bool:
        try:
            self._db.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='search_index'")
            return True
        except Exception:
            return False

    def index_conversation(self, entity_type: str, entity_id: int, title: str, body: str,
                           project_names: str = "", tags: str = "", source_name: str = "", path: str = "") -> None:
        """Index a conversation or message for full-text search."""
        if not self._fts5_available:
            return  # FTS5 not available, skip indexing
        sql = """
            INSERT INTO search_index (entity_type, entity_id, title, body, project_names, tags, source_name, path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (entity_type, entity_id, title, body, project_names, tags, source_name, path))

    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Full-text search using FTS5 MATCH operator."""
        if not self._fts5_available:
            return self._fallback_search(query, limit)

        sql = """
            SELECT entity_type, entity_id, title, body, rank
            FROM search_index
            WHERE search_index MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        rows = self.fetchall(sql, (query, limit))
        return [self._row_to_result(r) for r in rows]

    def delete_by_entity(self, entity_type: str, entity_id: int) -> None:
        if not self._fts5_available:
            return
        self.execute(
            "DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id)
        )

    def clear_all(self) -> None:
        if not self._fts5_available:
            return
        self.execute("DELETE FROM search_index")

    def _fallback_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback LIKE-based search when FTS5 is unavailable."""
        pattern = f"%{query}%"
        sql = """
            SELECT 'conversation', id, title, '', 0.0
            FROM conversations
            WHERE title LIKE ?
            UNION ALL
            SELECT 'message', id, '', content_text, 0.0
            FROM messages
            WHERE content_text LIKE ?
            LIMIT ?
        """
        rows = self.fetchall(sql, (pattern, pattern, limit))
        return [self._row_to_result(r) for r in rows]

    def _row_to_result(self, row: Tuple[Any, ...]) -> SearchResult:
        return SearchResult(
            entity_type=row[0],
            entity_id=row[1],
            title=row[2] if row[2] else None,
            body=row[3] if row[3] else None,
            rank=float(row[4]) if row[4] is not None else None,
        )
