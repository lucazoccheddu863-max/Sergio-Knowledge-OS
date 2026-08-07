"""Application service for AI provider operations."""
from __future__ import annotations

from typing import Any

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.domain.value_objects import SecretRef
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderPort
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.secret_port import SecretManagerPort


class AIService:
    def __init__(self, registry: Any, config: ConfigurationPort, secrets: SecretManagerPort) -> None:
        self._registry = registry
        self._config = config
        self._secrets = secrets

    def _get_provider(self, name: str) -> AIProviderPort:
        secret_key = f"{name.lower()}_api_key"
        try:
            api_key = self._secrets.get(SecretRef(key=secret_key))
        except Exception:
            api_key = ""
        base_url = self._config.get(f"ai_providers.{name.lower()}.base_url")
        timeout = self._config.get(f"ai_providers.{name.lower()}.timeout", default=60)
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        kwargs["timeout"] = timeout
        return self._registry.create(name, **kwargs)

    def chat(self, provider_name: str, messages: list[ChatMessage], **kwargs: Any) -> ChatResponse:
        provider = self._get_provider(provider_name)
        request = ChatRequest(messages=messages, **kwargs)
        return provider.chat(request)

    def embed(self, provider_name: str, texts: list[str], **kwargs: Any) -> EmbeddingResult:
        provider = self._get_provider(provider_name)
        request = EmbeddingRequest(texts=texts, **kwargs)
        return provider.embed(request)

    def health_check(self, provider_name: str) -> bool:
        provider = self._get_provider(provider_name)
        return provider.health_check()

    def list_models(self, provider_name: str) -> list[str]:
        provider = self._get_provider(provider_name)
        return provider.list_models()

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()
