"""Tests for M6.2 admin readiness API integration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort


def build_client(tmp_path: Path) -> TestClient:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    orchestrator = Mock(spec=QueryOrchestratorPort)
    orchestrator.health_check.return_value = True
    config = HierarchicalConfigAdapter(
        defaults={
            "database_path": str(tmp_path / "data" / "sergio.db"),
            "archive_root": str(tmp_path / "archive"),
            "backup_dir": str(tmp_path / "backups"),
            "m4": {"security": {"enabled": True, "auth_required": True}},
            "m5": {"persistence": {"mode": "persistent"}},
            "m6": {"environment": "production"},
        }
    )
    return TestClient(FastAPIAdapter(orchestrator=orchestrator, config=config).app)


def test_admin_readiness_endpoint_returns_report(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["environment"] == "production"
    assert data["ready"] is True
    assert {check["name"] for check in data["checks"]} >= {
        "environment",
        "persistence_mode",
        "security",
        "required_paths",
        "admin_assets",
    }


def test_admin_console_js_loads_readiness_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/admin/assets/app.js")

    assert response.status_code == 200
    assert "/api/v1/admin/readiness" in response.text
