"""Abstract database interface.

This module defines the contract that any database backend must implement.
Future backends: PostgreSQL, DuckDB, Qdrant, Milvus, ChromaDB.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional
from pathlib import Path


class Database(ABC):
    """Abstract database interface.

    All database implementations (SQLite, PostgreSQL, DuckDB, etc.)
    must conform to this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def execute(self, sql: str, parameters: Tuple[Any, ...] = ()) -> None:
        """Execute a single SQL statement."""
        pass

    @abstractmethod
    def executemany(self, sql: str, parameters: List[Tuple[Any, ...]]) -> None:
        """Execute a SQL statement multiple times."""
        pass

    @abstractmethod
    def fetchone(self, sql: str, parameters: Tuple[Any, ...] = ()) -> Optional[Tuple[Any, ...]]:
        """Execute query and return first row."""
        pass

    @abstractmethod
    def fetchall(self, sql: str, parameters: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
        """Execute query and return all rows."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback current transaction."""
        pass

    @abstractmethod
    def init_schema(self, schema_path: Optional[Path] = None) -> None:
        """Initialize database schema from SQL file."""
        pass

    @abstractmethod
    def lastrowid(self) -> int:
        """Return the row id of the last inserted row."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass
