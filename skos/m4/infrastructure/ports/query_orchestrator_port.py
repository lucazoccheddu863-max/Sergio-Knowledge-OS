"""Query Orchestrator Port — abstract interface for unified querying."""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult


class QueryOrchestratorPort(ABC):
    """Abstract port for unified query orchestration.

    Routes queries to the appropriate engine(s) based on query mode.
    """

    @abstractmethod
    def execute(self, query: UnifiedQuery) -> UnifiedResult:
        """Execute a unified query across all available engines."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if all engines are operational."""
        pass


class QueryOrchestratorError(Exception):
    """Base error for query orchestration operations."""
    pass
