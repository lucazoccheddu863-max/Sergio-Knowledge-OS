"""Tests for M4.9.5 — API Contract Freeze.

Verifies:
- All M4.9 endpoints continue to work (backward compatibility)
- APIError is returned on errors
- OpenAPI schema is generated correctly
- Admin routes are registered
- Contract documentation exists
"""
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


# ── M4.9 Backward Compatibility ────────────────────────────────────────────────

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
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "HTTP_422"

    def test_query_orchestrator_error_returns_api_error(self, client: TestClient, mock_orchestrator: Mock) -> None:
        from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorError
        mock_orchestrator.execute.side_effect = QueryOrchestratorError("boom")

        response = client.post("/api/v1/query", json={"text": "hello"})
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "HTTP_500"
        assert "message" in data
        assert "boom" in data["message"]
        assert "request_id" in data


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
        assert data["version"] == "0.4.0-alpha13"
        assert data["milestone"] == "M4.11"
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


# ── M4.9.5 Contract Tests ─────────────────────────────────────────────────────

class TestAPIErrorContract:
    def test_validation_error_returns_api_error_schema(self, client: TestClient) -> None:
        """422 errors must follow the unified APIError schema."""
        response = client.post("/api/v1/query", json={})
        assert response.status_code == 422
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "request_id" in data

    def test_internal_error_returns_api_error_schema(self, client: TestClient, mock_orchestrator: Mock) -> None:
        """500 errors must follow the unified APIError schema."""
        from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorError
        mock_orchestrator.execute.side_effect = QueryOrchestratorError("test error")

        response = client.post("/api/v1/query", json={"text": "test"})
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "HTTP_500"
        assert "message" in data
        assert "request_id" in data
        assert len(data["request_id"]) == 36  # UUID length


class TestOpenAPISchema:
    def test_openapi_json_available(self, client: TestClient) -> None:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Sergio Knowledge OS API"
        assert data["info"]["version"] == "0.4.0-alpha13"

    def test_openapi_contains_query_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/openapi.json")
        data = response.json()
        paths = data["paths"]
        assert "/api/v1/query" in paths
        assert "post" in paths["/api/v1/query"]

    def test_openapi_contains_error_schema(self, client: TestClient) -> None:
        response = client.get("/api/v1/openapi.json")
        data = response.json()
        schemas = data["components"]["schemas"]
        assert "APIError" in schemas


class TestAdminRoutes:
    def test_admin_status_endpoint_exists(self, client: TestClient) -> None:
        response = client.get("/api/v1/admin/status")
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "M4.11"
        assert data["status"] == "admin_reserved"

    def test_admin_routes_in_openapi(self, client: TestClient) -> None:
        response = client.get("/api/v1/openapi.json")
        data = response.json()
        assert "/api/v1/admin/status" in data["paths"]


class TestContractDocumentation:
    def test_api_contract_md_exists(self) -> None:
        import pathlib
        assert pathlib.Path("docs/api_contract.md").exists()

    def test_api_contract_md_contains_version(self) -> None:
        import pathlib
        content = pathlib.Path("docs/api_contract.md").read_text()
        assert "0.4.0-alpha13" in content
        assert "M4.9.5" in content
