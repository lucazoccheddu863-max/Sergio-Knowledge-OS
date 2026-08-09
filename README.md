# Sergio Knowledge OS

**Version:** 0.4.0  
**Status:** Production Ready  
**License:** MIT

Sergio Knowledge OS (SKOS) is a semantic knowledge platform built for AI-powered information retrieval, management, and exploration.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest tests/m4/ -v

# Start API
python -m skos.m4.infrastructure.adapters.api.fastapi_adapter
```

## Architecture

SKOS follows Clean Architecture with explicit layer separation:

- **Domain Layer:** Pure business logic, models, and value objects
- **Application Layer:** Orchestration services (embedding, RAG, search, KG)
- **Infrastructure Layer:** Adapters for external concerns (DB, AI providers, API, observability, security)

## API

REST API Contract v1 is frozen and documented at `docs/api_contract.md`.

Key endpoints:
- `POST /api/v1/query` — Unified query (semantic, RAG, graph, hybrid)
- `GET /api/v1/health` — Health check with subsystem status
- `GET /api/v1/status` — System status and version
- `GET /api/v1/engines` — List available engines
- `GET /api/v1/security/status` — Security subsystem status
- `GET /metrics` — Prometheus metrics
- `GET /api/v1/docs` — Swagger UI
- `GET /api/v1/redoc` — ReDoc

## Security

M4.11 introduces optional security layers:
- API Key Authentication (`x-api-key` or `Authorization: Bearer`)
- RBAC Authorization with wildcard patterns
- Sliding-window Rate Limiting
- Structured Audit Logging

Security is opt-in via configuration. When disabled, the API operates in open mode for backward compatibility.

## Observability

M4.10 introduces production observability:
- Prometheus metrics (`/metrics`)
- OpenTelemetry tracing
- Structured JSON logging
- Request counting and latency histograms

## Milestones

| Milestone | Version | Status |
|:---|:---|:---|
| M2 — Import Engine | 0.2.0 | Frozen |
| M3 — Database Layer | 0.3.0 | Frozen |
| M4.1 — DI & Config | 0.4.0-alpha1 | Frozen |
| M4.2 — Event Bus | 0.4.0-alpha2 | Frozen |
| M4.3 — Embeddings | 0.4.0-alpha3 | Frozen |
| M4.4 — Vector DB | 0.4.0-alpha4 | Frozen |
| M4.5 — Semantic Search | 0.4.0-alpha5 | Frozen |
| M4.6 — RAG Pipeline | 0.4.0-alpha6 | Frozen |
| M4.7 — Knowledge Graph | 0.4.0-alpha7 | Frozen |
| M4.8 — Query Orchestrator | 0.4.0-alpha8 | Frozen |
| M4.9 — REST API | 0.4.0-alpha9 | Frozen |
| M4.9.5 — API Contract Freeze | 0.4.0-alpha11 | Frozen |
| M4.10 — Observability | 0.4.0-alpha12 | Frozen |
| M4.11 — Security & Auth | 0.4.0-alpha13 | Frozen |
| **M4.12 — Release Engineering** | **0.4.0** | **Production** |

## Development

```bash
# Setup
python setup_milestone4_12.py

# Verify
python verify_milestone4_12.py

# Full test suite
pytest tests/m4/ -v
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## ADR

See [docs/ADR.md](docs/ADR.md).

## Security Checklist

See [docs/SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md).

## SBOM

See [SBOM.json](SBOM.json).
