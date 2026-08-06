"""Repository for messages table."""

import json
from typing import Optional, List, Tuple, Any
from ...domain.models import Message
from .base_repository import BaseRepository


class MessageRepository(BaseRepository):
    """Repository for managing messages with multi-AI support."""

    def create(self, msg: Message) -> int:
        sql = """
            INSERT INTO messages (conversation_id, parent_message_id, role, author, content_text, created_at, model, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            msg.conversation_id,
            msg.parent_message_id,
            msg.role,
            msg.author,
            msg.content_text,
            msg.created_at,
            msg.model,
            msg.metadata_json,
        ))
        self._db.commit()
        return self.lastrowid()

    def create_many(self, messages: List[Message]) -> None:
        """Batch insert for performance."""
        sql = """
            INSERT INTO messages (conversation_id, parent_message_id, role, author, content_text, created_at, model, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (m.conversation_id, m.parent_message_id, m.role, m.author,
             m.content_text, m.created_at, m.model, m.metadata_json)
            for m in messages
        ]
        self._db.executemany(sql, params)
        self._db.commit()

    def get_by_id(self, msg_id: int) -> Optional[Message]:
        row = self.fetchone("SELECT * FROM messages WHERE id = ?", (msg_id,))
        return self._row_to_message(row) if row else None

    def list_by_conversation(self, conversation_id: int) -> List[Message]:
        rows = self.fetchall(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC, id ASC",
            (conversation_id,)
        )
        return [self._row_to_message(r) for r in rows]

    def list_by_role(self, conversation_id: int, role: str) -> List[Message]:
        rows = self.fetchall(
            "SELECT * FROM messages WHERE conversation_id = ? AND role = ? ORDER BY created_at ASC",
            (conversation_id, role)
        )
        return [self._row_to_message(r) for r in rows]

    def delete_by_conversation(self, conversation_id: int) -> None:
        self.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        self._db.commit()

    def _row_to_message(self, row: Tuple[Any, ...]) -> Message:
        return Message(
            id=row[0],
            conversation_id=row[1],
            parent_message_id=row[2],
            role=row[3],
            author=row[4],
            content_text=row[5],
            created_at=row[6],
            model=row[7],
            metadata_json=row[8],
        )
