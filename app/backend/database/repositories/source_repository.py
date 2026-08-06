"""Repository for sources table."""

from typing import Optional, List, Tuple, Any
from ...domain.models import Source
from .base_repository import BaseRepository


class SourceRepository(BaseRepository):
    """Repository for managing AI data sources (ChatGPT, Gemini, etc.)."""

    def create(self, source: Source) -> int:
        sql = """
            INSERT INTO sources (source_type, name, root_path, created_at, last_import_at, is_original_immutable, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            source.source_type,
            source.name,
            source.root_path,
            source.created_at,
            source.last_import_at,
            int(source.is_original_immutable),
            source.notes,
        ))
        self._db.commit()
        return self.lastrowid()

    def get_by_id(self, source_id: int) -> Optional[Source]:
        row = self.fetchone("SELECT * FROM sources WHERE id = ?", (source_id,))
        return self._row_to_source(row) if row else None

    def get_by_type_and_name(self, source_type: str, name: str) -> Optional[Source]:
        row = self.fetchone(
            "SELECT * FROM sources WHERE source_type = ? AND name = ?",
            (source_type, name)
        )
        return self._row_to_source(row) if row else None

    def update_last_import(self, source_id: int, import_at: str) -> None:
        self.execute(
            "UPDATE sources SET last_import_at = ? WHERE id = ?",
            (import_at, source_id)
        )
        self._db.commit()

    def list_all(self) -> List[Source]:
        rows = self.fetchall("SELECT * FROM sources ORDER BY created_at DESC")
        return [self._row_to_source(r) for r in rows]

    def _row_to_source(self, row: Tuple[Any, ...]) -> Source:
        return Source(
            id=row[0],
            source_type=row[1],
            name=row[2],
            root_path=row[3],
            created_at=row[4],
            last_import_at=row[5],
            is_original_immutable=bool(row[6]),
            notes=row[7],
        )
