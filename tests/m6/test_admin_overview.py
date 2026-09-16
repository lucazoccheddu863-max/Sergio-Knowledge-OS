"""Tests for M6 admin overview aggregation."""
from __future__ import annotations

from pathlib import Path

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production import (
    build_admin_overview,
    build_admin_smoke_report,
    build_operator_snapshot,
    render_operator_snapshot_report,
)


def config_for(tmp_path: Path) -> HierarchicalConfigAdapter:
    return HierarchicalConfigAdapter(
        defaults={
            "database_path": str(tmp_path / "data" / "sergio.db"),
            "archive_root": str(tmp_path / "archive"),
            "backup_dir": str(tmp_path / "backups"),
            "m4": {"security": {"enabled": True, "auth_required": True}},
            "m5": {"persistence": {"mode": "persistent"}},
            "m6": {"environment": "production"},
        }
    )


def test_admin_overview_combines_release_readiness_and_backup(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")

    overview = build_admin_overview(config_for(tmp_path), root_path=tmp_path)

    assert overview.ready is True
    assert overview.release.version == Path("VERSION").read_text(encoding="utf-8").strip()
    assert overview.readiness.ready is True
    assert overview.backup.ready is True


def test_admin_overview_serializes_nested_reports(tmp_path: Path) -> None:
    data = build_admin_overview(config_for(tmp_path), root_path=tmp_path).as_dict()

    assert data["ready"] is False
    assert data["release"]["milestone"].startswith("M7.")
    assert "checks" in data["readiness"]
    assert "items" in data["backup"]


def test_admin_smoke_report_passes_for_ready_system(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")

    report = build_admin_smoke_report(config_for(tmp_path), root_path=tmp_path)

    assert report.ready is True
    assert {check.name for check in report.checks} == {
        "release",
        "readiness",
        "backup",
        "admin_console",
    }


def test_admin_smoke_report_serializes_failures(tmp_path: Path) -> None:
    data = build_admin_smoke_report(config_for(tmp_path), root_path=tmp_path).as_dict()

    assert data["ready"] is False
    assert any(check["name"] == "backup" and check["status"] == "fail" for check in data["checks"])


def test_operator_snapshot_returns_single_ready_verdict(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "VERSION").write_text("0.6.0-alpha19\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text(
        "\n".join(
            [
                "database_path: data/sergio.db",
                "archive_root: archive",
                "backup_dir: backups",
                "release_dir: releases",
            ]
        ),
        encoding="utf-8",
    )
    config = config_for(tmp_path)

    snapshot = build_operator_snapshot(config, root_path=tmp_path, port=8765)
    data = snapshot.as_dict()

    assert snapshot.ready is True
    assert data["verdict"] == "ready"
    assert data["summary"] == "System ready for local operation"
    assert "--port 8765" in data["launch"]["command"]
    assert data["next_actions"] == [
        "Run the local launch command and open the admin console",
        "Create a fresh backup before importing important data",
    ]


def test_operator_snapshot_reports_next_actions_for_attention(tmp_path: Path) -> None:
    data = build_operator_snapshot(config_for(tmp_path), root_path=tmp_path).as_dict()

    assert data["ready"] is False
    assert data["verdict"] == "attention"
    assert "Operator attention required" in data["summary"]
    assert any("Review readiness checks" in action for action in data["next_actions"])
    assert any("Prepare backup inputs" in action for action in data["next_actions"])


def test_operator_snapshot_report_is_readable_and_complete(tmp_path: Path) -> None:
    snapshot = build_operator_snapshot(config_for(tmp_path), root_path=tmp_path, port=8765)

    report = render_operator_snapshot_report(snapshot)

    assert report.startswith("Sergio Knowledge OS - Operator Snapshot\n")
    assert "Verdict: ATTENTION" in report
    assert "Launch:" in report and "--port 8765" in report
    assert "[PASS] admin_console:" in report
    assert "Next actions\n------------\n- " in report
