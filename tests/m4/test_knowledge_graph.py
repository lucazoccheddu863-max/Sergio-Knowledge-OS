"""Tests for Knowledge Graph (M4.7)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.knowledge_graph_models import Entity, GraphQuery, GraphResult, Relation
from skos.m4.infrastructure.adapters.knowledge_graph.inmemory_kg_adapter import InMemoryKnowledgeGraphAdapter
from skos.m4.infrastructure.ports.knowledge_graph_port import KnowledgeGraphPort, KnowledgeGraphError
from skos.m4.application.services.knowledge_graph_service import KnowledgeGraphService


class TestDomainModels:
    def test_entity_creation(self) -> None:
        e = Entity(id="e1", name="Python", entity_type="language")
        assert e.name == "Python"
        assert e.entity_type == "language"

    def test_relation_creation(self) -> None:
        r = Relation(source_id="e1", target_id="e2", relation_type="uses")
        assert r.relation_type == "uses"

    def test_graph_query_defaults(self) -> None:
        q = GraphQuery()
        assert q.depth == 1
        assert q.max_results == 20

    def test_graph_result_defaults(self) -> None:
        res = GraphResult(entities=[], relations=[])
        assert res.query_time_ms == 0.0


class TestKnowledgeGraphPort:
    def test_knowledge_graph_port_is_abc(self) -> None:
        assert hasattr(KnowledgeGraphPort, "add_entity")
        assert hasattr(KnowledgeGraphPort, "add_relation")
        assert hasattr(KnowledgeGraphPort, "query")
        assert hasattr(KnowledgeGraphPort, "health_check")


class TestInMemoryKnowledgeGraphAdapter:
    @pytest.fixture
    def adapter(self) -> InMemoryKnowledgeGraphAdapter:
        return InMemoryKnowledgeGraphAdapter()

    def test_add_and_get_entity(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        e = Entity(id="e1", name="Python", entity_type="language")
        adapter.add_entity(e)
        assert adapter.get_entity("e1") == e

    def test_add_relation(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        adapter.add_entity(Entity(id="e1", name="A", entity_type="x"))
        adapter.add_entity(Entity(id="e2", name="B", entity_type="x"))
        r = Relation(source_id="e1", target_id="e2", relation_type="links")
        adapter.add_relation(r)
        result = adapter.query(GraphQuery())
        assert len(result.relations) == 1

    def test_add_relation_missing_entity_raises(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        r = Relation(source_id="e1", target_id="e2", relation_type="links")
        with pytest.raises(KnowledgeGraphError):
            adapter.add_relation(r)

    def test_query_by_name(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        adapter.add_entity(Entity(id="e1", name="Python", entity_type="language"))
        adapter.add_entity(Entity(id="e2", name="JavaScript", entity_type="language"))
        result = adapter.query(GraphQuery(entity_name="Python"))
        assert len(result.entities) == 1
        assert result.entities[0].id == "e1"

    def test_query_by_type(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        adapter.add_entity(Entity(id="e1", name="Python", entity_type="language"))
        adapter.add_entity(Entity(id="e2", name="Django", entity_type="framework"))
        result = adapter.query(GraphQuery(entity_type="framework"))
        assert len(result.entities) == 1
        assert result.entities[0].id == "e2"

    def test_delete_entity_cascades_relations(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        adapter.add_entity(Entity(id="e1", name="A", entity_type="x"))
        adapter.add_entity(Entity(id="e2", name="B", entity_type="x"))
        adapter.add_relation(Relation(source_id="e1", target_id="e2", relation_type="r"))
        adapter.delete_entity("e1")
        assert adapter.get_entity("e1") is None
        result = adapter.query(GraphQuery())
        assert len(result.relations) == 0

    def test_health_check(self, adapter: InMemoryKnowledgeGraphAdapter) -> None:
        assert adapter.health_check() is True


class TestKnowledgeGraphService:
    @pytest.fixture
    def mock_deps(self) -> dict[str, MagicMock]:
        store = MagicMock()
        store.health_check.return_value = True
        store.query.return_value = GraphResult(entities=[], relations=[])

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.knowledge_graph.default_depth": 2,
            "m4.knowledge_graph.max_results": 50,
        }.get(key, default)

        bus = MagicMock()
        return {"store": store, "config": config, "bus": bus}

    def test_add_document_entities(self, mock_deps: dict[str, MagicMock]) -> None:
        service = KnowledgeGraphService(mock_deps["store"], mock_deps["config"], mock_deps["bus"])
        entities = [Entity(id="e1", name="Python", entity_type="language")]
        relations = [Relation(source_id="e1", target_id="e2", relation_type="uses")]
        service.add_document_entities("doc-1", entities, relations)
        mock_deps["store"].add_entity.assert_called()
        mock_deps["store"].add_relation.assert_called()
        calls = mock_deps["bus"].publish.call_args_list
        assert any("kg.document_indexed" in str(c) for c in calls)

    def test_query_delegates_and_emits_event(self, mock_deps: dict[str, MagicMock]) -> None:
        service = KnowledgeGraphService(mock_deps["store"], mock_deps["config"], mock_deps["bus"])
        service.query(GraphQuery(entity_name="Python"))
        mock_deps["store"].query.assert_called_once()
        calls = mock_deps["bus"].publish.call_args_list
        assert any("kg.queried" in str(c) for c in calls)

    def test_delete_entity_emits_event(self, mock_deps: dict[str, MagicMock]) -> None:
        service = KnowledgeGraphService(mock_deps["store"], mock_deps["config"], mock_deps["bus"])
        service.delete_entity("e1")
        mock_deps["store"].delete_entity.assert_called_once_with("e1")
        calls = mock_deps["bus"].publish.call_args_list
        assert any("kg.entity_deleted" in str(c) for c in calls)

    def test_health_check_delegates(self, mock_deps: dict[str, MagicMock]) -> None:
        service = KnowledgeGraphService(mock_deps["store"], mock_deps["config"], mock_deps["bus"])
        assert service.health_check() is True
