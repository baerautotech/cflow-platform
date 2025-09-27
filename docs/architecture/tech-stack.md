## Tech Stack (Dev Agent Always-Load)

Core Components
- BMAD API: Python 3.11, FastAPI-style service in `bmad_api_service/`
- WebMCP: HTTP server interface for MCP tool routing (Kubernetes deployed)
- Knowledge-RAG: Supabase Postgres + pgvector
- Infra: Kubernetes + Kyverno; OAuth2Proxy + Keycloak; MinIO for artifacts

Development Conventions
- Use environment variables for configuration; never commit secrets
- Prefer dependency injection for external services (DB, storage)
- Keep modules focused; avoid cyclic imports

Data & Storage
- Supabase tables: `cerebral_documents`, `cerebral_tasks`, `cerebral_activities`, `knowledge_embeddings`
- Artifacts stored in MinIO buckets; reference via URLs not raw blobs in code

APIs & Patterns
- HTTP endpoints should return explicit status and JSON payloads with error details
- Async where I/O bound; sync where CPU bound unless otherwise specified

Performance
- Use caching, connection pooling, and request deduplication helpers present in the repo where applicable

Observability
- Expose `/metrics` where feasible; log structured JSON for services


