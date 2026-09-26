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
    assert data["milestone"].startswith("M7.")
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
    assert "/api/v1/admin/release/gate" in response.text
    assert "/api/v1/admin/local/launch" in response.text
    assert "/api/v1/admin/local/bootstrap" in response.text
    assert "/api/v1/admin/manual" in response.text
    assert "/api/v1/admin/snapshot" in response.text
    assert "/api/v1/admin/snapshot/report" in response.text
    assert "/api/v1/admin/overview" in response.text
    assert "/api/v1/admin/smoke" in response.text


def test_admin_console_loads_backup_operations_panel(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    html_response = client.get("/admin")
    js_response = client.get("/admin/assets/app.js")

    assert html_response.status_code == 200
    assert js_response.status_code == 200
    assert "Backup e ripristino" in html_response.text
    assert "Controllo operativo" in html_response.text
    assert "Riepilogo operativo" in html_response.text
    assert "snapshot-download" in html_response.text
    assert "Pacchetto di rilascio" in html_response.text
    assert "Avvio locale" in html_response.text
    assert "Manuale operativo" in html_response.text
    assert "local-bootstrap" in html_response.text
    assert "release-package-inspect" in html_response.text
    assert "release-gate-run" in html_response.text
    assert "backup-create" in html_response.text
    assert "/api/v1/admin/backup/manifest" in js_response.text
    assert "/api/v1/admin/backup/restore/stage" in js_response.text


def test_admin_console_assets_include_operator_readability_helpers(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    js_response = client.get("/admin/assets/app.js")
    css_response = client.get("/admin/assets/styles.css")

    assert js_response.status_code == 200
    assert css_response.status_code == 200
    assert "setLaunchRows" in js_response.text
    assert "setBootstrapRows" in js_response.text
    assert "setManualRows" in js_response.text
    assert "setSnapshotRows" in js_response.text
    assert "escapeHtml" in js_response.text
    assert "manual-step" in css_response.text
    assert "overflow-wrap: anywhere" in css_response.text
    assert "check-list" in css_response.text
    assert "action-list" in css_response.text


def test_admin_snapshot_endpoint_returns_operator_snapshot(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/snapshot", params={"port": 8765})

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["verdict"] == "ready"
    assert data["release"]["version"] == Path("VERSION").read_text(encoding="utf-8").strip()
    assert data["smoke"]["ready"] is True
    assert "--port 8765" in data["launch"]["command"]
    assert data["next_actions"]


def test_admin_snapshot_report_endpoint_downloads_text_report(tmp_path: Path) -> None:
    seed_backup_inputs(tmp_path)
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/snapshot/report", params={"port": 8765})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "Sergio Knowledge OS - Operator Snapshot" in response.text
    assert "Verdict: READY" in response.text
    assert "--port 8765" in response.text


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


def test_admin_release_gate_endpoint_returns_distribution_verdict(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post("/api/v1/admin/release/gate", params={"label": "api-gate"})

    assert response.status_code == 200
    data = response.json()
    archive_path = Path(data["package"]["archive_path"])
    assert data["ready"] is True
    assert archive_path.exists()
    assert archive_path.parent == tmp_path / "releases"
    assert data["inspection"]["ready"] is True
    assert data["warnings"] == []


def test_admin_local_launch_endpoint_returns_operator_plan(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/local/launch", params={"port": 8765})

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert "--port 8765" in data["command"]
    assert data["admin_url"] == "http://127.0.0.1:8765/admin"


def test_admin_local_bootstrap_endpoint_prepares_workspace(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post("/api/v1/admin/local/bootstrap")

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert {item["name"] for item in data["items"]} >= {"data", "archive", "backups", "releases"}


def test_admin_manual_endpoint_returns_operator_manual(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/v1/admin/manual")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Sergio Knowledge OS Operator Manual"
    assert {section["title"] for section in data["sections"]} >= {"Start", "Backup", "Release"}


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
