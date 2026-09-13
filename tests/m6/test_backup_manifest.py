"""Tests for M6.3 backup manifest planning."""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production import build_backup_manifest, create_backup_archive


def config_for(tmp_path: Path) -> HierarchicalConfigAdapter:
    return HierarchicalConfigAdapter(
        defaults={
            "database_path": str(tmp_path / "data" / "sergio.db"),
            "archive_root": str(tmp_path / "archive"),
            "backup_dir": str(tmp_path / "backups"),
        }
    )


def test_backup_manifest_reports_database_and_archive_sizes(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")

    manifest = build_backup_manifest(config_for(tmp_path), root_path=tmp_path)

    assert manifest.ready is True
    assert manifest.total_files == 2
    assert manifest.total_bytes == len("database") + len("archive-item")
    assert manifest.warnings == ()


def test_backup_manifest_warns_for_missing_paths(tmp_path: Path) -> None:
    manifest = build_backup_manifest(config_for(tmp_path), root_path=tmp_path)

    assert manifest.ready is False
    assert "database_path does not exist" in manifest.warnings
    assert "archive_root does not exist" in manifest.warnings
    assert "backup_dir does not exist" in manifest.warnings


def test_backup_manifest_serializes_to_dict(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("db", encoding="utf-8")

    data = build_backup_manifest(config_for(tmp_path), root_path=tmp_path).as_dict()

    assert data["ready"] is True
    assert data["total_files"] == 1
    assert {item["name"] for item in data["items"]} == {"database", "archive"}


def test_backup_manifest_does_not_create_missing_backup_dir(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("db", encoding="utf-8")

    manifest = build_backup_manifest(config_for(tmp_path), root_path=tmp_path)

    assert manifest.ready is False
    assert not (tmp_path / "backups").exists()


def test_create_backup_archive_writes_zip_with_manifest(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")

    result = create_backup_archive(config_for(tmp_path), root_path=tmp_path, label="Sergio Test")

    archive_path = Path(result.archive_path)
    assert archive_path.exists()
    assert archive_path.parent == tmp_path / "backups"
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert "database/sergio.db" in names
    assert "archive/chat.txt" in names


def test_create_backup_archive_fails_when_manifest_not_ready(tmp_path: Path) -> None:
    try:
        create_backup_archive(config_for(tmp_path), root_path=tmp_path)
    except ValueError as exc:
        assert "backup manifest is not ready" in str(exc)
    else:
        raise AssertionError("expected backup creation to fail")
