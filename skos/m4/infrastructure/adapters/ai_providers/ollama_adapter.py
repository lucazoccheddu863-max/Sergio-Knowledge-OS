"""Ollama local adapter."""
from __future__ import annotations

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.infrastructure.adapters.ai_providers._http_mixin import HTTPMixin
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderError, AIProviderPort


class OllamaAdapter(HTTPMixin, AIProviderPort):
    DEFAULT_BASE_URL = "http://localhost:11434/api"
    DEFAULT_CHAT_MODEL = "llama3.1"
    DEFAULT_EMBED_MODEL = "nomic-embed-text"

    def __init__(self, api_key: str = "", base_url: str | None = None, timeout: int = 120) -> None:
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    def chat(self, request: ChatRequest) -> ChatResponse:
        url = f"{self._base_url}/chat"
        payload = {
            "model": request.model or self.DEFAULT_CHAT_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens
        payload.update(request.extra)
        try:
            resp = self._post_json(url, {}, payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        message = resp.get("message", {})
        return ChatResponse(
            content=message.get("content", ""),
            model=resp.get("model", request.model or self.DEFAULT_CHAT_MODEL),
            usage_prompt_tokens=resp.get("prompt_eval_count", 0),
            usage_completion_tokens=resp.get("eval_count", 0),
            finish_reason="stop",
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        url = f"{self._base_url}/embed"
        payload = {
            "model": request.model or self.DEFAULT_EMBED_MODEL,
            "input": request.texts,
        }
        try:
            resp = self._post_json(url, {}, payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        vectors = resp.get("embeddings", [])
        model = resp.get("model", request.model or self.DEFAULT_EMBED_MODEL)
        dims = len(vectors[0]) if vectors else 0
        return EmbeddingResult(vectors=vectors, model=model, dimensions=dims)

    def health_check(self) -> bool:
        try:
            self._get_json(f"{self._base_url}/tags", {}, timeout=5)
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._get_json(f"{self._base_url}/tags", {}, timeout=10)
            return sorted(m["name"] for m in resp.get("models", []))
        except Exception:
            return []
