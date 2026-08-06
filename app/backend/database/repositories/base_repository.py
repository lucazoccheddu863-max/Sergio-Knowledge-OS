"""Base repository with generic CRUD operations.

All repositories work through the abstract Database interface,
making them backend-agnostic.
"""

from typing import Any, List, Tuple, Optional
from ...database.database import Database


class BaseRepository:
    """Base repository class.

    Provides generic database operations. Subclasses define
    table-specific queries and mapping.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def execute(self, sql: str, parameters: Tuple[Any, ...] = ()) -> None:
        self._db.execute(sql, parameters)

    def fetchone(self, sql: str, parameters: Tuple[Any, ...] = ()) -> Optional[Tuple[Any, ...]]:
        return self._db.fetchone(sql, parameters)

    def fetchall(self, sql: str, parameters: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
        return self._db.fetchall(sql, parameters)

    def lastrowid(self) -> int:
        return self._db.lastrowid()
