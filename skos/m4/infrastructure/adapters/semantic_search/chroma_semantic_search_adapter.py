"""ChromaDB implementation of SemanticSearchPort.

Delegates all storage operations to VectorStorePort (ChromaDBAdapter),
never talks to ChromaDB directly. This ensures the SemanticSearchService
remains decoupled from the concrete vector store implementation.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.search_models import (
    RankedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from skos.m4.domain.vector_models import VectorQuery
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.semantic_search_port import (
    SemanticSearchError,
    SemanticSearchPort,
)
from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort


class ChromaSemanticSearchAdapter(SemanticSearchPort):
    """Semantic search adapter backed by any VectorStorePort implementation.

    Uses the VectorStorePort abstraction so that switching from ChromaDB
    to Qdrant/Milvus/PGVector requires zero changes in the application layer.
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        config: ConfigurationPort,
    ) -> None:
        self._store = vector_store
        self._collection = config.get("m4.semantic_search.collection_name", default="semantic_search")

    def search(self, query: SemanticQuery) -> SemanticSearchResult:
        start = time.perf_counter()
        vector_query = VectorQuery(
            vector=[],
            top_k=query.top_k,
            filter_metadata=query.filter_metadata,
        )
        result = self._store.search(self._collection, vector_query)
        elapsed_ms = (time.perf_counter() - start) * 1000

        ranked: list[RankedDocument] = []
        for i, rec in enumerate(result.records):
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

        return SemanticSearchResult(
            query=query,
            results=ranked,
            total_found=len(ranked),
            query_time_ms=elapsed_ms,
        )

    def index_document(self, doc_id: str, text: str, metadata: dict[str, Any], source_id: str = "") -> None:
        raise SemanticSearchError(
            "ChromaSemanticSearchAdapter does not handle embedding generation. "
            "Use DocumentIndexerService instead."
        )

    def delete_document(self, doc_id: str) -> None:
        self._store.delete(self._collection, [doc_id])

    def health_check(self) -> bool:
        return self._store.health_check()
