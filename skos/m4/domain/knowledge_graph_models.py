"""Domain models for Knowledge Graph operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Entity:
    """A named entity extracted from text."""
    id: str
    name: str
    entity_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Relation:
    """A relationship between two entities."""
    source_id: str
    target_id: str
    relation_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphQuery:
    """Query parameters for knowledge graph traversal."""
    entity_name: str | None = None
    entity_type: str | None = None
    relation_type: str | None = None
    depth: int = 1
    max_results: int = 20


@dataclass(frozen=True)
class GraphResult:
    """Result of a knowledge graph query."""
    entities: list[Entity]
    relations: list[Relation]
    query_time_ms: float = 0.0
