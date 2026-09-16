"""Operational status for the configured AI runtime."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from skos.m4.application.services.ai_service import AIService
from skos.m4.infrastructure.ports.config_port import ConfigurationPort


@dataclass(frozen=True)
class AIRuntimeStatus:
    provider: str
    healthy: bool
    ready: bool
    chat_model: str
    embedding_model: str
    models: tuple[str, ...]
    missing_models: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["models"] = list(self.models)
        result["missing_models"] = list(self.missing_models)
        return result


class AIRuntimeStatusService:
    """Report provider health and required model availability."""

    def __init__(self, ai_service: AIService, config: ConfigurationPort) -> None:
        self._ai_service = ai_service
        self._config = config

    def inspect(self) -> AIRuntimeStatus:
        provider = str(self._config.get("ai_primary_provider", default="ollama"))
        chat_model = str(self._config.get("ai_local_model", default=""))
        embedding_model = str(self._config.get("ai_embedding_model", default=""))
        healthy = self._ai_service.health_check(provider)
        models = tuple(self._ai_service.list_models(provider)) if healthy else ()
        required = tuple(model for model in (chat_model, embedding_model) if model)
        missing = tuple(model for model in required if not self._model_available(model, models))
        return AIRuntimeStatus(
            provider=provider,
            healthy=healthy,
            ready=healthy and not missing,
            chat_model=chat_model,
            embedding_model=embedding_model,
            models=models,
            missing_models=missing,
        )

    @staticmethod
    def _model_available(required: str, available: tuple[str, ...]) -> bool:
        required_base = required.split(":", 1)[0]
        return any(model == required or model.split(":", 1)[0] == required_base for model in available)
