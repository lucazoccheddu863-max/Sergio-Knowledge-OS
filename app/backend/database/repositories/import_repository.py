"""Repository for imports table."""

from typing import Optional, List, Tuple, Any
from ...domain.models import Import
from .base_repository import BaseRepository


class ImportRepository(BaseRepository):
    """Repository for tracking import sessions."""

    def create(self, imp: Import) -> int:
        sql = """
            INSERT INTO imports (source_id, started_at, finished_at, status, files_seen, files_new, files_duplicate, errors_count, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            imp.source_id,
            imp.started_at,
            imp.finished_at,
            imp.status,
            imp.files_seen,
            imp.files_new,
            imp.files_duplicate,
            imp.errors_count,
            imp.report_path,
        ))
        self._db.commit()
        return self.lastrowid()

    def update_status(self, import_id: int, status: str, finished_at: Optional[str] = None) -> None:
        if finished_at:
            self.execute(
                "UPDATE imports SET status = ?, finished_at = ? WHERE id = ?",
                (status, finished_at, import_id)
            )
        else:
            self.execute(
                "UPDATE imports SET status = ? WHERE id = ?",
                (status, import_id)
            )
        self._db.commit()

    def get_by_id(self, import_id: int) -> Optional[Import]:
        row = self.fetchone("SELECT * FROM imports WHERE id = ?", (import_id,))
        return self._row_to_import(row) if row else None

    def list_by_source(self, source_id: int) -> List[Import]:
        rows = self.fetchall(
            "SELECT * FROM imports WHERE source_id = ? ORDER BY started_at DESC",
            (source_id,)
        )
        return [self._row_to_import(r) for r in rows]

    def _row_to_import(self, row: Tuple[Any, ...]) -> Import:
        return Import(
            id=row[0],
            source_id=row[1],
            started_at=row[2],
            finished_at=row[3],
            status=row[4],
            files_seen=row[5],
            files_new=row[6],
            files_duplicate=row[7],
            errors_count=row[8],
            report_path=row[9],
        )
