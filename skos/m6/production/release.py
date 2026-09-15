"""Release status helpers for SKOS admin operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile


@dataclass(frozen=True)
class ReleaseStatus:
    """Current local release metadata for operator-facing status panels."""

    version: str
    milestone: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "milestone": self.milestone,
            "status": self.status,
        }


@dataclass(frozen=True)
class ReleasePackageFile:
    """Single file included in a clean source release package."""

    path: str
    sha256: str
    size_bytes: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class ReleasePackageManifest:
    """Manifest embedded in a clean release archive."""

    version: str
    milestone: str
    created_at: str
    files: tuple[ReleasePackageFile, ...]

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(file.size_bytes for file in self.files)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "milestone": self.milestone,
            "created_at": self.created_at,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "files": [file.as_dict() for file in self.files],
        }


@dataclass(frozen=True)
class ReleasePackageResult:
    """Result of creating a clean release ZIP package."""

    archive_path: str
    manifest: ReleasePackageManifest

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "manifest": self.manifest.as_dict(),
        }


def build_release_status(root_path: str | Path = ".") -> ReleaseStatus:
    """Build release metadata without changing the frozen public API status contract."""

    root = Path(root_path)
    version = _read_version(root)
    return ReleaseStatus(
        version=version,
        milestone=_derive_milestone(version),
        status="operational",
    )


def create_release_package(
    root_path: str | Path = ".",
    output_dir: str | Path = "data/releases",
    label: str | None = None,
) -> ReleasePackageResult:
    """Create a clean source release ZIP with a manifest and per-file hashes."""

    root = Path(root_path).resolve()
    destination = _resolve_output_dir(root, output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    status = build_release_status(root)
    created_at = datetime.now(timezone.utc).isoformat()
    source_files = tuple(_collect_release_files(root))
    package_files = tuple(_package_file(root, path) for path in source_files)
    manifest = ReleasePackageManifest(
        version=status.version,
        milestone=status.milestone,
        created_at=created_at,
        files=package_files,
    )

    safe_label = _safe_label(label or f"skos-{status.version}")
    archive_path = destination / f"{safe_label}-release.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "release_manifest.json",
            json.dumps(manifest.as_dict(), indent=2, sort_keys=True),
        )
        for path in source_files:
            archive.write(path, path.relative_to(root).as_posix())

    return ReleasePackageResult(archive_path=str(archive_path), manifest=manifest)


def _read_version(root: Path) -> str:
    version_path = root / "VERSION"
    if not version_path.exists():
        return "unknown"
    return version_path.read_text(encoding="utf-8").strip() or "unknown"


def _derive_milestone(version: str) -> str:
    if version.startswith("0.6.0-alpha"):
        suffix = version.removeprefix("0.6.0-alpha")
        if suffix.isdigit():
            return f"M6.{suffix}"
    if version.startswith("0.5.0-alpha"):
        suffix = version.removeprefix("0.5.0-alpha")
        if suffix.isdigit():
            return f"M5.{suffix}"
    if version == "0.4.0":
        return "M4.12"
    return "unknown"


def _resolve_output_dir(root: Path, output_dir: str | Path) -> Path:
    output = Path(output_dir)
    if output.is_absolute():
        return output
    return root / output


def _collect_release_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    root_files = (
        "VERSION",
        "README.md",
        "CHANGELOG.md",
        "TEST_REPORT.txt",
        "SHA256SUMS",
        "pyproject.toml",
        "requirements.txt",
        "config.yaml",
        "schema_v1.sql",
        "SBOM.json",
    )
    for name in root_files:
        path = root / name
        if path.is_file():
            paths.append(path)

    for pattern in ("setup_milestone*.py", "verify_milestone*.py"):
        paths.extend(path for path in root.glob(pattern) if path.is_file())

    for directory in ("skos", "tests", "docs", "config", "MILESTONES"):
        base = root / directory
        if base.exists():
            paths.extend(_walk_clean_files(base))

    return sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())


def _walk_clean_files(base: Path) -> list[Path]:
    files: list[Path] = []
    for path in base.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        parts = set(path.parts)
        if "__pycache__" in parts or ".pytest_cache" in parts:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return files


def _package_file(root: Path, path: Path) -> ReleasePackageFile:
    content = path.read_bytes()
    return ReleasePackageFile(
        path=path.relative_to(root).as_posix(),
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
    )


def _safe_label(label: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in label).strip("-")
    return safe or "skos"
