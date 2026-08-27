"""Tests for M5.2 runtime wiring."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus import InMemoryEventBus
from skos.m4.infrastructure.adapters.knowledge_graph.inmemory_kg_adapter import (
    InMemoryKnowledgeGraphAdapter,
)
from skos.m4.infrastructure.adapters.security.api_key_auth_adapter import APIKeyAuthAdapter
from skos.m4.infrastructure.adapters.security.inmemory_rate_limit_adapter import (
    InMemoryRateLimitAdapter,
)
from skos.m4.infrastructure.adapters.security.structured_audit_adapter import StructuredAuditAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter import PostgreSQLAuditAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter import PostgreSQLAuthAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter import (
    PostgreSQLKnowledgeGraphAdapter,
)
from skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter import RedisEventBusAdapter
from skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter import RedisRateLimitAdapter
from skos.m5.runtime.persistence_factory import build_persistence_runtime


def test_memory_mode_wires_dependency_free_adapters() -> None:
    config = HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "memory"}}})

    runtime = build_persistence_runtime(config)

    assert runtime.mode == "memory"
    assert isinstance(runtime.event_bus, InMemoryEventBus)
    assert isinstance(runtime.rate_limiter, InMemoryRateLimitAdapter)
    assert isinstance(runtime.audit, StructuredAuditAdapter)
    assert isinstance(runtime.auth, APIKeyAuthAdapter)
    assert isinstance(runtime.knowledge_graph, InMemoryKnowledgeGraphAdapter)
    assert runtime.health().healthy is True


@patch("skos.m5.runtime.persistence_factory.RedisEventBusAdapter")
@patch("skos.m5.runtime.persistence_factory.RedisRateLimitAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLAuditAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLAuthAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLKnowledgeGraphAdapter")
def test_persistent_mode_wires_configured_adapters(
    mock_kg: Mock,
    mock_auth: Mock,
    mock_audit: Mock,
    mock_rate: Mock,
    mock_bus: Mock,
) -> None:
    config = HierarchicalConfigAdapter(defaults={
        "m5": {
            "persistence": {"mode": "persistent"},
            "redis": {"url": "redis://redis:6379/3"},
            "postgresql": {"dsn": "postgresql://postgres/skos"},
            "rate_limit": {"default_limit": 120, "default_window_seconds": 30.0},
        }
    })

    runtime = build_persistence_runtime(config)

    assert runtime.mode == "persistent"
    mock_bus.assert_called_once_with(redis_url="redis://redis:6379/3")
    mock_rate.assert_called_once_with(
        redis_url="redis://redis:6379/3",
        default_limit=120,
        default_window_seconds=30.0,
        overrides={},
    )
    mock_audit.assert_called_once_with(dsn="postgresql://postgres/skos")
    mock_auth.assert_called_once_with(dsn="postgresql://postgres/skos")
    mock_kg.assert_called_once_with(dsn="postgresql://postgres/skos")


@patch("skos.m5.runtime.persistence_factory.RedisEventBusAdapter")
@patch("skos.m5.runtime.persistence_factory.RedisRateLimitAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLAuditAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLAuthAdapter")
@patch("skos.m5.runtime.persistence_factory.PostgreSQLKnowledgeGraphAdapter")
def test_auto_mode_falls_back_when_persistent_health_fails(
    mock_kg: Mock,
    mock_auth: Mock,
    mock_audit: Mock,
    mock_rate: Mock,
    mock_bus: Mock,
) -> None:
    for mock_cls in (mock_bus, mock_rate, mock_audit, mock_auth):
        mock_cls.return_value.health.return_value = False
    mock_kg.return_value.health_check.return_value = False
    config = HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "auto"}}})

    runtime = build_persistence_runtime(config)

    assert runtime.mode == "auto-memory-fallback"
    assert isinstance(runtime.event_bus, InMemoryEventBus)
    assert runtime.health().healthy is True


def test_invalid_mode_raises_clear_error() -> None:
    config = HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "wrong"}}})

    with pytest.raises(ValueError, match="m5.persistence.mode"):
        build_persistence_runtime(config)


def test_runtime_health_reports_individual_components() -> None:
    config = HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "memory"}}})

    health = build_persistence_runtime(config).health()

    assert health.as_dict() == {
        "event_bus": True,
        "rate_limiter": True,
        "audit": True,
        "auth": True,
        "knowledge_graph": True,
        "healthy": True,
    }
