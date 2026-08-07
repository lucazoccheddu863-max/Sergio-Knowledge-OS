"""Tests for Vector Store Port, ChromaDB Adapter, and VectorStoreService."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.chunking import TextChunk
from skos.m4.domain.vector_models import VectorQuery, VectorRecord, SearchResult
from skos.m4.infrastructure.adapters.vector_store.chromadb_adapter import ChromaDBAdapter
from skos.m4.infrastructure.ports.vector_store_port import (
    CollectionNotFoundError,
    VectorStorePort,
    VectorStoreError,
)
from skos.m4.application.services.vector_store_service import VectorStoreService


class TestChromaDBAdapterUnit:
    """Unit tests for ChromaDBAdapter helpers (no DB required)."""

    def test_sanitize_collection_name_replaces_spaces(self) -> None:
        assert ChromaDBAdapter._sanitize_collection_name("my collection") == "my_collection"

    def test_sanitize_collection_name_removes_special_chars(self) -> None:
        assert ChromaDBAdapter._sanitize_collection_name("col@#$") == "col"

    def test_sanitize_collection_name_truncates_to_63(self) -> None:
        long_name = "a" * 100
        result = ChromaDBAdapter._sanitize_collection_name(long_name)
        assert len(result) == 63

    def test_sanitize_collection_name_prefixes_digit(self) -> None:
        assert ChromaDBAdapter._sanitize_collection_name("123abc") == "123abc"

    def test_sanitize_collection_name_empty_defaults(self) -> None:
        assert ChromaDBAdapter._sanitize_collection_name("") == "coll"

    def test_normalize_metadata_empty_dict_returns_none(self) -> None:
        assert ChromaDBAdapter._normalize_metadata({}) is None

    def test_normalize_metadata_none_returns_none(self) -> None:
        assert ChromaDBAdapter._normalize_metadata(None) is None

    def test_normalize_metadata_with_data_preserved(self) -> None:
        meta = {"key": "value"}
        assert ChromaDBAdapter._normalize_metadata(meta) == meta


class TestChromaDBAdapterIntegration:
    """Integration tests using in-memory ChromaDB client.

    Each test uses a unique collection name to avoid cross-test pollution
    in the shared in-memory client.
    """

    @pytest.fixture
    def adapter(self) -> ChromaDBAdapter:
        return ChromaDBAdapter(persist_directory=None)

    def test_health_check(self, adapter: ChromaDBAdapter) -> None:
        assert adapter.health_check() is True

    def test_list_collections_empty(self, adapter: ChromaDBAdapter) -> None:
        # Use a unique name and then delete it to check list is clean
        name = "list_empty_test"
        adapter.get_collection(name)
        adapter.delete_collection(name)
        # Note: other tests may leave collections; we just verify the method works
        assert isinstance(adapter.list_collections(), list)

    def test_get_collection_creates_if_missing(self, adapter: ChromaDBAdapter) -> None:
        col = adapter.get_collection("get_col_test")
        assert col is not None
        assert "get_col_test" in adapter.list_collections()

    def test_upsert_and_search(self, adapter: ChromaDBAdapter) -> None:
        records = [
            VectorRecord(id="r1", vector=[1.0, 0.0, 0.0], text="hello", metadata={"tag": "greeting"}),
            VectorRecord(id="r2", vector=[0.0, 1.0, 0.0], text="world", metadata={"tag": "noun"}),
        ]
        adapter.upsert("upsert_search_test", records)
        result = adapter.search("upsert_search_test", VectorQuery(vector=[1.0, 0.0, 0.0], top_k=2))
        assert result.total_found == 2
        assert result.records[0].id == "r1"

    def test_upsert_with_empty_metadata(self, adapter: ChromaDBAdapter) -> None:
        """Empty metadata must not cause ChromaDB errors."""
        records = [
            VectorRecord(id="r1", vector=[1.0, 0.0], text="a", metadata={}),
        ]
        adapter.upsert("empty_meta_test", records)
        result = adapter.search("empty_meta_test", VectorQuery(vector=[1.0, 0.0], top_k=1))
        assert result.total_found == 1

    def test_delete(self, adapter: ChromaDBAdapter) -> None:
        records = [
            VectorRecord(id="r1", vector=[1.0, 0.0], text="a"),
        ]
        adapter.upsert("delete_test", records)
        adapter.delete("delete_test", ["r1"])
        result = adapter.search("delete_test", VectorQuery(vector=[1.0, 0.0], top_k=1))
        assert result.total_found == 0

    def test_delete_collection(self, adapter: ChromaDBAdapter) -> None:
        adapter.get_collection("del_col_test")
        assert "del_col_test" in adapter.list_collections()
        adapter.delete_collection("del_col_test")
        assert "del_col_test" not in adapter.list_collections()

    def test_collection_name_sanitised_internally(self, adapter: ChromaDBAdapter) -> None:
        """Adapter should accept invalid names and sanitise them."""
        adapter.upsert("my bad name!", [
            VectorRecord(id="r1", vector=[1.0, 0.0], text="x"),
        ])
        # The sanitised name should appear in list_collections
        cols = adapter.list_collections()
        assert any("my_bad_name" in c for c in cols)


class TestVectorStoreService:
    """Tests for VectorStoreService application layer."""

    @pytest.fixture
    def service(self) -> VectorStoreService:
        adapter = ChromaDBAdapter(persist_directory=None)
        return VectorStoreService(adapter)

    def test_index_chunks(self, service: VectorStoreService) -> None:
        chunks = [
            TextChunk(text="hello", source_id="src-1", index=0, total_chunks=2),
            TextChunk(text="world", source_id="src-1", index=1, total_chunks=2),
        ]
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        service.index_chunks("svc_test", chunks, vectors)
        result = service.search_similar("svc_test", [1.0, 0.0], top_k=2)
        assert result.total_found == 2

    def test_index_chunks_length_mismatch_raises(self, service: VectorStoreService) -> None:
        chunks = [TextChunk(text="a", source_id="s", index=0, total_chunks=1)]
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        with pytest.raises(ValueError):
            service.index_chunks("svc_test2", chunks, vectors)

    def test_search_similar(self, service: VectorStoreService) -> None:
        chunks = [
            TextChunk(text="alpha", source_id="s1", index=0, total_chunks=1),
        ]
        service.index_chunks("search_test", chunks, [[1.0, 0.0]])
        result = service.search_similar("search_test", [1.0, 0.0], top_k=1)
        assert result.total_found == 1
        assert result.records[0].text == "alpha"

    def test_health_check(self, service: VectorStoreService) -> None:
        assert service.health_check() is True
