"""End-to-end tests for M7 local document ingestion."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skos.m4.domain.query_orchestrator_models import UnifiedQuery
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
