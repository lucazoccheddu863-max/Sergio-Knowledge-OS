"""Executable application runtime assembly for Sergio Knowledge OS."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import uuid
from typing import Any, Callable

from fastapi import FastAPI

from skos.m4.application.services.ai_service import AIService
from skos.m4.application.services.knowledge_graph_service import KnowledgeGraphService
from skos.m4.application.services.query_orchestrator_service import QueryOrchestratorService
from skos.m4.application.services.rag_pipeline_service import RAGPipelineService
from skos.m4.application.services.semantic_search_service import SemanticSearchService
from skos.m4.infrastructure.adapters.ai_providers.claude_adapter import ClaudeAdapter
from skos.m4.infrastructure.adapters.ai_providers.gemini_adapter import GeminiAdapter
from skos.m4.infrastructure.adapters.ai_providers.kimi_adapter import KimiAdapter
from skos.m4.infrastructure.adapters.ai_providers.ollama_adapter import OllamaAdapter
from skos.m4.infrastructure.adapters.ai_providers.openai_adapter import OpenAIAdapter
from skos.m4.infrastructure.adapters.ai_providers.provider_registry import AIProviderRegistry
from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m4.infrastructure.adapters.secrets.env_secret_adapter import EnvSecretManagerAdapter
from skos.m4.infrastructure.adapters.vector_store.chromadb_adapter import ChromaDBAdapter
from skos.m4.infrastructure.ports.secret_port import SecretManagerPort
from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort
from skos.m4.infrastructure.ports.event_bus_port import DomainEvent, EventBusPort, Subscription
from skos.m5.runtime import PersistenceRuntime, build_persistence_runtime


@dataclass(frozen=True)
class ApplicationRuntime:
    """Fully assembled executable application and its core services."""

    root_path: Path
    config: HierarchicalConfigAdapter
    persistence: PersistenceRuntime
    event_bus: EventBusPort
    providers: AIProviderRegistry
    ai_service: AIService
    vector_store: VectorStorePort
    semantic_search: SemanticSearchService
    rag_pipeline: RAGPipelineService
    knowledge_graph: KnowledgeGraphService
    orchestrator: QueryOrchestratorService
    app: FastAPI


class ApplicationEventBus(EventBusPort):
    """Bridge application payload events to the frozen DomainEvent bus contract."""

    def __init__(self, delegate: EventBusPort) -> None:
        self._delegate = delegate

    def publish(self, event: DomainEvent | str, topic: str | dict[str, Any]) -> None:
        if isinstance(event, str) and isinstance(topic, dict):
            payload = dict(topic)
            event_type = str(payload.get("event", "application.event"))
            domain_event = DomainEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                correlation_id=str(payload.get("correlation_id", uuid.uuid4())),
                payload=payload,
            )
            self._delegate.publish(domain_event, event)
            return
        if not isinstance(event, DomainEvent) or not isinstance(topic, str):
            raise TypeError("publish requires DomainEvent/topic or topic/payload")
        self._delegate.publish(event, topic)

    def subscribe(
        self,
        topic: str,
        handler: Callable[[DomainEvent], None],
        group: str = "default",
    ) -> Subscription:
        return self._delegate.subscribe(topic, handler, group)

    def ack(self, delivery_tag: str) -> None:
        self._delegate.ack(delivery_tag)

    def nack(self, delivery_tag: str, requeue: bool = False) -> None:
        self._delegate.nack(delivery_tag, requeue)


def build_runtime_config(root_path: str | Path = ".") -> HierarchicalConfigAdapter:
    """Load runtime defaults and merge the repository config when present."""

    root = Path(root_path).resolve()
    config = HierarchicalConfigAdapter(
        defaults={
            "database_path": str(root / "data" / "sergio_knowledge.db"),
            "archive_root": str(root / "data" / "archive"),
            "backup_dir": str(root / "data" / "backups"),
            "release_dir": str(root / "data" / "releases"),
            "ai_primary_provider": "ollama",
            "m4": {
                "security": {"enabled": False, "auth_required": False},
                "semantic_search": {
                    "collection_name": "semantic_search",
                    "default_top_k": 5,
                    "max_results_per_query": 20,
                },
                "rag": {"default_top_k": 5},
            },
            "m5": {"persistence": {"mode": "memory"}},
            "m6": {"environment": "development"},
            "m7": {"vector_store": {"path": str(root / "data" / "chroma")}},
        }
    )
    config_path = root / "config.yaml"
    if config_path.is_file():
        config.load_from_file(config_path)
    return config


def build_provider_registry() -> AIProviderRegistry:
    """Register every supported AI provider adapter."""

    registry = AIProviderRegistry()
    registry.register("openai", OpenAIAdapter)
    registry.register("gemini", GeminiAdapter)
    registry.register("kimi", KimiAdapter)
    registry.register("claude", ClaudeAdapter)
    registry.register("ollama", OllamaAdapter)
    return registry


def build_application_runtime(
    root_path: str | Path = ".",
    *,
    vector_store: VectorStorePort | None = None,
    providers: AIProviderRegistry | None = None,
    secrets: SecretManagerPort | None = None,
) -> ApplicationRuntime:
    """Assemble the real query runtime and FastAPI application."""

    root = Path(root_path).resolve()
    config = build_runtime_config(root)
    persistence = build_persistence_runtime(config)
    event_bus = ApplicationEventBus(persistence.event_bus)
    provider_registry = providers or build_provider_registry()
    secret_manager = secrets or EnvSecretManagerAdapter()
    ai_service = AIService(provider_registry, config, secret_manager)
    configured_store_path = Path(
        config.get("m7.vector_store.path", default=root / "data" / "chroma")
    )
    store_path = configured_store_path if configured_store_path.is_absolute() else root / configured_store_path
    store = vector_store or ChromaDBAdapter(persist_directory=str(store_path))
    semantic_search = SemanticSearchService(store, ai_service, config, event_bus)
    rag_pipeline = RAGPipelineService(semantic_search, ai_service, config, event_bus)
    knowledge_graph = KnowledgeGraphService(
        persistence.knowledge_graph,
        config,
        event_bus,
    )
    orchestrator = QueryOrchestratorService(
        semantic_search,
        rag_pipeline,
        knowledge_graph,
        config,
        event_bus,
    )
    app = FastAPIAdapter(
        orchestrator=orchestrator,
        config=config,
        auth=persistence.auth,
        rate_limiter=persistence.rate_limiter,
        audit=persistence.audit,
    ).app
    return ApplicationRuntime(
        root_path=root,
        config=config,
        persistence=persistence,
        event_bus=event_bus,
        providers=provider_registry,
        ai_service=ai_service,
        vector_store=store,
        semantic_search=semantic_search,
        rag_pipeline=rag_pipeline,
        knowledge_graph=knowledge_graph,
        orchestrator=orchestrator,
        app=app,
    )
