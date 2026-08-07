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
