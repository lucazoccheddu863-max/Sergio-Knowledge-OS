"""Tests for M4.11 — Security & Auth."""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from skos.m4.infrastructure.ports.auth_port import AuthPort, SecurityContext, AuthError
from skos.m4.infrastructure.ports.authorization_port import AuthorizationPort, AuthorizationError
from skos.m4.infrastructure.ports.rate_limit_port import RateLimitPort, RateLimitStatus, RateLimitExceededError
from skos.m4.infrastructure.ports.audit_port import AuditPort, AuditEvent

from skos.m4.infrastructure.adapters.security.api_key_auth_adapter import APIKeyAuthAdapter
from skos.m4.infrastructure.adapters.security.rbac_authorization_adapter import RBACAuthorizationAdapter
from skos.m4.infrastructure.adapters.security.inmemory_rate_limit_adapter import InMemoryRateLimitAdapter
from skos.m4.infrastructure.adapters.security.structured_audit_adapter import StructuredAuditAdapter

from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort
from skos.m4.infrastructure.ports.config_port import ConfigurationPort


# ── Port Tests ──────────────────────────────────────────────────────────────────

class TestAuthPort:
    def test_auth_port_is_abc(self) -> None:
        assert hasattr(AuthPort, "__abstractmethods__")
        assert "authenticate" in AuthPort.__abstractmethods__

    def test_security_context_defaults(self) -> None:
        ctx = SecurityContext()
        assert ctx.authenticated is False
        assert ctx.principal is None
        assert ctx.roles == []
        assert ctx.api_key_id is None

    def test_security_context_with_values(self) -> None:
        ctx = SecurityContext(
            authenticated=True,
            principal="alice",
            roles=["admin", "user"],
            api_key_id="abc123",
        )
        assert ctx.authenticated is True
        assert ctx.principal == "alice"
        assert ctx.roles == ["admin", "user"]
        assert ctx.api_key_id == "abc123"


class TestAuthorizationPort:
    def test_authorization_port_is_abc(self) -> None:
        assert hasattr(AuthorizationPort, "__abstractmethods__")
        assert "authorize" in AuthorizationPort.__abstractmethods__


class TestRateLimitPort:
    def test_rate_limit_port_is_abc(self) -> None:
        assert hasattr(RateLimitPort, "__abstractmethods__")
        assert "check" in RateLimitPort.__abstractmethods__

    def test_rate_limit_status_defaults(self) -> None:
        status = RateLimitStatus(allowed=True, remaining=10, reset_after_seconds=60.0, limit=100)
        assert status.allowed is True
        assert status.remaining == 10


class TestAuditPort:
    def test_audit_port_is_abc(self) -> None:
        assert hasattr(AuditPort, "__abstractmethods__")
        assert "record" in AuditPort.__abstractmethods__

    def test_audit_event_creation(self) -> None:
        event = AuditEvent(
            timestamp="2026-08-09T19:00:00Z",
            event_type="query",
            principal="alice",
            action="POST",
            resource="/api/v1/query",
            status="success",
            details={"mode": "auto"},
        )
        assert event.event_type == "query"
        assert event.principal == "alice"


# ── APIKeyAuthAdapter Tests ────────────────────────────────────────────────────

class TestAPIKeyAuthAdapter:
    def test_authenticate_valid_key(self) -> None:
        adapter = APIKeyAuthAdapter(keys={"secret123": {"roles": ["user"], "metadata": {"name": "Alice"}}})
        ctx = adapter.authenticate("secret123")
        assert ctx.authenticated is True
        assert ctx.principal == "Alice"
        assert "user" in ctx.roles

    def test_authenticate_invalid_key(self) -> None:
        adapter = APIKeyAuthAdapter(keys={"secret123": {"roles": ["user"]}})
        ctx = adapter.authenticate("wrong")
        assert ctx.authenticated is False

    def test_authenticate_bearer_prefix(self) -> None:
        adapter = APIKeyAuthAdapter(keys={"secret123": {"roles": ["user"], "metadata": {"name": "Alice"}}})
        ctx = adapter.authenticate("Bearer secret123")
        assert ctx.authenticated is True
        assert ctx.principal == "Alice"

    def test_authenticate_none(self) -> None:
        adapter = APIKeyAuthAdapter()
        ctx = adapter.authenticate(None)
        assert ctx.authenticated is False

    def test_register_and_revoke_key(self) -> None:
        adapter = APIKeyAuthAdapter()
        adapter.register_key("newkey", roles=["admin"])
        ctx = adapter.authenticate("newkey")
        assert ctx.authenticated is True
        assert adapter.revoke_key("newkey") is True
        ctx2 = adapter.authenticate("newkey")
        assert ctx2.authenticated is False

    def test_health_returns_true(self) -> None:
        adapter = APIKeyAuthAdapter()
        assert adapter.health() is True


# ── RBACAuthorizationAdapter Tests ────────────────────────────────────────────

class TestRBACAuthorizationAdapter:
    def test_authorize_matching_role(self) -> None:
        adapter = RBACAuthorizationAdapter(policies={"user": [("read", "/api/v1/query")]})
        ctx = SecurityContext(authenticated=True, roles=["user"])
        assert adapter.authorize(ctx, "read", "/api/v1/query") is True

    def test_authorize_no_matching_role(self) -> None:
        adapter = RBACAuthorizationAdapter(policies={"user": [("read", "/api/v1/query")]})
        ctx = SecurityContext(authenticated=True, roles=["admin"])
        assert adapter.authorize(ctx, "read", "/api/v1/query") is False

    def test_authorize_unauthenticated(self) -> None:
        adapter = RBACAuthorizationAdapter(policies={"user": [("read", "*")]})
        ctx = SecurityContext(authenticated=False)
        assert adapter.authorize(ctx, "read", "/api/v1/query") is False

    def test_authorize_wildcard_action(self) -> None:
        adapter = RBACAuthorizationAdapter(policies={"admin": [("*", "/api/v1/admin/*")]})
        ctx = SecurityContext(authenticated=True, roles=["admin"])
        assert adapter.authorize(ctx, "delete", "/api/v1/admin/status") is True

    def test_authorize_wildcard_resource(self) -> None:
        adapter = RBACAuthorizationAdapter(policies={"user": [("read", "*")]})
        ctx = SecurityContext(authenticated=True, roles=["user"])
        assert adapter.authorize(ctx, "read", "/api/v1/anything") is True

    def test_grant_and_revoke(self) -> None:
        adapter = RBACAuthorizationAdapter()
        adapter.grant("user", "write", "/api/v1/query")
        ctx = SecurityContext(authenticated=True, roles=["user"])
        assert adapter.authorize(ctx, "write", "/api/v1/query") is True
        assert adapter.revoke("user", "write", "/api/v1/query") is True
        assert adapter.authorize(ctx, "write", "/api/v1/query") is False

    def test_health_returns_true(self) -> None:
        adapter = RBACAuthorizationAdapter()
        assert adapter.health() is True


# ── InMemoryRateLimitAdapter Tests ────────────────────────────────────────────

class TestInMemoryRateLimitAdapter:
    def test_check_within_limit(self) -> None:
        adapter = InMemoryRateLimitAdapter(default_limit=5, default_window_seconds=60.0)
        status = adapter.check("client1", "/api/v1/query")
        assert status.allowed is True
        assert status.remaining == 4

    def test_check_exceeds_limit(self) -> None:
        adapter = InMemoryRateLimitAdapter(default_limit=2, default_window_seconds=60.0)
        adapter.check("client1", "/api/v1/query")
        adapter.check("client1", "/api/v1/query")
        status = adapter.check("client1", "/api/v1/query")
        assert status.allowed is False
        assert status.remaining == 0

    def test_check_different_clients_independent(self) -> None:
        adapter = InMemoryRateLimitAdapter(default_limit=1, default_window_seconds=60.0)
        s1 = adapter.check("client1", "/api/v1/query")
        s2 = adapter.check("client2", "/api/v1/query")
        assert s1.allowed is True
        assert s2.allowed is True

    def test_health_returns_true(self) -> None:
        adapter = InMemoryRateLimitAdapter()
        assert adapter.health() is True

    def test_override_applies(self) -> None:
        adapter = InMemoryRateLimitAdapter(
            default_limit=1,
            overrides={"/api/v1/query": {"limit": 10}},
        )
        for _ in range(5):
            status = adapter.check("c1", "/api/v1/query")
        assert status.allowed is True
        assert status.remaining == 5


# ── StructuredAuditAdapter Tests ──────────────────────────────────────────────

class TestStructuredAuditAdapter:
    def test_record_outputs_json(self) -> None:
        buf = io.StringIO()
        adapter = StructuredAuditAdapter(service_name="skos", output=buf)
        event = AuditEvent(
            timestamp="2026-08-09T19:00:00Z",
            event_type="query",
            principal="alice",
            action="POST",
            resource="/api/v1/query",
            status="success",
            details={"mode": "auto"},
        )
        adapter.record(event)
        buf.seek(0)
        entry = json.loads(buf.readline())
        assert entry["service"] == "skos"
        assert entry["event_type"] == "query"
        assert entry["principal"] == "alice"
        assert entry["status"] == "success"
        assert entry["details"]["mode"] == "auto"

    def test_health_returns_true(self) -> None:
        adapter = StructuredAuditAdapter()
        assert adapter.health() is True


# ── FastAPIAdapter Security Integration ───────────────────────────────────────

@pytest.fixture
def mock_orchestrator() -> Mock:
    return Mock(spec=QueryOrchestratorPort)


@pytest.fixture
def mock_config() -> Mock:
    return Mock(spec=ConfigurationPort)


class TestSecurityStatusEndpoint:
    def test_security_status_no_security(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.return_value = False
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/security/status")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["auth_healthy"] is False
        assert data["auth_required"] is False

    def test_security_status_with_security(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": True,
        }.get(key, default)

        auth = APIKeyAuthAdapter(keys={"key1": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"user": [("read", "*")]})
        rate = InMemoryRateLimitAdapter()
        audit = StructuredAuditAdapter()

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
            rate_limiter=rate,
            audit=audit,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/security/status")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["auth_healthy"] is True
        assert data["authorization_healthy"] is True
        assert data["rate_limit_healthy"] is True
        assert data["audit_healthy"] is True
        assert data["auth_required"] is True


class TestAuthRequiredQuery:
    def test_query_without_auth_returns_401(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": True,
        }.get(key, default)

        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"user": [("write", "*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.post("/api/v1/query", json={"text": "hello"})
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "HTTP_401"

    def test_query_with_valid_auth(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": True,
        }.get(key, default)

        from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
        mock_orchestrator.execute.return_value = UnifiedResult(
            query=UnifiedQuery(text="hello", mode="auto"),
            engines_used=["semantic_search"],
            total_time_ms=10.0,
        )
        mock_orchestrator.health_check.return_value = True

        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"user": [("write", "*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.post(
            "/api/v1/query",
            json={"text": "hello"},
            headers={"x-api-key": "secret"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["engines_used"] == ["semantic_search"]

    def test_query_with_invalid_auth_returns_401(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": True,
        }.get(key, default)

        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"user": [("write", "*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.post(
            "/api/v1/query",
            json={"text": "hello"},
            headers={"x-api-key": "wrong"},
        )
        assert response.status_code == 401


class TestAuthorizationQuery:
    def test_query_forbidden_returns_403(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": True,
        }.get(key, default)

        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"admin": [("write", "*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.post(
            "/api/v1/query",
            json={"text": "hello"},
            headers={"x-api-key": "secret"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "HTTP_403"


class TestRateLimitQuery:
    def test_rate_limit_exceeded_returns_429(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_config.get.side_effect = lambda key, default=None: {
            "m4.security.enabled": True,
            "m4.security.auth_required": False,
        }.get(key, default)

        rate = InMemoryRateLimitAdapter(default_limit=1, default_window_seconds=60.0)

        from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult
        mock_orchestrator.execute.return_value = UnifiedResult(
            query=UnifiedQuery(text="hello", mode="auto"),
            engines_used=["semantic_search"],
            total_time_ms=10.0,
        )
        mock_orchestrator.health_check.return_value = True

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            rate_limiter=rate,
        )
        client = TestClient(adapter.app)
        # First request succeeds
        r1 = client.post("/api/v1/query", json={"text": "hello"})
        assert r1.status_code == 200
        # Second request is rate limited
        r2 = client.post("/api/v1/query", json={"text": "hello"})
        assert r2.status_code == 429
        data = r2.json()
        assert data["error_code"] == "HTTP_429"


class TestAdminAuthRequired:
    def test_admin_without_auth_returns_401(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["admin"]}})
        authz = RBACAuthorizationAdapter(policies={"admin": [("admin", "/api/v1/admin/*")]})
        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/admin/status")
        assert response.status_code == 401

    def test_admin_with_auth_but_no_role_returns_403(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter(policies={"admin": [("admin", "/api/v1/admin/*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/admin/status", headers={"x-api-key": "secret"})
        assert response.status_code == 403

    def test_admin_with_admin_role(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["admin"]}})
        authz = RBACAuthorizationAdapter(policies={"admin": [("admin", "/api/v1/admin/*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/admin/status", headers={"x-api-key": "secret"})
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "M4.12"


class TestVersionAndMilestone:
    def test_status_returns_m4_11(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.4.0"
        assert data["milestone"] == "M4.12"

    def test_admin_status_returns_m4_11(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["admin"]}})
        authz = RBACAuthorizationAdapter(policies={"admin": [("admin", "/api/v1/admin/*")]})

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/admin/status", headers={"x-api-key": "secret"})
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "M4.12"


class TestHealthWithSecurity:
    def test_health_includes_security_status(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_orchestrator.health_check.return_value = True
        auth = APIKeyAuthAdapter(keys={"secret": {"roles": ["user"]}})
        authz = RBACAuthorizationAdapter()
        rate = InMemoryRateLimitAdapter()
        audit = StructuredAuditAdapter()

        adapter = FastAPIAdapter(
            orchestrator=mock_orchestrator,
            config=mock_config,
            auth=auth,
            authorization=authz,
            rate_limiter=rate,
            audit=audit,
        )
        client = TestClient(adapter.app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["engines"]["auth"] is True
        assert data["engines"]["authorization"] is True
        assert data["engines"]["rate_limit"] is True
        assert data["engines"]["audit"] is True
