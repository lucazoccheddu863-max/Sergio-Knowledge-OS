# Architecture Decision Records (ADR)

## ADR-001: Clean Architecture with Ports & Adapters

**Status:** Accepted  
**Date:** 2026-08-05

**Context:** SKOS needs to support multiple AI providers, databases, and deployment environments without coupling domain logic to infrastructure.

**Decision:** Adopt Clean Architecture with explicit Ports (abstract interfaces) and Adapters (concrete implementations). Domain and Application layers depend only on Ports. Infrastructure adapters implement Ports.

**Consequences:**
- ✅ Easy to swap AI providers (OpenAI, Gemini, Claude, Kimi, Ollama)
- ✅ Easy to swap databases (SQLite, ChromaDB, future Neo4j)
- ✅ Testable with mocks
- ❌ More boilerplate than direct imports

## ADR-002: API Contract Freeze at v1

**Status:** Accepted  
**Date:** 2026-08-08

**Context:** As SKOS approaches production, API stability becomes critical for consumers.

**Decision:** Freeze API Contract v1 at M4.9.5. All endpoints, request/response schemas, and error formats are version-locked. Breaking changes require a major version bump.

**Consequences:**
- ✅ Consumers can rely on stable contracts
- ✅ OpenAPI schema is the single source of truth
- ❌ Future breaking changes require v2

## ADR-003: Optional Observability

**Status:** Accepted  
**Date:** 2026-08-09

**Context:** Production deployments need metrics, tracing, and logging, but local development should not require Prometheus or OpenTelemetry.

**Decision:** All observability adapters are optional. FastAPIAdapter accepts optional `metrics`, `tracer`, `logger` parameters. When absent, the system operates with no-op fallbacks.

**Consequences:**
- ✅ Zero friction for local development
- ✅ Production-ready with full observability
- ✅ Isolated CollectorRegistry prevents metric collisions

## ADR-004: Optional Security

**Status:** Accepted  
**Date:** 2026-08-09

**Context:** Security requirements vary by deployment. Some environments need full auth, others run in trusted networks.

**Decision:** All security adapters (auth, authorization, rate limit, audit) are optional and opt-in via configuration. When disabled, the API operates in open mode preserving backward compatibility.

**Consequences:**
- ✅ Backward compatible with M4.1-M4.10
- ✅ Security can be enabled incrementally
- ✅ Admin routes protected only when auth is configured

## ADR-005: Zero External HTTP Dependencies for AI Adapters

**Status:** Accepted  
**Date:** 2026-08-07

**Context:** SKOS should minimize dependency surface and remain testable without network.

**Decision:** All AI provider adapters use `urllib.request` (stdlib) instead of `requests` or `httpx`. HTTP calls are fully mockable for testing.

**Consequences:**
- ✅ Zero HTTP library dependencies
- ✅ Fully mockable in tests
- ❌ Slightly more verbose than `requests`

## ADR-006: In-Memory Defaults with Swappable Backends

**Status:** Accepted  
**Date:** 2026-08-09

**Context:** SKOS needs to work out-of-the-box for demos and small deployments, but scale to production backends.

**Decision:** Default adapters use in-memory stores (event bus, knowledge graph, rate limiter, auth). Production deployments swap in persistent backends (Redis, Neo4j, PostgreSQL) by implementing the same Port interface.

**Consequences:**
- ✅ Works immediately after `pip install`
- ✅ Zero configuration for first run
- ✅ Production backends require only adapter swap
