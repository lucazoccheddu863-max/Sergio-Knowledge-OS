"""Domain models for AI provider interactions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatRequest:
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponse:
    content: str
    model: str
    usage_prompt_tokens: int = 0
    usage_completion_tokens: int = 0
    finish_reason: str = "stop"


@dataclass(frozen=True)
class EmbeddingRequest:
    texts: list[str]
    model: str | None = None
    dimensions: int | None = None


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    dimensions: int
