## Technical Stack

- Language: Python 3.11
- Packaging/venv: uv + .venv
- Test framework: pytest 8.x
- Vector DB: ChromaDB (local), Supabase Postgres + pgvector (remote)
- Embeddings: Hardware-agnostic GPU accelerator (Apple Silicon MPS, NVIDIA CUDA, CPU fallback)
- CLI: argparse entrypoints under `pyproject.toml` [project.scripts]
- Observability: structured JSON outputs, iteration checkpoints in `.cerebraflow/`
- Frontend: React Native + React Native Web + TypeScript
- Backend: Python FastAPI (full Python stack)
- Storage: MinIO S3 (self-hosted)

### Model Provider

- Primary: Cerebral Server (private server cluster of nodes)
- Transport: HTTP/gRPC (env-configured); local fallback when cluster unavailable
- Selection: environment-driven provider abstraction (no AWS dependency)

### MCP/Docs/Search

- MCP transport: stdio servers
- Docs: Context7 MCP for library docs; sources required
- Search: DuckDuckGo MCP for real-time information (off by default)
- Optional: Desktop Commander (off by default)
- Note: AWS Labs MCPs and AWS Docs MCP are not used in our environment (can remain documented as optional for portability)

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

