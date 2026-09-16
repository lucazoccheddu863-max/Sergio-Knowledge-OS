"""Tests for the complete M7 application runtime assembly."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from skos.m4.domain.ai_models import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResult
from skos.m4.domain.query_orchestrator_models import UnifiedQuery
from skos.m4.domain.vector_models import SearchResult, VectorQuery, VectorRecord
from skos.m4.infrastructure.adapters.ai_providers.provider_registry import AIProviderRegistry
from skos.m4.infrastructure.ports.ai_provider_port import AIProviderPort
from skos.m4.infrastructure.ports.secret_port import SecretManagerPort
from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort
from skos.m7.runtime import build_application_runtime, build_provider_registry


class RuntimeProvider(AIProviderPort):
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    @property
    def provider_name(self) -> str:
        return "ollama"

    def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(content="runtime answer", model="runtime-chat")

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            vectors=[[0.1, 0.2, 0.3] for _ in request.texts],
            model="runtime-embed",
            dimensions=3,
        )

    def health_check(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return ["runtime-chat", "runtime-embed"]


class RuntimeSecrets(SecretManagerPort):
    def get(self, ref):
        raise KeyError(ref.key)

    def set(self, ref, value: str) -> None:
        return None

    def delete(self, ref) -> None:
        return None

    def exists(self, ref) -> bool:
        return False

    def list_keys(self, namespace: str = "default") -> list[str]:
        return []


class MemoryVectorStore(VectorStorePort):
    def __init__(self) -> None:
        self.records = [
            VectorRecord(
                id="doc-1",
                vector=[0.1, 0.2, 0.3],
                text="Sergio Knowledge OS runtime document",
                metadata={"source": "test"},
                source_id="source-1",
            )
        ]

    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        self.records = list(records)

    def search(self, collection_name: str, query: VectorQuery) -> SearchResult:
        return SearchResult(records=self.records[: query.top_k], total_found=len(self.records))

    def delete(self, collection_name: str, ids: list[str]) -> None:
        self.records = [record for record in self.records if record.id not in ids]

    def get_collection(self, collection_name: str):
        return collection_name

    def list_collections(self) -> list[str]:
        return ["semantic_search"]

    def delete_collection(self, collection_name: str) -> None:
        self.records = []

    def health_check(self) -> bool:
        return True


def runtime_registry() -> AIProviderRegistry:
    registry = AIProviderRegistry()
    registry.register("ollama", RuntimeProvider)
    return registry


def build_test_runtime(tmp_path: Path):
    return build_application_runtime(
        root_path=tmp_path,
        vector_store=MemoryVectorStore(),
        providers=runtime_registry(),
        secrets=RuntimeSecrets(),
    )


def test_provider_registry_contains_all_supported_adapters() -> None:
    assert build_provider_registry().list_providers() == [
        "claude",
        "gemini",
        "kimi",
        "ollama",
        "openai",
    ]


def test_application_runtime_assembles_real_services(tmp_path: Path) -> None:
    runtime = build_test_runtime(tmp_path)

    assert runtime.persistence.mode == "memory"
    assert runtime.orchestrator.health_check() is True
    assert runtime.app.title == "Sergio Knowledge OS API"


def test_semantic_query_runs_through_assembled_runtime(tmp_path: Path) -> None:
    runtime = build_test_runtime(tmp_path)

    result = runtime.orchestrator.execute(UnifiedQuery(text="runtime", mode="semantic"))

    assert result.engines_used == ["semantic"]
    assert result.semantic_result is not None
    assert result.semantic_result.results[0].id == "doc-1"
    assert result.semantic_result.embedding_model == "runtime-embed"


def test_query_api_uses_assembled_graph_runtime(tmp_path: Path) -> None:
    client = TestClient(build_test_runtime(tmp_path).app)

    response = client.post("/api/v1/query", json={"text": "Sergio", "mode": "graph"})

    assert response.status_code == 200
    assert response.json()["engines_used"] == ["graph"]


def test_local_admin_routes_are_open_when_auth_is_disabled(tmp_path: Path) -> None:
    client = TestClient(build_test_runtime(tmp_path).app)

    response = client.get("/api/v1/admin/snapshot")

    assert response.status_code == 200
    assert response.json()["release"]["version"]


def test_rag_query_api_returns_answer_with_sources(tmp_path: Path) -> None:
    client = TestClient(build_test_runtime(tmp_path).app)

    response = client.post(
        "/api/v1/query",
        json={"text": "What is in the knowledge base?", "mode": "rag", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["rag_result"]["response"]["content"] == "runtime answer"
    assert payload["rag_result"]["context"]["documents"][0]["source_id"] == "source-1"
