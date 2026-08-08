"""Tests for Semantic Search Engine (M4.5)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.search_models import (
    RankedDocument,
    SearchFilter,
    SemanticQuery,
    SemanticSearchResult,
)
from skos.m4.domain.vector_models import SearchResult, VectorRecord
from skos.m4.infrastructure.adapters.semantic_search.chroma_semantic_search_adapter import (
    ChromaSemanticSearchAdapter,
)
from skos.m4.infrastructure.ports.semantic_search_port import SemanticSearchPort, SemanticSearchError
from skos.m4.application.services.semantic_search_service import SemanticSearchService
from skos.m4.application.services.document_indexer_service import DocumentIndexerService


class TestDomainModels:
    def test_semantic_query_creation(self) -> None:
        q = SemanticQuery(text="hello world", top_k=10)
        assert q.text == "hello world"
        assert q.top_k == 10
        assert q.filter_metadata is None
        assert q.min_similarity is None

    def test_semantic_query_with_filter(self) -> None:
        q = SemanticQuery(text="test", top_k=3, filter_metadata={"tag": "important"}, min_similarity=0.8)
        assert q.filter_metadata == {"tag": "important"}
        assert q.min_similarity == 0.8

    def test_ranked_document_defaults(self) -> None:
        doc = RankedDocument(id="d1", text="hello")
        assert doc.similarity_score == 0.0
        assert doc.rank == 0
        assert doc.metadata == {}
        assert doc.source_id == ""

    def test_ranked_document_score_in_range(self) -> None:
        doc = RankedDocument(id="d1", text="hello", similarity_score=0.95)
        assert 0.0 <= doc.similarity_score <= 1.0

    def test_search_filter_defaults(self) -> None:
        f = SearchFilter()
        assert f.source_ids is None
        assert f.date_range is None
        assert f.tags is None

    def test_semantic_search_result_defaults(self) -> None:
        q = SemanticQuery(text="x")
        r = SemanticSearchResult(query=q, results=[], total_found=0)
        assert r.query_time_ms == 0.0
        assert r.embedding_model == ""


class TestSemanticSearchPort:
    def test_semantic_search_port_is_abc(self) -> None:
        assert hasattr(SemanticSearchPort, "search")
        assert hasattr(SemanticSearchPort, "index_document")
        assert hasattr(SemanticSearchPort, "delete_document")
        assert hasattr(SemanticSearchPort, "health_check")


class TestChromaSemanticSearchAdapter:
    @pytest.fixture
    def mock_store(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.semantic_search.collection_name": "semantic_search",
        }.get(key, default)
        return config

    def test_adapter_delegates_health_check(self, mock_store: MagicMock, mock_config: MagicMock) -> None:
        mock_store.health_check.return_value = True
        adapter = ChromaSemanticSearchAdapter(mock_store, mock_config)
        assert adapter.health_check() is True
        mock_store.health_check.assert_called_once()

    def test_adapter_delegates_delete(self, mock_store: MagicMock, mock_config: MagicMock) -> None:
        adapter = ChromaSemanticSearchAdapter(mock_store, mock_config)
        adapter.delete_document("doc-1")
        mock_store.delete.assert_called_once_with("semantic_search", ["doc-1"])

    def test_adapter_search_delegates_to_store(self, mock_store: MagicMock, mock_config: MagicMock) -> None:
        mock_store.search.return_value = SearchResult(records=[], total_found=0)
        adapter = ChromaSemanticSearchAdapter(mock_store, mock_config)
        query = SemanticQuery(text="hello", top_k=5)
        result = adapter.search(query)
        assert result.total_found == 0
        mock_store.search.assert_called_once()

    def test_adapter_index_document_raises(self, mock_store: MagicMock, mock_config: MagicMock) -> None:
        adapter = ChromaSemanticSearchAdapter(mock_store, mock_config)
        with pytest.raises(SemanticSearchError):
            adapter.index_document("d1", "text", {})


class TestSemanticSearchService:
    @pytest.fixture
    def mock_deps(self) -> dict[str, MagicMock]:
        store = MagicMock()
        store.search.return_value = SearchResult(
            records=[
                VectorRecord(id="r1", vector=[1.0], text="hello", metadata={}),
                VectorRecord(id="r2", vector=[0.9], text="world", metadata={}),
            ],
            total_found=2,
        )
        store.health_check.return_value = True

        ai = MagicMock()
        from skos.m4.domain.ai_models import EmbeddingResult
        ai.embed.return_value = EmbeddingResult(vectors=[[1.0, 0.0]], model="test-model", dimensions=2)

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.semantic_search.collection_name": "semantic_search",
            "m4.semantic_search.default_top_k": 5,
            "m4.semantic_search.max_results_per_query": 20,
        }.get(key, default)

        bus = MagicMock()
        return {"store": store, "ai": ai, "config": config, "bus": bus}

    def test_search_returns_ranked_documents(self, mock_deps: dict[str, MagicMock]) -> None:
        service = SemanticSearchService(
            mock_deps["store"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        query = SemanticQuery(text="hello", top_k=2)
        result = service.search(query)
        assert result.total_found == 2
        assert len(result.results) == 2
        assert result.results[0].rank == 1
        assert result.embedding_model == "test-model"

    def test_search_emits_completed_event(self, mock_deps: dict[str, MagicMock]) -> None:
        service = SemanticSearchService(
            mock_deps["store"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        service.search(SemanticQuery(text="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("search.completed" in str(c) for c in calls)

    def test_search_with_min_similarity_filters(self, mock_deps: dict[str, MagicMock]) -> None:
        service = SemanticSearchService(
            mock_deps["store"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        query = SemanticQuery(text="test", top_k=2, min_similarity=0.9)
        result = service.search(query)
        assert all(r.similarity_score >= 0.9 for r in result.results)

    def test_search_emits_failed_event_on_error(self, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["ai"].embed.side_effect = RuntimeError("embedding failed")
        service = SemanticSearchService(
            mock_deps["store"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        with pytest.raises(RuntimeError):
            service.search(SemanticQuery(text="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("search.failed" in str(c) for c in calls)

    def test_health_check_delegates(self, mock_deps: dict[str, MagicMock]) -> None:
        service = SemanticSearchService(
            mock_deps["store"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        assert service.health_check() is True


class TestDocumentIndexerService:
    @pytest.fixture
    def mock_indexer_deps(self) -> dict[str, MagicMock]:
        embed_pipeline = MagicMock()
        embed_pipeline.embed_chunks.return_value = [[1.0, 0.0], [0.0, 1.0]]

        store_service = MagicMock()
        store_service.health_check.return_value = True

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.semantic_search.collection_name": "semantic_search",
        }.get(key, default)

        bus = MagicMock()
        return {"embed": embed_pipeline, "store": store_service, "config": config, "bus": bus}

    def test_index_text_chunks_embeds_and_stores(self, mock_indexer_deps: dict[str, MagicMock]) -> None:
        service = DocumentIndexerService(
            mock_indexer_deps["embed"], mock_indexer_deps["store"],
            mock_indexer_deps["config"], mock_indexer_deps["bus"]
        )
        service.index_text("Hello world. This is a test.", doc_id="doc-1")
        mock_indexer_deps["embed"].embed_chunks.assert_called_once()
        mock_indexer_deps["store"].index_chunks.assert_called_once()

    def test_index_text_emits_indexed_event(self, mock_indexer_deps: dict[str, MagicMock]) -> None:
        service = DocumentIndexerService(
            mock_indexer_deps["embed"], mock_indexer_deps["store"],
            mock_indexer_deps["config"], mock_indexer_deps["bus"]
        )
        service.index_text("Short text.", doc_id="doc-2")
        calls = mock_indexer_deps["bus"].publish.call_args_list
        assert any("document.indexed" in str(c) for c in calls)

    def test_index_text_emits_failed_event_on_error(self, mock_indexer_deps: dict[str, MagicMock]) -> None:
        mock_indexer_deps["embed"].embed_chunks.side_effect = RuntimeError("embed fail")
        service = DocumentIndexerService(
            mock_indexer_deps["embed"], mock_indexer_deps["store"],
            mock_indexer_deps["config"], mock_indexer_deps["bus"]
        )
        with pytest.raises(RuntimeError):
            service.index_text("Text.", doc_id="doc-3")
        calls = mock_indexer_deps["bus"].publish.call_args_list
        assert any("document.index_failed" in str(c) for c in calls)

    def test_health_check_delegates(self, mock_indexer_deps: dict[str, MagicMock]) -> None:
        service = DocumentIndexerService(
            mock_indexer_deps["embed"], mock_indexer_deps["store"],
            mock_indexer_deps["config"], mock_indexer_deps["bus"]
        )
        assert service.health_check() is True
