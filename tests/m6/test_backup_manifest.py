"""Tests for M6 backup and restore inspection."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production import (
    build_backup_manifest,
    create_backup_archive,
    inspect_backup_archive,
    stage_backup_restore,
)


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


def test_inspect_backup_archive_accepts_valid_archive(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")

    result = create_backup_archive(config_for(tmp_path), root_path=tmp_path)
    inspection = inspect_backup_archive(result.archive_path)

    assert inspection.ready is True
    assert inspection.warnings == ()
    assert "manifest.json" in inspection.entries
    assert inspection.manifest["ready"] is True


def test_inspect_backup_archive_warns_when_manifest_is_missing(tmp_path: Path) -> None:
    archive_path = tmp_path / "broken.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("database/sergio.db", "database")

    inspection = inspect_backup_archive(archive_path)

    assert inspection.ready is False
    assert "manifest.json missing from backup archive" in inspection.warnings


def test_inspect_backup_archive_warns_when_database_entry_is_missing(tmp_path: Path) -> None:
    manifest = {
        "ready": True,
        "items": [
            {
                "name": "database",
                "path": str(tmp_path / "data" / "sergio.db"),
                "exists": True,
                "file_count": 1,
                "total_bytes": 8,
            },
            {
                "name": "archive",
                "path": str(tmp_path / "archive"),
                "exists": True,
                "file_count": 1,
                "total_bytes": 12,
            },
        ],
    }
    archive_path = tmp_path / "incomplete.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("archive/chat.txt", "archive-item")

    inspection = inspect_backup_archive(archive_path)

    assert inspection.ready is False
    assert "database entry missing from backup archive" in inspection.warnings


def test_stage_backup_restore_extracts_to_empty_target(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")
    result = create_backup_archive(config_for(tmp_path), root_path=tmp_path)

    restore = stage_backup_restore(result.archive_path, tmp_path / "restore-stage")

    target = Path(restore.target_dir)
    assert restore.inspection.ready is True
    assert (target / "manifest.json").exists()
    assert (target / "database" / "sergio.db").read_text(encoding="utf-8") == "database"
    assert (target / "archive" / "chat.txt").read_text(encoding="utf-8") == "archive-item"
    assert len(restore.extracted_files) == 3


def test_stage_backup_restore_refuses_non_empty_target(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "data" / "sergio.db").write_text("database", encoding="utf-8")
    (tmp_path / "archive" / "chat.txt").write_text("archive-item", encoding="utf-8")
    result = create_backup_archive(config_for(tmp_path), root_path=tmp_path)
    target = tmp_path / "restore-stage"
    target.mkdir()
    (target / "existing.txt").write_text("keep-me", encoding="utf-8")

    try:
        stage_backup_restore(result.archive_path, target)
    except ValueError as exc:
        assert "restore target directory must be empty" in str(exc)
    else:
        raise AssertionError("expected staged restore to refuse non-empty target")
    assert (target / "existing.txt").read_text(encoding="utf-8") == "keep-me"


def test_stage_backup_restore_refuses_unready_archive(tmp_path: Path) -> None:
    archive_path = tmp_path / "broken.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("database/sergio.db", "database")

    try:
        stage_backup_restore(archive_path, tmp_path / "restore-stage")
    except ValueError as exc:
        assert "backup archive is not ready for restore" in str(exc)
    else:
        raise AssertionError("expected staged restore to refuse unready archive")
    assert not (tmp_path / "restore-stage").exists()


def test_stage_backup_restore_blocks_zip_path_traversal(tmp_path: Path) -> None:
    manifest = {
        "ready": True,
        "items": [
            {
                "name": "database",
                "path": str(tmp_path / "data" / "sergio.db"),
                "exists": True,
                "file_count": 1,
                "total_bytes": 8,
            }
        ],
    }
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("database/sergio.db", "database")
        archive.writestr("../outside.txt", "unsafe")

    try:
        stage_backup_restore(archive_path, tmp_path / "restore-stage")
    except ValueError as exc:
        assert "unsafe path" in str(exc)
    else:
        raise AssertionError("expected staged restore to block unsafe paths")
    assert not (tmp_path / "outside.txt").exists()
