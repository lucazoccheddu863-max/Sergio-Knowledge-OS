"""Application service for indexing documents into the vector store.

Orchestrates chunking → embedding → storage.
Talks to EmbeddingPipeline and VectorStoreService, never to concrete adapters.
"""
from __future__ import annotations

from typing import Any

from skos.m4.domain.chunking import ParagraphChunking
from skos.m4.application.services.embedding_pipeline import EmbeddingPipeline
from skos.m4.application.services.vector_store_service import VectorStoreService
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort


class DocumentIndexerService:
    """Indexes text documents into the vector store for semantic search.

    Dependencies:
        - EmbeddingPipeline: generates embeddings for text chunks
        - VectorStoreService: abstracts vector storage operations
        - ConfigurationPort: reads indexing config
        - EventBusPort: publishes indexing events
    """

    def __init__(
        self,
        embedding_pipeline: EmbeddingPipeline,
        vector_store_service: VectorStoreService,
        config: ConfigurationPort,
        event_bus: EventBusPort,
    ) -> None:
        self._embed = embedding_pipeline
        self._store = vector_store_service
        self._config = config
        self._bus = event_bus
        self._collection = config.get("m4.semantic_search.collection_name", default="semantic_search")

    def index_text(
        self,
        text: str,
        doc_id: str,
        source_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index a text document: chunk → embed → store."""
        try:
            chunker = ParagraphChunking()
            chunks = chunker.chunk(text, source_id=source_id or doc_id)
            vectors = self._embed.embed_chunks(chunks)
            self._store.index_chunks(self._collection, chunks, vectors)

            self._bus.publish(
                "indexing.events",
                {
                    "event": "document.indexed",
                    "doc_id": doc_id,
                    "chunk_count": len(chunks),
                    "collection": self._collection,
                    "source_id": source_id,
                },
            )

        except Exception as exc:
            self._bus.publish(
                "indexing.events",
                {
                    "event": "document.index_failed",
                    "doc_id": doc_id,
                    "error": str(exc),
                    "source_id": source_id,
                },
            )
            raise

    def health_check(self) -> bool:
        return self._store.health_check()
