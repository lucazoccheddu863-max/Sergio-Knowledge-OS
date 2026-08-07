
## [0.4.4-alpha1] — 2026-08-07 — M4.4 Vector Database

### Added
- `VectorStorePort` abstract interface with full CRUD, search, and collection management
- `ChromaVectorStoreAdapter` — ChromaDB-backed implementation with multi-collection support
- `VectorStoreService` — application-layer orchestrator with event emission
- `vector_store_module.py` — standalone DI registration (container.py untouched)
- Domain models: `VectorDocument`, `VectorQuery`, `SearchResult`, `CollectionConfig`
- `config/vector_store.yaml` — isolated module configuration
- Storage path: `./storage/chroma/` (prepared for `./storage/sqlite/`, `./storage/cache/`)
- Event types: `vector_store.document.upserted`, `vector_store.document.deleted`,
  `vector_store.collection.created`, `vector_store.collection.deleted`,
  `vector_store.health_check`
- Comprehensive test suite: contract, adapter, service, integration

### Architecture
- Clean Architecture preserved: zero Chroma dependency in application/domain layers
- Swap-ready: Chroma adapter replaceable with Qdrant adapter via same port
- `container.py` remains frozen; DI wired via `vector_store_module.py`
