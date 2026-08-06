"""Transaction context manager for any Database implementation."""

from contextlib import contextmanager
from typing import Generator

from .database import Database


@contextmanager
def transaction(db: Database) -> Generator[Database, None, None]:
    """Context manager for database transactions.

    Usage:
        with transaction(db) as tx:
            tx.execute("INSERT INTO ...")
            # auto-commit on success, rollback on exception
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
