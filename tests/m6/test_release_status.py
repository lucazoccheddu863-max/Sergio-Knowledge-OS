"""Tests for M6 release status metadata."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from skos.m6.production import (
    build_release_status,
    create_release_package,
    inspect_release_package,
    run_release_readiness_gate,
)


def current_version() -> str:
    return Path("VERSION").read_text(encoding="utf-8").strip()


def test_release_status_reads_current_version() -> None:
    status = build_release_status()

    assert status.version == current_version()
    assert status.milestone.startswith("M6.")
    assert status.status == "operational"


def test_release_status_serializes_to_dict() -> None:
    data = build_release_status().as_dict()

    assert data["version"] == current_version()
    assert data["milestone"].startswith("M6.")
    assert data["status"] == "operational"


def test_create_release_package_writes_clean_zip(tmp_path: Path) -> None:
    result = create_release_package(output_dir=tmp_path, label="Sergio Release")

    archive_path = Path(result.archive_path)
    assert archive_path.exists()
    assert archive_path.parent == tmp_path
    assert result.manifest.version == current_version()
    assert result.manifest.milestone.startswith("M6.")

    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())

    assert "release_manifest.json" in names
    assert "VERSION" in names
    assert "README.md" in names
    assert "skos/m6/production/release.py" in names
    assert not any("__pycache__" in name for name in names)
    assert not any(name.startswith("data/") for name in names)


def test_release_package_manifest_contains_file_hashes(tmp_path: Path) -> None:
    result = create_release_package(output_dir=tmp_path)

    with ZipFile(result.archive_path) as archive:
        manifest = json.loads(archive.read("release_manifest.json").decode("utf-8"))

    assert manifest["version"] == current_version()
    assert manifest["total_files"] > 0
    version_file = next(file for file in manifest["files"] if file["path"] == "VERSION")
    assert len(version_file["sha256"]) == 64
    assert version_file["size_bytes"] == len(Path("VERSION").read_bytes())


def test_inspect_release_package_accepts_valid_archive(tmp_path: Path) -> None:
    result = create_release_package(output_dir=tmp_path)

    inspection = inspect_release_package(result.archive_path)

    assert inspection.ready is True
    assert inspection.warnings == ()
    assert "release_manifest.json" in inspection.entries
    assert inspection.manifest["version"] == current_version()


def test_inspect_release_package_warns_for_missing_manifest(tmp_path: Path) -> None:
    archive_path = tmp_path / "broken-release.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("VERSION", current_version())

    inspection = inspect_release_package(archive_path)

    assert inspection.ready is False
    assert "release_manifest.json missing from release package" in inspection.warnings


def test_inspect_release_package_warns_for_hash_mismatch(tmp_path: Path) -> None:
    result = create_release_package(output_dir=tmp_path)
    archive_path = tmp_path / "tampered-release.zip"
    with ZipFile(result.archive_path) as source, ZipFile(archive_path, "w") as target:
        for name in source.namelist():
            content = b"tampered" if name == "VERSION" else source.read(name)
            target.writestr(name, content)

    inspection = inspect_release_package(archive_path)

    assert inspection.ready is False
    assert "VERSION sha256 mismatch" in inspection.warnings


def test_release_readiness_gate_creates_and_inspects_package(tmp_path: Path) -> None:
    gate = run_release_readiness_gate(output_dir=tmp_path, label="gate-test")

    assert gate.ready is True
    assert gate.warnings == ()
    assert Path(gate.package.archive_path).exists()
    assert gate.inspection.ready is True
    assert gate.release.version == current_version()


def test_release_readiness_gate_serializes_to_dict(tmp_path: Path) -> None:
    data = run_release_readiness_gate(output_dir=tmp_path).as_dict()

    assert data["ready"] is True
    assert data["release"]["version"] == current_version()
    assert data["package"]["archive_path"].endswith("-release.zip")
    assert data["inspection"]["ready"] is True
    assert data["warnings"] == []
