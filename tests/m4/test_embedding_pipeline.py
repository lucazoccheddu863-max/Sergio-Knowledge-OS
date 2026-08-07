"""Tests for the Embedding Generation Pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.ai_models import EmbeddingResult
from skos.m4.domain.chunking import FixedSizeChunking, ParagraphChunking, TextChunk
from skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus import InMemoryEventBus
from skos.m4.infrastructure.ports.event_bus_port import DomainEvent
from skos.m4.application.services.embedding_pipeline import EmbeddingPipeline


class MockAIService:
    """Mock AI service for testing."""

    def __init__(self) -> None:
        self.call_count = 0
        self.last_texts: list[str] = []

    def embed(self, provider_name: str, texts: list[str]) -> EmbeddingResult:
        self.call_count += 1
        self.last_texts = texts
        vectors = [[0.1, 0.2, 0.3] for _ in texts]
        return EmbeddingResult(vectors=vectors, model="mock-model", dimensions=3)


class TestFixedSizeChunking:
    def test_empty_text(self) -> None:
        strategy = FixedSizeChunking(chunk_size=10, overlap=2)
        assert strategy.chunk("") == []

    def test_short_text_no_split(self) -> None:
        strategy = FixedSizeChunking(chunk_size=10, overlap=2)
        chunks = strategy.chunk("hello world", source_id="src-1")
        assert len(chunks) == 1
        assert chunks[0].text == "hello world"
        assert chunks[0].source_id == "src-1"
        assert chunks[0].index == 0
        assert chunks[0].total_chunks == 1

    def test_long_text_split(self) -> None:
        strategy = FixedSizeChunking(chunk_size=5, overlap=1)
        text = "one two three four five six seven eight nine ten"
        chunks = strategy.chunk(text, source_id="src-1")
        assert len(chunks) > 1
        assert all(c.source_id == "src-1" for c in chunks)
        assert all(c.total_chunks == len(chunks) for c in chunks)
        # Check indices are sequential
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_overlap_preserves_context(self) -> None:
        strategy = FixedSizeChunking(chunk_size=4, overlap=2)
        text = "a b c d e f g h"
        chunks = strategy.chunk(text)
        assert len(chunks) >= 2
        # Last words of chunk 0 should appear in chunk 1
        words_0 = set(chunks[0].text.split())
        words_1 = set(chunks[1].text.split())
        assert len(words_0 & words_1) > 0

    def test_invalid_chunk_size(self) -> None:
        with pytest.raises(ValueError):
            FixedSizeChunking(chunk_size=0)

    def test_invalid_overlap(self) -> None:
        with pytest.raises(ValueError):
            FixedSizeChunking(chunk_size=10, overlap=10)


class TestParagraphChunking:
    def test_empty_text(self) -> None:
        strategy = ParagraphChunking(chunk_size=10)
        assert strategy.chunk("") == []

    def test_single_paragraph(self) -> None:
        strategy = ParagraphChunking(chunk_size=10)
        chunks = strategy.chunk("hello world", source_id="src-1")
        assert len(chunks) == 1
        assert chunks[0].text == "hello world"

    def test_multiple_paragraphs(self) -> None:
        strategy = ParagraphChunking(chunk_size=100)
        text = "First paragraph here.\n\nSecond paragraph there.\n\nThird paragraph everywhere."
        chunks = strategy.chunk(text, source_id="src-1")
        assert len(chunks) == 3
        assert chunks[0].text == "First paragraph here."
        assert chunks[1].text == "Second paragraph there."
        assert chunks[2].text == "Third paragraph everywhere."

    def test_long_paragraph_fallback(self) -> None:
        strategy = ParagraphChunking(chunk_size=5, overlap=1)
        text = "a b c d e f g h i j k l m n o p"
        chunks = strategy.chunk(text, source_id="src-1")
        assert len(chunks) > 1  # Fallback to fixed-size


class TestEmbeddingPipeline:
    def test_embed_short_texts(self) -> None:
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.embedding.batch_size": 100,
            "m4.embedding.chunk_size": 500,
            "m4.embedding.chunk_overlap": 50,
        }.get(key, default)

        ai_service = MockAIService()
        pipeline = EmbeddingPipeline(ai_service, bus, config)

        captured: list[DomainEvent] = []
        bus.subscribe("embedding.events", lambda e: captured.append(e))

        result = pipeline.embed_texts(["hello world", "foo bar"], provider_name="mock", source_id="src-1")

        assert len(result.vectors) == 2
        assert result.model == "mock-model"
        assert result.dimensions == 3
        assert ai_service.call_count == 1
        assert len(captured) == 1
        assert captured[0].event_type == "embedding.completed"
        assert captured[0].payload["chunks_processed"] == 2

    def test_embed_long_texts_with_chunking(self) -> None:
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.embedding.batch_size": 100,
            "m4.embedding.chunk_size": 5,
            "m4.embedding.chunk_overlap": 1,
        }.get(key, default)

        ai_service = MockAIService()
        pipeline = EmbeddingPipeline(ai_service, bus, config)

        # A text with many words will be chunked
        long_text = " ".join([f"word{i}" for i in range(20)])
        result = pipeline.embed_texts([long_text], provider_name="mock", source_id="src-2")

        assert len(result.vectors) > 1  # Multiple chunks
        assert ai_service.call_count >= 1

    def test_embed_chunks_directly(self) -> None:
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.embedding.batch_size": 100,
            "m4.embedding.chunk_size": 500,
            "m4.embedding.chunk_overlap": 50,
        }.get(key, default)

        ai_service = MockAIService()
        pipeline = EmbeddingPipeline(ai_service, bus, config)

        chunks = [
            TextChunk(text="chunk one", source_id="src-3", index=0, total_chunks=2),
            TextChunk(text="chunk two", source_id="src-3", index=1, total_chunks=2),
        ]
        result = pipeline.embed_chunks(chunks, provider_name="mock")

        assert len(result.vectors) == 2
        assert ai_service.last_texts == ["chunk one", "chunk two"]

    def test_empty_texts(self) -> None:
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.embedding.batch_size": 100,
            "m4.embedding.chunk_size": 500,
            "m4.embedding.chunk_overlap": 50,
        }.get(key, default)

        ai_service = MockAIService()
        pipeline = EmbeddingPipeline(ai_service, bus, config)

        result = pipeline.embed_texts([], provider_name="mock")
        assert result.vectors == []
        assert result.dimensions == 0
        assert ai_service.call_count == 0

    def test_batch_processing(self) -> None:
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.embedding.batch_size": 2,
            "m4.embedding.chunk_size": 500,
            "m4.embedding.chunk_overlap": 50,
        }.get(key, default)

        ai_service = MockAIService()
        pipeline = EmbeddingPipeline(ai_service, bus, config)

        texts = ["text1", "text2", "text3", "text4", "text5"]
        result = pipeline.embed_texts(texts, provider_name="mock")

        assert len(result.vectors) == 5
        assert ai_service.call_count == 3  # 2+2+1 batches
