"""Backup and restore inspection for SKOS production hardening."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

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


@dataclass(frozen=True)
class BackupResult:
    """Result of a completed backup package creation."""

    archive_path: str
    manifest: BackupManifest

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "manifest": self.manifest.as_dict(),
        }


@dataclass(frozen=True)
class BackupArchiveInspection:
    """Side-effect-free inspection of a backup archive before restore."""

    archive_path: str
    ready: bool
    manifest: dict[str, Any]
    entries: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "ready": self.ready,
            "manifest": self.manifest,
            "entries": list(self.entries),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class BackupRestoreResult:
    """Result of a staged backup restore extraction."""

    archive_path: str
    target_dir: str
    extracted_files: tuple[str, ...]
    inspection: BackupArchiveInspection

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "target_dir": self.target_dir,
            "extracted_files": list(self.extracted_files),
            "inspection": self.inspection.as_dict(),
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


def create_backup_archive(
    config: ConfigurationPort,
    root_path: str | Path = ".",
    label: str | None = None,
) -> BackupResult:
    """Create a ZIP backup package when the backup manifest is ready."""

    manifest = build_backup_manifest(config, root_path=root_path)
    if not manifest.ready:
        raise ValueError("backup manifest is not ready: " + "; ".join(manifest.warnings))

    destination = Path(manifest.destination)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label or "skos")
    archive_path = destination / f"{safe_label}-backup-{timestamp}.zip"

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest.as_dict(), indent=2, sort_keys=True))
        for item in manifest.items:
            _write_item(archive, item)

    return BackupResult(archive_path=str(archive_path), manifest=manifest)


def inspect_backup_archive(archive_path: str | Path) -> BackupArchiveInspection:
    """Inspect a backup ZIP without extracting or modifying local data."""

    path = Path(archive_path)
    warnings: list[str] = []
    manifest: dict[str, Any] = {}
    entries: tuple[str, ...] = ()

    if not path.exists():
        return BackupArchiveInspection(
            archive_path=str(path),
            ready=False,
            manifest=manifest,
            entries=entries,
            warnings=("backup archive does not exist",),
        )

    try:
        with ZipFile(path) as archive:
            entries = tuple(sorted(name for name in archive.namelist() if not name.endswith("/")))
            if "manifest.json" not in entries:
                warnings.append("manifest.json missing from backup archive")
            else:
                loaded = json.loads(archive.read("manifest.json").decode("utf-8"))
                if isinstance(loaded, dict):
                    manifest = loaded
                else:
                    warnings.append("manifest.json is not an object")
    except (BadZipFile, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return BackupArchiveInspection(
            archive_path=str(path),
            ready=False,
            manifest=manifest,
            entries=entries,
            warnings=("backup archive is not a readable SKOS ZIP",),
        )

    warnings.extend(_collect_archive_warnings(manifest, entries))
    return BackupArchiveInspection(
        archive_path=str(path),
        ready=not warnings,
        manifest=manifest,
        entries=entries,
        warnings=tuple(warnings),
    )


def stage_backup_restore(
    archive_path: str | Path,
    target_dir: str | Path,
) -> BackupRestoreResult:
    """Extract a verified backup into an empty staging directory."""

    inspection = inspect_backup_archive(archive_path)
    if not inspection.ready:
        raise ValueError("backup archive is not ready for restore: " + "; ".join(inspection.warnings))

    target = Path(target_dir)
    if target.exists() and any(target.iterdir()):
        raise ValueError("restore target directory must be empty")
    target.mkdir(parents=True, exist_ok=True)

    extracted: list[str] = []
    with ZipFile(inspection.archive_path) as archive:
        destinations = tuple(_safe_extract_destination(target, entry) for entry in inspection.entries)
        for entry, destination in zip(inspection.entries, destinations, strict=True):
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, destination.open("wb") as output:
                output.write(source.read())
            extracted.append(str(destination))

    return BackupRestoreResult(
        archive_path=inspection.archive_path,
        target_dir=str(target),
        extracted_files=tuple(extracted),
        inspection=inspection,
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


def _write_item(archive: ZipFile, item: BackupItem) -> None:
    source = Path(item.path)
    if not source.exists():
        return
    if source.is_file():
        archive.write(source, arcname=f"{item.name}/{source.name}")
        return
    for child in sorted(source.rglob("*")):
        if child.is_file():
            archive.write(child, arcname=f"{item.name}/{child.relative_to(source)}")


def _safe_label(label: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in label).strip("-")
    return cleaned or "skos"


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


def _collect_archive_warnings(manifest: dict[str, Any], entries: tuple[str, ...]) -> list[str]:
    warnings: list[str] = []
    if not manifest:
        return warnings
    if manifest.get("ready") is not True:
        warnings.append("manifest is not ready")

    items = manifest.get("items")
    if not isinstance(items, list):
        warnings.append("manifest items are missing")
        return warnings

    for item in items:
        if not isinstance(item, dict):
            warnings.append("manifest item is not an object")
            continue
        name = item.get("name")
        exists = item.get("exists") is True
        file_count = item.get("file_count") if isinstance(item.get("file_count"), int) else 0
        if not exists or file_count <= 0:
            continue
        if name == "database":
            database_name = Path(str(item.get("path", ""))).name
            if database_name and f"database/{database_name}" not in entries:
                warnings.append("database entry missing from backup archive")
        elif name == "archive" and not any(entry.startswith("archive/") for entry in entries):
            warnings.append("archive entries missing from backup archive")
    return warnings


def _safe_extract_destination(target: Path, entry: str) -> Path:
    path = Path(entry)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("backup archive contains an unsafe path")
    destination = target / path
    resolved_target = target.resolve()
    resolved_destination = destination.resolve()
    if resolved_target != resolved_destination and resolved_target not in resolved_destination.parents:
        raise ValueError("backup archive contains an unsafe path")
    return destination


def _resolve(root: Path, value: str) -> Path:
    path = Path(value) if value else Path()
    return path if path.is_absolute() else root / path


def _get_str(config: ConfigurationPort, path: str, default: str) -> str:
    value = config.get(path, default=default)
    return value if isinstance(value, str) else default
