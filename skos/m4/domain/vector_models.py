"""Domain models for vector store operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VectorRecord:
    """A single vector record with metadata."""
    id: str
    vector: list[float]
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_id: str = ""


@dataclass(frozen=True)
class VectorQuery:
    """Query parameters for vector similarity search."""
    vector: list[float]
    top_k: int = 5
    filter_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class SearchResult:
    """Result of a vector similarity search."""
    records: list[VectorRecord]
    total_found: int
    query_time_ms: float = 0.0
