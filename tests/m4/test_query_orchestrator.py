"""Tests for Query Orchestrator (M4.8)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
from skos.m4.domain.rag_models import RAGContext, RAGQuery, RAGResult
from skos.m4.domain.search_models import RankedDocument, SemanticQuery, SemanticSearchResult
from skos.m4.domain.knowledge_graph_models import Entity, GraphQuery, GraphResult, Relation
from skos.m4.domain.ai_models import ChatResponse
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort, QueryOrchestratorError
from skos.m4.application.services.query_orchestrator_service import QueryOrchestratorService


class TestDomainModels:
    def test_unified_query_defaults(self) -> None:
        q = UnifiedQuery(text="hello")
        assert q.mode == "auto"
        assert q.top_k == 5
        assert q.graph_depth == 1

    def test_unified_query_custom_mode(self) -> None:
        q = UnifiedQuery(text="test", mode="rag", top_k=3)
        assert q.mode == "rag"
        assert q.top_k == 3

    def test_unified_result_defaults(self) -> None:
        q = UnifiedQuery(text="x")
        r = UnifiedResult(query=q)
        assert r.total_time_ms == 0.0
        assert r.engines_used == []
        assert r.semantic_result is None
        assert r.rag_result is None
        assert r.graph_result is None


class TestQueryOrchestratorPort:
    def test_port_is_abc(self) -> None:
        assert hasattr(QueryOrchestratorPort, "execute")
        assert hasattr(QueryOrchestratorPort, "health_check")


class TestQueryOrchestratorService:
    @pytest.fixture
    def mock_deps(self) -> dict[str, MagicMock]:
        semantic = MagicMock()
        semantic.search.return_value = SemanticSearchResult(
            query=SemanticQuery(text="test"),
            results=[RankedDocument(id="r1", text="hello", similarity_score=0.95, rank=1)],
            total_found=1,
        )
        semantic.health_check.return_value = True

        rag = MagicMock()
        rag.answer.return_value = RAGResult(
            query=RAGQuery(question="test"),
            context=RAGContext(documents=[], total_found=0),
            response=ChatResponse(content="Answer", model="gpt-4"),
        )
        rag.health_check.return_value = True

        kg = MagicMock()
        kg.query.return_value = GraphResult(entities=[], relations=[])
        kg.health_check.return_value = True

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.orchestrator.default_mode": "auto",
        }.get(key, default)

        bus = MagicMock()
        return {"semantic": semantic, "rag": rag, "kg": kg, "config": config, "bus": bus}

    def test_execute_auto_routes_to_all(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        result = service.execute(UnifiedQuery(text="test", mode="auto"))
        assert "semantic" in result.engines_used
        assert "rag" in result.engines_used
        mock_deps["semantic"].search.assert_called_once()
        mock_deps["rag"].answer.assert_called_once()

    def test_execute_semantic_only(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        result = service.execute(UnifiedQuery(text="test", mode="semantic"))
        assert result.engines_used == ["semantic"]
        mock_deps["semantic"].search.assert_called_once()
        mock_deps["rag"].answer.assert_not_called()

    def test_execute_rag_only(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        result = service.execute(UnifiedQuery(text="test", mode="rag"))
        assert result.engines_used == ["rag"]
        mock_deps["rag"].answer.assert_called_once()
        mock_deps["semantic"].search.assert_not_called()

    def test_execute_graph_only(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        result = service.execute(UnifiedQuery(text="test", mode="graph"))
        assert result.engines_used == ["graph"]
        mock_deps["kg"].query.assert_called_once()

    def test_execute_hybrid_routes_to_all(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        result = service.execute(UnifiedQuery(text="test", mode="hybrid"))
        assert "semantic" in result.engines_used
        assert "rag" in result.engines_used
        assert "graph" in result.engines_used

    def test_execute_emits_event(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        service.execute(UnifiedQuery(text="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("orchestrator.query_executed" in str(c) for c in calls)

    def test_execute_emits_failed_event_on_error(self, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["semantic"].search.side_effect = RuntimeError("search failed")
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        with pytest.raises(QueryOrchestratorError):
            service.execute(UnifiedQuery(text="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("orchestrator.query_failed" in str(c) for c in calls)

    def test_health_check_delegates(self, mock_deps: dict[str, MagicMock]) -> None:
        service = QueryOrchestratorService(
            mock_deps["semantic"], mock_deps["rag"], mock_deps["kg"],
            mock_deps["config"], mock_deps["bus"]
        )
        assert service.health_check() is True
