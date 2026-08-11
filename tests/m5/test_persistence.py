"""Tests for M5.1 — Persistence Layer.

Tests persistent adapters with mocked Redis/PostgreSQL.
"""
from __future__ import annotations

import json
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from skos.m4.infrastructure.ports.event_bus_port import DomainEvent, EventHandler
from skos.m4.infrastructure.ports.rate_limit_port import RateLimitStatus
from skos.m4.infrastructure.ports.audit_port import AuditEvent
from skos.m4.infrastructure.ports.auth_port import SecurityContext
from skos.m4.domain.knowledge_graph_models import Entity, Relation, GraphQuery, GraphResult

from skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter import RedisEventBusAdapter
from skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter import RedisRateLimitAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter import PostgreSQLAuditAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter import PostgreSQLAuthAdapter
from skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter import PostgreSQLKnowledgeGraphAdapter


# ── RedisEventBusAdapter Tests ────────────────────────────────────────────────

class TestRedisEventBusAdapter:
    @patch("skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter.redis.from_url")
    def test_publish(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        adapter = RedisEventBusAdapter(redis_url="redis://localhost:6379/0")
        event = DomainEvent(event_id="evt-1", event_type="test", correlation_id="corr-1", payload={"data": 1})
        adapter.publish(event, "test.topic")

        mock_client.publish.assert_called_once()
        mock_client.xadd.assert_called_once()

    @patch("skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter.redis.from_url")
    def test_subscribe(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        adapter = RedisEventBusAdapter()
        handler = Mock()
        sub = adapter.subscribe("test.topic", handler)
        assert sub.topic == "test.topic"

    @patch("skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter.redis.from_url")
    def test_health_true(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        adapter = RedisEventBusAdapter()
        assert adapter.health() is True

    @patch("skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter.redis.from_url")
    def test_health_false(self, mock_from_url: Mock) -> None:
        mock_from_url.side_effect = Exception("Connection refused")

        adapter = RedisEventBusAdapter()
        assert adapter.health() is False


# ── RedisRateLimitAdapter Tests ─────────────────────────────────────────────────

class TestRedisRateLimitAdapter:
    @patch("skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter.redis.from_url")
    def test_check_within_limit(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_pipe = Mock()
        mock_client.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 0, 1, 1]  # zrem, zcard, zadd, expire
        mock_from_url.return_value = mock_client

        adapter = RedisRateLimitAdapter(default_limit=5, default_window_seconds=60.0)
        status = adapter.check("client1", "/api/v1/query")
        assert status.allowed is True
        assert status.remaining == 4

    @patch("skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter.redis.from_url")
    def test_check_exceeds_limit(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_pipe = Mock()
        mock_client.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [0, 5, 6, 1]  # zcard=5 means 5 existing + 1 new = 6 > limit 5
        mock_from_url.return_value = mock_client

        adapter = RedisRateLimitAdapter(default_limit=5, default_window_seconds=60.0)
        status = adapter.check("client1", "/api/v1/query")
        # With zcard=5 before zadd, after zadd it's 6, remaining = 5-5-1 = -1
        # The adapter should reject
        # Actually let me trace: current_count = results[1] = 5, remaining = 5 - 5 - 1 = -1
        # Since -1 < 0, it rolls back
        assert status.allowed is False
        assert status.remaining == 0

    @patch("skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter.redis.from_url")
    def test_health(self, mock_from_url: Mock) -> None:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        adapter = RedisRateLimitAdapter()
        assert adapter.health() is True


# ── PostgreSQLAuditAdapter Tests ──────────────────────────────────────────────

class TestPostgreSQLAuditAdapter:
    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter.psycopg2.connect")
    def test_record(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLAuditAdapter(dsn="postgresql://localhost/skos")
        event = AuditEvent(
            timestamp="2026-08-10T00:00:00Z",
            event_type="query",
            principal="alice",
            action="POST",
            resource="/api/v1/query",
            status="success",
            details={"mode": "auto"},
        )
        adapter.record(event)

        mock_cur.execute.assert_called()
        assert "INSERT INTO audit_events" in mock_cur.execute.call_args[0][0]

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter.psycopg2.connect")
    def test_health_true(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLAuditAdapter()
        assert adapter.health() is True

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter.psycopg2.connect")
    def test_health_false(self, mock_connect: Mock) -> None:
        mock_connect.side_effect = Exception("Connection refused")

        adapter = PostgreSQLAuditAdapter()
        assert adapter.health() is False


# ── PostgreSQLAuthAdapter Tests ─────────────────────────────────────────────────

class TestPostgreSQLAuthAdapter:
    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter.psycopg2.connect")
    def test_authenticate_valid_key(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.fetchone.return_value = ("alice", ["user"], {"team": "alpha"})
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLAuthAdapter()
        adapter.register_key("secret123", principal="alice", roles=["user"], metadata={"team": "alpha"})
        ctx = adapter.authenticate("secret123")
        assert ctx.authenticated is True
        assert ctx.principal == "alice"
        assert "user" in ctx.roles

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter.psycopg2.connect")
    def test_authenticate_invalid_key(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLAuthAdapter()
        ctx = adapter.authenticate("wrong")
        assert ctx.authenticated is False

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter.psycopg2.connect")
    def test_revoke_key(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.rowcount = 1
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLAuthAdapter()
        result = adapter.revoke_key("secret123")
        assert result is True


# ── PostgreSQLKnowledgeGraphAdapter Tests ───────────────────────────────────────

class TestPostgreSQLKnowledgeGraphAdapter:
    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_add_entity(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        entity = Entity(id="e1", name="Python", entity_type="language")
        adapter.add_entity(entity)

        mock_cur.execute.assert_called()
        assert "INSERT INTO kg_entities" in mock_cur.execute.call_args[0][0]

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_add_relation(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        relation = Relation(source_id="e1", target_id="e2", relation_type="uses")
        adapter.add_relation(relation)

        mock_cur.execute.assert_called()
        assert "INSERT INTO kg_relations" in mock_cur.execute.call_args[0][0]

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_get_entity(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.fetchone.return_value = ("e1", "Python", "language", {})
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        entity = adapter.get_entity("e1")
        assert entity is not None
        assert entity.name == "Python"

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_delete_entity(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        adapter.delete_entity("e1")

        # _ensure_tables calls execute first, then delete_entity calls it again
        assert mock_cur.execute.call_count >= 2
        last_call = mock_cur.execute.call_args_list[-1]
        assert "DELETE FROM kg_entities" in last_call[0][0]

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_health(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        mock_cur.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        assert adapter.health_check() is True

    @patch("skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter.psycopg2.connect")
    def test_query(self, mock_connect: Mock) -> None:
        mock_conn = Mock()
        mock_conn.autocommit = True
        mock_cur = Mock()
        # First query returns entities, second returns relations
        mock_cur.fetchall.side_effect = [
            [("e1", "Python", "language", {}), ("e2", "FastAPI", "framework", {})],
            [("e1", "e2", "uses", {})],
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        adapter = PostgreSQLKnowledgeGraphAdapter()
        result = adapter.query(GraphQuery(entity_name="Python", depth=1, max_results=10))
        assert isinstance(result, GraphResult)
        assert len(result.entities) == 2
        assert len(result.relations) == 1


# ── Port Contract Compliance ────────────────────────────────────────────────────

class TestPortCompliance:
    def test_redis_eventbus_implements_port(self) -> None:
        from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
        assert issubclass(RedisEventBusAdapter, EventBusPort)

    def test_redis_ratelimit_implements_port(self) -> None:
        from skos.m4.infrastructure.ports.rate_limit_port import RateLimitPort
        assert issubclass(RedisRateLimitAdapter, RateLimitPort)

    def test_postgresql_audit_implements_port(self) -> None:
        from skos.m4.infrastructure.ports.audit_port import AuditPort
        assert issubclass(PostgreSQLAuditAdapter, AuditPort)

    def test_postgresql_auth_implements_port(self) -> None:
        from skos.m4.infrastructure.ports.auth_port import AuthPort
        assert issubclass(PostgreSQLAuthAdapter, AuthPort)

    def test_postgresql_kg_implements_port(self) -> None:
        from skos.m4.infrastructure.ports.knowledge_graph_port import KnowledgeGraphPort
        assert issubclass(PostgreSQLKnowledgeGraphAdapter, KnowledgeGraphPort)
