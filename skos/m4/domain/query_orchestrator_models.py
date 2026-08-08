"""Domain models for Query Orchestrator operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from skos.m4.domain.ai_models import ChatResponse
from skos.m4.domain.knowledge_graph_models import GraphResult
from skos.m4.domain.rag_models import RAGResult
from skos.m4.domain.search_models import SemanticSearchResult


@dataclass(frozen=True)
class UnifiedQuery:
    """A unified query that can be routed to multiple engines."""
    text: str
    mode: str = "auto"  # "auto", "semantic", "rag", "graph", "hybrid"
    top_k: int = 5
    filter_metadata: dict[str, Any] | None = None
    min_similarity: float | None = None
    graph_depth: int = 1
    system_prompt: str | None = None


@dataclass(frozen=True)
class UnifiedResult:
    """Unified result from the Query Orchestrator."""
    query: UnifiedQuery
    semantic_result: SemanticSearchResult | None = None
    rag_result: RAGResult | None = None
    graph_result: GraphResult | None = None
    total_time_ms: float = 0.0
    engines_used: list[str] = field(default_factory=list)
