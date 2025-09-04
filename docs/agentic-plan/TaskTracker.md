## AEMI + VEG Task Tracker (Unified)

- [ ] Phase 0: Foundation (CLI + Configuration)
  - [x] 0.1 CLI bootstrap: `cflow agent` entrypoint and loop shell
  - [ ] 0.2 Model provider abstraction (Cerebral Server cluster; local fallback; env-driven)
  - [ ] 0.3 Iteration budgets and restart heuristics (timeouts, max steps)

- [ ] Phase 1: Cflow Core Agent Loop
  - [x] 1.1 MCP tool: testing.run_pytest
    - [x] 1.1.1 Design spec
    - [x] 1.1.2 Implement executor
    - [x] 1.1.3 Log parser
    - [x] 1.1.4 CLI wiring
    - [x] 1.1.5 Unit tests
  - [x] 1.2 Failure parser and report synthesizer
    - [x] 1.2.1 Coverage tests
  - [x] 1.3 Minimal edit applier (file‑scoped, SRP)
    - [x] 1.3.1 Safety checks (allowlist, rollback)
  - [x] 1.4 Lint/pre‑commit integration
    - [x] 1.4.1 Fail‑closed before re‑testing; honor hooks
  - [x] 1.5 Dry‑run edits + diff presentation
  - [x] 1.6 E2E on a seeded failing test (turns suite green)

- [ ] Phase 2: Reasoning + Instruction Profiles
  - [ ] 2.1 Instruction profiles loader
    - [x] 2.1.1 Schema + discovery
    - [x] 2.1.2 Loader + precedence (project > defaults)
    - [x] 2.1.3 Unit tests
  - [ ] 2.2 MCP tool: code_reasoning.plan
    - [ ] 2.2.1 Plan schema (bounded SRP steps + success checks)
    - [ ] 2.2.2 Implement tool
    - [ ] 2.2.3 Minimal‑edit constraints
    - [ ] 2.2.4 Unit tests

- [ ] Phase 3: MCP Servers & Docs/Search
  - [ ] 3.1 Sandboxed execution: sandbox.run_python
    - [ ] 3.1.1 Sandbox policy (no network; CPU/mem/time caps; FS allowlist)
    - [ ] 3.1.2 Executor
    - [ ] 3.1.3 Policy tests
  - [ ] 3.2 Up‑to‑date docs (Context7) in loop
    - [ ] 3.2.1 Symbol extraction from traces
    - [ ] 3.2.2 Context7 fetch + summarization
    - [ ] 3.2.3 Toggle + tests
  - [ ] 3.3 Internet search MCP integration (DuckDuckGo)
    - [ ] 3.3.1 Server wiring and allowlist
    - [ ] 3.3.2 Result summarization + sources

- [ ] Phase 6: Memory & Supabase Sync (RDB + Vectors)
  - [ ] 6.1 Supabase connectivity validation CLI (`cflow-memory-check`)
    - [ ] 6.1.1 Validate `SUPABASE_URL`/`SUPABASE_ANON_KEY`; RPC availability; read/write
    - [ ] 6.1.2 `.env` loader precedence (repo `/.env` then `/.cerebraflow/.env`) and warnings on invalid URL
  - [ ] 6.2 Migrations & schemas
    - [ ] 6.2.1 Tables (preferred): `knowledge_items`, `knowledge_embeddings`; legacy `memory_*` view compatibility
    - [ ] 6.2.2 Indices: HNSW on vector_cosine_ops; optional IVFFlat; ANALYZE after bulk load
    - [ ] 6.2.3 RPC: `search_agentic_embeddings` with tenant/content filters; grant execute
  - [ ] 6.3 Dual‑write pipeline
    - [ ] 6.3.1 Implement dual‑write in `ChromaDBSupabaseSyncService`
    - [ ] 6.3.2 On write: local embed + Chroma, raw content/metadata in RDB, embedding in pgvector, realtime event emit
  - [ ] 6.4 Filesystem ingestion (Cursor artifacts)
    - [ ] 6.4.1 `cflow-memory-watch` watches `AGENTS.md`, `.cursor/rules/**`, `docs/**/*.mdc`, `commands/**`
    - [ ] 6.4.2 Pre‑commit integration to enqueue ingestion for changed artifacts
  - [ ] 6.5 Request routing
    - [ ] 6.5.1 Ensure agent loop uses memory_add/search by default; prefer CerebralMemory before external RAG

- [ ] Phase 7: Sub‑agents & Orchestration
  - [ ] 7.1 Define `PlanAgent`, `ImplementAgent`, `TestAgent` with explicit I/O contracts
  - [ ] 7.2 Orchestrator composes Plan → Implement (edits) → Test (pytest) with fresh contexts per stage
  - [ ] 7.3 Each sub‑agent runnable independently

- [ ] Phase 9: Restart Heuristics & Budgets
  - [ ] 9.1 Enforce iteration wall‑clock and step budgets
  - [ ] 9.2 Restart on oscillation (same failures across N iterations) or repeated no‑op edits

- [ ] Phase 5: Platform Integration & Documentation
  - [ ] 5.1 Dev workflow integration (no duplication)
  - [ ] 5.2 Documentation (examples, governance)
  - [ ] 5.3 Telemetry and guardrails (opt‑in)

- [ ] Phase 8: Post‑run System Updates & Auto‑commit (optional)
  - [ ] 8.1 Update Cursor artifacts after successful runs (`AGENTS.md`, `.cursor/rules/**`, `docs/*.mdc`, `commands/*`)
  - [ ] 8.2 Optional safe auto‑commit cadence gated by pre‑commit
    - [ ] 8.2.1 `core/git_ops.py` for atomic commits when tests green and hooks pass
    - [ ] 8.2.2 Env flag `CFLOW_AUTOCOMMIT=1`; message template includes task id and plan step

- [ ] Phase 4: Optional Packs (Off by default)
  - [ ] 4.1 Provider portability (document non-default cloud packs)
    - [ ] 4.1.1 Document AWS MCP profile as non-default (not used on Cerebral cluster)
    - [ ] 4.1.2 Safeguards and documentation for portability only
  - [ ] 4.2 Desktop notifications bridge (desktop_commander)
    - [ ] 4.2.1 Minimal notifier wiring
    - [ ] 4.2.2 Usage docs

- [ ] Phase 10: Apple Silicon Embeddings Acceptance
  - [ ] 10.1 Ensure Apple Silicon MPS embedder is default provider locally; CPU fallback
  - [ ] 10.2 Record model/dims in metadata; performance SLOs for local vectors; enforce padding/truncation to dims

### Stair-step Build Order Adjustments

Order of execution:
1) Phase 0 → Phase 1
2) Phase 2 (reasoning/profiles) enables minimal-edit planning
3) Phase 3 (sandbox + docs/search) to improve fix cycles
4) Phase 6 (memory & sync) to persist artifacts and enable RAG-first retrieval
5) Phase 7 (sub-agents) to isolate contexts per stage
6) Phase 9 (budgets/restarts) to stabilize long loops
7) Phase 5 (platform integration & docs) to finalize user-facing artifacts
8) Phase 8 (post‑run updates & optional auto‑commit)
9) Phase 4 (optional packs) — only if needed for environment portability
10) Phase 10 (embeddings acceptance)

Rationale: memory & sync (Phase 6) precedes orchestration (Phase 7) to ensure sub-agents operate with durable context; budgets/restarts (Phase 9) stabilize before introducing auto‑commit (Phase 8).

### Validation Gates
- [x] Gate A: tests runner + failure parser validated
- [ ] Gate B: end‑to‑end fix via minimal edit + lint + re‑run → green
- [ ] Gate C: reasoning profiles + bounded plans with success checks
- [ ] Gate D: sandbox policy enforced (limits; no network)
- [ ] Gate E: docs/search integration shows sources; pre‑commit green; telemetry opt‑in
- [ ] Gate P: provider configured for Cerebral Server cluster; local fallback validated
- [ ] Gate M: memory checkpoints created; iteration roll‑forward after restart
- [ ] Gate RAG: Cursor artifacts mirrored into CerebralMemory; RAG lookups return latest versions
- [ ] Gate VEC: Apple Silicon MPS embedder used locally; vectors stored in Chroma + pgvector; model/dims recorded
- [ ] Gate RDB: Relational retrieval via Supabase; referential integrity and indices verified; realtime healthy
- [ ] Gate R: restart budgets enforced; structured restart reasons emitted; no infinite loops
- [ ] Gate Cmt: commits only when hooks pass and tests green; disabled by default

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

