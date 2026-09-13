"""Backup manifest planning for SKOS production hardening."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skos.m4.infrastructure.ports.config_port import ConfigurationPort


@dataclass(frozen=True)
class BackupItem:
    """Single file or directory that belongs in a backup."""

    name: str
    path: str
    exists: bool
    file_count: int
    total_bytes: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "exists": self.exists,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
        }


@dataclass(frozen=True)
class BackupManifest:
    """Side-effect-free backup plan."""

    ready: bool
    destination: str
    items: tuple[BackupItem, ...]
    warnings: tuple[str, ...]

    @property
    def total_files(self) -> int:
        return sum(item.file_count for item in self.items)

    @property
    def total_bytes(self) -> int:
        return sum(item.total_bytes for item in self.items)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "destination": self.destination,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "warnings": list(self.warnings),
            "items": [item.as_dict() for item in self.items],
        }


def build_backup_manifest(
    config: ConfigurationPort,
    root_path: str | Path = ".",
) -> BackupManifest:
    """Build a side-effect-free backup manifest from configured storage paths."""

    root = Path(root_path)
    database_path = _resolve(root, _get_str(config, "database_path", ""))
    archive_root = _resolve(root, _get_str(config, "archive_root", ""))
    backup_dir = _resolve(root, _get_str(config, "backup_dir", ""))

    items = (
        _inspect_path("database", database_path),
        _inspect_path("archive", archive_root),
    )
    warnings = tuple(_collect_warnings(database_path, archive_root, backup_dir))
    return BackupManifest(
        ready=not warnings,
        destination=str(backup_dir),
        items=items,
        warnings=warnings,
    )


def _inspect_path(name: str, path: Path) -> BackupItem:
    if not path.exists():
        return BackupItem(name=name, path=str(path), exists=False, file_count=0, total_bytes=0)
    if path.is_file():
        return BackupItem(
            name=name,
            path=str(path),
            exists=True,
            file_count=1,
            total_bytes=path.stat().st_size,
        )

    file_count = 0
    total_bytes = 0
    for child in path.rglob("*"):
        if child.is_file():
            file_count += 1
            total_bytes += child.stat().st_size
    return BackupItem(
        name=name,
        path=str(path),
        exists=True,
        file_count=file_count,
        total_bytes=total_bytes,
    )


def _collect_warnings(database_path: Path, archive_root: Path, backup_dir: Path) -> list[str]:
    warnings: list[str] = []
    if not database_path.exists():
        warnings.append("database_path does not exist")
    if not archive_root.exists():
        warnings.append("archive_root does not exist")
    if not backup_dir.exists():
        warnings.append("backup_dir does not exist")
    elif not backup_dir.is_dir():
        warnings.append("backup_dir is not a directory")
    return warnings


def _resolve(root: Path, value: str) -> Path:
    path = Path(value) if value else Path()
    return path if path.is_absolute() else root / path


def _get_str(config: ConfigurationPort, path: str, default: str) -> str:
    value = config.get(path, default=default)
    return value if isinstance(value, str) else default
