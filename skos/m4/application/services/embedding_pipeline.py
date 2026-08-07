"""Embedding Generation Pipeline.

Orchestrates text chunking, batch embedding generation, and event emission.
Uses AIProviderPort (via AIService) for actual embedding computation.
"""
from __future__ import annotations

from typing import Any

from skos.m4.domain.ai_models import EmbeddingRequest, EmbeddingResult
from skos.m4.domain.chunking import ChunkingStrategy, FixedSizeChunking, TextChunk
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import DomainEvent, EventBusPort


class EmbeddingPipeline:
    """High-level pipeline for generating embeddings from texts.

    Usage:
        pipeline = EmbeddingPipeline(ai_service, event_bus, config)
        result = pipeline.embed_texts(["text one", "text two"], provider="ollama")
    """

    def __init__(
        self,
        ai_service: Any,
        event_bus: EventBusPort,
        config: ConfigurationPort,
        chunking_strategy: ChunkingStrategy | None = None,
    ) -> None:
        self._ai_service = ai_service
        self._event_bus = event_bus
        self._config = config
        self._chunking = chunking_strategy or FixedSizeChunking(
            chunk_size=config.get("m4.embedding.chunk_size", default=500),
            overlap=config.get("m4.embedding.chunk_overlap", default=50),
        )

    def embed_texts(
        self,
        texts: list[str],
        provider_name: str = "ollama",
        source_id: str = "",
    ) -> EmbeddingResult:
        """Generate embeddings for a list of texts with automatic chunking and batching."""
        batch_size = self._config.get("m4.embedding.batch_size", default=100)

        # Step 1: Chunk all texts
        all_chunks: list[TextChunk] = []
        for text in texts:
            chunks = self._chunking.chunk(text, source_id=source_id)
            all_chunks.extend(chunks)

        if not all_chunks:
            return EmbeddingResult(vectors=[], model="", dimensions=0)

        # Step 2: Batch embedding generation
        all_vectors: list[list[float]] = []
        model_name = ""
        dimensions = 0

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            batch_texts = [c.text for c in batch]
            result = self._ai_service.embed(provider_name, batch_texts)
            all_vectors.extend(result.vectors)
            model_name = result.model
            dimensions = result.dimensions

        # Step 3: Emit completion event
        self._emit_completion(source_id, len(all_chunks), model_name)

        return EmbeddingResult(vectors=all_vectors, model=model_name, dimensions=dimensions)

    def embed_chunks(
        self,
        chunks: list[TextChunk],
        provider_name: str = "ollama",
    ) -> EmbeddingResult:
        """Generate embeddings for pre-chunked texts."""
        batch_size = self._config.get("m4.embedding.batch_size", default=100)

        if not chunks:
            return EmbeddingResult(vectors=[], model="", dimensions=0)

        all_vectors: list[list[float]] = []
        model_name = ""
        dimensions = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_texts = [c.text for c in batch]
            result = self._ai_service.embed(provider_name, batch_texts)
            all_vectors.extend(result.vectors)
            model_name = result.model
            dimensions = result.dimensions

        source_id = chunks[0].source_id if chunks else ""
        self._emit_completion(source_id, len(chunks), model_name)

        return EmbeddingResult(vectors=all_vectors, model=model_name, dimensions=dimensions)

    def _emit_completion(self, source_id: str, chunks_processed: int, model: str) -> None:
        event = DomainEvent(
            event_id=f"embedding-completed-{source_id}",
            event_type="embedding.completed",
            correlation_id=f"corr-{source_id}",
            payload={
                "source_id": source_id,
                "chunks_processed": chunks_processed,
                "model": model,
            },
        )
        self._event_bus.publish(event, topic="embedding.events")
