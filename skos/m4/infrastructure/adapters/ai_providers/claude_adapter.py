"""Anthropic Claude adapter."""
from __future__ import annotations

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.infrastructure.adapters.ai_providers._http_mixin import HTTPMixin
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderAuthError, AIProviderError, AIProviderPort


class ClaudeAdapter(HTTPMixin, AIProviderPort):
    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    DEFAULT_CHAT_MODEL = "claude-3-haiku-20240307"

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 60) -> None:
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "claude"

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key, "anthropic-version": "2023-06-01"}

    def chat(self, request: ChatRequest) -> ChatResponse:
        url = f"{self._base_url}/messages"
        system_msg = ""
        messages = []
        for m in request.messages:
            if m.role == "system":
                system_msg = m.content
            else:
                messages.append({"role": m.role, "content": m.content})
        payload: dict[str, Any] = {
            "model": request.model or self.DEFAULT_CHAT_MODEL,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
        }
        if system_msg:
            payload["system"] = system_msg
        payload.update(request.extra)
        try:
            resp = self._post_json(url, self._headers(), payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        content = resp["content"][0]["text"]
        usage = resp.get("usage", {})
        return ChatResponse(
            content=content,
            model=resp.get("model", request.model or self.DEFAULT_CHAT_MODEL),
            usage_prompt_tokens=usage.get("input_tokens", 0),
            usage_completion_tokens=usage.get("output_tokens", 0),
            finish_reason=resp.get("stop_reason", "end_turn"),
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        raise NotImplementedError("Claude embedding API is not available. Use another provider.")

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
