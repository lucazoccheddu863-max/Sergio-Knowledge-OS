"""FastAPI Infrastructure Adapter for SKOS M4.9.

FastAPI is EXCLUSIVELY an infrastructure adapter.
No Service depends on FastAPI.
All Services depend only on Ports.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
from skos.m4.domain.search_models import SemanticSearchResult, RankedDocument
from skos.m4.domain.rag_models import RAGResult, RAGContext
from skos.m4.domain.knowledge_graph_models import GraphResult
from skos.m4.domain.ai_models import ChatResponse
from skos.m4.infrastructure.ports.query_orchestrator_port import (
    QueryOrchestratorPort,
    QueryOrchestratorError,
)
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.adapters.api.dto import (
    QueryRequest,
    QueryResponse,
    RankedDocumentDTO,
    SemanticSearchResultDTO,
    ChatResponseDTO,
    RAGContextDTO,
    RAGResultDTO,
    GraphResultDTO,
    HealthResponse,
    StatusResponse,
    EnginesResponse,
)


class FastAPIAdapter:
    """FastAPI application adapter.

    Dependencies:
        - QueryOrchestratorPort: routes queries to engines
        - ConfigurationPort: reads API config
    """

    def __init__(
        self,
        orchestrator: QueryOrchestratorPort,
        config: ConfigurationPort,
    ) -> None:
        self._orchestrator = orchestrator
        self._config = config
        self._app = FastAPI(
            title="Sergio Knowledge OS API",
            version="0.4.0-alpha10",
            description="REST API for the Sergio Knowledge OS Query Engine",
        )
        self._setup_routes()

    @property
    def app(self) -> FastAPI:
        return self._app

    def _setup_routes(self) -> None:
        @self._app.post(
            "/api/v1/query",
            response_model=QueryResponse,
            summary="Execute a unified query",
            tags=["Query"],
        )
        async def query_endpoint(req: QueryRequest) -> QueryResponse:
            try:
                unified_query = UnifiedQuery(
                    text=req.text,
                    mode=req.mode,
                    top_k=req.top_k,
                    filter_metadata=req.filter_metadata,
                    min_similarity=req.min_similarity,
                    graph_depth=req.graph_depth,
                    system_prompt=req.system_prompt,
                )
                result = self._orchestrator.execute(unified_query)
                return self._to_query_response(result)
            except QueryOrchestratorError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(exc),
                ) from exc
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal error: {exc}",
                ) from exc

        @self._app.get(
            "/api/v1/health",
            response_model=HealthResponse,
            summary="Health check",
            tags=["System"],
        )
        async def health_endpoint() -> HealthResponse:
            try:
                healthy = self._orchestrator.health_check()
                return HealthResponse(
                    status="healthy" if healthy else "unhealthy",
                    engines={"query_orchestrator": healthy},
                )
            except Exception as exc:
                return HealthResponse(
                    status="unhealthy",
                    engines={"query_orchestrator": False, "error": str(exc)},
                )

        @self._app.get(
            "/api/v1/status",
            response_model=StatusResponse,
            summary="System status",
            tags=["System"],
        )
        async def status_endpoint() -> StatusResponse:
            return StatusResponse(
                version="0.4.0-alpha10",
                milestone="M4.9",
                status="operational",
            )

        @self._app.get(
            "/api/v1/engines",
            response_model=EnginesResponse,
            summary="List available engines",
            tags=["System"],
        )
        async def engines_endpoint() -> EnginesResponse:
            return EnginesResponse(
                engines=[
                    "semantic_search",
                    "rag",
                    "knowledge_graph",
                    "query_orchestrator",
                ]
            )

    # ── Domain → DTO mappers ──────────────────────────────────────────────────

    def _to_query_response(self, result: UnifiedResult) -> QueryResponse:
        return QueryResponse(
            query=QueryRequest(
                text=result.query.text,
                mode=result.query.mode,
                top_k=result.query.top_k,
                filter_metadata=result.query.filter_metadata,
                min_similarity=result.query.min_similarity,
                graph_depth=result.query.graph_depth,
                system_prompt=result.query.system_prompt,
            ),
            semantic_result=self._to_semantic_dto(result.semantic_result),
            rag_result=self._to_rag_dto(result.rag_result),
            graph_result=self._to_graph_dto(result.graph_result),
            total_time_ms=result.total_time_ms,
            engines_used=result.engines_used,
        )

    def _to_semantic_dto(
        self, result: SemanticSearchResult | None
    ) -> SemanticSearchResultDTO | None:
        if result is None:
            return None
        return SemanticSearchResultDTO(
            query_text=result.query.text,
            results=[
                RankedDocumentDTO(
                    id=r.id,
                    text=r.text,
                    metadata=r.metadata,
                    source_id=r.source_id,
                    similarity_score=r.similarity_score,
                    rank=r.rank,
                )
                for r in result.results
            ],
            total_found=result.total_found,
            query_time_ms=result.query_time_ms,
            embedding_model=result.embedding_model,
        )

    def _to_rag_dto(self, result: RAGResult | None) -> RAGResultDTO | None:
        if result is None:
            return None
        return RAGResultDTO(
            question=result.query.question,
            context=RAGContextDTO(
                documents=[
                    RankedDocumentDTO(
                        id=d.id,
                        text=d.text,
                        metadata=d.metadata,
                        source_id=d.source_id,
                        similarity_score=d.similarity_score,
                        rank=d.rank,
                    )
                    for d in result.context.documents
                ],
                total_found=result.context.total_found,
                query_time_ms=result.context.query_time_ms,
            ),
            response=ChatResponseDTO(
                content=result.response.content,
                model=result.response.model,
                usage_prompt_tokens=result.response.usage_prompt_tokens,
                usage_completion_tokens=result.response.usage_completion_tokens,
                finish_reason=result.response.finish_reason,
            ),
            total_time_ms=result.total_time_ms,
        )

    def _to_graph_dto(self, result: GraphResult | None) -> GraphResultDTO | None:
        if result is None:
            return None
        return GraphResultDTO(
            entities=[e.__dict__ if hasattr(e, "__dict__") else dict(e) for e in getattr(result, "entities", [])],
            relations=[r.__dict__ if hasattr(r, "__dict__") else dict(r) for r in getattr(result, "relations", [])],
            total_found=getattr(result, "total_found", 0),
            query_time_ms=getattr(result, "query_time_ms", 0.0),
        )
