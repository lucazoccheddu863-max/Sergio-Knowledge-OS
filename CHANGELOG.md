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
