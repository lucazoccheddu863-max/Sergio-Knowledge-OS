"""Tests for M6 release status metadata."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from skos.m6.production import build_release_status, create_release_package


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
