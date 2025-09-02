## Product Requirements Document (PRD)

### Purpose
Deliver a cohesive CLI agent loop for CerebraFlow that mirrors Fowler’s agent workflow with strict VEG/AEMI execution, uv/.venv, and ChromaDB‑first architecture.

### Users
- Internal developers running automated refactor/fix loops on local codebases.

### Functional Requirements
- Run tests, parse failures, plan minimal edits, apply edits safely, lint, re‑run tests, and report.
- Memory integration backed by local Chroma and Supabase (RDB + pgvector) for persistence and RAG.
- Apple Silicon embeddings as default local embedder; CPU fallback.

### Non‑Functional Requirements
- Deterministic behavior, non‑interactive execution, safe diffs, and rollback.
- Fast local vectorization (<200ms/1KB on M2) and bounded output/truncation.

### Constraints
- uv/.venv only; no network in sandbox; pre‑commit enforced; VEG/AEMI compliance.

