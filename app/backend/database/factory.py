"""Database factory for creating database instances.

Supports future backends:
    - sqlite  → SQLiteDatabase
    - postgres → PostgreSQLDatabase (future)
    - duckdb  → DuckDBDatabase (future)
    - qdrant  → QdrantDatabase (future)
"""

from pathlib import Path
from typing import Any, Optional, Dict, Type

from .database import Database
from .sqlite_database import SQLiteDatabase


class DatabaseFactory:
    """Factory for creating database instances by type name."""

    _registry: Dict[str, Type[Database]] = {
        "sqlite": SQLiteDatabase,
        # Future registrations:
        # "postgres": PostgreSQLDatabase,
        # "duckdb": DuckDBDatabase,
    }

    @classmethod
    def create(cls, backend: str, config: Any) -> Database:
        """Create a database instance.

        Args:
            backend: Database backend name (e.g., "sqlite")
            config: Config instance with database_path attribute

        Returns:
            Database instance

        Raises:
            ValueError: If backend is not supported
        """
        backend = backend.lower()
        if backend not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(f"Unsupported database backend: {backend}. Supported: {supported}")

        db_class = cls._registry[backend]
        if backend == "sqlite":
            return db_class(config.database_path)
        # Future: elif backend == "postgres": ...
        return db_class(config.database_path)

    @classmethod
    def register(cls, name: str, db_class: Type[Database]) -> None:
        """Register a new database backend."""
        cls._registry[name.lower()] = db_class

    @classmethod
    def supported_backends(cls) -> list:
        """Return list of supported backend names."""
        return list(cls._registry.keys())
