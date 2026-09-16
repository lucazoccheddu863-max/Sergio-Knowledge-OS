"""Local SKOS server entrypoint for operator testing."""
from __future__ import annotations

from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort


class LocalHealthOrchestrator(QueryOrchestratorPort):
    """Minimal local orchestrator for admin console and health preflight."""

    def execute(self, query: UnifiedQuery) -> UnifiedResult:
        return UnifiedResult(
            query=query,
            total_time_ms=0.0,
            engines_used=["local_health"],
        )

    def health_check(self) -> bool:
        return True


def build_local_config() -> HierarchicalConfigAdapter:
    """Build local defaults that match the repository config file."""

    return HierarchicalConfigAdapter(
        defaults={
            "database_path": "./data/sergio_knowledge.db",
            "archive_root": "./data/archive",
            "backup_dir": "./data/backups",
            "release_dir": "./data/releases",
            "m4": {"security": {"enabled": False, "auth_required": False}},
            "m5": {"persistence": {"mode": "memory"}},
            "m6": {"environment": "development"},
        }
    )


def build_local_app():
    """Build a local FastAPI app for manual checks and admin console use."""

    return FastAPIAdapter(
        orchestrator=LocalHealthOrchestrator(),
        config=build_local_config(),
    ).app


app = build_local_app()
