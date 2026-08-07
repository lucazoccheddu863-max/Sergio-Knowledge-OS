"""Chunking strategies for text segmentation before embedding generation.

Long texts must be split into manageable chunks to fit within
model token limits and improve retrieval granularity.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A segment of text with metadata for traceability."""
    text: str
    source_id: str
    index: int
    total_chunks: int
    metadata: dict[str, str] | None = None


class ChunkingStrategy(ABC):
    """Abstract strategy for splitting text into chunks."""

    @abstractmethod
    def chunk(self, text: str, source_id: str = "") -> list[TextChunk]:
        """Split text into chunks."""


class FixedSizeChunking(ChunkingStrategy):
    """Split text into fixed-size chunks with optional overlap.

    Splits on word boundaries when possible to avoid cutting words.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, source_id: str = "") -> list[TextChunk]:
        if not text:
            return []

        words = text.split()
        if len(words) <= self.chunk_size:
            return [TextChunk(text=text, source_id=source_id, index=0, total_chunks=1)]

        chunks: list[TextChunk] = []
        step = self.chunk_size - self.overlap
        idx = 0

        while idx < len(words):
            end = min(idx + self.chunk_size, len(words))
            chunk_text = " ".join(words[idx:end])
            chunks.append(TextChunk(
                text=chunk_text,
                source_id=source_id,
                index=len(chunks),
                total_chunks=0,  # filled later
            ))
            if end == len(words):
                break
            idx += step

        total = len(chunks)
        return [
            TextChunk(text=c.text, source_id=c.source_id, index=c.index, total_chunks=total)
            for c in chunks
        ]


class ParagraphChunking(ChunkingStrategy):
    """Split text on paragraph boundaries.

    Useful for documents where paragraph structure carries semantic meaning.
    Falls back to FixedSizeChunking for paragraphs exceeding chunk_size.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        safe_overlap = min(overlap, max(0, chunk_size - 1))
        self._fallback = FixedSizeChunking(chunk_size=chunk_size, overlap=safe_overlap)
        self.chunk_size = chunk_size

    def chunk(self, text: str, source_id: str = "") -> list[TextChunk]:
        if not text:
            return []

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        chunks: list[TextChunk] = []
        for para in paragraphs:
            words = para.split()
            if len(words) > self.chunk_size:
                # Paragraph too long — use fallback
                sub_chunks = self._fallback.chunk(para, source_id=source_id)
                chunks.extend(sub_chunks)
            else:
                chunks.append(TextChunk(
                    text=para,
                    source_id=source_id,
                    index=len(chunks),
                    total_chunks=0,
                ))

        total = len(chunks)
        return [
            TextChunk(text=c.text, source_id=c.source_id, index=c.index, total_chunks=total)
            for c in chunks
        ]
