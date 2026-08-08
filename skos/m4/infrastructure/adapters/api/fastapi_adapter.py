"""FastAPI Infrastructure Adapter for SKOS M4.9.5 — API Contract Freeze.

FastAPI is EXCLUSIVELY an infrastructure adapter.
No Service depends on FastAPI.
All Services depend only on Ports.

API Contract v1 is frozen. All endpoints, request/response schemas,
and error formats are version-locked.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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
    APIError,
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
            version="0.4.0-alpha11",
            description="REST API for the Sergio Knowledge OS Query Engine — Contract v1",
            docs_url="/api/v1/docs",
            redoc_url="/api/v1/redoc",
            openapi_url="/api/v1/openapi.json",
        )
        self._setup_error_handlers()
        self._setup_public_routes()
        self._setup_admin_routes()

    @property
    def app(self) -> FastAPI:
        return self._app

    # ── Error Handlers ────────────────────────────────────────────────────────

    def _setup_error_handlers(self) -> None:
        @self._app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
            request_id = str(uuid.uuid4())
            error = APIError(
                error_code="HTTP_422",
                message="Request validation failed",
                detail={"errors": exc.errors()},
                request_id=request_id,
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error.model_dump(),
            )

        @self._app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
            request_id = str(uuid.uuid4())
            error = APIError(
                error_code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                request_id=request_id,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error.model_dump(),
            )

        @self._app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            request_id = str(uuid.uuid4())
            error = APIError(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                detail={"type": type(exc).__name__, "info": str(exc)},
                request_id=request_id,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error.model_dump(),
            )

    # ── Public Routes (/api/v1/*) ─────────────────────────────────────────────

    def _setup_public_routes(self) -> None:
        @self._app.post(
            "/api/v1/query",
            response_model=QueryResponse,
            responses={
                500: {"model": APIError, "description": "Query execution failed"},
            },
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
                version="0.4.0-alpha11",
                milestone="M4.9.5",
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

    # ── Admin Routes (/api/v1/admin/*) ──────────────────────────────────────────

    def _setup_admin_routes(self) -> None:
        @self._app.get(
            "/api/v1/admin/status",
            response_model=StatusResponse,
            summary="Admin status endpoint (reserved)",
            tags=["Admin"],
            include_in_schema=True,
        )
        async def admin_status_endpoint() -> StatusResponse:
            return StatusResponse(
                version="0.4.0-alpha11",
                milestone="M4.9.5",
                status="admin_reserved",
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
