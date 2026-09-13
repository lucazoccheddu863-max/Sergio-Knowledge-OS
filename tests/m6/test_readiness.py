"""Tests for M6.1 production readiness checks."""
from __future__ import annotations

from pathlib import Path

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production import run_production_readiness


def base_defaults(tmp_path: Path) -> dict:
    return {
        "database_path": str(tmp_path / "data" / "sergio.db"),
        "archive_root": str(tmp_path / "archive"),
        "backup_dir": str(tmp_path / "backups"),
        "m4": {"security": {"enabled": True, "auth_required": True}},
        "m5": {"persistence": {"mode": "persistent"}},
        "m6": {"environment": "production"},
    }


def create_required_dirs(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()


def test_production_readiness_passes_for_hardened_config(tmp_path: Path) -> None:
    create_required_dirs(tmp_path)
    config = HierarchicalConfigAdapter(defaults=base_defaults(tmp_path))

    report = run_production_readiness(config, root_path=tmp_path)

    assert report.ready is True
    assert all(check.status == "pass" for check in report.checks)


def test_production_readiness_fails_when_production_uses_memory_mode(tmp_path: Path) -> None:
    create_required_dirs(tmp_path)
    defaults = base_defaults(tmp_path)
    defaults["m5"]["persistence"]["mode"] = "memory"
    config = HierarchicalConfigAdapter(defaults=defaults)

    report = run_production_readiness(config, root_path=tmp_path)

    assert report.ready is False
    assert any(
        check.name == "persistence_mode" and check.status == "fail"
        for check in report.checks
    )


def test_development_readiness_warns_but_does_not_fail_for_open_security(tmp_path: Path) -> None:
    create_required_dirs(tmp_path)
    defaults = base_defaults(tmp_path)
    defaults["m6"]["environment"] = "development"
    defaults["m5"]["persistence"]["mode"] = "memory"
    defaults["m4"]["security"]["enabled"] = False
    defaults["m4"]["security"]["auth_required"] = False
    config = HierarchicalConfigAdapter(defaults=defaults)

    report = run_production_readiness(config, root_path=tmp_path)

    assert report.ready is True
    assert any(check.name == "security" and check.status == "warn" for check in report.checks)


def test_readiness_report_serializes_to_dict(tmp_path: Path) -> None:
    create_required_dirs(tmp_path)
    config = HierarchicalConfigAdapter(defaults=base_defaults(tmp_path))

    data = run_production_readiness(config, root_path=tmp_path).as_dict()

    assert data["environment"] == "production"
    assert data["ready"] is True
    assert {check["name"] for check in data["checks"]} >= {
        "environment",
        "persistence_mode",
        "security",
        "required_paths",
        "admin_assets",
    }
