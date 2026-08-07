"""Application service for vector store operations."""
from __future__ import annotations

from typing import Any

from skos.m4.domain.chunking import TextChunk
from skos.m4.domain.vector_models import VectorQuery, VectorRecord, SearchResult
from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort


class VectorStoreService:
    """High-level service for indexing and searching vector data.

    Bridges the embedding pipeline (M4.3) with the vector database (M4.4).
    """

    def __init__(self, vector_store: VectorStorePort) -> None:
        self._store = vector_store

    def index_chunks(
        self,
        collection_name: str,
        chunks: list[TextChunk],
        vectors: list[list[float]],
    ) -> None:
        """Index text chunks with their embeddings.

        Args:
            collection_name: Target collection (sanitised by adapter).
            chunks: Text chunks from the chunking pipeline.
            vectors: Embedding vectors aligned with chunks.
        """
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        records: list[VectorRecord] = []
        for i, chunk in enumerate(chunks):
            meta: dict[str, Any] = {}
            if chunk.metadata:
                meta.update(chunk.metadata)
            meta["source_id"] = chunk.source_id
            meta["chunk_index"] = chunk.index
            meta["total_chunks"] = chunk.total_chunks

            records.append(VectorRecord(
                id=f"{chunk.source_id}_{chunk.index}",
                vector=vectors[i],
                text=chunk.text,
                metadata=meta,
                source_id=chunk.source_id,
            ))

        self._store.upsert(collection_name, records)

    def search_similar(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Search for similar vectors in a collection."""
        query = VectorQuery(
            vector=query_vector,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
        return self._store.search(collection_name, query)

    def delete_by_source(self, collection_name: str, source_id: str) -> None:
        """Delete all records belonging to a source.

        Note: ChromaDB does not support delete-by-metadata efficiently.
        This is a placeholder for future metadata-based deletion.
        """
        pass

    def health_check(self) -> bool:
        return self._store.health_check()
