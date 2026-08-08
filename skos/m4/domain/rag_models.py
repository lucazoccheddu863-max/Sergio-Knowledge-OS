"""Domain models for RAG (Retrieval Augmented Generation) pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from skos.m4.domain.ai_models import ChatResponse
from skos.m4.domain.search_models import RankedDocument


@dataclass(frozen=True)
class RAGQuery:
    """A user question for the RAG pipeline."""
    question: str
    top_k: int = 5
    filter_metadata: dict[str, Any] | None = None
    min_similarity: float | None = None
    system_prompt: str | None = None


@dataclass(frozen=True)
class RAGContext:
    """Retrieved context documents for RAG."""
    documents: list[RankedDocument]
    total_found: int
    query_time_ms: float = 0.0


@dataclass(frozen=True)
class RAGResult:
    """Complete result of a RAG pipeline execution."""
    query: RAGQuery
    context: RAGContext
    response: ChatResponse
    total_time_ms: float = 0.0
