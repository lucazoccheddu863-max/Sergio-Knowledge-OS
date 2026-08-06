# Changelog

All notable changes to this project are documented in this file.

## [0.4.0-alpha2] — 2026-08-07

### Milestone 4.1 — Step 2: Event Bus & Application Layer

#### Added
- `InMemoryEventBus` adapter — thread-safe, synchronous pub/sub event bus
- `ImportOrchestrator` application service — emits domain events for import lifecycle
- Event bus tests (5 test cases) covering pub/sub, unsubscribe, multi-subscriber, fault tolerance
- Application service tests (3 test cases) covering start, complete, and failed import events
- Architecture rule verification — domain layer has zero infrastructure imports
- `docs/ROADMAP.md` — canonical project roadmap
- `docs/ARCHITECTURE.md` — system architecture documentation
- `MILESTONES/M4/STATUS.md` — milestone tracking

#### Changed
- `VERSION` bumped to `0.4.0-alpha2`

#### Frozen Baselines
- M2 (v0.2.x) — untouched
- M3 (v0.3.0) — untouched
- M4.1 Step 1 — untouched

---

## [0.4.0-alpha1] — 2026-08-05

### Milestone 4.1 — Step 1: Foundation

#### Added
- Service Container with Dependency Injection (singleton, scoped, transient lifecycles)
- Hierarchical Configuration Adapter (defaults, env vars, scoped overrides, deep merge)
- Environment Variable Secret Manager Adapter
- Abstract ports: `ConfigurationPort`, `SecretManagerPort`, `EventBusPort`
- Domain value objects: `ConfigScope`, `ConfigPath`, `SecretRef`
- 28 tests with 100% pass rate for Step 1 components

---

## [0.3.0] — 2026-08-05

### Milestone 3: Database Layer & Repository Pattern

#### Added
- Abstract Database interface (`Database` ABC)
- SQLiteDatabase implementation with WAL mode
- DatabaseFactory with extensible backend registry
- Transaction context manager
- Repository Pattern for all core tables
- KnowledgeEngine abstract interface
- FTS5Engine full-text search implementation
- SemanticQuery placeholder for future semantic search
- ImportSession lifecycle management
- DbImportManager (M2→DB adapter, zero M2 changes)
- Domain models with multi-AI fields
- 49 new tests with 86% coverage

---

## [0.2.0] — 2026-08-04

### Milestone 2: Import Engine

#### Added
- ChatGPT and Gemini conversation parsers
- Import manager with deduplication
- SHA-256 content hashing
- JSON report generation
- 53 tests
