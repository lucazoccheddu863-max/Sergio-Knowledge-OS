"""Tests for M6 local launch preflight."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI

from skos.m6.production import bootstrap_local_workspace, build_local_launch_plan
from skos.m6.production.local_server import build_local_app


def test_local_launch_plan_reports_command_and_urls() -> None:
    plan = build_local_launch_plan(port=8765)

    assert plan.ready is True
    assert "skos.m6.production.local_server:create_app" in plan.command
    assert "--factory" in plan.command
    assert "--port 8765" in plan.command
    assert plan.admin_url == "http://127.0.0.1:8765/admin"
    assert plan.api_url == "http://127.0.0.1:8765/api/v1/health"


def test_local_launch_plan_serializes_checks() -> None:
    data = build_local_launch_plan().as_dict()

    assert data["ready"] is True
    assert {check["name"] for check in data["checks"]} >= {
        "release",
        "config",
        "admin_assets",
        "local_server",
    }


def test_local_launch_plan_warns_when_config_missing(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("0.6.0-alpha15", encoding="utf-8")

    plan = build_local_launch_plan(root_path=tmp_path)

    assert plan.ready is False
    assert any(check.name == "config" and check.status == "fail" for check in plan.checks)


def test_local_server_factory_delegates_to_application_runtime(monkeypatch) -> None:
    expected_app = FastAPI()
    monkeypatch.setattr(
        "skos.m6.production.local_server.build_application_runtime",
        lambda root_path: SimpleNamespace(app=expected_app),
    )

    assert build_local_app() is expected_app


def test_bootstrap_local_workspace_creates_runtime_directories(tmp_path: Path) -> None:
    result = bootstrap_local_workspace(root_path=tmp_path)

    assert result.ready is True
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "data" / "archive").is_dir()
    assert (tmp_path / "data" / "backups").is_dir()
    assert (tmp_path / "data" / "releases").is_dir()
    assert any(item.created for item in result.items)


def test_bootstrap_local_workspace_is_idempotent(tmp_path: Path) -> None:
    bootstrap_local_workspace(root_path=tmp_path)
    result = bootstrap_local_workspace(root_path=tmp_path)

    assert result.ready is True
    assert all(not item.created for item in result.items)


def test_bootstrap_local_workspace_warns_for_file_collision(tmp_path: Path) -> None:
    (tmp_path / "data").write_text("not-a-directory", encoding="utf-8")

    result = bootstrap_local_workspace(root_path=tmp_path)

    assert result.ready is False
    assert "data path exists but is not a directory" in result.warnings
