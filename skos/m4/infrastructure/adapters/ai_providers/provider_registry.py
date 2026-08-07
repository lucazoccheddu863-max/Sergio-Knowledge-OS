"""Provider registry and factory for AI adapters."""
from __future__ import annotations

from typing import Any, TypeVar

from skos.m4.infrastructure.ports.ai_provider_port import AIProviderPort

T = TypeVar("T", bound=AIProviderPort)


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[AIProviderPort]] = {}

    def register(self, name: str, provider_class: type[T]) -> None:
        if not issubclass(provider_class, AIProviderPort):
            raise ValueError(f"{provider_class.__name__} must implement AIProviderPort")
        self._providers[name.lower()] = provider_class

    def create(self, name: str, **kwargs: Any) -> AIProviderPort:
        key = name.lower()
        if key not in self._providers:
            raise KeyError(f"Unknown AI provider: {name}. Available: {self.list_providers()}")
        return self._providers[key](**kwargs)

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def is_registered(self, name: str) -> bool:
        return name.lower() in self._providers

    def unregister(self, name: str) -> None:
        self._providers.pop(name.lower(), None)
