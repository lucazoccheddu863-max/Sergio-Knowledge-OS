"""Tests for M6 admin API integration."""
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
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "archive").mkdir(exist_ok=True)
    (tmp_path / "backups").mkdir(exist_ok=True)
    orchestrator = Mock(spec=QueryOrchestratorPort)
    orchestrator.health_check.return_value = True
    config = HierarchicalConfigAdapter(
        defaults={
            "database_path": str(tmp_path / "data" / "sergio.db"),
            "archive_root": str(tmp_path / "archive"),
            "backup_dir": str(tmp_path / "backups"),
            "release_dir": str(tmp_path / "releases"),
            "m4": {"security": {"enabled": True, "auth_required": True}},
            "m5": {"persistence": {"mode": "persistent"}},
            "m6": {"environment": "production"},
        }
    )
    return TestClient(FastAPIAdapter(orchestrator=orchestrator, config=config).app)


def seed_backup_inputs(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "archive").mkdir(exist_ok=True)
    (tmp_path / "backups").mkdir(exist_ok=True)
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")


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


def test_admin_release_endpoint_returns_current_release(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/release")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == Path("VERSION").read_text(encoding="utf-8").strip()
    assert data["milestone"].startswith("M6.")
    assert data["status"] == "operational"


def test_admin_overview_endpoint_returns_operator_snapshot(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["release"]["version"] == Path("VERSION").read_text(encoding="utf-8").strip()
    assert data["readiness"]["ready"] is True
    assert data["backup"]["ready"] is True


def test_admin_smoke_endpoint_returns_operator_checks(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/smoke")

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert {check["name"] for check in data["checks"]} >= {
        "release",
        "readiness",
        "backup",
        "admin_console",
    }


def test_admin_console_js_loads_readiness_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/admin/assets/app.js")

    assert response.status_code == 200
    assert "/api/v1/admin/readiness" in response.text
    assert "/api/v1/admin/release" in response.text
    assert "/api/v1/admin/release/package" in response.text
    assert "/api/v1/admin/release/package/inspect" in response.text
    assert "/api/v1/admin/overview" in response.text
    assert "/api/v1/admin/smoke" in response.text


def test_admin_console_loads_backup_operations_panel(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    html_response = client.get("/admin")
    js_response = client.get("/admin/assets/app.js")

    assert html_response.status_code == 200
    assert js_response.status_code == 200
    assert "Backup Operations" in html_response.text
    assert "Operator Smoke Check" in html_response.text
    assert "Release Package" in html_response.text
    assert "release-package-inspect" in html_response.text
    assert "backup-create" in html_response.text
    assert "/api/v1/admin/backup/manifest" in js_response.text
    assert "/api/v1/admin/backup/restore/stage" in js_response.text


def test_admin_release_package_endpoint_creates_zip(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post("/api/v1/admin/release/package", params={"label": "api-release"})

    assert response.status_code == 200
    data = response.json()
    archive_path = Path(data["archive_path"])
    assert archive_path.exists()
    assert archive_path.parent == tmp_path / "releases"
    assert data["manifest"]["version"] == Path("VERSION").read_text(encoding="utf-8").strip()
    assert data["manifest"]["total_files"] > 0


def test_admin_release_package_inspect_endpoint_validates_zip(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    create_response = client.post("/api/v1/admin/release/package")
    archive_path = create_response.json()["archive_path"]

    response = client.get(
        "/api/v1/admin/release/package/inspect",
        params={"archive_path": archive_path},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["warnings"] == []
    assert "release_manifest.json" in data["entries"]


def test_admin_backup_manifest_endpoint_returns_report(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/backup/manifest")

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["total_files"] == 2
    assert {item["name"] for item in data["items"]} == {"database", "archive"}


def test_admin_backup_create_and_inspect_endpoints(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    create_response = client.post("/api/v1/admin/backup/create", params={"label": "api-test"})

    assert create_response.status_code == 200
    archive_path = create_response.json()["archive_path"]
    assert Path(archive_path).exists()

    inspect_response = client.get(
        "/api/v1/admin/backup/inspect",
        params={"archive_path": archive_path},
    )

    assert inspect_response.status_code == 200
    data = inspect_response.json()
    assert data["ready"] is True
    assert "manifest.json" in data["entries"]


def test_admin_backup_restore_stage_endpoint_extracts_to_target(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)
    create_response = client.post("/api/v1/admin/backup/create")
    archive_path = create_response.json()["archive_path"]
    target_dir = tmp_path / "restore-stage"

    response = client.post(
        "/api/v1/admin/backup/restore/stage",
        params={"archive_path": archive_path, "target_dir": str(target_dir)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_dir"] == str(target_dir)
    assert (target_dir / "database" / "sergio.db").read_text(encoding="utf-8") == "database"
    assert (target_dir / "archive" / "chat.txt").read_text(encoding="utf-8") == "archive-item"


def test_admin_backup_restore_stage_endpoint_rejects_invalid_archive(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    broken_archive = tmp_path / "broken.zip"
    broken_archive.write_text("not-a-zip", encoding="utf-8")

    response = client.post(
        "/api/v1/admin/backup/restore/stage",
        params={"archive_path": str(broken_archive), "target_dir": str(tmp_path / "restore-stage")},
    )

    assert response.status_code == 400
    assert "backup archive is not ready for restore" in response.json()["message"]
