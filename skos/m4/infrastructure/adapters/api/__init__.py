"""FastAPI Infrastructure Adapter for SKOS M4.9.5 — API Contract v1."""
from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.adapters.api.dto import (
    APIError,
    QueryRequest,
    QueryResponse,
    HealthResponse,
    StatusResponse,
    EnginesResponse,
)

__all__ = [
    "FastAPIAdapter",
    "APIError",
    "QueryRequest",
    "QueryResponse",
    "HealthResponse",
    "StatusResponse",
    "EnginesResponse",
]
