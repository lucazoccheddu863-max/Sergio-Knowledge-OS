"""Application service for semantic search operations.

Orchestrates the full search flow: query embedding → vector search → ranking.
Talks ONLY to VectorStorePort and AIService, never to concrete adapters.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.ai_models import EmbeddingRequest
from skos.m4.domain.search_models import (
    RankedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from skos.m4.domain.vector_models import VectorQuery
from skos.m4.application.services.ai_service import AIService
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort


class SemanticSearchService:
    """High-level semantic search orchestrator.

    Dependencies:
        - VectorStorePort: abstract vector storage (ChromaDB, Qdrant, etc.)
        - AIService: generates query embeddings
        - ConfigurationPort: reads search config
        - EventBusPort: publishes search events
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        ai_service: AIService,
        config: ConfigurationPort,
        event_bus: EventBusPort,
    ) -> None:
        self._store = vector_store
        self._ai = ai_service
        self._config = config
        self._bus = event_bus
        self._collection = config.get("m4.semantic_search.collection_name", default="semantic_search")
        self._default_top_k = config.get("m4.semantic_search.default_top_k", default=5)
        self._max_results = config.get("m4.semantic_search.max_results_per_query", default=20)

    def search(self, query: SemanticQuery) -> SemanticSearchResult:
        """Execute semantic search: embed query → vector search → rank → emit event."""
        start = time.perf_counter()
        try:
            embed_req = EmbeddingRequest(texts=[query.text])
            embed_result = self._ai.embed(embed_req)
            query_vector = embed_result.vectors[0]

            top_k = min(query.top_k or self._default_top_k, self._max_results)
            vector_query = VectorQuery(
                vector=query_vector,
                top_k=top_k,
                filter_metadata=query.filter_metadata,
            )
            store_result = self._store.search(self._collection, vector_query)

            ranked = self._rank_results(store_result, query)
            elapsed_ms = (time.perf_counter() - start) * 1000

            result = SemanticSearchResult(
                query=query,
                results=ranked,
                total_found=len(ranked),
                query_time_ms=elapsed_ms,
                embedding_model=embed_result.model or "",
            )

            self._bus.publish(
                "search.events",
                {
                    "event": "search.completed",
                    "query_text": query.text,
                    "result_count": len(ranked),
                    "query_time_ms": elapsed_ms,
                    "collection": self._collection,
                },
            )
            return result

        except Exception as exc:
            self._bus.publish(
                "search.events",
                {
                    "event": "search.failed",
                    "query_text": query.text,
                    "error": str(exc),
                },
            )
            raise

    def _rank_results(self, store_result: Any, query: SemanticQuery) -> list[RankedDocument]:
        from skos.m4.domain.vector_models import SearchResult
        if not isinstance(store_result, SearchResult):
            return []

        ranked: list[RankedDocument] = []
        for i, rec in enumerate(store_result.records):
            score = max(0.0, 1.0 - (i * 0.15))
            if query.min_similarity is not None and score < query.min_similarity:
                continue
            ranked.append(RankedDocument(
                id=rec.id,
                text=rec.text,
                metadata=rec.metadata,
                source_id=rec.source_id,
                similarity_score=round(score, 4),
                rank=i + 1,
            ))
        return ranked

    def health_check(self) -> bool:
        return self._store.health_check()
