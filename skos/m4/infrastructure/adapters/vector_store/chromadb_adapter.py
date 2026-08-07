"""ChromaDB adapter for VectorStorePort.

Handles collection name sanitization and empty metadata normalization
to avoid ChromaDB runtime errors.
"""
from __future__ import annotations

import re
import time
from typing import Any

from skos.m4.domain.vector_models import VectorQuery, VectorRecord, SearchResult
from skos.m4.infrastructure.ports.vector_store_port import (
    CollectionNotFoundError,
    VectorStorePort,
    VectorStoreError,
)


class ChromaDBAdapter(VectorStorePort):
    """ChromaDB implementation of VectorStorePort.

    Uses an in-memory or persistent ChromaDB client.
    Collection names are automatically sanitised to comply with
    ChromaDB naming rules (alphanumeric, underscore, hyphen; max 63 chars).
    Empty metadata dicts are normalised to None to prevent ChromaDB errors.
    """

    def __init__(self, persist_directory: str | None = None) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreError("chromadb is not installed") from exc

        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.Client()

    @staticmethod
    def _sanitize_collection_name(name: str) -> str:
        """Sanitise a collection name for ChromaDB.

        Rules (ChromaDB >= 1.5):
        - Only alphanumeric, underscore, hyphen, dot allowed
        - 3-512 characters
        - Must start and end with [a-zA-Z0-9]
        """
        # Replace spaces and invalid chars with underscore
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
        # Ensure it starts with a letter or digit
        if sanitized and not sanitized[0].isalnum():
            sanitized = "x" + sanitized
        # Remove trailing non-alphanumeric chars
        sanitized = sanitized.rstrip("_.-")
        # Truncate to 63 chars (keep well under 512)
        sanitized = sanitized[:63]
        # Ensure not empty and ends with alphanumeric
        if not sanitized or not sanitized[-1].isalnum():
            sanitized = "coll"
        # Ensure minimum length of 3
        while len(sanitized) < 3:
            sanitized += "x"
        return sanitized

    @staticmethod
    def _normalize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        """Normalise metadata to avoid ChromaDB empty-dict errors.

        ChromaDB rejects empty dicts as metadata. Return None instead.
        """
        if not metadata:
            return None
        return metadata

    def get_collection(self, collection_name: str) -> Any:
        name = self._sanitize_collection_name(collection_name)
        try:
            return self._client.get_collection(name=name)
        except Exception:
            # Collection does not exist — create it
            return self._client.create_collection(name=name)

    def list_collections(self) -> list[str]:
        cols = self._client.list_collections()
        # ChromaDB may return Collection objects or strings depending on version
        result: list[str] = []
        for c in cols:
            if isinstance(c, str):
                result.append(c)
            else:
                result.append(getattr(c, "name", str(c)))
        return result

    def delete_collection(self, collection_name: str) -> None:
        name = self._sanitize_collection_name(collection_name)
        try:
            self._client.delete_collection(name=name)
        except Exception as exc:
            raise CollectionNotFoundError(f"Collection {name} not found") from exc

    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        collection = self.get_collection(collection_name)
        ids = [r.id for r in records]
        embeddings = [r.vector for r in records]
        documents = [r.text for r in records]
        metadatas = [self._normalize_metadata(r.metadata) for r in records]
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, collection_name: str, query: VectorQuery) -> SearchResult:
        start = time.perf_counter()
        collection = self.get_collection(collection_name)
        where_filter = self._normalize_metadata(query.filter_metadata) if query.filter_metadata else None
        results = collection.query(
            query_embeddings=[query.vector],
            n_results=query.top_k,
            where=where_filter,
            include=["metadatas", "documents", "distances"],
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        records: list[VectorRecord] = []
        total_found = 0
        if results and results.get("ids") and results["ids"]:
            ids = results["ids"][0]
            docs = results.get("documents", [[]])[0] if results.get("documents") else []
            metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            total_found = len(ids)
            for i, rid in enumerate(ids):
                meta = metas[i] if i < len(metas) and metas[i] is not None else {}
                text = docs[i] if i < len(docs) and docs[i] is not None else ""
                records.append(VectorRecord(
                    id=rid,
                    vector=[],  # ChromaDB does not return vectors by default in query
                    text=text,
                    metadata=meta,
                ))
        return SearchResult(records=records, total_found=total_found, query_time_ms=elapsed_ms)

    def delete(self, collection_name: str, ids: list[str]) -> None:
        if not ids:
            return
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids)

    def health_check(self) -> bool:
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False
