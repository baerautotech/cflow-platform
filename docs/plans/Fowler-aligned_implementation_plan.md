### CerebraFlow Unified CLI Agent Loop Implementation Plan (Fowler‑aligned)

This plan has moved. See the new structure under `docs/agentic-plan/`:
- `docs/agentic-plan/README.md` (index)
- `docs/agentic-plan/TaskTracker.md` (unified AEMI + VEG tasks)
- `docs/agentic-plan/ValidationGates.md` (gates)
- Architecture/PRD/Stack/Schema and more under `docs/agentic-plan/`

The legacy sections were removed to avoid duplication.
### CerebraFlow Unified CLI Agent Loop Implementation Plan (Fowler‑aligned)

Note: This legacy plan has been reorganized per `docs/ProjectBuildGuide.md` into `docs/agentic-plan/`:
- Overview and index: `docs/agentic-plan/README.md`
- Unified tracker: `docs/agentic-plan/TaskTracker.md`
- Validation: `docs/agentic-plan/ValidationGates.md`
- Architecture/PRD/Stack/Schema and more under `docs/agentic-plan/`

The sections below remain for historical reference and will be fully deprecated after Phase 1.

## Next Steps (Sync, Vectors, Memory) — AEMI Checklist

- [ ] Vector DB wiring (remote Supabase pgvector)
  - [ ] Define target tables/columns for task/doc embeddings
  - [ ] Add embedding compute or load existing vectors; implement pgvector push/pull
  - [ ] Gate consistency: local Chroma counts and remote row counts must match post-sync

- [ ] cflowMemory integration
  - [ ] Promote `project_memory.py` and `memory_api.py` to first-class module
  - [ ] Add memory collections/tables and scalar metadata mapping
  - [ ] Include in sync loop with counts parity checks

- [ ] Supabase Realtime
  - [ ] Subscribe to tasks/docs channel updates; trigger incremental pulls on change
  - [ ] Provide exit-on-converge CLI mode for one-shot syncs

- [ ] Consistency gates (RDB + VDB)
  - [ ] `cflow-sync status` must report equal counts for tasks/docs (local vs remote)
  - [ ] CI check to fail on drift beyond threshold

- [ ] Import Apple Silicon vectorization services
  - [ ] Ensure Apple Silicon (MPS/Accelerate) vectorization services from Cerebral repo are imported and wired
  - [ ] Validate embeddings parity and performance on Apple Silicon

Reference: [Building your own CLI Coding Agent with Pydantic‑AI](https://tracking.tldrnewsletter.com/CL0/https:%2F%2Fmartinfowler.com%2Farticles%2Fbuild-own-coding-agent.html%3Futm_source=tldrwebdev/1/01000198f0691548-18c31833-3176-442d-9483-1fea2a8d53b0-000000/9mTnUagldPRXwcmtww2guqpC_aBR_dte89oI8fJqGPM=420)

#### Goal
Implement a cohesive developer agent loop for CerebraFlow that mirrors the article’s capabilities while preserving VEG/AEMI, uv/.venv, and ChromaDB‑first architecture. Deliver a small CLI orchestration (“cflow agent”), focused MCP tools, instruction profiles, and documentation. This file will be parsed to create tasks once the Cflow migration to its separate repository completes.

#### Build Order
- Build Cflow portions first. Platform‑level add‑ons (AWS MCP pack, desktop notifications) are optional and can follow without blocking the core loop.

#### Core Loop (from article)
- run tests → inspect failing tests → read implementation → fetch docs → make minimal edits → lint → re‑run tests → repeat.
- Named capabilities analogs to include: `run_python`/sandboxed execution, `code_reasoning` planning, Context7 docs integration, optional AWS MCPs, optional desktop notifications.

---

### AEMI + VEG Task Tracker

- [ ] Phase 1: Cflow Core Agent Loop
  - [x] 1.1 MCP tool: testing.run_pytest
    - [x] 1.1.1 Design spec: testing.run_pytest schema and truncation policy (VEG Gate 1 complete)
    - [x] 1.1.2 Implement pytest executor (uv, non‑interactive, size caps)
    - [x] 1.1.3 Implement log parser (summary JSON)
    - [x] 1.1.4 Add CLI subcommand wiring and help
    - [x] 1.1.5 Unit tests for runner + parser
  - [x] 1.2 CLI entrypoint: cflow agent (default loop orchestrator)
    - [x] 1.2.1 Draft agent loop sequence + flags
    - [x] 1.2.2 Implement loop shell (context → tests → plan → edit → lint → tests)
    - [ ] 1.2.3 Add dry‑run edits + diff presentation
    - [ ] 1.2.4 Integrate pre‑commit, bail on violations
    - [ ] 1.2.5 End‑to‑end tests on a sample failing test
  - [x] 1.3 Failure parser and report synthesizer
    - [x] 1.3.1 Failure parser coverage tests (common pytest patterns)
  - [ ] 1.4 Minimal edit applier (file‑scoped, SRP)
    - [ ] 1.4.1 Safety checks (allowlist paths, rollback)

- [ ] Phase 2: Reasoning + Instruction Profiles
  - [ ] 2.1 Instruction profiles loader
    - [ ] 2.1.1 Define instruction profile schema and discovery
    - [ ] 2.1.2 Implement loader + precedence
    - [ ] 2.1.3 Profile unit tests
  - [ ] 2.2 MCP tool: code_reasoning.plan
    - [ ] 2.2.1 Define plan output schema (hypotheses, steps, success checks)
    - [ ] 2.2.2 Implement code_reasoning.plan tool
    - [ ] 2.2.3 Add minimal‑edit constraints (SRP, scope)
    - [ ] 2.2.4 Plan tool unit tests
  - [ ] 2.3 Lint and pre‑commit integration step
    - [ ] 2.3.1 Lint step integration; fail‑closed behavior

- [x] Phase 3: Sandboxed Execution + Docs Auto‑Assist
  - [x] 3.1 MCP tool: sandbox.run_python
    - [x] 3.1.1 Sandbox policy (limits, FS allowlist)
    - [x] 3.1.2 Implement sandbox.run_python executor
    - [x] 3.1.3 Policy enforcement tests
  - [ ] 3.2 Context7 auto‑docs in loop
    - [ ] 3.2.1 Error → symbol extraction for docs lookup
    - [ ] 3.2.2 Integrate Context7 fetch + summarization
    - [ ] 3.2.3 Add toggle, tests

- [ ] Phase 4: Optional Packs (Off by default)
  - [ ] 4.1 AWS MCP profile
    - [ ] 4.1.1 AWS profile config and env detection
    - [ ] 4.1.2 Document profile and safeguards
  - [ ] 4.2 Desktop notifications bridge (minimal)
    - [ ] 4.2.1 Minimal notifier with OS allowlist
    - [ ] 4.2.2 Documentation for off‑by‑default operation

- [ ] Phase 5: Platform Integration & Documentation
  - [ ] 5.1 Dev workflow integration
    - [ ] 5.1.1 Dev workflow glue (no duplication)
  - [ ] 5.2 Documentation
    - [ ] 5.2.1 Author docs and examples
  - [ ] 5.3 Telemetry and guardrails
    - [ ] 5.3.1 Add opt‑in telemetry hooks and docs

---

## Phase 1: Cflow Core Agent Loop (High priority)

- 1.1 MCP tool: testing.run_pytest (uv pytest with summarized output)
  - Description: Non‑interactive `uv run pytest -xvs tests/` with stdout/stderr capture, truncation, and a failure summary (test name, file:line, error type, top lines of trace).
  - Inputs: path/markers; truncation limits; verbosity.
  - Outputs: raw logs; structured JSON summary; boolean pass/fail.
  - Acceptance:
    - Executes within `.venv` using `uv` only; no interactivity; no pager.
    - Handles large output with safe truncation and clear “truncated” markers.
    - Returns pass/fail plus a de‑duplicated, structured failure list.

- 1.2 CLI entrypoint: cflow agent (default loop orchestrator)
  - Description: Orchestrates RAG context pull → run_pytest → parse → minimal edits → lint → run_pytest → report. Prints short plan, diffs applied, and final status.
  - Inputs: flags (e.g., `--profile=strict`, `--docs=auto`, `--dry-run`).
  - Outputs: console report; optional JSON report for CI.
  - Acceptance:
    - Single command performs end‑to‑end loop.
    - Honors pre‑commit; aborts on violations (no `--no-verify`).
    - Supports dry‑run with diff preview before apply.

- 1.3 Failure parser and report synthesizer
  - Description: Parse pytest logs to structured errors (test id, file:line, error type, message, top trace); de‑duplicate; map to files/functions.
  - Acceptance:
    - Correctly parses common pytest patterns (>95%).
    - Produces actionable mapping from failure → candidate files/functions.

- 1.4 Minimal edit applier (file‑scoped, SRP)
  - Description: Apply targeted edits returned by reasoning tool with safety checks (allowlisted paths, conflict detection), dry‑run support, and revert on failure.
  - Acceptance:
    - Never writes outside allowlisted directories.
    - Aborts on merge conflicts; prints unified diffs; supports rollback.

---

## Phase 2: Reasoning + Instruction Profiles

- 2.1 Instruction profiles loader
  - Description: Load instruction blocks (e.g., “fix implementation before tests”, “minimal diffs”, SRP) from project rules (`.cursor/rules` and workspace rules). Inject into agent loop.
  - Acceptance:
    - Profile applied every run; toggle via `--profile`.
    - Deterministic precedence rules (project > workspace defaults).

- 2.2 MCP tool: code_reasoning.plan
  - Description: Given parsed failures + code snippets, emit a short plan: hypotheses, minimal edits, and verification steps (including success checks and re‑test conditions).
  - Acceptance:
    - Deterministic JSON schema; bounded step count (small, SRP‑compliant).
    - Each step has explicit success criteria and file scope.

- 2.3 Lint and pre‑commit integration step
  - Description: Auto‑run lint/format; present violations; re‑run tests only if lint passes.
  - Acceptance:
    - Honors local pre‑commit hooks; fails closed on violations.

---

## Phase 3: Sandboxed Execution + Docs Auto‑Assist

- 3.1 MCP tool: sandbox.run_python
  - Description: Execute Python snippets via `uv run` with CPU/memory/time caps; filesystem allowlist; no network; clean stdout/stderr.
  - Acceptance:
    - Enforced limits; deny network; fail closed on policy violations.

- 3.2 Context7 auto‑docs in loop
  - Description: On stack traces referencing external APIs/symbols, auto‑fetch relevant docs via Context7 and inject top summaries into the reasoning context.
  - Acceptance:
    - Off by default, enable with `--docs=auto`.
    - Shows top 1–2 doc extracts with source links.

---

## Phase 4: Optional Packs (Off by default)

- 4.1 AWS MCP profile
  - Description: Optional profile enabling AWS Labs MCPs for cloud‑native teams; gated via `--profile=aws`.
  - Acceptance:
    - Disabled by default; clean failure when credentials missing.

- 4.2 Desktop notifications bridge (minimal)
  - Description: Scoped local notifications (e.g., “tests completed”). No system control or file operations.
  - Acceptance:
    - Disabled by default; respects OS notification policies.

---

## Phase 5: Platform Integration & Documentation

- 5.1 Dev workflow integration
  - Description: Wire agent results into existing dev workflow tools (code review, pre‑commit, post‑commit) without duplication.
  - Acceptance:
    - Zero new violations; unchanged hooks behavior; green pre‑commit.

- 5.2 Documentation
  - Description: Add docs under `docs/tools/agent-loop/` for usage, flags, profiles, safety, troubleshooting.
  - Acceptance:
    - Includes examples; governance notes (VEG/AEMI, uv/.venv, ChromaDB‑first).

- 5.3 Telemetry and guardrails
  - Description: Minimal non‑PII telemetry on loop outcomes; configurable opt‑out.
  - Acceptance:
    - Config flag documented; auditability.

---

## Apple Silicon Accelerator Integration (Core)

- Completed
  - [x] Core accelerator implemented under `cflow_platform/core/embeddings/apple_silicon_accelerator.py` (no stubs; no emojis in source)
  - [x] Embedder rewired to core: `cflow_platform/core/embeddings/apple_mps.py` only uses core accelerator (no vendor/HF paths)
  - [x] Core embedding service added: `cflow_platform/core/services/ai/embedding_service.py` (singleton, caching)
  - [x] Pre‑commit hardened: emoji guard in source files; embeddings never run in pre‑commit

- Remaining to port (from Cerebral)
  - [ ] services/shared/singleton_embedding_service.py → `core/services/shared/singleton_embedding_service.py`
  - [ ] services/enterprise_rag/enterprise_embedding_service.py → `core/services/enterprise_rag/enterprise_embedding_service.py`
  - [ ] services/enterprise_rag/enterprise_embedding_service_clean.py → `core/services/enterprise_rag/enterprise_embedding_service_clean.py`
  - [ ] services/specialized_ai_services_accelerated.py → `core/services/specialized_ai_services_accelerated.py`
  - [ ] services/unified_enterprise_rag.py → `core/services/unified_enterprise_rag.py`
  - [ ] services/enterprise_codebase_vectorization_service.py → `core/services/enterprise_codebase_vectorization_service.py`
  - [ ] services/ai/enhanced_data_lake_apple_silicon_accelerator.py → `core/services/ai/enhanced_data_lake_apple_silicon_accelerator.py`
  - [ ] api/caef_apple_silicon_routes.py → wire into CLI/API as needed (no web server required for core)
  - [ ] config/memory_config_local_apple_silicon.yml → `config/` with loader in core
  - [ ] scripts: vectorizer/optimizer/simple_test → `scripts/` namespaced for local use

- Wiring and acceptance
  - [ ] Replace any remaining imports to use `cflow_platform/core/...` modules
  - [ ] Ensure `unified_realtime_sync_service.py` and `chromadb_supabase_sync_service.py` call core services only
  - [x] Add unit smoke tests that call the core embedding service and return vectors without any HF/network
  - [ ] End‑to‑end: `cflow-memory-watch` and agent loop produce embeddings using core accelerator with `CFLOW_SKIP_APPLE_MPS=1` honored in hooks

---

## AEMI Atomic Breakdown

Merged into the AEMI + VEG Task Tracker above for single-source sequencing and status. This section intentionally removed to avoid duplicate numbering.

---

## Task Documentation Template (apply to each atomic task)

```
- Title: <>=15 chars>
- Description: <>=80 chars detailed description, goals, constraints (VEG/AEMI, uv/.venv, ChromaDB‑first)>
- Inputs: <flags, environment, configs>
- Outputs: <artifacts, tool endpoints, docs>
- Dependencies: <task IDs>
- Acceptance Criteria:
  - <deterministic checks, tests to run, success/failure flags>
- Validation Steps:
  - <commands, expected results>
- Risk/Notes:
  - <edge cases, security constraints>
- Estimate: <time>
- Owner: <name>
```

---

## Validation Gates

- [x] Gate A: 1.1 + 1.3 pass; `testing.run_pytest` returns structured JSON with correct pass/fail and truncation markers.
- [ ] Gate B: 1.2 e2e: a known failing test is fixed via minimal edit + lint + re‑run → green.
- [ ] Gate C: 2.x reasoning: plans are bounded, SRP‑compliant, reproducible; steps include success checks.
- [x] Gate D: 3.x sandbox: limits enforced; no network; FS allowlist respected; policy tests pass.
- [ ] Gate E: Docs complete; pre‑commit green; telemetry disabled by default with clear opt‑in.

---

## 1.1.1 Design Spec: testing.run_pytest (Completed)

- VEG/AEMI Gate 1 (Documentation) passed; aligns with Fowler loop and current implementation.
- Tool name: `testing_run_pytest`
- Execution: `uv run pytest -xvs <path>` with optional `-k <markers>`; capture stdout/stderr; non‑interactive; no pager.

Inputs (all optional):

```
{
  "path": { "type": "string", "description": "Tests path; default auto-detects nearest tests/" },
  "markers": { "type": "string", "description": "Pytest -k expression" },
  "max_output_bytes": { "type": "integer", "default": 200000, "description": "Truncate combined stdout+stderr beyond this size and append [TRUNCATED]" },
  "verbose": { "type": "boolean", "default": false, "description": "Include raw_logs in result" }
}
```

Behavior:
- Assemble command: `uv run pytest -xvs <path> [ -k <markers> ]`.
- Capture stdout and stderr; combine in order; apply size cap with `[TRUNCATED]` sentinel.
- Return structured JSON with pass/fail and concise failure summary suitable for agent loop.

Output shape:

```
{
  "status": "success",
  "exit_code": 0,
  "passed": true,
  "truncated": false,
  "summary": {
    "failures": [ { "test": "<id/header>", "trace": "<last 20 lines>" } ],
    "summary_line": "=== 1 failed, 12 passed in 2.34s ==="
  },
  "raw_logs": "... included only when verbose=true ..."
}
```

Constraints & Safety:
- `.venv` + `uv` only; non‑interactive; no pager; deterministic output.
- Handles missing tests path or no tests (non‑zero exit with informative summary).
- Truncation is size‑bounded with explicit marker.

Notes:
- Further gates will validate executor behavior (Gate A), parser coverage (1.3), and end‑to‑end loop (1.2).


## Risks & Constraints

- Must adhere to VEG/AEMI, uv/.venv only, no `--no-verify`, ChromaDB‑first storage.
- Edit applier must never write outside allowlisted directories; dry‑run default for safety.
- Optional packs (AWS, desktop notifications) remain opt‑in; disabled by default.

---

## Capability Alignment (quick)

- Core MCP extensibility: Aligned
- Single CLI agent loop: Delivered via `cflow agent`
- First‑class test runner: `testing.run_pytest`
- Sandboxed Python exec: `sandbox.run_python`
- Up‑to‑date docs: Context7 auto‑assist (opt‑in)
- AWS MCPs: Optional profile
- Desktop notifications: Optional minimal bridge
- Strict execution standards: Enforced

---

## Next Steps (post‑migration)

- [ ] Parse this `Fowler-aligned_implementation_plan.md` to seed tasks with IDs, dependencies, and acceptance notes.
- [ ] Execute Phases 1 → 2 → 3; then optional packs (4); finalize platform integration and docs (5).



---

### Agentic Swarm Alignment (Zach Wills’ 8 Rules)

Reference: [I Managed a Swarm of 20 AI Agents for a Week and Built a Product. Here Are the 8 Rules I Learned.](https://zachwills.net/i-managed-a-swarm-of-20-ai-agents-for-a-week-here-are-the-8-rules-i-learned/)

This section maps the article’s principles onto our Fowler‑aligned plan and the current codebase to close gaps toward a production‑ready, autonomous, multi‑agent loop.

#### Quick Gap Analysis (Plan ↔ Codebase)
- Present
  - Core loop scaffold in `cflow_platform/core/agent_loop.py` (plan/verify; runs tests).
  - Structured test runner in `cflow_platform/core/test_runner.py` with in‑process and `uv` modes, timeouts, and summaries.
  - Minimal edit applier implemented (`cflow_platform/core/minimal_edit_applier.py`).
  - MCP tool routing and handlers (`core/direct_client.py`, `core/tool_registry.py`, `handlers/*`).
  - RAG/TDD generation stub (`handlers/rag_handlers.py`) and plan parser scaffolding.
  - Pre‑commit safety hooks (`hooks/pre_commit_runner.py`).
  - Apple Silicon embeddings present under `core/embeddings/` (ensure usage per memory policy).
- Missing/Partial
  - Failure parser (Phase 1.3) not integrated into loop; de‑dup and file/function mapping not implemented.
  - Minimal edit application (Phase 1.4) not wired into `agent_loop` with allowlist and rollback.
  - Lint/pre‑commit step (Phase 2.3) not in loop; no fail‑closed before re‑testing.
  - Instruction profiles loader (Phase 2.1) limited to hardcoded `DEFAULT_PROFILES`.
  - Reasoning tool `code_reasoning.plan` (Phase 2.2) not implemented.
  - Sandboxed execution `sandbox.run_python` (Phase 3.1) missing.
  - Context7 docs auto‑assist (Phase 3.2) not integrated into loop.
  - Sub‑agent orchestration (plan → implement → test with fresh context) absent.
  - Memory checkpointing and self‑updating `CLAUDE.md`/progress logs absent.
  - Restart policy/iteration budgets and “long‑running agent = bug” heuristics absent.
  - Early/atomic commit cadence gated by pre‑commit absent.
  - PR/ticket comment checkpointing absent (local fallback needed).

#### Tasks Mapped to the 8 Rules

- Rule 1: Align on the plan, not just the goal
  - [ ] 2.2.x Implement `code_reasoning.plan` MCP tool
    - Inputs: parsed failures, suspect files/snippets
    - Output: bounded JSON plan with steps, success checks, and file scopes
    - Acceptance: deterministic schema; max steps enforced; integrates with profiles (2.1)
  - [ ] 2.1.x Instruction profiles loader
    - Load from `.cursor/rules/` and workspace rules; precedence (project > defaults)
  
- Rule 2: Long‑running agent is a bug
  - [ ] 1.2.6 Add per‑iteration wall‑clock and step budgets to `agent_loop`
    - Flags: `--iteration-timeout-sec`, `--max-steps`, `--overall-timeout-sec`
    - Acceptance: loop aborts and restarts with a fresh context on timeout; emits structured reason
  
- Rule 3: Actively manage memory
  - [ ] 2.6 Memory checkpoints and progress logs (Cursor + CerebralMemory)
    - Implement `core/memory/checkpointer.py` to:
      - Write per‑iteration checkpoints to `.cerebraflow/progress/iteration_<n>.mdc` (Markdown+Context format)
      - Update Cursor‑aligned artifacts instead of `CLAUDE.md`:
        - `AGENTS.md` (root) for readable root‑level instructions
        - `.cursor/rules/` for structured configuration and instruction profiles
        - `docs/*.mdc` for planning/docs notes and AI‑assisted tasks
        - `commands/*` for reusable task‑specific commands
      - Persist episodic and procedural memories via `vendor/cerebral/backend-python/shared/project_memory.py` → `CerebralProjectMemory`:
        - Use `store_episode(run_id, task_id, content, metadata)` for iteration logs
        - Use `store_procedure_update(...)` for durable procedure updates
        - Tag metadata to link artifacts: `{artifact_path, artifact_type, cursor_kind, iteration, task_id, run_id}`
    - Hook `agent_loop` to checkpoint: after planning, after edits, after test pass/fail; push to CerebralMemory and update on‑disk artifacts atomically
    - Acceptance:
      - `.mdc` iteration files created; `AGENTS.md`, `.cursor/rules/*`, and `commands/*` updated when relevant
      - Corresponding memories stored with metadata for fast RAG lookup (local Chroma + Supabase sync)
      - Safe on re‑runs (idempotent updates; versioned backups under `.cerebraflow/`)
  
- Rule 4: Manage context with sub‑agents
  - [ ] 2.5 Sub‑agent scaffolding
    - Define `PlanAgent`, `ImplementAgent`, `TestAgent` in `cflow_platform/core/agents/` with explicit I/O contracts and fresh contexts per stage
    - Main loop dispatches: Plan → Implement (edits via minimal applier) → Test (pytest)
    - Acceptance: each sub‑agent can be run independently and composed by the orchestrator
  
- Rule 5: Trust the autonomous loop
  - [ ] 1.2.7 Integrate failure parser (1.3) + minimal edits (1.4) + lint (2.3) into `agent_loop`
    - Flow: run_pytest → parse → plan → apply minimal edits (allowlist + dry‑run) → lint/pre‑commit → re‑run tests
    - Acceptance: end‑to‑end loop fixes a seeded failing test and turns suite green (Gate B)
  - [ ] 3.4 Ephemeral test writer
    - Add `core/test_writer.py` to generate a targeted failing test from a bug description and include it in the run
    - Acceptance: new test appears under `tests/` with clear cleanup instructions; loop turns it green
  
- Rule 6: Automate the system, not just the code
  - [ ] 5.4 Post‑run system updates (Cursor + CerebralMemory)
    - Auto‑update `AGENTS.md`, `.cursor/rules/*`, `docs/*.mdc`, and `commands/*` after successful runs; `README.md` as needed
    - Persist a structured summary and diffs to CerebralMemory with `{type: procedure|context, cursor_kind, artifact_path}`
    - Optional: self‑refine instruction profiles in `.cursor/rules/` by appending observed success heuristics (guarded behind a flag)
    - Acceptance: doc and rule diffs are generated, gated by pre‑commit, and mirrored into CerebralMemory for RAG
  
- Rule 7: Be ruthless about restarting
  - [ ] 1.2.8 Restart heuristics
    - If plan oscillates (same failing tests across N iterations) or edit application repeatedly no‑ops, trigger fast restart with a trimmed plan
    - Acceptance: loop emits restart events and recovers; prevents unbounded drift
  
- Rule 8: Commit early and often
  - [ ] 5.5 Safe auto‑commit cadence
    - Implement `core/git_ops.py` to perform atomic commits per successful iteration (post‑lint, post‑tests‑green), gated by pre‑commit
    - Flags: `CFLOW_AUTOCOMMIT=1`, message template includes task id and plan step
    - Acceptance: commits only when hooks pass; includes diffs summary in body; disabled by default

#### Additional Integrations
- Cursor modular knowledge mapping
  - [ ] Replace single‑file `CLAUDE.md` workflows with Cursor’s modular structure:
    - `AGENTS.md` for root instructions; `.cursor/rules/` for complex instruction profiles
    - `.mdc` files in `docs/` for plans and context; `commands/` for quick reusable actions
  - [ ] Every artifact update is mirrored to CerebralMemory with rich metadata for retrieval and cross‑linking
  - Acceptance: Cursor artifacts exist and stay in sync with CerebralMemory entries; RAG lookups return the latest versions rapidly
- CerebralMemory + Cursor artifact pipeline (storage, vectors, watchers)
  - [ ] Storage separation & schemas (Supabase RDB + pgvector)
    - Define tables: `memory_items(id, type, scope, classification, title, content, metadata jsonb, created_at, updated_at)`, `memory_vectors(id, item_id fk, vector pgvector, dims, model, created_at)`
    - Define tables for Cursor artifacts: `cursor_rules`, `cursor_docs`, `cursor_commands` with cross‑links to `memory_items`
    - Acceptance: migrations applied; CRUD works; foreign keys enforced; indices on `type`, `scope`, `created_at`
  - [ ] Dual‑write pipeline in `ChromaDBSupabaseSyncService`
    - Implement `add_document(collection_type, content, metadata)` and `search_documents(collection_type, query, limit, filters)`
    - On write: perform local embedding, store in Chroma; store raw content/metadata in Supabase RDB; store embedding in pgvector; enqueue realtime sync events
    - Acceptance: writes create records in both VDB and RDB; realtime sync emits events; search returns consistent results across stores
  - [ ] Apple Silicon (MPS) embeddings
    - Wire `cflow_platform/core/embeddings/enhanced_apple_silicon_accelerator.py` as the default embedder for local vectors; CPU fallback; model/dim metadata persisted
    - Acceptance: local embeds complete under 200ms/1KB text on M2; parity checks on re‑embedding; metadata records model/dims
  - [ ] Filesystem → memory ingestion (Cursor artifacts)
    - Implement `cflow-memory-watch` CLI to watch `AGENTS.md`, `.cursor/rules/**`, `docs/**/*.mdc`, `commands/**` and route to CerebralMemory with correct `type` and `cursor_kind`
    - Add pre‑commit integration to enqueue ingestion for changed artifacts
    - Acceptance: creating/modifying artifacts triggers ingestion; records appear in RDB and vectors; agent `memory_search` retrieves them
  - [ ] Agent request routing
    - Ensure `memory_add`, `memory_store_procedure`, and episodic checkpoints are used by default in the agent loop and planning flows
    - Extend `.cursor/rules/cflow.profile.json` to instruct agents to call `memory_search` before external RAG
    - Acceptance: loop logs show memory calls; Context is sourced from CerebralMemory first
  - [ ] Supabase connectivity validation
    - Implement `cflow-memory-check` CLI: verifies SUPABASE_URL/ANON_KEY validity, RPC availability, and read/write to `memory_items`/`memory_vectors`
    - Add `.env` loader precedence: repo `/.env` then `/.cerebraflow/.env` (override) and emit warnings on invalid URL format
    - Acceptance: check returns green; sample add→search returns ≥1 hit via pgvector path
  - [ ] Supabase security and performance
    - RLS policies: add row-level security for `memory_items`/`memory_vectors` with anon insert/select scoped to project; grant execute on `match_memory_vectors`
    - Indexes: create `ivfflat`/`hnsw` index on `memory_vectors.embedding` with appropriate opclass; ANALYZE after bulk load
    - Env: support `SUPABASE_MATCH_RPC` override; document in `AGENTS.md`
    - Acceptance: anon can insert/select via key; RPC callable; pgvector index used in EXPLAIN
- [ ] 3.1 Sandboxed Python execution
  - Implement `sandbox.run_python` MCP tool with CPU/mem/time caps and FS allowlist; deny network
- [ ] 3.2 Context7 docs auto‑assist
  - On unresolved symbols in traces, call Context7 docs tool and inject 1–2 extracts with links into PlanAgent context
- [ ] 4.3 Supabase Realtime signals (optional)
  - Subscribe to tasks/docs changes to trigger incremental runs; off by default
- Apple Silicon embeddings
  - [ ] Ensure Apple Silicon MPS embedding path is the default provider in vectorization flows for local runs to honor performance policy

#### Acceptance & Validation Addenda
- [ ] Gate B+ (autonomous loop): seeded failing test fixed by loop with minimal edits; Cursor artifacts (`AGENTS.md`, `.cursor/rules/*`, `docs/*.mdc`, `commands/*`) updated; optional auto‑commit created when enabled
- [ ] Gate M (memory): per‑iteration checkpoints written and roll forward correctly after restart
- [ ] Gate R (restart): loop enforces iteration and time budgets; produces structured restart reasons; no infinite loops
- [ ] Gate Cmt (commit): commits occur only when pre‑commit passes and tests are green; disabled by default
- [ ] Gate RAG (memory sync): updated Cursor artifacts are mirrored into CerebralMemory and discoverable via RAG search within latency SLOs
- [ ] Gate VEC (embeddings): Apple Silicon MPS embedder used locally; vectors stored in Chroma and pgvector; search latency SLO met; model/dims recorded
- [ ] Gate RDB (relational): human‑readable retrieval works via Supabase; referential integrity and indices verified; realtime sync healthy

