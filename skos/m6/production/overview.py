"""Admin overview aggregation for SKOS operations."""
from __future__ import annotations

from dataclasses import dataclass
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
