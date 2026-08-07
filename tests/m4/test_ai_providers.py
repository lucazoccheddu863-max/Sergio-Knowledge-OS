"""Tests for AI Provider adapters, registry, and application service."""
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest
from skos.m4.domain.ai_models import ChatMessage, ChatRequest, EmbeddingRequest
from skos.m4.infrastructure.adapters.ai_providers.claude_adapter import ClaudeAdapter
from skos.m4.infrastructure.adapters.ai_providers.gemini_adapter import GeminiAdapter
from skos.m4.infrastructure.adapters.ai_providers.kimi_adapter import KimiAdapter
from skos.m4.infrastructure.adapters.ai_providers.ollama_adapter import OllamaAdapter
from skos.m4.infrastructure.adapters.ai_providers.openai_adapter import OpenAIAdapter
from skos.m4.infrastructure.adapters.ai_providers.provider_registry import AIProviderRegistry
from skos.m4.application.services.ai_service import AIService
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderError


class MockHTTPResponse:
    def __init__(self, body: dict, status: int = 200) -> None:
        self._body = json.dumps(body).encode("utf-8")
        self.status = status
        self.code = status
    def read(self) -> bytes:
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *args) -> None:
        pass


def mock_urlopen(body: dict, status: int = 200):
    return patch("skos.m4.infrastructure.adapters.ai_providers._http_mixin.urllib.request.urlopen", return_value=MockHTTPResponse(body, status))


class TestOpenAIAdapter:
    def test_chat_success(self) -> None:
        adapter = OpenAIAdapter(api_key="sk-test")
        resp_body = {"model": "gpt-4o-mini", "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))
        assert result.content == "Hello!"
        assert result.model == "gpt-4o-mini"
        assert result.usage_prompt_tokens == 10

    def test_embed_success(self) -> None:
        adapter = OpenAIAdapter(api_key="sk-test")
        resp_body = {"model": "text-embedding-3-small", "data": [{"embedding": [0.1, 0.2, 0.3]}, {"embedding": [0.4, 0.5, 0.6]}]}
        with mock_urlopen(resp_body):
            result = adapter.embed(EmbeddingRequest(texts=["a", "b"]))
        assert len(result.vectors) == 2
        assert result.dimensions == 3

    def test_health_check_success(self) -> None:
        adapter = OpenAIAdapter(api_key="sk-test")
        with mock_urlopen({"data": []}):
            assert adapter.health_check() is True

    def test_list_models(self) -> None:
        adapter = OpenAIAdapter(api_key="sk-test")
        with mock_urlopen({"data": [{"id": "gpt-4"}, {"id": "gpt-3.5"}]}):
            models = adapter.list_models()
        assert models == ["gpt-3.5", "gpt-4"]

    def test_chat_http_error(self) -> None:
        adapter = OpenAIAdapter(api_key="sk-test")
        with patch("skos.m4.infrastructure.adapters.ai_providers._http_mixin.urllib.request.urlopen", side_effect=urllib.error.HTTPError("", 500, "Internal", {}, None)):
            with pytest.raises(AIProviderError):
                adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))


class TestGeminiAdapter:
    def test_chat_success(self) -> None:
        adapter = GeminiAdapter(api_key="gem-test")
        resp_body = {"candidates": [{"content": {"parts": [{"text": "Ciao!"}]}, "finishReason": "STOP"}], "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2}}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Ciao")]))
        assert result.content == "Ciao!"
        assert result.usage_prompt_tokens == 5

    def test_embed_success(self) -> None:
        adapter = GeminiAdapter(api_key="gem-test")
        resp_body = {"embeddings": [{"embedding": {"values": [0.1, 0.2]}}, {"embedding": {"values": [0.3, 0.4]}}]}
        with mock_urlopen(resp_body):
            result = adapter.embed(EmbeddingRequest(texts=["x", "y"]))
        assert len(result.vectors) == 2
        assert result.dimensions == 2

    def test_list_models(self) -> None:
        adapter = GeminiAdapter(api_key="gem-test")
        with mock_urlopen({"models": [{"name": "models/gemini-pro"}]}):
            models = adapter.list_models()
        assert models == ["gemini-pro"]


class TestKimiAdapter:
    def test_chat_success(self) -> None:
        adapter = KimiAdapter(api_key="kimi-test")
        resp_body = {"model": "moonshot-v1-8k", "choices": [{"message": {"content": "你好"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))
        assert result.content == "你好"

    def test_embed_not_implemented(self) -> None:
        adapter = KimiAdapter(api_key="kimi-test")
        with pytest.raises(NotImplementedError):
            adapter.embed(EmbeddingRequest(texts=["a"]))


class TestClaudeAdapter:
    def test_chat_success(self) -> None:
        adapter = ClaudeAdapter(api_key="claude-test")
        resp_body = {"model": "claude-3-haiku", "content": [{"type": "text", "text": "Bonjour!"}], "usage": {"input_tokens": 4, "output_tokens": 2}, "stop_reason": "end_turn"}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))
        assert result.content == "Bonjour!"
        assert result.usage_prompt_tokens == 4

    def test_chat_with_system_message(self) -> None:
        adapter = ClaudeAdapter(api_key="claude-test")
        resp_body = {"model": "claude-3-haiku", "content": [{"type": "text", "text": "OK"}], "usage": {}, "stop_reason": "end_turn"}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="system", content="Be helpful"), ChatMessage(role="user", content="Hi")]))
        assert result.content == "OK"

    def test_embed_not_implemented(self) -> None:
        adapter = ClaudeAdapter(api_key="claude-test")
        with pytest.raises(NotImplementedError):
            adapter.embed(EmbeddingRequest(texts=["a"]))


class TestOllamaAdapter:
    def test_chat_success(self) -> None:
        adapter = OllamaAdapter()
        resp_body = {"model": "llama3.1", "message": {"role": "assistant", "content": "Hola!"}, "prompt_eval_count": 3, "eval_count": 2}
        with mock_urlopen(resp_body):
            result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))
        assert result.content == "Hola!"

    def test_embed_success(self) -> None:
        adapter = OllamaAdapter()
        resp_body = {"model": "nomic-embed-text", "embeddings": [[0.1, 0.2], [0.3, 0.4]]}
        with mock_urlopen(resp_body):
            result = adapter.embed(EmbeddingRequest(texts=["a", "b"]))
        assert len(result.vectors) == 2
        assert result.dimensions == 2


class TestAIProviderRegistry:
    def test_register_and_create(self) -> None:
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        provider = registry.create("openai", api_key="sk-test")
        assert isinstance(provider, OpenAIAdapter)

    def test_list_providers(self) -> None:
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        registry.register("ollama", OllamaAdapter)
        assert registry.list_providers() == ["ollama", "openai"]

    def test_unknown_provider_raises(self) -> None:
        registry = AIProviderRegistry()
        with pytest.raises(KeyError):
            registry.create("unknown", api_key="x")

    def test_is_registered(self) -> None:
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        assert registry.is_registered("openai") is True
        assert registry.is_registered("gemini") is False

    def test_unregister(self) -> None:
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        registry.unregister("openai")
        assert registry.is_registered("openai") is False

    def test_invalid_class_raises(self) -> None:
        registry = AIProviderRegistry()
        with pytest.raises(ValueError):
            registry.register("bad", str)


class TestAIService:
    def test_chat_delegates_to_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SKOS_SECRET__OPENAI_API_KEY", "sk-test")
        from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import HierarchicalConfigAdapter
        from skos.m4.infrastructure.adapters.secrets.env_secret_adapter import EnvSecretManagerAdapter
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        config = HierarchicalConfigAdapter()
        secrets = EnvSecretManagerAdapter()
        service = AIService(registry, config, secrets)
        resp_body = {"model": "gpt-4o-mini", "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        with mock_urlopen(resp_body):
            result = service.chat("openai", [ChatMessage(role="user", content="Hi")])
        assert result.content == "OK"

    def test_list_providers(self) -> None:
        registry = AIProviderRegistry()
        registry.register("openai", OpenAIAdapter)
        registry.register("ollama", OllamaAdapter)
        config = MagicMock()
        secrets = MagicMock()
        service = AIService(registry, config, secrets)
        assert service.list_providers() == ["ollama", "openai"]
