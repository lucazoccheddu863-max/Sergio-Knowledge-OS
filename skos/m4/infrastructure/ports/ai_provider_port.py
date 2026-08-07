"""AI Provider Port — abstract interface for AI services."""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.domain.ai_models import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult


class AIProviderPort(ABC):
    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResponse:
        pass

    @abstractmethod
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class AIProviderError(Exception):
    pass


class AIProviderAuthError(AIProviderError):
    pass


class AIProviderRateLimitError(AIProviderError):
    pass


class AIProviderNotFoundError(AIProviderError):
    pass
