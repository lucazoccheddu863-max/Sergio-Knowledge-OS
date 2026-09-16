"""Admin overview aggregation for SKOS operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m6.production.backup import BackupManifest, build_backup_manifest
from skos.m6.production.launch import LocalLaunchPlan, build_local_launch_plan
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


@dataclass(frozen=True)
class OperatorSnapshot:
    """Single operator-facing readiness snapshot for local operation."""

    generated_at: str
    verdict: str
    summary: str
    release: ReleaseStatus
    readiness: ReadinessReport
    backup: BackupManifest
    smoke: AdminSmokeReport
    launch: LocalLaunchPlan
    next_actions: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.verdict == "ready"

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "ready": self.ready,
            "verdict": self.verdict,
            "summary": self.summary,
            "release": self.release.as_dict(),
            "readiness": self.readiness.as_dict(),
            "backup": self.backup.as_dict(),
            "smoke": self.smoke.as_dict(),
            "launch": self.launch.as_dict(),
            "next_actions": list(self.next_actions),
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


def build_operator_snapshot(
    config: ConfigurationPort,
    root_path: str | Path = ".",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> OperatorSnapshot:
    """Build a compact, read-only snapshot for the local operator console."""

    release = build_release_status(root_path)
    readiness = run_production_readiness(config, root_path=root_path)
    backup = build_backup_manifest(config, root_path=root_path)
    smoke = AdminSmokeReport(
        checks=(
            _check_release(release),
            _check_readiness(readiness),
            _check_backup(backup),
            _check_admin_console_assets(),
        )
    )
    launch = build_local_launch_plan(root_path=root_path, host=host, port=port)
    next_actions = _build_next_actions(readiness, backup, launch)
    verdict = "ready" if readiness.ready and backup.ready and smoke.ready and launch.ready else "attention"
    summary = (
        "System ready for local operation"
        if verdict == "ready"
        else "Operator attention required before local operation"
    )
    return OperatorSnapshot(
        generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        verdict=verdict,
        summary=summary,
        release=release,
        readiness=readiness,
        backup=backup,
        smoke=smoke,
        launch=launch,
        next_actions=tuple(next_actions),
    )


def render_operator_snapshot_report(snapshot: OperatorSnapshot) -> str:
    """Render an operator snapshot as a portable plain-text report."""

    lines = [
        "Sergio Knowledge OS - Operator Snapshot",
        "=" * 39,
        f"Generated: {snapshot.generated_at}",
        f"Verdict: {snapshot.verdict.upper()}",
        f"Summary: {snapshot.summary}",
        f"Version: {snapshot.release.version}",
        f"Milestone: {snapshot.release.milestone}",
        f"Launch: {snapshot.launch.command}",
        "",
        "Checks",
        "------",
    ]
    lines.extend(
        f"[{check.status.upper()}] {check.name}: {check.message}"
        for check in snapshot.smoke.checks
    )
    lines.extend(["", "Next actions", "------------"])
    lines.extend(f"- {action}" for action in snapshot.next_actions)
    return "\n".join(lines) + "\n"


def _build_next_actions(
    readiness: ReadinessReport,
    backup: BackupManifest,
    launch: LocalLaunchPlan,
) -> list[str]:
    actions: list[str] = []
    if not readiness.ready:
        failed = [check.name for check in readiness.checks if not check.passed]
        actions.append("Review readiness checks: " + ", ".join(failed))
    if not backup.ready:
        actions.append("Prepare backup inputs: " + "; ".join(backup.warnings))
    if not launch.ready:
        failed = [check.name for check in launch.checks if not check.passed]
        actions.append("Fix local launch checks: " + ", ".join(failed))
    if not actions:
        actions.append("Run the local launch command and open the admin console")
        actions.append("Create a fresh backup before importing important data")
    return actions


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
