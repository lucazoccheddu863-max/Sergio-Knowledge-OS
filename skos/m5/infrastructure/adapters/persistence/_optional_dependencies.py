"""Optional dependency shims for M5.1 persistence adapters."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class _MissingDependency:
    def __init__(self, package_name: str) -> None:
        self._package_name = package_name

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            f"Missing optional dependency '{self._package_name}'. "
            f"Install it to use this persistence adapter."
        )


def _raise_missing(package_name: str) -> Any:
    raise RuntimeError(
        f"Missing optional dependency '{package_name}'. "
        f"Install it to use this persistence adapter."
    )


def load_redis() -> Any:
    try:
        import redis

        return redis
    except ImportError:
        return SimpleNamespace(
            from_url=lambda *args, **kwargs: _raise_missing("redis"),
            ResponseError=RuntimeError,
            Redis=Any,
            client=SimpleNamespace(PubSub=Any),
        )


def load_psycopg2() -> Any:
    try:
        import psycopg2
        import psycopg2.extras

        return psycopg2
    except ImportError:
        return SimpleNamespace(
            connect=lambda *args, **kwargs: _raise_missing("psycopg2-binary"),
            extras=SimpleNamespace(Json=lambda value: value, RealDictCursor=Any),
            extensions=SimpleNamespace(connection=Any),
        )
