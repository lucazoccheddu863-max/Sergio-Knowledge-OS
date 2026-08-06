"""Repository for conversations table."""

import json
from typing import Optional, List, Tuple, Any
from ...domain.models import Conversation
from .base_repository import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for managing conversations with multi-AI support."""

    def create(self, conv: Conversation) -> int:
        sql = """
            INSERT INTO conversations (source_id, external_id, title, created_at, updated_at, model, url, raw_json_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            conv.source_id,
            conv.external_id,
            conv.title,
            conv.created_at,
            conv.updated_at,
            conv.model,
            conv.url,
            conv.raw_json_path,
        ))
        self._db.commit()
        return self.lastrowid()

    def get_by_id(self, conv_id: int) -> Optional[Conversation]:
        row = self.fetchone("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        return self._row_to_conversation(row) if row else None

    def get_by_external_id(self, external_id: str, source_id: int) -> Optional[Conversation]:
        row = self.fetchone(
            "SELECT * FROM conversations WHERE external_id = ? AND source_id = ?",
            (external_id, source_id)
        )
        return self._row_to_conversation(row) if row else None

    def list_by_source(self, source_id: int) -> List[Conversation]:
        rows = self.fetchall(
            "SELECT * FROM conversations WHERE source_id = ? ORDER BY created_at DESC",
            (source_id,)
        )
        return [self._row_to_conversation(r) for r in rows]

    def list_by_provider(self, provider: str) -> List[Conversation]:
        """Filter by provider (stored in metadata or inferred from source)."""
        rows = self.fetchall(
            "SELECT * FROM conversations WHERE model LIKE ? ORDER BY created_at DESC",
            (f"%{provider}%",)
        )
        return [self._row_to_conversation(r) for r in rows]

    def update(self, conv: Conversation) -> None:
        self.execute(
            """UPDATE conversations SET
                title = ?, created_at = ?, updated_at = ?, model = ?,
                url = ?, raw_json_path = ?
            WHERE id = ?""",
            (conv.title, conv.created_at, conv.updated_at, conv.model,
             conv.url, conv.raw_json_path, conv.id)
        )
        self._db.commit()

    def delete_by_source(self, source_id: int) -> None:
        self.execute("DELETE FROM conversations WHERE source_id = ?", (source_id,))
        self._db.commit()

    def _row_to_conversation(self, row: Tuple[Any, ...]) -> Conversation:
        return Conversation(
            id=row[0],
            source_id=row[1],
            external_id=row[2],
            title=row[3],
            created_at=row[4],
            updated_at=row[5],
            model=row[6],
            url=row[7],
            raw_json_path=row[8],
        )
