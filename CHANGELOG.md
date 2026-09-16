# Changelog

## [0.6.0-alpha18] — 2026-09-16

### Milestone 6.18 — Admin Console UX Polish

#### Added
- Reusable admin console row renderers for readable operator output
- Code-style rendering for launch commands, local URLs and bootstrap paths
- Step-based manual rendering in the Operator Manual panel
- Console asset test covering readability helpers and responsive wrapping
- `setup_milestone6_18.py` + `verify_milestone6_18.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha18`
- `pyproject.toml` bumped to `0.6.0-alpha18`
- README, roadmap and test report updated for M6.18

#### Design Decisions
- UX polish stays client-side and does not change admin API contracts
- Long commands and filesystem paths wrap safely on compact screens
- Console renderers escape dynamic text before inserting it into HTML

#### Test Results
- M6 total: 57/57 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha17] — 2026-09-16

### Milestone 6.17 — Local Workspace Bootstrap

#### Added
- `skos.m6.production.bootstrap_local_workspace()` — non-destructive local runtime directory preparation
- `POST /api/v1/admin/local/bootstrap` — admin endpoint for preparing configured local paths
- Console action to prepare the local workspace from the Local Launch panel
- Tests covering directory creation, idempotency, collision warnings and API output
- `setup_milestone6_17.py` + `verify_milestone6_17.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha17`
- `pyproject.toml` bumped to `0.6.0-alpha17`
- README, roadmap and test report updated for M6.17

#### Design Decisions
- Bootstrap creates only missing directories and never overwrites existing files
- API bootstrap uses configured paths, so tests and local runs prepare the intended workspace
- Re-running bootstrap is safe and reports existing paths as already present

#### Test Results
- M6 total: 56/56 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha16] — 2026-09-16

### Milestone 6.16 — Operator Manual

#### Added
- `skos.m6.production.build_operator_manual()` — structured local operator manual
- `GET /api/v1/admin/manual` — operator manual endpoint
- Operator Manual panel in the `/admin` console
- Tests covering manual sections, safety guidance and API output
- `setup_milestone6_16.py` + `verify_milestone6_16.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha16`
- `pyproject.toml` bumped to `0.6.0-alpha16`
- README, roadmap and test report updated for M6.16

#### Design Decisions
- The manual is structured data, not only prose, so UI and API can reuse it
- Manual guidance focuses on local start, daily checks, backup safety and release gating
- The admin console shows operational steps without requiring file browsing

#### Test Results
- M6 total: 52/52 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha15] — 2026-09-15

### Milestone 6.15 — Local Launch Preflight

#### Added
- `skos.m6.production.local_server` — local FastAPI app entrypoint for admin/health testing
- `skos.m6.production.build_local_launch_plan()` — local launch command and preflight checks
- `GET /api/v1/admin/local/launch` — operator launch plan endpoint
- Local Launch panel in the `/admin` console
- Tests covering launch plan checks, local server health/admin routes and API output
- `setup_milestone6_15.py` + `verify_milestone6_15.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha15`
- `pyproject.toml` bumped to `0.6.0-alpha15`
- README, roadmap and test report updated for M6.15

#### Design Decisions
- Local launch preflight is non-destructive and does not start external services
- The local server uses memory-mode defaults and an internal health orchestrator
- The admin console now shows the command and URLs Luca can use for local testing

#### Test Results
- M6 total: 48/48 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha14] — 2026-09-15

### Milestone 6.14 — Release Readiness Gate

#### Added
- `skos.m6.production.run_release_readiness_gate()` — final package creation and inspection verdict
- `ReleaseReadinessGate` model for distribution readiness results
- `POST /api/v1/admin/release/gate` — operator release gate endpoint
- Admin console action to run the release readiness gate
- Tests covering gate creation, serialization and API output
- `setup_milestone6_14.py` + `verify_milestone6_14.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha14`
- `pyproject.toml` bumped to `0.6.0-alpha14`
- README, roadmap and test report updated for M6.14

#### Design Decisions
- The gate creates a fresh release package, inspects it and returns one distribution verdict
- Gate warnings combine package inspection warnings and release metadata mismatches
- The public API contract remains frozen; release gate remains admin-only

#### Test Results
- M6 total: 43/43 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha13] — 2026-09-15

### Milestone 6.13 — Release Package Inspection

#### Added
- `skos.m6.production.inspect_release_package()` — side-effect-free release ZIP inspection
- `ReleasePackageInspection` model for package verification results
- `GET /api/v1/admin/release/package/inspect` — operator release package validation endpoint
- Admin console action to inspect a generated release ZIP
- Tests for valid packages, missing manifests, hash mismatches and API output
- `setup_milestone6_13.py` + `verify_milestone6_13.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha13`
- `pyproject.toml` bumped to `0.6.0-alpha13`
- README, roadmap and test report updated for M6.13

#### Design Decisions
- Release inspection never extracts or modifies package contents
- Inspection verifies manifest presence, required entries, per-file SHA256 and size
- Packages containing local data, cache files or unlisted entries are flagged before distribution

#### Test Results
- M6 total: 40/40 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha12] — 2026-09-15

### Milestone 6.12 — Release Package Export

#### Added
- `skos.m6.production.create_release_package()` — clean source release ZIP export
- `ReleasePackageManifest` with per-file SHA256 hashes and byte counts
- `POST /api/v1/admin/release/package` — operator-triggered release package creation
- Release Package panel in the `/admin` console
- Release package tests covering archive contents, manifest hashes and API output
- `setup_milestone6_12.py` + `verify_milestone6_12.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha12`
- `pyproject.toml` bumped to `0.6.0-alpha12`
- README, config and roadmap updated for M6.12

#### Design Decisions
- Release packages use an explicit allowlist of source, test, config and documentation paths
- Local data, cache files and generated Python bytecode are excluded from release ZIPs
- The public API contract remains frozen; packaging is exposed only under admin routes

#### Test Results
- M6 total: 36/36 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha11] — 2026-09-14

### Milestone 6.11 — Admin Smoke Check

#### Added
- `skos.m6.production.build_admin_smoke_report()` — compact operator smoke report
- `GET /api/v1/admin/smoke` — release, readiness, backup and admin console checks
- Operator Smoke Check panel in the `/admin` console
- Smoke tests covering ready and failing states plus API output
- `setup_milestone6_11.py` + `verify_milestone6_11.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha11`
- `pyproject.toml` bumped to `0.6.0-alpha11`
- README and roadmap updated for M6.11

#### Design Decisions
- Smoke checks are side-effect free and operator-facing
- The smoke report summarizes the minimum evidence needed before manual local testing
- The admin console displays the smoke result separately from detailed readiness

#### Test Results
- M6 total: 33/33 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha10] — 2026-09-14

### Milestone 6.10 — Admin Overview

#### Added
- `skos.m6.production.build_admin_overview()` — aggregated operator snapshot
- `GET /api/v1/admin/overview` — release, readiness and backup status in one response
- Admin console wiring for the overview endpoint
- Overview tests covering aggregation, serialization and API output
- `setup_milestone6_10.py` + `verify_milestone6_10.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha10`
- `pyproject.toml` bumped to `0.6.0-alpha10`
- README and roadmap updated for M6.10

#### Design Decisions
- Overview reuses existing release, readiness and backup reports instead of duplicating logic
- The endpoint is side-effect free and operator-facing under `/api/v1/admin/*`
- The admin console can load its core status from one stable admin endpoint

#### Test Results
- M6 total: 30/30 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha9] — 2026-09-14

### Milestone 6.9 — Admin Release Status

#### Added
- `skos.m6.production.build_release_status()` — operator-facing release metadata
- `GET /api/v1/admin/release` — current release status endpoint
- Admin console wiring for real release version and milestone display
- Release status tests covering metadata serialization and API output
- `setup_milestone6_9.py` + `verify_milestone6_9.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha9`
- `pyproject.toml` bumped to `0.6.0-alpha9`
- README and roadmap updated for M6.9

#### Design Decisions
- Public `/api/v1/status` remains frozen for API Contract v1 compatibility
- Operator-facing `/api/v1/admin/release` reports the active SKOS release
- Admin console displays release metadata from the admin endpoint

#### Test Results
- M6 total: 27/27 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha8] — 2026-09-13

### Milestone 6.8 — Admin Backup Console

#### Added
- Backup Operations panel in the `/admin` console
- Console controls for backup creation, archive inspection and staged restore
- Backup manifest summary in the admin dashboard
- Admin console asset tests covering backup panel and endpoint wiring
- `setup_milestone6_8.py` + `verify_milestone6_8.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha8`
- `pyproject.toml` bumped to `0.6.0-alpha8`
- README and roadmap updated for M6.8

#### Design Decisions
- The console uses the M6.7 admin backup API instead of duplicating backup logic
- Restore remains staged and requires an explicit target directory
- The UI exposes operational controls without changing public API Contract v1

#### Test Results
- M6 total: 24/24 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha7] — 2026-09-13

### Milestone 6.7 — Admin Backup API

#### Added
- `GET /api/v1/admin/backup/manifest` — backup manifest report
- `POST /api/v1/admin/backup/create` — backup ZIP creation
- `GET /api/v1/admin/backup/inspect` — backup archive inspection
- `POST /api/v1/admin/backup/restore/stage` — staged backup restore
- Admin API tests covering manifest, create, inspect, staged restore and invalid restore errors
- `setup_milestone6_7.py` + `verify_milestone6_7.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha7`
- `pyproject.toml` bumped to `0.6.0-alpha7`
- README and roadmap updated for M6.7

#### Design Decisions
- Backup operations are exposed only under admin routes
- Restore remains staged and never overwrites live configured paths
- Admin backup errors use the existing APIError contract

#### Test Results
- M6 total: 23/23 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha6] — 2026-09-13

### Milestone 6.6 — Staged Backup Restore

#### Added
- `skos.m6.production.stage_backup_restore()` — safe extraction of verified backup archives into an empty staging directory
- `BackupRestoreResult` model for restore staging metadata
- Path traversal protection before extraction starts
- Staged restore tests covering successful extraction, non-empty target refusal, unready archive refusal and unsafe ZIP paths
- `setup_milestone6_6.py` + `verify_milestone6_6.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha6`
- `pyproject.toml` bumped to `0.6.0-alpha6`
- README and roadmap updated for M6.6

#### Design Decisions
- Restore remains staged: it never overwrites configured live database or archive paths
- Restore target must be empty to avoid mixing old and restored files
- ZIP paths are validated before any extraction occurs

#### Test Results
- M6 total: 19/19 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha5] — 2026-09-13

### Milestone 6.5 — Backup Restore Inspection

#### Added
- `skos.m6.production.inspect_backup_archive()` — side-effect-free backup ZIP inspection before restore
- `BackupArchiveInspection` model for restore preflight metadata
- Backup inspection checks for readable ZIP packages, `manifest.json`, database payload and archive payload
- Restore inspection tests covering valid backups, missing manifest and missing database entries
- `setup_milestone6_5.py` + `verify_milestone6_5.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha5`
- `pyproject.toml` bumped to `0.6.0-alpha5`
- README and roadmap updated for M6.5

#### Design Decisions
- M6.5 does not extract, overwrite or restore data
- Restore safety starts with a dry-run archive inspection
- Destructive restore execution remains deferred until stronger operator controls exist

#### Test Results
- M6 total: 15/15 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha4] — 2026-09-13

### Milestone 6.4 — Backup Archive

#### Added
- `skos.m6.production.create_backup_archive()` — ZIP backup creation guarded by the backup manifest
- `BackupResult` model for completed backup package metadata
- `manifest.json` embedded inside each backup ZIP
- Backup archive tests covering ZIP contents and failure on unready manifests
- `setup_milestone6_4.py` + `verify_milestone6_4.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha4`
- `pyproject.toml` bumped to `0.6.0-alpha4`
- README and roadmap updated for M6.4

#### Design Decisions
- Backup creation only writes inside configured `backup_dir`
- Backup creation fails fast when the manifest is not ready
- Database and archive paths are preserved under clear ZIP prefixes

#### Test Results
- M6 total: 12/12 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha3] — 2026-09-13

### Milestone 6.3 — Backup Manifest

#### Added
- `skos.m6.production.build_backup_manifest()` — side-effect-free backup manifest planner
- `BackupItem` and `BackupManifest` models for structured backup planning
- Backup inventory for configured database and archive paths
- Warnings for missing database, archive or backup destination paths
- `tests/m6/test_backup_manifest.py` — 4 tests covering sizing, missing paths, serialization and no directory creation
- `setup_milestone6_3.py` + `verify_milestone6_3.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha3`
- `pyproject.toml` bumped to `0.6.0-alpha3`
- README and roadmap updated for M6.3

#### Design Decisions
- Backup planning is side-effect free: it never creates directories or copies data
- Backup manifest uses existing configured `database_path`, `archive_root` and `backup_dir`
- Backup execution is intentionally deferred to a later milestone

#### Test Results
- M6 total: 10/10 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha2] — 2026-09-13

### Milestone 6.2 — Admin Readiness

#### Added
- `GET /api/v1/admin/readiness` endpoint exposing the structured M6 readiness report
- Production Readiness panel in the `/admin` console
- Console integration with the readiness endpoint via packaged JavaScript assets
- `tests/m6/test_admin_readiness_api.py` — 2 tests covering the endpoint and console asset wiring
- `setup_milestone6_2.py` + `verify_milestone6_2.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha2`
- `pyproject.toml` bumped to `0.6.0-alpha2`
- README and roadmap updated for M6.2

#### Design Decisions
- The readiness report is available to operators without adding external services
- Admin readiness is an additive admin route; API Contract v1 query/error behavior remains unchanged
- The console continues to use packaged static assets and existing FastAPI serving

#### Test Results
- M6 total: 6/6 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.6.0-alpha1] — 2026-09-13

### Milestone 6.1 — Production Readiness

#### Added
- `skos.m6.production.run_production_readiness()` — side-effect-free readiness checker
- `ReadinessCheck` and `ReadinessReport` models for structured hardening reports
- Checks for environment, persistence mode, security posture, storage paths and admin assets
- `m6.environment` configuration key in `config.yaml`
- `tests/m6/test_readiness.py` — 4 tests covering hardened production, unsafe production, development warnings and serialization
- `setup_milestone6_1.py` + `verify_milestone6_1.py`

#### Changed
- `VERSION` bumped to `0.6.0-alpha1`
- `pyproject.toml` bumped to `0.6.0-alpha1`
- `pytest` discovery now includes `tests/m6`
- README and roadmap updated for M6.1

#### Design Decisions
- Readiness checks are side-effect free: no directory creation, socket checks or external service dependencies
- Production mode requires persistent storage and mandatory auth
- Development mode may warn without blocking local use

#### Test Results
- M6 total: 4/4 PASS
- M5 regression: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.5.0-alpha3] — 2026-09-07

### Milestone 5.3 — Admin Console

#### Added
- `/admin` browser console served by the existing FastAPI adapter
- Packaged admin assets under `skos.m5.admin_console.assets`
- Dashboard cards for system status, version, milestone and security mode
- Live health and engine panels backed by existing `/api/v1/*` endpoints
- `tests/m5/test_admin_console.py` — 3 tests covering HTML, CSS and JS assets
- `setup_milestone5_3.py` + `verify_milestone5_3.py`

#### Changed
- `VERSION` bumped to `0.5.0-alpha3`
- `pyproject.toml` bumped to `0.5.0-alpha3`
- README and roadmap updated for M5.3

#### Design Decisions
- API Contract v1 remains frozen; the admin console is served outside `/api/v1`
- Frontend assets are package data, not an external build step
- The console reuses existing health, status, security and engines endpoints

#### Test Results
- M5 total: 32/32 PASS
- M4 regression: 238/238 PASS

* * *

## [0.5.0-alpha2] — 2026-08-26

### Milestone 5.2 — Runtime Wiring

#### Added
- `skos.m5.runtime.PersistenceRuntime` — runtime container for M5 persistence services
- `skos.m5.runtime.build_persistence_runtime()` — factory for memory, persistent and auto-fallback modes
- `RuntimeHealth` — component-level health snapshot for event bus, rate limiter, audit, auth and knowledge graph
- M5 configuration keys in `config.yaml` for persistence mode, Redis, PostgreSQL and rate limiting
- `tests/m5/test_runtime_wiring.py` — 5 tests covering memory wiring, persistent wiring, auto fallback, invalid mode and health output
- `setup_milestone5_2.py` + `verify_milestone5_2.py`

#### Changed
- `VERSION` bumped to `0.5.0-alpha2`
- `pyproject.toml` bumped to `0.5.0-alpha2`
- README and roadmap updated for M5.2

#### Design Decisions
- Default runtime mode remains `memory`, so local development stays dependency-free
- Persistent mode wires Redis/PostgreSQL adapters explicitly through configuration
- Auto mode attempts persistent adapters and falls back to memory if health checks fail
- M5.1 adapter contracts remain untouched
- M4 baseline remains untouched

#### Test Results
- M5 total: 29/29 PASS
- M4 regression: 238/238 PASS

* * *

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
## [0.5.0-alpha1] — 2026-08-10

### Milestone 5.1 — Persistence Layer

#### Added
- `RedisEventBusAdapter` — Redis pub/sub + Streams persistent event bus
- `RedisRateLimitAdapter` — Distributed sliding-window rate limiter via Redis sorted sets
- `PostgreSQLAuditAdapter` — Persistent structured audit logging with JSONB
- `PostgreSQLAuthAdapter` — Hashed API key authentication with PostgreSQL backend
- `PostgreSQLKnowledgeGraphAdapter` — Adjacency-list knowledge graph with recursive CTE traversal
- `tests/m5/test_persistence.py` — 24 tests covering all persistent adapters
- `setup_milestone5_1.py` + `verify_milestone5_1.py`

#### Design Decisions
- All persistence adapters implement existing M4 ports (zero port changes)
- Redis chosen for EventBus (pub/sub native) and RateLimit (atomic operations)
- PostgreSQL chosen for Audit (structured queries), Auth (relational), KG (recursive CTEs)
- Neo4j not selected: PostgreSQL recursive CTEs sufficient for current graph depth/complexity
- All adapters gracefully degrade to `health() = False` when DB unavailable
- M4 baseline untouched: in-memory adapters still default, persistent adapters are opt-in

#### Test Results
- M5.1: 24/24 PASS
- M4 regression: 238/238 PASS

* * *

## [0.4.0] — 2026-08-09

### Milestone 4.12 — Release Engineering / Production Readiness

#### Added
- `README.md` — comprehensive project documentation
- `docs/ADR.md` — Architecture Decision Records (6 ADRs)
- `docs/SECURITY_CHECKLIST.md` — complete security audit checklist
- `docs/BENCHMARK_REPORT.md` — test coverage and performance baseline
- `SBOM.json` — Software Bill of Materials (SPDX-2.3)
- `setup_milestone4_12.py` — release setup script
- `verify_milestone4_12.py` — E2E verification script
- E2E smoke tests covering: health, status, query, OpenAPI, metrics, security status

#### Changed
- `VERSION` bumped to `0.4.0` (production release)
- `FastAPIAdapter` version bumped to `0.4.0`
- `FastAPIAdapter` milestone bumped to `M4.12`
- `pyproject.toml` version bumped to `0.4.0`
- `docs/api_contract.md` updated for production

#### Production Readiness Checklist
- [x] Benchmark raggiunti e documentati (238 tests, ~3.5s)
- [x] E2E verdi, incluso restart container (smoke tests)
- [x] Security checklist completata (M4.11)
- [x] ADR + OpenAPI + README + CHANGELOG completi
- [x] API contract congelato/versionato (v1)
- [x] Nessuna issue critica (0 failed)
- [x] Observability operativa (M4.10)
- [x] Release artifact verificato
- [x] Checksum + SBOM generati
- [x] Test/regression completamente verdi (238/238)
- [x] ZIP finale verificato

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
- M4.10 — untouched
- M4.11 — untouched

* * *

## [0.4.0-alpha13] — 2026-08-09

### Milestone 4.11 — Security & Auth

#### Added
- `AuthPort` — infrastructure port for authentication
- `AuthorizationPort` — infrastructure port for RBAC authorization
- `RateLimitPort` — infrastructure port for rate limiting
- `AuditPort` — infrastructure port for security audit logging
- `APIKeyAuthAdapter` — in-memory API key authentication with Bearer support
- `RBACAuthorizationAdapter` — in-memory role-based access control with wildcard patterns
- `InMemoryRateLimitAdapter` — sliding-window rate limiter with per-resource overrides
- `StructuredAuditAdapter` — JSON-structured audit logging
- Security integration in `FastAPIAdapter`:
  - Optional authentication via `x-api-key` or `Authorization: Bearer` headers
  - Optional authorization with RBAC on all endpoints
  - Optional rate limiting with 429 responses and quota headers
  - Optional audit logging on all endpoints
  - `GET /api/v1/security/status` — security subsystem status endpoint
  - Admin routes (`/api/v1/admin/*`) require auth + admin role when security is configured
  - Health endpoint reports auth, authorization, rate_limit, audit status
- `tests/m4/test_security.py` — 41 tests covering ports, adapters, and integration
- `setup_milestone4_11.py` and `verify_milestone4_11.py`

#### Changed
- `FastAPIAdapter` version bumped to `0.4.0-alpha13`
- `FastAPIAdapter` milestone bumped to `M4.11`
- `FastAPIAdapter.__init__` accepts optional `auth`, `authorization`, `rate_limiter`, `audit` parameters
- DTOs extended with `SecurityStatusResponse`
- `docs/api_contract.md` updated to reflect M4.11

#### Design Decisions
- All security adapters are optional — FastAPIAdapter works without them (backward compatible)
- Authentication supports raw API key and `Bearer <key>` formats
- RBAC patterns support wildcard `*` for actions and resource prefixes
- Rate limiter uses sliding window with automatic eviction of expired entries
- Audit events include timestamp, principal, action, resource, status, and details
- Admin routes are protected only when an auth adapter is configured
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
- M4.10 — untouched

* * *


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
