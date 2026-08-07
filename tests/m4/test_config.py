"""Tests for the Configuration Layer and Secret Manager."""
import pytest
from unittest.mock import MagicMock
from skos.m4.domain.value_objects import ConfigScope, SecretRef
from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import HierarchicalConfigAdapter
from skos.m4.infrastructure.adapters.secrets.env_secret_adapter import EnvSecretManagerAdapter
from skos.m4.infrastructure.ports.secret_port import SecretNotFoundError


class TestHierarchicalConfigAdapter:
    def test_get_from_defaults(self) -> None:
        defaults = {"m4": {"embedding": {"batch_size": 100, "model": "nomic-embed-text"}}}
        config = HierarchicalConfigAdapter(defaults=defaults)
        assert config.get("m4.embedding.batch_size") == 100
        assert config.get("m4.embedding.model") == "nomic-embed-text"

    def test_get_default_value(self) -> None:
        config = HierarchicalConfigAdapter()
        assert config.get("nonexistent.path", default="fallback") == "fallback"
        assert config.get("nonexistent.path") is None

    def test_set_and_get(self) -> None:
        config = HierarchicalConfigAdapter()
        config.set("m4.vector_store.provider", "qdrant")
        assert config.get("m4.vector_store.provider") == "qdrant"

    def test_scope_override(self) -> None:
        config = HierarchicalConfigAdapter()
        config.set("m4.embedding.batch_size", 100)
        ws_scope = ConfigScope(workspace_id="ws-1")
        config.set("m4.embedding.batch_size", 50, scope=ws_scope)
        assert config.get("m4.embedding.batch_size") == 100
        assert config.get("m4.embedding.batch_size", scope=ws_scope) == 50

    def test_scope_fallback(self) -> None:
        config = HierarchicalConfigAdapter()
        config.set("m4.embedding.model", "nomic-embed-text")
        ws_scope = ConfigScope(workspace_id="ws-1")
        assert config.get("m4.embedding.model", scope=ws_scope) == "nomic-embed-text"

    def test_deep_merge(self) -> None:
        config = HierarchicalConfigAdapter()
        config.set("m4.embedding.batch_size", 100)
        config.set("m4.embedding.model", "nomic")
        ws_scope = ConfigScope(workspace_id="ws-1")
        config.set("m4.embedding.batch_size", 50, scope=ws_scope)
        dumped = config.dump(scope=ws_scope)
        assert dumped["m4"]["embedding"]["batch_size"] == 50
        assert dumped["m4"]["embedding"]["model"] == "nomic"

    def test_env_var_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_M4_EMBEDDING__BATCH_SIZE", "200")
        monkeypatch.setenv("SKOS_M4_VECTOR_STORE__PROVIDER", "qdrant")
        monkeypatch.setenv("SKOS_M4_RAG__ENABLED", "true")
        config = HierarchicalConfigAdapter()
        assert config.get("embedding.batch_size") == 200
        assert config.get("vector_store.provider") == "qdrant"
        assert config.get("rag.enabled") is True

    def test_env_var_type_coercion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_M4_INT_VAL", "42")
        monkeypatch.setenv("SKOS_M4_FLOAT_VAL", "3.14")
        monkeypatch.setenv("SKOS_M4_BOOL_VAL", "false")
        monkeypatch.setenv("SKOS_M4_NULL_VAL", "null")
        monkeypatch.setenv("SKOS_M4_JSON_VAL", "[1, 2, 3]")
        config = HierarchicalConfigAdapter()
        assert config.get("int_val") == 42
        assert config.get("float_val") == 3.14
        assert config.get("bool_val") is False
        assert config.get("null_val") is None
        assert config.get("json_val") == [1, 2, 3]

    def test_subscribe_and_notify(self) -> None:
        config = HierarchicalConfigAdapter()
        callback = MagicMock()
        sub = config.subscribe("m4.embedding.batch_size", callback)
        config.set("m4.embedding.batch_size", 100)
        callback.assert_called_once_with(100)
        sub.unsubscribe()

    def test_get_with_fallback_scopes(self) -> None:
        config = HierarchicalConfigAdapter()
        scope_a = ConfigScope(workspace_id="ws-a")
        scope_b = ConfigScope(workspace_id="ws-b")
        config.set("key", "value-a", scope=scope_a)
        assert config.get_with_fallback("key", [scope_b, scope_a]) == "value-a"


class TestEnvSecretManagerAdapter:
    def test_get_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_SECRET__API_KEY", "super-secret")
        manager = EnvSecretManagerAdapter()
        ref = SecretRef(key="api_key")
        assert manager.get(ref) == "super-secret"

    def test_get_secret_not_found(self) -> None:
        manager = EnvSecretManagerAdapter()
        ref = SecretRef(key="nonexistent")
        with pytest.raises(SecretNotFoundError):
            manager.get(ref)

    def test_set_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKOS_SECRET__NEW_KEY", raising=False)
        manager = EnvSecretManagerAdapter()
        ref = SecretRef(key="new_key")
        manager.set(ref, "new-value")
        assert manager.get(ref) == "new-value"

    def test_delete_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_SECRET__DELETE_ME", "value")
        manager = EnvSecretManagerAdapter()
        ref = SecretRef(key="delete_me")
        assert manager.exists(ref) is True
        manager.delete(ref)
        assert manager.exists(ref) is False

    def test_namespaced_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_SECRET__PROD__DB_PASSWORD", "prod-pass")
        manager = EnvSecretManagerAdapter()
        ref = SecretRef(key="db_password", namespace="prod")
        assert manager.get(ref) == "prod-pass"

    def test_list_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_SECRET__KEY1", "v1")
        monkeypatch.setenv("SKOS_SECRET__KEY2", "v2")
        manager = EnvSecretManagerAdapter()
        keys = manager.list_keys()
        assert "key1" in keys
        assert "key2" in keys
