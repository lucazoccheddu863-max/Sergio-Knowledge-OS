"""Moonshot Kimi adapter."""
from __future__ import annotations

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.infrastructure.adapters.ai_providers._http_mixin import HTTPMixin
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderAuthError, AIProviderError, AIProviderPort


class KimiAdapter(HTTPMixin, AIProviderPort):
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_CHAT_MODEL = "moonshot-v1-8k"

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 60) -> None:
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "kimi"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def chat(self, request: ChatRequest) -> ChatResponse:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": request.model or self.DEFAULT_CHAT_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        payload.update(request.extra)
        try:
            resp = self._post_json(url, self._headers(), payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        choice = resp["choices"][0]
        usage = resp.get("usage", {})
        return ChatResponse(
            content=choice["message"]["content"],
            model=resp.get("model", request.model or self.DEFAULT_CHAT_MODEL),
            usage_prompt_tokens=usage.get("prompt_tokens", 0),
            usage_completion_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        raise NotImplementedError("Kimi embedding API is not available. Use another provider.")

    def health_check(self) -> bool:
        try:
            self._get_json(f"{self._base_url}/models", self._headers(), timeout=10)
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._get_json(f"{self._base_url}/models", self._headers(), timeout=10)
            return sorted(m["id"] for m in resp.get("data", []))
        except Exception:
            return []
