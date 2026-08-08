"""Domain models for semantic search operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SemanticQuery:
    """A user query for semantic search."""
    text: str
    top_k: int = 5
    filter_metadata: dict[str, Any] | None = None
    min_similarity: float | None = None


@dataclass(frozen=True)
class RankedDocument:
    """A document result from semantic search with ranking info."""
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_id: str = ""
    similarity_score: float = 0.0
    rank: int = 0


@dataclass(frozen=True)
class SemanticSearchResult:
    """Complete result of a semantic search operation."""
    query: SemanticQuery
    results: list[RankedDocument]
    total_found: int
    query_time_ms: float = 0.0
    embedding_model: str = ""


@dataclass(frozen=True)
class SearchFilter:
    """Optional filters for semantic search results."""
    source_ids: list[str] | None = None
    date_range: tuple[str, str] | None = None
    tags: list[str] | None = None
