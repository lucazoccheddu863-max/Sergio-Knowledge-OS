# Sergio Knowledge OS — Roadmap

## Vision
A semantic knowledge platform that ingests, indexes, and retrieves information across multiple AI providers (ChatGPT, Kimi, Gemini, Claude, Ollama) with vector search and RAG capabilities.

## Milestones

### M2 — Import Engine ✅ FROZEN
- ChatGPT / Gemini parsers
- Deduplication via SHA-256
- JSON report generation

### M3 — Database Layer ✅ FROZEN
- Abstract database interface + SQLite implementation
- Repository pattern for all tables
- FTS5 full-text search
- Transaction management

### M4 — Semantic Layer & Vector Search 🔄 IN PROGRESS

#### M4.1 — Foundation
- **Step 1** ✅ — DI Container, Config, Secrets, Architecture rules
- **Step 2** 🔄 — Event Bus, Application Services
- **Step 3** — AI Provider Abstraction (ChatGPT, Kimi, Gemini, Claude, Ollama)
- **Step 4** — Embeddings Generation (local + API)
- **Step 5** — Vector Database Integration (ChromaDB / Qdrant)
- **Step 6** — Semantic Search Engine
- **Step 7** — RAG Pipeline Foundation

### M5 — API & Frontend
- FastAPI REST layer
- Web UI for search and conversation browsing
- Real-time indexing pipeline

### M6 — Production Hardening
- PostgreSQL / DuckDB backends
- Distributed event bus (Redis / RabbitMQ)
- Monitoring & observability
- Deployment automation

## Definition of Done (per milestone)
1. Design approved
2. Full implementation
3. Automatic tests (new code)
4. Regression tests (all frozen baselines)
5. VERSION updated
6. CHANGELOG updated
7. TEST_REPORT generated
8. SHA256SUMS generated
9. Setup script provided
10. Verify script provided
11. Single ZIP release
12. GitHub commit + freeze
