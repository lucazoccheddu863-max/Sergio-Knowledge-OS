"""SQLite implementation of the Database interface."""

import sqlite3
from pathlib import Path
from typing import Any, List, Tuple, Optional

from .database import Database


class SQLiteDatabase(Database):
    """SQLite backend for Sergio Knowledge OS.

    Configurable via config.yaml:
        database_path: ./data/sergio_knowledge.db

    PRAGMAs set:
        foreign_keys = ON
        journal_mode = WAL

    Connection uses timeout=30.0 to avoid "database is locked" errors
    when multiple connections open the same file (e.g. in verification scripts).
    """

    def __init__(self, database_path: Path) -> None:
        self._database_path = Path(database_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None

    def connect(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            str(self._database_path),
            timeout=30.0,  # Wait up to 30s for locks (prevents "database is locked")
            check_same_thread=False,  # Allow use across threads if needed
        )
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._cursor = self._connection.cursor()

    def close(self) -> None:
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, parameters: Tuple[Any, ...] = ()) -> None:
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        self._connection.execute(sql, parameters)

    def executemany(self, sql: str, parameters: List[Tuple[Any, ...]]) -> None:
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        self._connection.executemany(sql, parameters)

    def fetchone(self, sql: str, parameters: Tuple[Any, ...] = ()) -> Optional[Tuple[Any, ...]]:
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        cursor = self._connection.execute(sql, parameters)
        return cursor.fetchone()

    def fetchall(self, sql: str, parameters: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        cursor = self._connection.execute(sql, parameters)
        return cursor.fetchall()

    def commit(self) -> None:
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        if self._connection:
            self._connection.rollback()

    def init_schema(self, schema_path: Optional[Path] = None) -> None:
        if schema_path is None:
            schema_path = Path(__file__).parent.parent.parent.parent / "schema_v1.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        sql = schema_path.read_text(encoding="utf-8")
        # executescript implicitly commits; ensure no pending transaction
        self._connection.executescript(sql)
        self.commit()

    def lastrowid(self) -> int:
        if self._connection is None:
            raise RuntimeError("Database not connected.")
        cursor = self._connection.execute("SELECT last_insert_rowid()")
        row = cursor.fetchone()
        return row[0] if row else 0

    def is_connected(self) -> bool:
        return self._connection is not None

    def __enter__(self) -> "SQLiteDatabase":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
