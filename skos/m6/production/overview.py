"""Admin overview aggregation for SKOS operations."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m6.production.backup import BackupManifest, build_backup_manifest
from skos.m6.production.readiness import ReadinessReport, run_production_readiness
from skos.m6.production.release import ReleaseStatus, build_release_status


@dataclass(frozen=True)
class AdminOverview:
    """Operator-facing snapshot for the admin console."""

    release: ReleaseStatus
    readiness: ReadinessReport
    backup: BackupManifest

    @property
    def ready(self) -> bool:
        return self.readiness.ready and self.backup.ready

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "release": self.release.as_dict(),
            "readiness": self.readiness.as_dict(),
            "backup": self.backup.as_dict(),
        }


@dataclass(frozen=True)
class AdminSmokeCheck:
    """Single operator smoke-check result."""

    name: str
    status: str
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class AdminSmokeReport:
    """Compact operator smoke report for the admin console."""

    checks: tuple[AdminSmokeCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "checks": [check.as_dict() for check in self.checks],
        }


def build_admin_overview(
    config: ConfigurationPort,
    root_path: str | Path = ".",
) -> AdminOverview:
    """Build a side-effect-free admin overview from existing production reports."""

    return AdminOverview(
        release=build_release_status(),
        readiness=run_production_readiness(config, root_path=root_path),
        backup=build_backup_manifest(config, root_path=root_path),
    )


def build_admin_smoke_report(
    config: ConfigurationPort,
    root_path: str | Path = ".",
) -> AdminSmokeReport:
    """Build a compact smoke report for operator-facing admin checks."""

    overview = build_admin_overview(config, root_path=root_path)
    checks = [
        _check_release(overview.release),
        _check_readiness(overview.readiness),
        _check_backup(overview.backup),
        _check_admin_console_assets(),
    ]
    return AdminSmokeReport(checks=tuple(checks))


def _check_release(release: ReleaseStatus) -> AdminSmokeCheck:
    if release.version == "unknown" or release.milestone == "unknown":
        return AdminSmokeCheck("release", "fail", "release metadata is unavailable")
    return AdminSmokeCheck("release", "pass", f"{release.version} ({release.milestone})")


def _check_readiness(readiness: ReadinessReport) -> AdminSmokeCheck:
    if readiness.ready:
        return AdminSmokeCheck("readiness", "pass", "production readiness checks pass")
    failed = [check.name for check in readiness.checks if not check.passed]
    return AdminSmokeCheck("readiness", "fail", "attention required: " + ", ".join(failed))


def _check_backup(backup: BackupManifest) -> AdminSmokeCheck:
    if backup.ready:
        return AdminSmokeCheck("backup", "pass", f"{backup.total_files} files addressable")
    return AdminSmokeCheck("backup", "fail", "; ".join(backup.warnings))


def _check_admin_console_assets() -> AdminSmokeCheck:
    try:
        assets = resources.files("skos.m5.admin_console.assets")
        for filename in ("index.html", "styles.css", "app.js"):
            if not assets.joinpath(filename).is_file():
                return AdminSmokeCheck("admin_console", "fail", f"missing asset: {filename}")
    except Exception as exc:
        return AdminSmokeCheck("admin_console", "fail", f"admin assets unavailable: {exc}")
    return AdminSmokeCheck("admin_console", "pass", "admin console assets are packaged")
