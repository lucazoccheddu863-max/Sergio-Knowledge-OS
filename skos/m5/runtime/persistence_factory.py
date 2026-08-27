"""M5.2 runtime wiring for persistence-backed adapters.

The factory keeps production wiring explicit while preserving a local,
dependency-light fallback for development and tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus import InMemoryEventBus
from skos.m4.infrastructure.adapters.knowledge_graph.inmemory_kg_adapter import (
    InMemoryKnowledgeGraphAdapter,
)
from skos.m4.infrastructure.adapters.security.api_key_auth_adapter import APIKeyAuthAdapter
from skos.m4.infrastructure.adapters.security.inmemory_rate_limit_adapter import (
    InMemoryRateLimitAdapter,
)
from skos.m4.infrastructure.adapters.security.structured_audit_adapter import StructuredAuditAdapter
from skos.m4.infrastructure.ports.audit_port import AuditPort
from skos.m4.infrastructure.ports.auth_port import AuthPort
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
from skos.m4.infrastructure.ports.knowledge_graph_port import KnowledgeGraphPort
from skos.m4.infrastructure.ports.rate_limit_port import RateLimitPort
from skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter import PostgreSQLAuditAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter import PostgreSQLAuthAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter import (
    PostgreSQLKnowledgeGraphAdapter,
)
from skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter import RedisEventBusAdapter
from skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter import RedisRateLimitAdapter


@dataclass(frozen=True)
class RuntimeHealth:
    """Health snapshot for runtime-wired persistence services."""

    event_bus: bool
    rate_limiter: bool
    audit: bool
    auth: bool
    knowledge_graph: bool

    @property
    def healthy(self) -> bool:
        return all((
            self.event_bus,
            self.rate_limiter,
            self.audit,
            self.auth,
            self.knowledge_graph,
        ))

    def as_dict(self) -> dict[str, bool]:
        return {
            "event_bus": self.event_bus,
            "rate_limiter": self.rate_limiter,
            "audit": self.audit,
            "auth": self.auth,
            "knowledge_graph": self.knowledge_graph,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class PersistenceRuntime:
    """Runtime-selected infrastructure adapters."""

    event_bus: EventBusPort
    rate_limiter: RateLimitPort
    audit: AuditPort
    auth: AuthPort
    knowledge_graph: KnowledgeGraphPort
    mode: str

    def health(self) -> RuntimeHealth:
        return RuntimeHealth(
            event_bus=_call_health(self.event_bus, default=True),
            rate_limiter=_call_health(self.rate_limiter),
            audit=_call_health(self.audit),
            auth=_call_health(self.auth),
            knowledge_graph=_call_health(self.knowledge_graph),
        )


def build_persistence_runtime(config: ConfigurationPort) -> PersistenceRuntime:
    """Build persistence services from configuration.

    Supported modes:
    - ``memory``: local, dependency-free adapters.
    - ``persistent``: Redis/PostgreSQL adapters.
    - ``auto``: try persistent adapters and fall back to memory if unhealthy.
    """
    mode = _get_str(config, "m5.persistence.mode", "memory").lower()
    if mode not in {"memory", "persistent", "auto"}:
        raise ValueError("m5.persistence.mode must be one of: memory, persistent, auto")

    if mode == "memory":
        return _build_memory_runtime()

    persistent = _build_persistent_runtime(config)
    if mode == "persistent":
        return persistent

    if persistent.health().healthy:
        return persistent
    return _build_memory_runtime(mode="auto-memory-fallback")


def _build_memory_runtime(mode: str = "memory") -> PersistenceRuntime:
    return PersistenceRuntime(
        event_bus=InMemoryEventBus(),
        rate_limiter=InMemoryRateLimitAdapter(),
        audit=StructuredAuditAdapter(),
        auth=APIKeyAuthAdapter(),
        knowledge_graph=InMemoryKnowledgeGraphAdapter(),
        mode=mode,
    )


def _build_persistent_runtime(config: ConfigurationPort) -> PersistenceRuntime:
    redis_url = _get_str(config, "m5.redis.url", "redis://localhost:6379/0")
    pg_dsn = _get_str(config, "m5.postgresql.dsn", "postgresql://localhost:5432/skos")
    rate_limit = _get_int(config, "m5.rate_limit.default_limit", 60)
    rate_window = _get_float(config, "m5.rate_limit.default_window_seconds", 60.0)
    overrides = _get_dict(config, "m5.rate_limit.overrides", {})

    return PersistenceRuntime(
        event_bus=RedisEventBusAdapter(redis_url=redis_url),
        rate_limiter=RedisRateLimitAdapter(
            redis_url=redis_url,
            default_limit=rate_limit,
            default_window_seconds=rate_window,
            overrides=overrides,
        ),
        audit=PostgreSQLAuditAdapter(dsn=pg_dsn),
        auth=PostgreSQLAuthAdapter(dsn=pg_dsn),
        knowledge_graph=PostgreSQLKnowledgeGraphAdapter(dsn=pg_dsn),
        mode="persistent",
    )


def _call_health(adapter: Any, default: bool = False) -> bool:
    if hasattr(adapter, "health"):
        return bool(adapter.health())
    if hasattr(adapter, "health_check"):
        return bool(adapter.health_check())
    return default


def _get_str(config: ConfigurationPort, path: str, default: str) -> str:
    value = config.get(path, default=default)
    return value if isinstance(value, str) else default


def _get_int(config: ConfigurationPort, path: str, default: int) -> int:
    value = config.get(path, default=default)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _get_float(config: ConfigurationPort, path: str, default: float) -> float:
    value = config.get(path, default=default)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _get_dict(config: ConfigurationPort, path: str, default: dict[str, Any]) -> dict[str, Any]:
    value = config.get(path, default=default)
    return dict(value) if isinstance(value, dict) else dict(default)
