"""Tests for the executable AI service contract used by search and RAG."""
from __future__ import annotations

from skos.m4.application.services.ai_service import AIService
from skos.m4.domain.ai_models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResult,
)
from skos.m4.infrastructure.adapters.ai_providers.provider_registry import AIProviderRegistry
from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderPort
from skos.m4.infrastructure.ports.secret_port import SecretManagerPort
from skos.m6.production import build_release_status


class FakeProvider(AIProviderPort):
    last_chat_model = ""
    last_embedding_model = ""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    @property
    def provider_name(self) -> str:
        return "fake"

    def chat(self, request: ChatRequest) -> ChatResponse:
        type(self).last_chat_model = request.model
        return ChatResponse(content=request.messages[-1].content, model="fake-chat")

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        type(self).last_embedding_model = request.model
        return EmbeddingResult(
            vectors=[[float(len(text))] for text in request.texts],
            model="fake-embed",
            dimensions=1,
        )

    def health_check(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return ["fake-chat", "fake-embed"]


class EmptySecrets(SecretManagerPort):
    def get(self, ref):
        raise KeyError(ref.key)

    def set(self, ref, value: str) -> None:
        return None

    def delete(self, ref) -> None:
        return None

    def exists(self, ref) -> bool:
        return False

    def list_keys(self, namespace: str = "default") -> list[str]:
        return []


def build_service() -> AIService:
    registry = AIProviderRegistry()
    registry.register("fake", FakeProvider)
    config = HierarchicalConfigAdapter(defaults={"ai_primary_provider": "fake"})
    return AIService(registry, config, EmptySecrets())


def test_structured_embedding_request_uses_configured_provider() -> None:
    result = build_service().embed(EmbeddingRequest(texts=["one", "three"]))

    assert result.model == "fake-embed"
    assert result.vectors == [[3.0], [5.0]]


def test_structured_chat_request_uses_configured_provider() -> None:
    request = ChatRequest(messages=[ChatMessage(role="user", content="hello runtime")])

    result = build_service().chat(request)

    assert result.content == "hello runtime"
    assert result.model == "fake-chat"


def test_health_check_uses_configured_provider_by_default() -> None:
    assert build_service().health_check() is True


def test_release_status_supports_m7_and_future_alpha_milestones(tmp_path) -> None:
    (tmp_path / "VERSION").write_text("0.7.0-alpha1\n", encoding="utf-8")

    status = build_release_status(tmp_path)

    assert status.milestone == "M7.1"


def test_structured_requests_use_configured_models() -> None:
    registry = AIProviderRegistry()
    registry.register("fake", FakeProvider)
    config = HierarchicalConfigAdapter(
        defaults={
            "ai_primary_provider": "fake",
            "ai_local_model": "configured-chat",
            "ai_embedding_model": "configured-embed",
        }
    )
    service = AIService(registry, config, EmptySecrets())

    service.chat(ChatRequest(messages=[ChatMessage(role="user", content="hello")]))
    service.embed(EmbeddingRequest(texts=["knowledge"]))

    assert FakeProvider.last_chat_model == "configured-chat"
    assert FakeProvider.last_embedding_model == "configured-embed"
