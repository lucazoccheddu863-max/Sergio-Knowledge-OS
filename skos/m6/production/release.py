"""Release status helpers for SKOS admin operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile


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


@dataclass(frozen=True)
class ReleasePackageInspection:
    """Side-effect-free inspection of a release ZIP package."""

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
class ReleaseReadinessGate:
    """Final operator gate before distributing a release package."""

    ready: bool
    release: ReleaseStatus
    package: ReleasePackageResult
    inspection: ReleasePackageInspection
    checks: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "release": self.release.as_dict(),
            "package": self.package.as_dict(),
            "inspection": self.inspection.as_dict(),
            "checks": list(self.checks),
            "warnings": list(self.warnings),
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


def inspect_release_package(archive_path: str | Path) -> ReleasePackageInspection:
    """Inspect a release ZIP and verify manifest, entries and SHA256 hashes."""

    path = Path(archive_path)
    if not path.exists():
        return ReleasePackageInspection(
            archive_path=str(path),
            ready=False,
            manifest={},
            entries=(),
            warnings=("release package does not exist",),
        )

    manifest: dict[str, Any] = {}
    warnings: list[str] = []
    try:
        with ZipFile(path) as archive:
            entries = tuple(sorted(name for name in archive.namelist() if not name.endswith("/")))
            if "release_manifest.json" not in entries:
                warnings.append("release_manifest.json missing from release package")
            else:
                loaded = json.loads(archive.read("release_manifest.json").decode("utf-8"))
                if isinstance(loaded, dict):
                    manifest = loaded
                else:
                    warnings.append("release_manifest.json is not an object")
            warnings.extend(_collect_release_package_warnings(archive, manifest, entries))
    except (BadZipFile, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ReleasePackageInspection(
            archive_path=str(path),
            ready=False,
            manifest={},
            entries=(),
            warnings=("release package is not a readable SKOS ZIP",),
        )

    return ReleasePackageInspection(
        archive_path=str(path),
        ready=not warnings,
        manifest=manifest,
        entries=entries,
        warnings=tuple(warnings),
    )


def run_release_readiness_gate(
    root_path: str | Path = ".",
    output_dir: str | Path = "data/releases",
    label: str | None = None,
) -> ReleaseReadinessGate:
    """Create and inspect a release package, then return one distribution verdict."""

    release = build_release_status(root_path)
    package = create_release_package(root_path=root_path, output_dir=output_dir, label=label)
    inspection = inspect_release_package(package.archive_path)
    warnings = list(inspection.warnings)
    checks = [
        f"release metadata: {release.version} ({release.milestone})",
        f"package archive: {package.archive_path}",
        f"package entries: {len(inspection.entries)}",
    ]

    if release.version == "unknown" or release.milestone == "unknown":
        warnings.append("release metadata is unavailable")
    if inspection.manifest.get("version") != release.version:
        warnings.append("release package version does not match current VERSION")
    if inspection.manifest.get("milestone") != release.milestone:
        warnings.append("release package milestone does not match current release milestone")

    return ReleaseReadinessGate(
        ready=not warnings,
        release=release,
        package=package,
        inspection=inspection,
        checks=tuple(checks),
        warnings=tuple(warnings),
    )


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


def _collect_release_package_warnings(
    archive: ZipFile,
    manifest: dict[str, Any],
    entries: tuple[str, ...],
) -> list[str]:
    warnings: list[str] = []
    if not manifest:
        return warnings

    files = manifest.get("files")
    if not isinstance(files, list):
        return ["release manifest files list missing"]

    entry_set = set(entries)
    if "VERSION" not in entry_set:
        warnings.append("VERSION missing from release package")
    if "README.md" not in entry_set:
        warnings.append("README.md missing from release package")
    if any(entry.startswith("data/") for entry in entries):
        warnings.append("local data entries must not be included")
    if any("__pycache__" in entry or entry.endswith(".pyc") for entry in entries):
        warnings.append("cache or bytecode entries must not be included")

    manifest_paths = set()
    for file_info in files:
        if not isinstance(file_info, dict):
            warnings.append("release manifest contains a non-object file entry")
            continue
        file_path = file_info.get("path")
        expected_sha = file_info.get("sha256")
        expected_size = file_info.get("size_bytes")
        if not isinstance(file_path, str):
            warnings.append("release manifest file entry missing path")
            continue
        manifest_paths.add(file_path)
        if file_path not in entry_set:
            warnings.append(f"{file_path} missing from release package")
            continue
        content = archive.read(file_path)
        actual_sha = hashlib.sha256(content).hexdigest()
        if actual_sha != expected_sha:
            warnings.append(f"{file_path} sha256 mismatch")
        if len(content) != expected_size:
            warnings.append(f"{file_path} size mismatch")

    extra_entries = entry_set - manifest_paths - {"release_manifest.json"}
    if extra_entries:
        warnings.append("release package contains entries not listed in manifest")
    return warnings
