"""Tests for M4.9 — REST API Adapter (FastAPI)."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
from skos.m4.domain.search_models import SemanticQuery, SemanticSearchResult, RankedDocument
from skos.m4.domain.rag_models import RAGQuery, RAGResult, RAGContext
from skos.m4.domain.knowledge_graph_models import GraphQuery, GraphResult
from skos.m4.domain.ai_models import ChatResponse
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter


@pytest.fixture
def mock_orchestrator() -> Mock:
    return Mock(spec=QueryOrchestratorPort)


@pytest.fixture
def mock_config() -> Mock:
    return Mock(spec=ConfigurationPort)


@pytest.fixture
def client(mock_orchestrator: Mock, mock_config: Mock) -> TestClient:
    adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
    return TestClient(adapter.app)


class TestQueryEndpoint:
    def test_query_auto_mode_success(self, client: TestClient, mock_orchestrator: Mock) -> None:
        mock_result = UnifiedResult(
            query=UnifiedQuery(text="hello", mode="auto"),
            semantic_result=SemanticSearchResult(
                query=SemanticQuery(text="hello"),
                results=[RankedDocument(id="1", text="doc1", similarity_score=0.9, rank=1)],
                total_found=1,
                query_time_ms=12.0,
            ),
            rag_result=RAGResult(
                query=RAGQuery(question="hello"),
                context=RAGContext(documents=[], total_found=0),
                response=ChatResponse(content="answer", model="gpt-4"),
                total_time_ms=34.0,
            ),
            total_time_ms=46.0,
            engines_used=["semantic", "rag"],
        )
        mock_orchestrator.execute.return_value = mock_result

        response = client.post("/api/v1/query", json={"text": "hello", "mode": "auto"})

        assert response.status_code == 200
        data = response.json()
        assert data["query"]["text"] == "hello"
        assert data["query"]["mode"] == "auto"
        assert data["total_time_ms"] == 46.0
        assert data["engines_used"] == ["semantic", "rag"]
        assert data["semantic_result"]["total_found"] == 1
        assert data["rag_result"]["response"]["content"] == "answer"
        mock_orchestrator.execute.assert_called_once()

    def test_query_missing_text(self, client: TestClient) -> None:
        response = client.post("/api/v1/query", json={"mode": "auto"})
        assert response.status_code == 422

    def test_query_orchestrator_error(self, client: TestClient, mock_orchestrator: Mock) -> None:
        from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorError
        mock_orchestrator.execute.side_effect = QueryOrchestratorError("boom")

        response = client.post("/api/v1/query", json={"text": "hello"})
        assert response.status_code == 500
        assert "boom" in response.json()["detail"]


class TestHealthEndpoint:
    def test_health_healthy(self, client: TestClient, mock_orchestrator: Mock) -> None:
        mock_orchestrator.health_check.return_value = True

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["engines"]["query_orchestrator"] is True

    def test_health_unhealthy(self, client: TestClient, mock_orchestrator: Mock) -> None:
        mock_orchestrator.health_check.return_value = False

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["engines"]["query_orchestrator"] is False


class TestStatusEndpoint:
    def test_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.4.0-alpha10"
        assert data["milestone"] == "M4.9"
        assert data["status"] == "operational"


class TestEnginesEndpoint:
    def test_engines(self, client: TestClient) -> None:
        response = client.get("/api/v1/engines")
        assert response.status_code == 200
        data = response.json()
        assert "semantic_search" in data["engines"]
        assert "rag" in data["engines"]
        assert "knowledge_graph" in data["engines"]
        assert "query_orchestrator" in data["engines"]
