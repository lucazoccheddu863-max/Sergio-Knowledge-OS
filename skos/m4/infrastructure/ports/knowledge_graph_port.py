"""Knowledge Graph Port — abstract interface for graph databases."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from skos.m4.domain.knowledge_graph_models import Entity, GraphQuery, GraphResult, Relation


class KnowledgeGraphPort(ABC):
    """Abstract port for knowledge graph operations."""

    @abstractmethod
    def add_entity(self, entity: Entity) -> None:
        """Add or update an entity in the graph."""
        pass

    @abstractmethod
    def add_relation(self, relation: Relation) -> None:
        """Add a relation between entities."""
        pass

    @abstractmethod
    def query(self, query: GraphQuery) -> GraphResult:
        """Query the knowledge graph."""
        pass

    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        pass

    @abstractmethod
    def delete_entity(self, entity_id: str) -> None:
        """Delete an entity and its relations."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the graph store is operational."""
        pass


class KnowledgeGraphError(Exception):
    """Base error for knowledge graph operations."""
    pass
