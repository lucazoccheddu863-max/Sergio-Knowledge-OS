"""DTOs for the FastAPI REST API Adapter.

Pydantic models that mirror the domain models for request/response serialization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Query ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """POST /api/v1/query request body."""
    text: str = Field(..., min_length=1, description="Query text")
    mode: str = Field(default="auto", description="Query mode: auto, semantic, rag, graph, hybrid")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of top results")
    filter_metadata: dict[str, Any] | None = Field(default=None, description="Metadata filters")
    min_similarity: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity threshold")
    graph_depth: int = Field(default=1, ge=1, le=5, description="Knowledge graph traversal depth")
    system_prompt: str | None = Field(default=None, description="Custom system prompt for RAG")


class RankedDocumentDTO(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_id: str = ""
    similarity_score: float = 0.0
    rank: int = 0


class SemanticSearchResultDTO(BaseModel):
    query_text: str
    results: list[RankedDocumentDTO] = Field(default_factory=list)
    total_found: int = 0
    query_time_ms: float = 0.0
    embedding_model: str = ""


class ChatMessageDTO(BaseModel):
    role: str
    content: str


class ChatResponseDTO(BaseModel):
    content: str
    model: str
    usage_prompt_tokens: int = 0
    usage_completion_tokens: int = 0
    finish_reason: str = "stop"


class RAGContextDTO(BaseModel):
    documents: list[RankedDocumentDTO] = Field(default_factory=list)
    total_found: int = 0
    query_time_ms: float = 0.0


class RAGResultDTO(BaseModel):
    question: str
    context: RAGContextDTO
    response: ChatResponseDTO
    total_time_ms: float = 0.0


class GraphResultDTO(BaseModel):
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    total_found: int = 0
    query_time_ms: float = 0.0


class QueryResponse(BaseModel):
    """POST /api/v1/query response body."""
    query: QueryRequest
    semantic_result: SemanticSearchResultDTO | None = None
    rag_result: RAGResultDTO | None = None
    graph_result: GraphResultDTO | None = None
    total_time_ms: float = 0.0
    engines_used: list[str] = Field(default_factory=list)


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """GET /api/v1/health response body."""
    status: str = Field(..., description="Overall health status: healthy | unhealthy")
    engines: dict[str, bool] = Field(default_factory=dict, description="Per-engine health")


# ── Status ───────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    """GET /api/v1/status response body."""
    version: str
    milestone: str
    status: str = "operational"


# ── Engines ────────────────────────────────────────────────────────────────────

class EnginesResponse(BaseModel):
    """GET /api/v1/engines response body."""
    engines: list[str] = Field(default_factory=list)
