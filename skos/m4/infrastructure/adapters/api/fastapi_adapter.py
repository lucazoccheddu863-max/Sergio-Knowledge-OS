"""FastAPI Infrastructure Adapter for SKOS M4.11 — Security & Auth.

FastAPI is EXCLUSIVELY an infrastructure adapter.
No Service depends on FastAPI.
All Services depend only on Ports.

API Contract v1 is frozen. All endpoints, request/response schemas,
and error formats are version-locked.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

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
from skos.m4.infrastructure.ports.metrics_port import MetricsPort
from skos.m4.infrastructure.ports.tracing_port import TracingPort
from skos.m4.infrastructure.ports.logging_port import LoggingPort
from skos.m4.infrastructure.ports.auth_port import AuthPort, SecurityContext
from skos.m4.infrastructure.ports.authorization_port import AuthorizationPort
from skos.m4.infrastructure.ports.rate_limit_port import RateLimitPort, RateLimitStatus
from skos.m4.infrastructure.ports.audit_port import AuditPort, AuditEvent
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
    SecurityStatusResponse,
)


class FastAPIAdapter:
    """FastAPI application adapter.

    Dependencies:
    - QueryOrchestratorPort: routes queries to engines
    - ConfigurationPort: reads API config
    - MetricsPort (optional): collects Prometheus metrics
    - TracingPort (optional): distributed tracing
    - LoggingPort (optional): structured logging
    - AuthPort (optional): authentication
    - AuthorizationPort (optional): authorization
    - RateLimitPort (optional): rate limiting
    - AuditPort (optional): audit logging
    """

    def __init__(
        self,
        orchestrator: QueryOrchestratorPort,
        config: ConfigurationPort,
        metrics: MetricsPort | None = None,
        tracer: TracingPort | None = None,
        logger: LoggingPort | None = None,
        auth: AuthPort | None = None,
        authorization: AuthorizationPort | None = None,
        rate_limiter: RateLimitPort | None = None,
        audit: AuditPort | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._config = config
        self._metrics = metrics
        self._tracer = tracer
        self._logger = logger
        self._auth = auth
        self._authorization = authorization
        self._rate_limiter = rate_limiter
        self._audit = audit
        self._app = FastAPI(
            title="Sergio Knowledge OS API",
            version="0.4.0",
            description="REST API for the Sergio Knowledge OS Query Engine — Contract v1",
            docs_url="/api/v1/docs",
            redoc_url="/api/v1/redoc",
            openapi_url="/api/v1/openapi.json",
        )
        self._setup_error_handlers()
        self._setup_public_routes()
        self._setup_admin_routes()
        self._setup_observability_routes()
        self._setup_security_routes()

    @property
    def app(self) -> FastAPI:
        return self._app

    # ── Observability Helpers ─────────────────────────────────────────────────

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        if self._logger:
            getattr(self._logger, level)(message, **kwargs)

    def _count_request(self, method: str, path: str, status_code: int) -> None:
        if self._metrics:
            self._metrics.counter(
                "http_requests_total",
                labels={"method": method, "path": path, "status": str(status_code)},
            )

    def _observe_latency(self, path: str, duration_ms: float) -> None:
        if self._metrics:
            self._metrics.histogram(
                "http_request_duration_seconds",
                duration_ms / 1000.0,
                labels={"path": path},
            )

    # ── Security Helpers ──────────────────────────────────────────────────────

    def _get_security_config(self) -> dict[str, Any]:
        """Read security configuration from config port."""
        try:
            enabled = self._config.get("m4.security.enabled", default=False)
            auth_required = self._config.get("m4.security.auth_required", default=False)
            # Guard against Mock objects from older tests that do not set these keys
            if not isinstance(enabled, bool):
                enabled = False
            if not isinstance(auth_required, bool):
                auth_required = False
            return {"enabled": enabled, "auth_required": auth_required}
        except Exception:
            return {"enabled": False, "auth_required": False}

    def _resolve_security_context(self, request: Request) -> SecurityContext:
        """Extract credentials from request and authenticate."""
        if not self._auth:
            return SecurityContext(authenticated=False)
        api_key = request.headers.get("x-api-key") or request.headers.get("authorization")
        return self._auth.authenticate(api_key)

    def _require_auth(self, context: SecurityContext) -> None:
        """Raise 401 if not authenticated."""
        if not context.authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _require_authorization(
        self, context: SecurityContext, action: str, resource: str
    ) -> None:
        """Raise 403 if not authorized."""
        if not self._authorization:
            return
        if not self._authorization.authorize(context, action, resource):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    def _check_rate_limit(self, client_id: str, resource: str) -> RateLimitStatus:
        """Check rate limit and raise 429 if exceeded."""
        if not self._rate_limiter:
            return RateLimitStatus(allowed=True, remaining=-1, reset_after_seconds=0.0, limit=-1)
        status_result = self._rate_limiter.check(client_id, resource)
        if not status_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(status_result.limit),
                    "X-RateLimit-Remaining": str(status_result.remaining),
                    "X-RateLimit-Reset": str(int(status_result.reset_after_seconds)),
                },
            )
        return status_result

    def _audit_event(
        self,
        event_type: str,
        principal: str | None,
        action: str,
        resource: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an audit event if audit port is available."""
        if not self._audit:
            return
        from datetime import datetime, timezone
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            principal=principal,
            action=action,
            resource=resource,
            status=status,
            details=details or {},
        )
        self._audit.record(event)

    # ── Error Handlers ────────────────────────────────────────────────────────

    def _setup_error_handlers(self) -> None:
        @self._app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
            self._count_request(request.method, request.url.path, 422)
            self._log("warning", "Validation error", path=request.url.path, errors=exc.errors())
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
            self._count_request(request.method, request.url.path, exc.status_code)
            self._log("warning", "HTTP exception", path=request.url.path, status=exc.status_code)
            request_id = str(uuid.uuid4())
            error = APIError(
                error_code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                request_id=request_id,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error.model_dump(),
                headers=getattr(exc, "headers", None) or {},
            )

        @self._app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            self._count_request(request.method, request.url.path, 500)
            self._log("error", "Unhandled exception", path=request.url.path, exception=str(exc))
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
                401: {"model": APIError, "description": "Authentication required"},
                403: {"model": APIError, "description": "Forbidden"},
                429: {"model": APIError, "description": "Rate limit exceeded"},
                500: {"model": APIError, "description": "Query execution failed"},
            },
            summary="Execute a unified query",
            tags=["Query"],
        )
        async def query_endpoint(request: Request, req: QueryRequest) -> QueryResponse:
            sec_cfg = self._get_security_config()
            ctx = self._resolve_security_context(request)

            if sec_cfg["auth_required"]:
                self._require_auth(ctx)
            self._require_authorization(ctx, "write", "/api/v1/query")

            client_id = ctx.api_key_id or request.client.host if request.client else "anonymous"
            self._check_rate_limit(client_id, "/api/v1/query")

            start = time.perf_counter()
            span = None
            if self._tracer:
                span = self._tracer.start_span("query_endpoint")
            try:
                self._log("info", "Query received", text=req.text, mode=req.mode, principal=ctx.principal)
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
                self._log("info", "Query completed", engines=result.engines_used, principal=ctx.principal)
                response = self._to_query_response(result)
                self._count_request("POST", "/api/v1/query", 200)
                self._audit_event(
                    "query", ctx.principal, "POST", "/api/v1/query", "success",
                    {"mode": req.mode, "engines": result.engines_used},
                )
                return response
            except QueryOrchestratorError as exc:
                self._log("error", "Query orchestrator error", error=str(exc), principal=ctx.principal)
                self._audit_event("query", ctx.principal, "POST", "/api/v1/query", "failed", {"error": str(exc)})
                if self._tracer and span:
                    self._tracer.record_exception(span, exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(exc),
                ) from exc
            except Exception as exc:
                self._log("error", "Query unexpected error", error=str(exc), principal=ctx.principal)
                self._audit_event("query", ctx.principal, "POST", "/api/v1/query", "failed", {"error": str(exc)})
                if self._tracer and span:
                    self._tracer.record_exception(span, exc)
                raise
            finally:
                if self._tracer and span:
                    self._tracer.end_span(span)
                duration_ms = (time.perf_counter() - start) * 1000
                self._observe_latency("/api/v1/query", duration_ms)

        @self._app.get(
            "/api/v1/health",
            response_model=HealthResponse,
            summary="Health check",
            tags=["System"],
        )
        async def health_endpoint(request: Request) -> HealthResponse:
            ctx = self._resolve_security_context(request)
            try:
                healthy = self._orchestrator.health_check()
                engines: dict[str, Any] = {"query_orchestrator": healthy}
                if self._metrics:
                    engines["metrics"] = self._metrics.health()
                if self._tracer:
                    engines["tracing"] = self._tracer.health()
                if self._logger:
                    engines["logging"] = self._logger.health()
                if self._auth:
                    engines["auth"] = self._auth.health()
                if self._authorization:
                    engines["authorization"] = self._authorization.health()
                if self._rate_limiter:
                    engines["rate_limit"] = self._rate_limiter.health()
                if self._audit:
                    engines["audit"] = self._audit.health()
                self._count_request("GET", "/api/v1/health", 200)
                self._audit_event("health", ctx.principal, "GET", "/api/v1/health", "success")
                return HealthResponse(
                    status="healthy" if healthy else "unhealthy",
                    engines=engines,
                )
            except Exception as exc:
                self._log("error", "Health check failed", error=str(exc))
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
        async def status_endpoint(request: Request) -> StatusResponse:
            ctx = self._resolve_security_context(request)
            self._count_request("GET", "/api/v1/status", 200)
            self._audit_event("status", ctx.principal, "GET", "/api/v1/status", "success")
            return StatusResponse(
                version="0.4.0",
                milestone="M4.12",
                status="operational",
            )

        @self._app.get(
            "/api/v1/engines",
            response_model=EnginesResponse,
            summary="List available engines",
            tags=["System"],
        )
        async def engines_endpoint(request: Request) -> EnginesResponse:
            ctx = self._resolve_security_context(request)
            self._count_request("GET", "/api/v1/engines", 200)
            self._audit_event("engines", ctx.principal, "GET", "/api/v1/engines", "success")
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
        async def admin_status_endpoint(request: Request) -> StatusResponse:
            ctx = self._resolve_security_context(request)
            if self._auth:
                self._require_auth(ctx)
                self._require_authorization(ctx, "admin", "/api/v1/admin/*")
            self._count_request("GET", "/api/v1/admin/status", 200)
            self._audit_event("admin", ctx.principal, "GET", "/api/v1/admin/status", "success")
            return StatusResponse(
                version="0.4.0",
                milestone="M4.12",
                status="admin_reserved",
            )

    # ── Observability Routes ────────────────────────────────────────────────────

    def _setup_observability_routes(self) -> None:
        @self._app.get(
            "/metrics",
            response_class=PlainTextResponse,
            summary="Prometheus metrics endpoint",
            tags=["Observability"],
        )
        async def metrics_endpoint(request: Request) -> PlainTextResponse:
            ctx = self._resolve_security_context(request)
            self._audit_event("metrics", ctx.principal, "GET", "/metrics", "success")
            if self._metrics:
                self._count_request("GET", "/metrics", 200)
                return PlainTextResponse(
                    content=self._metrics.render(),
                    media_type="text/plain; version=0.0.4",
                )
            return PlainTextResponse(
                content="# metrics not configured\n",
                media_type="text/plain; version=0.0.4",
            )

    # ── Security Routes ─────────────────────────────────────────────────────────

    def _setup_security_routes(self) -> None:
        @self._app.get(
            "/api/v1/security/status",
            response_model=SecurityStatusResponse,
            summary="Security subsystem status",
            tags=["Security"],
        )
        async def security_status_endpoint(request: Request) -> SecurityStatusResponse:
            ctx = self._resolve_security_context(request)
            sec_cfg = self._get_security_config()
            self._count_request("GET", "/api/v1/security/status", 200)
            self._audit_event("security", ctx.principal, "GET", "/api/v1/security/status", "success")
            return SecurityStatusResponse(
                enabled=sec_cfg["enabled"],
                auth_healthy=self._auth.health() if self._auth else False,
                authorization_healthy=self._authorization.health() if self._authorization else False,
                rate_limit_healthy=self._rate_limiter.health() if self._rate_limiter else False,
                audit_healthy=self._audit.health() if self._audit else False,
                auth_required=sec_cfg["auth_required"],
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
