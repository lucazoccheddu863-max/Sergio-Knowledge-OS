"""Tests for M6 admin overview aggregation."""
from __future__ import annotations

from pathlib import Path

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production import build_admin_overview


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
    assert data["release"]["milestone"].startswith("M6.")
    assert "checks" in data["readiness"]
    assert "items" in data["backup"]
