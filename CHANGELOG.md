## [0.4.0-alpha12] — 2026-08-09

### Milestone 4.10 — Observability & Operations Adapter

#### Added
- `MetricsPort` — infrastructure port for metrics collection
- `TracingPort` — infrastructure port for distributed tracing
- `LoggingPort` — infrastructure port for structured logging
- `PrometheusMetricsAdapter` — Prometheus-backed metrics with isolated `CollectorRegistry`
- `OpenTelemetryTracerAdapter` — OpenTelemetry tracing with no-op fallback
- `StructuredLoggingAdapter` — JSON-structured logging to configurable output
- `/metrics` endpoint — Prometheus exposition format
- Observability integration in `FastAPIAdapter`:
  - Request counting via `http_requests_total`
  - Latency histogram via `http_request_duration_seconds`
  - Structured logging on all endpoints
  - Span tracing on query endpoint
  - Extended health check including metrics/tracing/logging status
- `tests/m4/test_observability.py` — 25 tests covering ports, adapters, and integration
- `setup_milestone4_10.py` and `verify_milestone4_10.py`

#### Changed
- `FastAPIAdapter` version bumped to `0.4.0-alpha12`
- `FastAPIAdapter` milestone bumped to `M4.10`
- `FastAPIAdapter.__init__` accepts optional `metrics`, `tracer`, `logger` parameters
- Health endpoint now reports observability subsystem status
- Error handlers now log structured messages and count requests

#### Design Decisions
- All observability adapters are optional — FastAPIAdapter works without them
- Prometheus adapter uses isolated `CollectorRegistry` to avoid `DuplicateTimeseries`
- OpenTelemetry adapter falls back to no-op spans when library unavailable
- Structured logging writes JSON to configurable output stream
- No breaking changes to API Contract v1 (frozen in M4.9.5)

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched
- M4.6 — untouched
- M4.7 — untouched
- M4.8 — untouched
- M4.9 — untouched
- M4.9.5 — untouched

* * *

## [0.4.0-alpha11] — 2026-08-08

### Milestone 4.9.5 — API Contract Freeze

#### Added
- `APIError` unified error model in DTOs
- `RequestValidationError` handler returning unified `APIError` schema
- `HTTPException` handler returning unified `APIError` schema
- Generic `Exception` handler returning unified `APIError` schema
- Admin route placeholder: `GET /api/v1/admin/status`
- OpenAPI schema auto-generation at `/api/v1/openapi.json`
- Swagger UI at `/api/v1/docs`
- ReDoc at `/api/v1/redoc`
- `docs/api_contract.md` — frozen API Contract v1 documentation
- `setup_milestone4_95.py` and `verify_milestone4_95.py`
- Contract tests: OpenAPI schema validation, error schema validation, admin routes

#### Changed
- `FastAPIAdapter` version bumped to `0.4.0-alpha11`
- `FastAPIAdapter` milestone bumped to `M4.9.5`
- Error responses now follow unified `APIError` schema with `request_id` UUID
- `VERSION` and `VERSION.m4.4` bumped to `0.4.0-alpha11`

#### Design Decisions
- API Contract v1 is frozen — no breaking changes without major version bump
- All error responses (422, 500, unexpected) follow identical `APIError` schema
- Admin routes are prefixed with `/api/v1/admin/*` and reserved for M4.10+
- OpenAPI schema is the single source of truth for API documentation

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched
- M4.6 — untouched
- M4.7 — untouched
- M4.8 — untouched
- M4.9 — untouched

* * *

## [0.4.0-alpha10] — 2026-08-08

### Milestone 4.9 — REST API Adapter

#### Added
- `FastAPIAdapter` — FastAPI infrastructure adapter exposing REST API
- Domain DTOs in `skos/m4/infrastructure/adapters/api/dto.py`
- Endpoints:
  - `POST /api/v1/query` — unified query execution
  - `GET /api/v1/health` — system health check
  - `GET /api/v1/status` — system status and version
  - `GET /api/v1/engines` — list available engines
- `tests/m4/test_api_adapter.py` — 7 tests covering all endpoints
- `setup_milestone4_9.py` and `verify_milestone4_9.py`

#### Changed
- `VERSION` bumped to `0.4.0-alpha10`
- `pyproject.toml` version bump
- `MILESTONES/M4/STATUS.md` updated to reflect real state

#### Design Decisions
- FastAPI is exclusively an infrastructure adapter — zero dependency from domain/application layers
- `FastAPIAdapter` receives `QueryOrchestratorPort` and `ConfigurationPort` via constructor
- All DTOs are Pydantic models decoupled from domain dataclasses
- Forward-compatible with M4.9.5 (Admin API) and M5 (full production API)

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched
- M4.6 — untouched
- M4.7 — untouched
- M4.8 — untouched

* * *

## [0.4.0-alpha9] — 2026-08-08

### Milestone 4.8 — Query Orchestrator

#### Added
- `QueryOrchestratorPort` — abstract interface for unified querying
- `QueryOrchestratorService` — routes queries to semantic search, RAG, and knowledge graph
- Domain models: `UnifiedQuery`, `UnifiedResult`
- Query modes: `auto`, `semantic`, `rag`, `graph`, `hybrid`
- `tests/m4/test_query_orchestrator.py` — 12 tests covering all routing modes
- Events: `orchestrator.query_executed`, `orchestrator.query_failed`
- Config keys: `m4.orchestrator.default_mode`, `m4.orchestrator.max_query_time_ms`

#### Changed
- `VERSION` bumped to `0.4.0-alpha9`
- `pyproject.toml` version bump
- `config.yaml` adds `m4.orchestrator.*` configuration
- `skos/m4/domain/__init__.py` exports orchestrator models

#### Design Decisions
- `QueryOrchestratorService` talks ONLY to application services, never to concrete adapters
- `auto` mode routes to semantic search + RAG (default for end users)
- `hybrid` mode routes to all three engines (semantic + RAG + graph)
- `graph` mode queries the knowledge graph by entity name
- Forward-compatible with M5 (API Layer): `UnifiedResult` is the contract for API responses

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched
- M4.6 — untouched
- M4.7 — untouched

---

## [0.4.0-alpha8] — 2026-08-08

### Milestone 4.7 — Knowledge Graph Integration

#### Added
- `KnowledgeGraphPort` — abstract interface for graph databases
- `InMemoryKnowledgeGraphAdapter` — in-memory graph store (prototype)
- `KnowledgeGraphService` — orchestrates entity/relation indexing and querying
- Domain models: `Entity`, `Relation`, `GraphQuery`, `GraphResult`
- `tests/m4/test_knowledge_graph.py` — 18 tests covering domain, adapter, service
- Events: `kg.document_indexed`, `kg.queried`, `kg.entity_deleted`
- Config keys: `m4.knowledge_graph.default_depth`, `m4.knowledge_graph.max_results`

#### Changed
- `VERSION` bumped to `0.4.0-alpha8`
- `pyproject.toml` version bump
- `config.yaml` adds `m4.knowledge_graph.*` configuration
- `skos/m4/domain/__init__.py` exports KG models

#### Design Decisions
- `KnowledgeGraphService` talks ONLY to `KnowledgeGraphPort`, never to concrete adapters
- `InMemoryKnowledgeGraphAdapter` validates entity existence before adding relations
- Forward-compatible with Neo4j/NetworkX: swap adapter, zero application changes
- Graph query supports filtering by entity name (substring), type, and relation type

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched
- M4.6 — untouched

---

## [0.4.0-alpha7] — 2026-08-08

### Milestone 4.6 — RAG Pipeline

#### Added
- `RAGPipelinePort` — abstract interface for RAG implementations
- `RAGPipelineService` — orchestrates retrieve → augment → generate
- Domain models: `RAGQuery`, `RAGContext`, `RAGResult`
- `tests/m4/test_rag_pipeline.py` — 12 tests covering full RAG flow
- Events: `rag.response_generated`, `rag.failed`
- Config keys: `m4.rag.default_top_k`, `m4.rag.system_prompt`

#### Changed
- `VERSION` bumped to `0.4.0-alpha7`
- `pyproject.toml` version bump
- `config.yaml` adds `m4.rag.*` configuration
- `skos/m4/domain/__init__.py` exports RAG models

#### Design Decisions
- `RAGPipelineService` talks to `SemanticSearchService` and `AIService`, never to concrete adapters
- Context built from `RankedDocument` list, formatted as `[Document N] text` blocks
- Custom system prompt supported per-query via `RAGQuery.system_prompt`
- Forward-compatible with M5 (API Layer): RAGResult provides complete response + context

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched
- M4.5 — untouched

---

## [0.4.0-alpha6] — 2026-08-08

### Milestone 4.5 — Semantic Search Engine

#### Added
- `SemanticSearchPort` — abstract interface for semantic search engines
- `ChromaSemanticSearchAdapter` — ChromaDB implementation delegating to VectorStorePort
- `SemanticSearchService` — orchestrates query embedding → vector search → ranking → events
- `DocumentIndexerService` — orchestrates chunking → embedding → indexing → events
- Domain models: `SemanticQuery`, `SemanticSearchResult`, `RankedDocument`, `SearchFilter`
- `tests/m4/test_semantic_search.py` — 19 tests covering domain, port, adapter, services
- Events: `search.completed`, `search.failed`, `document.indexed`, `document.index_failed`

#### Changed
- `VERSION` bumped to `0.4.0-alpha6`
- `pyproject.toml` version bump
- `config.yaml` adds `m4.semantic_search.*` configuration keys
- `skos/m4/domain/__init__.py` exports search models

#### Design Decisions
- `SemanticSearchService` talks ONLY to `VectorStorePort` and `AIService`, never to concrete adapters
- `DocumentIndexerService` talks to `EmbeddingPipeline` and `VectorStoreService`, never to concrete adapters
- Forward-compatible with M4.6 (RAG): `RankedDocument` provides the contract between search and RAG
- Empty `index_document` on adapter forces use of `DocumentIndexerService` for embedding generation

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched
- M4.4 — untouched

---

## [0.4.0-alpha5] — 2026-08-07

### Milestone 4.4 — Vector DB Integration

#### Added
- `VectorStorePort` — abstract interface for vector database operations
- `ChromaDBAdapter` — ChromaDB implementation with:
  - Automatic collection name sanitisation (alphanumeric, underscore, hyphen; max 63 chars)
  - Empty metadata normalisation to prevent ChromaDB runtime errors
  - In-memory and persistent client support
- Domain models: `VectorRecord`, `VectorQuery`, `SearchResult`
- `VectorStoreService` — application service bridging embedding pipeline and vector store
- `tests/m4/test_vector_store.py` — 15 tests covering unit, integration, and service layers

#### Changed
- `VERSION` bumped to `0.4.0-alpha5`
- `pyproject.toml` adds `chromadb>=0.5.0` dependency
- `skos/m4/domain/__init__.py` exports vector models

#### Design Decisions
- Vector store is infrastructure (adapter pattern) — stays in infrastructure layer
- VectorStoreService is application orchestration — uses VectorStorePort
- Collection names sanitised transparently to shield users from ChromaDB constraints
- Empty metadata normalised to None to avoid ChromaDB empty-dict rejection

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched
- M4.3 — untouched

---

# Changelog

## [0.4.0-alpha4] — 2026-08-07

### Milestone 4.3 — Embeddings Generation Pipeline

#### Added
- `ChunkingStrategy` ABC with two implementations:
  - `FixedSizeChunking` — word-based sliding window with configurable overlap
  - `ParagraphChunking` — paragraph boundary splitting with fallback to fixed-size
- `TextChunk` value object with source tracking and metadata
- `EmbeddingPipeline` application service:
  - Automatic text chunking before embedding generation
  - Configurable batch processing (respects `m4.embedding.batch_size`)
  - Event emission (`embedding.completed`) via EventBus
  - Direct chunk embedding for pre-chunked content
- `tests/m4/test_embedding_pipeline.py` — 11 tests covering chunking strategies and pipeline

#### Changed
- `VERSION` bumped to `0.4.0-alpha4`
- `skos/m4/domain/__init__.py` exports chunking classes

#### Design Decisions
- Chunking is domain logic (strategy pattern) — stays in domain layer
- Pipeline is application orchestration — uses AIService, EventBus, Config
- Batch size configurable via hierarchical config
- Events decouple embedding completion from downstream consumers (M4.4 Vector DB)

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched
- M4.2 — untouched

---

# Changelog

## [0.4.0-alpha3] — 2026-08-07

### Milestone 4.2 — AI Provider Abstraction

#### Added
- `AIProviderPort` — unified abstract interface for chat and embeddings
- `OpenAIAdapter`, `GeminiAdapter`, `KimiAdapter`, `ClaudeAdapter`, `OllamaAdapter`
- `AIProviderRegistry` — runtime registry/factory for provider adapters
- `AIService` — application service orchestrating provider operations
- Domain models: `ChatMessage`, `ChatRequest`, `ChatResponse`, `EmbeddingRequest`, `EmbeddingResult`
- `tests/m4/test_ai_providers.py` — 23 tests with mocked HTTP
- Architecture rule verification extended to AI provider layer

#### Changed
- `VERSION` bumped to `0.4.0-alpha3`
- `skos/m4/domain/__init__.py` exports AI models

#### Design Decisions
- All adapters use `urllib.request` (stdlib) — zero external HTTP dependencies
- Embeddings unavailable for Kimi and Claude — raise `NotImplementedError`
- HTTP calls fully mockable for testing

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched
- M4.1 Step 2 — untouched

---

## [0.4.0-alpha2] — 2026-08-07

### Milestone 4.1 — Step 2: Event Bus & Application Layer

#### Added
- `InMemoryEventBus` adapter
- `ImportOrchestrator` application service
- Event bus and application service tests

---

## [0.4.0-alpha1] — 2026-08-05

### Milestone 4.1 — Step 1: Foundation

#### Added
- Service Container with DI
- Hierarchical Configuration Adapter
- Environment Variable Secret Manager Adapter

---

## [0.3.0] — 2026-08-05

### Milestone 3: Database Layer & Repository Pattern

#### Added
- Abstract Database interface, SQLite implementation, Repository Pattern
- FTS5Engine, ImportSession, DbImportManager

---

## [0.2.0] — 2026-08-04

### Milestone 2: Import Engine

#### Added
- ChatGPT and Gemini parsers, Import manager, SHA-256 hashing
