"""Application service for Query Orchestrator.

Unifies Semantic Search, RAG, and Knowledge Graph into a single facade.
Routes queries based on mode: auto, semantic, rag, graph, hybrid.
Talks to application services, never to concrete adapters.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
from skos.m4.domain.rag_models import RAGQuery
from skos.m4.domain.search_models import SemanticQuery
from skos.m4.domain.knowledge_graph_models import GraphQuery
from skos.m4.application.services.semantic_search_service import SemanticSearchService
from skos.m4.application.services.rag_pipeline_service import RAGPipelineService
from skos.m4.application.services.knowledge_graph_service import KnowledgeGraphService
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
from skos.m4.infrastructure.ports.query_orchestrator_port import (
    QueryOrchestratorPort,
    QueryOrchestratorError,
)


class QueryOrchestratorService(QueryOrchestratorPort):
    """High-level query orchestrator.

    Dependencies:
        - SemanticSearchService: semantic search engine
        - RAGPipelineService: RAG pipeline
        - KnowledgeGraphService: knowledge graph
        - ConfigurationPort: reads orchestrator config
        - EventBusPort: publishes orchestrator events
    """

    def __init__(
        self,
        semantic_search: SemanticSearchService,
        rag_pipeline: RAGPipelineService,
        knowledge_graph: KnowledgeGraphService,
        config: ConfigurationPort,
        event_bus: EventBusPort,
    ) -> None:
        self._semantic = semantic_search
        self._rag = rag_pipeline
        self._kg = knowledge_graph
        self._config = config
        self._bus = event_bus

    def execute(self, query: UnifiedQuery) -> UnifiedResult:
        """Execute unified query based on mode."""
        start = time.perf_counter()
        engines_used: list[str] = []

        semantic_result = None
        rag_result = None
        graph_result = None

        try:
            if query.mode in ("semantic", "auto", "hybrid"):
                semantic_query = SemanticQuery(
                    text=query.text,
                    top_k=query.top_k,
                    filter_metadata=query.filter_metadata,
                    min_similarity=query.min_similarity,
                )
                semantic_result = self._semantic.search(semantic_query)
                engines_used.append("semantic")

            if query.mode in ("rag", "auto", "hybrid"):
                rag_query = RAGQuery(
                    question=query.text,
                    top_k=query.top_k,
                    filter_metadata=query.filter_metadata,
                    min_similarity=query.min_similarity,
                    system_prompt=query.system_prompt,
                )
                rag_result = self._rag.answer(rag_query)
                engines_used.append("rag")

            if query.mode in ("graph", "hybrid"):
                graph_query = GraphQuery(
                    entity_name=query.text,
                    depth=query.graph_depth,
                    max_results=query.top_k * 4,
                )
                graph_result = self._kg.query(graph_query)
                engines_used.append("graph")

            elapsed_ms = (time.perf_counter() - start) * 1000

            result = UnifiedResult(
                query=query,
                semantic_result=semantic_result,
                rag_result=rag_result,
                graph_result=graph_result,
                total_time_ms=elapsed_ms,
                engines_used=engines_used,
            )

            self._bus.publish(
                "orchestrator.events",
                {
                    "event": "orchestrator.query_executed",
                    "query_text": query.text,
                    "mode": query.mode,
                    "engines_used": engines_used,
                    "total_time_ms": elapsed_ms,
                },
            )
            return result

        except Exception as exc:
            self._bus.publish(
                "orchestrator.events",
                {
                    "event": "orchestrator.query_failed",
                    "query_text": query.text,
                    "mode": query.mode,
                    "error": str(exc),
                },
            )
            raise QueryOrchestratorError(f"Query orchestration failed: {exc}") from exc

    def health_check(self) -> bool:
        return (
            self._semantic.health_check()
            and self._rag.health_check()
            and self._kg.health_check()
        )
