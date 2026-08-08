"""Application service for Knowledge Graph operations.

Provides high-level operations for entity extraction, relation building, and graph querying.
Talks to KnowledgeGraphPort, never to concrete adapters.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.knowledge_graph_models import (
    Entity,
    GraphQuery,
    GraphResult,
    Relation,
)
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
from skos.m4.infrastructure.ports.knowledge_graph_port import KnowledgeGraphPort


class KnowledgeGraphService:
    """High-level knowledge graph orchestrator.

    Dependencies:
        - KnowledgeGraphPort: abstract graph storage
        - ConfigurationPort: reads KG config
        - EventBusPort: publishes KG events
    """

    def __init__(
        self,
        graph_store: KnowledgeGraphPort,
        config: ConfigurationPort,
        event_bus: EventBusPort,
    ) -> None:
        self._store = graph_store
        self._config = config
        self._bus = event_bus

    def add_document_entities(
        self,
        doc_id: str,
        entities: list[Entity],
        relations: list[Relation],
    ) -> None:
        """Index extracted entities and relations from a document."""
        for entity in entities:
            self._store.add_entity(entity)
        for relation in relations:
            self._store.add_relation(relation)

        self._bus.publish(
            "kg.events",
            {
                "event": "kg.document_indexed",
                "doc_id": doc_id,
                "entity_count": len(entities),
                "relation_count": len(relations),
            },
        )

    def query(self, query: GraphQuery) -> GraphResult:
        """Query the knowledge graph."""
        start = time.perf_counter()
        result = self._store.query(query)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self._bus.publish(
            "kg.events",
            {
                "event": "kg.queried",
                "entity_name": query.entity_name,
                "entity_type": query.entity_type,
                "result_count": len(result.entities),
                "query_time_ms": elapsed_ms,
            },
        )
        return result

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._store.get_entity(entity_id)

    def delete_entity(self, entity_id: str) -> None:
        self._store.delete_entity(entity_id)
        self._bus.publish(
            "kg.events",
            {
                "event": "kg.entity_deleted",
                "entity_id": entity_id,
            },
        )

    def health_check(self) -> bool:
        return self._store.health_check()
