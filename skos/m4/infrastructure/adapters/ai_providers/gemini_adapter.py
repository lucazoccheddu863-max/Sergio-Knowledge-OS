"""Google Gemini adapter."""
from __future__ import annotations

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.infrastructure.adapters.ai_providers._http_mixin import HTTPMixin
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderAuthError, AIProviderError, AIProviderPort


class GeminiAdapter(HTTPMixin, AIProviderPort):
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_CHAT_MODEL = "gemini-1.5-flash"
    DEFAULT_EMBED_MODEL = "text-embedding-004"

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 60) -> None:
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _headers(self) -> dict[str, str]:
        return {"x-goog-api-key": self._api_key}

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.DEFAULT_CHAT_MODEL
        url = f"{self._base_url}/models/{model}:generateContent"
        contents = []
        for m in request.messages:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        payload = {"contents": contents}
        try:
            resp = self._post_json(url, self._headers(), payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        candidate = resp["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]
        usage = resp.get("usageMetadata", {})
        return ChatResponse(
            content=text,
            model=model,
            usage_prompt_tokens=usage.get("promptTokenCount", 0),
            usage_completion_tokens=usage.get("candidatesTokenCount", 0),
            finish_reason=candidate.get("finishReason", "STOP").lower(),
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        model = request.model or self.DEFAULT_EMBED_MODEL
        url = f"{self._base_url}/models/{model}:batchEmbedContents"
        payload = {
            "requests": [
                {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
                for t in request.texts
            ]
        }
        try:
            resp = self._post_json(url, self._headers(), payload, timeout=self._timeout)
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc
        vectors = [item["embedding"]["values"] for item in resp["embeddings"]]
        dims = len(vectors[0]) if vectors else 0
        return EmbeddingResult(vectors=vectors, model=model, dimensions=dims)

    def health_check(self) -> bool:
        try:
            url = f"{self._base_url}/models?key={self._api_key}"
            self._get_json(url, {}, timeout=10)
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            url = f"{self._base_url}/models?key={self._api_key}"
            resp = self._get_json(url, {}, timeout=10)
            return sorted(m["name"].replace("models/", "") for m in resp.get("models", []))
        except Exception:
            return []
