## Technical Stack

- Language: Python 3.11
- Packaging/venv: uv + .venv
- Test framework: pytest 8.x
- Vector DB: ChromaDB (local), Supabase Postgres + pgvector (remote)
- Embeddings: Apple Silicon MPS accelerator (fallback CPU)
- CLI: argparse entrypoints under `pyproject.toml` [project.scripts]
- Observability: structured JSON outputs, iteration checkpoints in `.cerebraflow/`

