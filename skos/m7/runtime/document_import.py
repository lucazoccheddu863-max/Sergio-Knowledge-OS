"""Safe local document ingestion for the executable M7 runtime."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile

from skos.m4.application.services.document_indexer_service import DocumentIndexerService


SUPPORTED_EXTENSIONS = frozenset({".json", ".md", ".txt"})


@dataclass(frozen=True)
class DocumentImportResult:
    status: str
    source_path: str
    archived_path: str
    sha256: str
    doc_id: str
    byte_count: int
    chunk_count: int

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


class DocumentImportService:
    """Archive an original local document and index its textual content."""

    def __init__(self, archive_root: str | Path, indexer: DocumentIndexerService) -> None:
        self._archive_root = Path(archive_root).expanduser().resolve()
        self._indexer = indexer

    def import_file(self, source_path: str | Path) -> DocumentImportResult:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Document not found: {source}")
        suffix = source.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported document type {suffix or '(none)'}; supported: {supported}")

        raw = source.read_bytes()
        digest = sha256(raw).hexdigest()
        text = self._extract_text(raw, suffix)
        if not text.strip():
            raise ValueError("Document contains no indexable text")

        archive_dir = self._archive_root / "imported" / digest[:2]
        archived = archive_dir / f"{digest}{suffix}"
        indexed_marker = archived.with_suffix(f"{suffix}.indexed")
        archived_exists = archived.is_file()
        duplicate = archived_exists and indexed_marker.is_file()
        if archived_exists and sha256(archived.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Archived document checksum mismatch: {archived}")
        if not archived_exists:
            self._archive_original(source, archived)

        doc_id = f"document:{digest}"
        chunk_count = 0
        if not duplicate:
            chunk_count = self._indexer.index_text(
                text,
                doc_id=doc_id,
                source_id=digest,
                metadata={
                    "doc_id": doc_id,
                    "sha256": digest,
                    "source_name": source.name,
                    "source_path": str(source),
                    "archived_path": str(archived),
                    "media_type": suffix.lstrip("."),
                },
            )
            indexed_marker.write_text(str(chunk_count), encoding="ascii")

        return DocumentImportResult(
            status="duplicate" if duplicate else "imported",
            source_path=str(source),
            archived_path=str(archived),
            sha256=digest,
            doc_id=doc_id,
            byte_count=len(raw),
            chunk_count=chunk_count,
        )

    @staticmethod
    def _extract_text(raw: bytes, suffix: str) -> str:
        try:
            decoded = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Document must use UTF-8 text encoding") from exc
        if suffix == ".json":
            try:
                data = json.loads(decoded)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON document: {exc.msg}") from exc
            return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        return decoded

    @staticmethod
    def _archive_original(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=".import-", dir=destination.parent)
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
