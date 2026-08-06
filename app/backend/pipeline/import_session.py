"""Import session lifecycle management.

Tracks the beginning, progress, and completion of an import operation
in the database. Integrates with the operation_log table for auditability.
"""

from datetime import datetime, timezone
from typing import Optional

from ..database.database import Database
from ..database.repositories.source_repository import SourceRepository
from ..database.repositories.import_repository import ImportRepository
from ..domain.models import Source, Import


class ImportSession:
    """Manages a single import session lifecycle.

    Usage:
        session = ImportSession(db, "chatgpt", "ChatGPT Export")
        session.begin()
        try:
            # ... import files ...
            session.commit(files_seen=10, files_new=5)
        except Exception:
            session.rollback()
    """

    def __init__(self, db: Database, source_type: str, source_name: str,
                 root_path: Optional[str] = None) -> None:
        self._db = db
        self._source_repo = SourceRepository(db)
        self._import_repo = ImportRepository(db)
        self._source_type = source_type
        self._source_name = source_name
        self._root_path = root_path
        self._source_id: Optional[int] = None
        self._import_id: Optional[int] = None

    def begin(self) -> None:
        """Start a new import session. Creates or updates source record."""
        now = datetime.now(timezone.utc).isoformat()

        # Find or create source
        source = self._source_repo.get_by_type_and_name(self._source_type, self._source_name)
        if source is None:
            source = Source(
                source_type=self._source_type,
                name=self._source_name,
                root_path=self._root_path,
                created_at=now,
                last_import_at=now,
                is_original_immutable=True,
            )
            self._source_id = self._source_repo.create(source)
        else:
            self._source_id = source.id
            self._source_repo.update_last_import(self._source_id, now)

        # Create import record
        imp = Import(
            source_id=self._source_id,
            started_at=now,
            status="running",
        )
        self._import_id = self._import_repo.create(imp)

    def commit(self, files_seen: int = 0, files_new: int = 0,
               files_duplicate: int = 0, errors_count: int = 0) -> None:
        """Commit the import session with statistics."""
        if self._import_id is None:
            raise RuntimeError("Import session not started. Call begin() first.")

        now = datetime.now(timezone.utc).isoformat()
        self._import_repo.update_status(self._import_id, "completed", now)

        # Update statistics
        self._db.execute(
            """UPDATE imports SET
                files_seen = ?, files_new = ?, files_duplicate = ?, errors_count = ?
            WHERE id = ?""",
            (files_seen, files_new, files_duplicate, errors_count, self._import_id)
        )
        self._db.commit()

    def rollback(self) -> None:
        """Mark the import session as failed."""
        if self._import_id is not None:
            now = datetime.now(timezone.utc).isoformat()
            self._import_repo.update_status(self._import_id, "failed", now)

    @property
    def source_id(self) -> Optional[int]:
        return self._source_id

    @property
    def import_id(self) -> Optional[int]:
        return self._import_id
