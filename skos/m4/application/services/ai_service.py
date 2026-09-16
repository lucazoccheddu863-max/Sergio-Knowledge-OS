"""Application service for AI provider operations."""
from __future__ import annotations

from dataclasses import replace
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

    def _default_provider_name(self) -> str:
        provider = self._config.get("ai_primary_provider", default="ollama")
        return provider if isinstance(provider, str) and provider else "ollama"

    def chat(
        self,
        provider_or_request: str | ChatRequest,
        messages: list[ChatMessage] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if isinstance(provider_or_request, ChatRequest):
            provider_name = self._default_provider_name()
            request = provider_or_request
            if not request.model:
                configured_model = self._config.get(
                    f"ai_providers.{provider_name}.chat_model",
                    default=self._config.get("ai_local_model", default=""),
                )
                if configured_model:
                    request = replace(request, model=str(configured_model))
        else:
            provider_name = provider_or_request
            request = ChatRequest(messages=messages or [], **kwargs)
        provider = self._get_provider(provider_name)
        return provider.chat(request)

    def embed(
        self,
        provider_or_request: str | EmbeddingRequest,
        texts: list[str] | None = None,
        **kwargs: Any,
    ) -> EmbeddingResult:
        if isinstance(provider_or_request, EmbeddingRequest):
            provider_name = self._default_provider_name()
            request = provider_or_request
            if not request.model:
                configured_model = self._config.get(
                    f"ai_providers.{provider_name}.embedding_model",
                    default=self._config.get("ai_embedding_model", default=""),
                )
                if configured_model:
                    request = replace(request, model=str(configured_model))
        else:
            provider_name = provider_or_request
            request = EmbeddingRequest(texts=texts or [], **kwargs)
        provider = self._get_provider(provider_name)
        return provider.embed(request)

    def health_check(self, provider_name: str | None = None) -> bool:
        provider = self._get_provider(provider_name or self._default_provider_name())
        return provider.health_check()

    def list_models(self, provider_name: str) -> list[str]:
        provider = self._get_provider(provider_name)
        return provider.list_models()

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()
