"""End-to-end tests for M7 local document ingestion."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skos.m4.domain.query_orchestrator_models import UnifiedQuery
from skos.m7.runtime.document_import import DocumentImportService
from tests.m7.test_application_runtime import build_test_runtime


def test_import_archives_indexes_and_finds_document(tmp_path: Path) -> None:
    source = tmp_path / "knowledge.md"
    source.write_text("Sergio conserva conoscenza verificabile.\n\nRicerca locale affidabile.", encoding="utf-8")
    runtime = build_test_runtime(tmp_path)

    result = runtime.document_import.import_file(source)

    assert result.status == "imported"
    assert result.chunk_count == 2
    assert Path(result.archived_path).read_bytes() == source.read_bytes()
    assert len(runtime.vector_store.records) == 2
    assert runtime.vector_store.records[0].metadata["source_name"] == "knowledge.md"
    search = runtime.orchestrator.execute(UnifiedQuery(text="conoscenza", mode="semantic"))
    assert search.semantic_result is not None
    assert search.semantic_result.results[0].text == "Sergio conserva conoscenza verificabile."


def test_markdown_import_keeps_heading_with_section_body(tmp_path: Path) -> None:
    source = tmp_path / "roadmap.md"
    source.write_text(
        "# Roadmap\n\nIntro.\n\n## Milestone 7\n\n- Importazione\n- Ricerca\n\n## Future\n\nLater.",
        encoding="utf-8",
    )
    runtime = build_test_runtime(tmp_path)

    result = runtime.document_import.import_file(source)

    assert result.chunk_count == 3
    milestone = runtime.vector_store.records[1]
    assert "## Milestone 7" in milestone.text
    assert "- Importazione" in milestone.text
    assert "- Ricerca" in milestone.text


def test_duplicate_content_is_not_archived_or_indexed_twice(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("Identical durable knowledge", encoding="utf-8")
    second.write_bytes(first.read_bytes())
    runtime = build_test_runtime(tmp_path)

    imported = runtime.document_import.import_file(first)
    record_count = len(runtime.vector_store.records)
    duplicate = runtime.document_import.import_file(second)

    assert duplicate.status == "duplicate"
    assert duplicate.archived_path == imported.archived_path
    assert duplicate.chunk_count == 0
    assert len(runtime.vector_store.records) == record_count


def test_new_index_generation_reindexes_preserved_archive(tmp_path: Path) -> None:
    source = tmp_path / "knowledge.txt"
    source.write_text("Versioned local knowledge", encoding="utf-8")
    first_runtime = build_test_runtime(tmp_path)
    legacy_import = DocumentImportService(
        tmp_path / "data" / "archive",
        first_runtime.document_indexer,
    )
    legacy_import.import_file(source)
    second_runtime = build_test_runtime(tmp_path)
    versioned_import = DocumentImportService(
        tmp_path / "data" / "archive",
        second_runtime.document_indexer,
        index_generation="m7_9",
    )

    result = versioned_import.import_file(source)

    assert result.status == "imported"
    assert result.chunk_count == 1


def test_unsupported_document_is_rejected_without_archive(tmp_path: Path) -> None:
    source = tmp_path / "binary.pdf"
    source.write_bytes(b"not a supported document")
    runtime = build_test_runtime(tmp_path)

    with pytest.raises(ValueError, match="Unsupported document type"):
        runtime.document_import.import_file(source)

    assert not (tmp_path / "data" / "archive").exists()


def test_import_api_exposes_structured_result_and_errors(tmp_path: Path) -> None:
    source = tmp_path / "notes.json"
    source.write_text('{"topic": "local knowledge"}', encoding="utf-8")
    client = TestClient(build_test_runtime(tmp_path).app)

    response = client.post("/api/v1/admin/import/file", params={"source_path": str(source)})
    missing = client.post(
        "/api/v1/admin/import/file",
        params={"source_path": str(tmp_path / "missing.txt")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "imported"
    assert response.json()["chunk_count"] == 1
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "HTTP_404"


def test_upload_api_archives_indexes_and_deduplicates_bytes(tmp_path: Path) -> None:
    runtime = build_test_runtime(tmp_path)
    client = TestClient(runtime.app)
    content = b"Knowledge uploaded from the admin console"

    imported = client.post(
        "/api/v1/admin/import/upload",
        params={"filename": "console-note.txt"},
        content=content,
        headers={"content-type": "application/octet-stream"},
    )
    duplicate = client.post(
        "/api/v1/admin/import/upload",
        params={"filename": "renamed-note.txt"},
        content=content,
        headers={"content-type": "application/octet-stream"},
    )

    assert imported.status_code == 200
    assert imported.json()["status"] == "imported"
    assert Path(imported.json()["archived_path"]).read_bytes() == content
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"


def test_upload_api_rejects_unsupported_extension(tmp_path: Path) -> None:
    client = TestClient(build_test_runtime(tmp_path).app)

    response = client.post(
        "/api/v1/admin/import/upload",
        params={"filename": "manual.pdf"},
        content=b"unsupported",
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "HTTP_400"
