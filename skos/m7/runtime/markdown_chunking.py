"""Markdown section chunking for locally imported knowledge documents."""
from __future__ import annotations

import re

from skos.m4.domain.chunking import ChunkingStrategy, FixedSizeChunking, ParagraphChunking, TextChunk


class MarkdownSectionChunking(ChunkingStrategy):
    """Keep Markdown headings with their section body for useful retrieval."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self._chunk_size = chunk_size
        self._fallback = ParagraphChunking(chunk_size=chunk_size, overlap=overlap)
        self._splitter = FixedSizeChunking(chunk_size=chunk_size, overlap=overlap)

    def chunk(self, text: str, source_id: str = "") -> list[TextChunk]:
        if not text.strip():
            return []
        sections = self._sections(text)
        if not sections:
            return self._fallback.chunk(text, source_id=source_id)

        pieces: list[str] = []
        for section in sections:
            if len(section.split()) <= self._chunk_size:
                pieces.append(section)
            else:
                pieces.extend(chunk.text for chunk in self._splitter.chunk(section, source_id=source_id))
        total = len(pieces)
        return [
            TextChunk(text=piece, source_id=source_id, index=index, total_chunks=total)
            for index, piece in enumerate(pieces)
        ]

    @staticmethod
    def _sections(text: str) -> list[str]:
        sections: list[list[str]] = []
        current: list[str] = []
        saw_heading = False
        for line in text.splitlines():
            if re.match(r"^#{1,6}\s+\S", line):
                saw_heading = True
                if current and any(part.strip() for part in current):
                    sections.append(current)
                current = [line]
            else:
                current.append(line)
        if current and any(part.strip() for part in current):
            sections.append(current)
        if not saw_heading:
            return []
        return ["\n".join(lines).strip() for lines in sections if "\n".join(lines).strip()]
