"""Runtime wiring for SKOS M5."""

from skos.m5.runtime.persistence_factory import (
    PersistenceRuntime,
    RuntimeHealth,
    build_persistence_runtime,
)

__all__ = [
    "PersistenceRuntime",
    "RuntimeHealth",
    "build_persistence_runtime",
]
