"""In-memory implementation of KnowledgeGraphPort.

Simple graph store using Python dicts. Suitable for prototyping and testing.
Production deployments can swap this for Neo4jAdapter, NetworkXAdapter, etc.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.knowledge_graph_models import Entity, GraphQuery, GraphResult, Relation
from skos.m4.infrastructure.ports.knowledge_graph_port import (
    KnowledgeGraphError,
    KnowledgeGraphPort,
)


class InMemoryKnowledgeGraphAdapter(KnowledgeGraphPort):
    """In-memory knowledge graph store.

    Stores entities and relations in Python dictionaries.
    Not persistent — data is lost when the process exits.
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relations: list[Relation] = []

    def add_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity

    def add_relation(self, relation: Relation) -> None:
        if relation.source_id not in self._entities:
            raise KnowledgeGraphError(f"Source entity {relation.source_id} not found")
        if relation.target_id not in self._entities:
            raise KnowledgeGraphError(f"Target entity {relation.target_id} not found")
        self._relations.append(relation)

    def query(self, query: GraphQuery) -> GraphResult:
        start = time.perf_counter()
        matched_entities: list[Entity] = []
        matched_relations: list[Relation] = []

        # Filter entities
        for entity in self._entities.values():
            if query.entity_name and query.entity_name.lower() not in entity.name.lower():
                continue
            if query.entity_type and entity.entity_type != query.entity_type:
                continue
            matched_entities.append(entity)
            if len(matched_entities) >= query.max_results:
                break

        # Filter relations
        if query.relation_type:
            matched_relations = [r for r in self._relations if r.relation_type == query.relation_type]
        else:
            matched_relations = list(self._relations)

        elapsed_ms = (time.perf_counter() - start) * 1000
        return GraphResult(
            entities=matched_entities,
            relations=matched_relations,
            query_time_ms=elapsed_ms,
        )

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def delete_entity(self, entity_id: str) -> None:
        if entity_id in self._entities:
            del self._entities[entity_id]
        self._relations = [r for r in self._relations if r.source_id != entity_id and r.target_id != entity_id]

    def health_check(self) -> bool:
        return True
