"""Tests for M5.3 admin console."""
from __future__ import annotations

from unittest.mock import Mock

from fastapi.testclient import TestClient

from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort


def build_client() -> TestClient:
    orchestrator = Mock(spec=QueryOrchestratorPort)
    orchestrator.health_check.return_value = True
    config = Mock(spec=ConfigurationPort)
    return TestClient(FastAPIAdapter(orchestrator=orchestrator, config=config).app)


def test_admin_console_serves_html() -> None:
    client = build_client()

    response = client.get("/admin")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sergio Knowledge OS" in response.text
    assert "/admin/assets/app.js" in response.text
    assert 'id="document-file"' in response.text
    assert 'id="document-import"' in response.text
    assert 'id="query-text"' in response.text
    assert 'id="query-submit"' in response.text
    assert 'id="ai-summary"' in response.text
    assert 'id="ai-list"' in response.text


def test_admin_console_serves_css_asset() -> None:
    client = build_client()

    response = client.get("/admin/assets/styles.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".status-grid" in response.text


def test_admin_console_uses_sergio_control_room_identity() -> None:
    client = build_client()

    html = client.get("/admin").text
    css = client.get("/admin/assets/styles.css").text

    assert 'class="sidebar"' in html
    assert "Assistente personale della conoscenza" in html
    assert "Sistema locale" in html
    assert "Sergio Knowledge OS" in html
    assert ".app-shell" in css
    assert ".brand-lockup" in css
    assert "color-scheme: dark" in css


def test_admin_console_serves_js_asset() -> None:
    client = build_client()

    response = client.get("/admin/assets/app.js")

    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    assert "/api/v1/health" in response.text
    assert "/api/v1/admin/import/upload" in response.text
    assert 'document.getElementById("document-import")' in response.text
    assert 'document.getElementById("query-submit")' in response.text
    assert "result.rag_result?.context?.documents" in response.text
    assert "/api/v1/admin/ai/status" in response.text
