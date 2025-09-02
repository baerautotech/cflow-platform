## High‑Level Architecture

- Core Loop: `cflow_platform/core/agent_loop.py` orchestrates Plan → Verify (tests) with checkpoints.
- Test Runner: `cflow_platform/core/test_runner.py` provides in‑process and uv subprocess execution.
- Failure Parser: `cflow_platform/core/failure_parser.py` parses pytest output into structured failures.
- Minimal Edit Applier: `cflow_platform/core/minimal_edit_applier.py` applies scoped diffs (to integrate).
- Memory/Sync: Local Chroma; remote Supabase RDB + pgvector via vendor sync services.
- Apple Silicon: `core/embeddings/*` Vectorization path with MPS accelerator.

### MCP Servers (Extensibility)

- run_python: Sandboxed Python evaluation (`@pydantic/mcp-run-python`) to support quick experiments in isolation
- internet_search: Real-time search via `duckduckgo-mcp-server` for current information
- context7.docs: Library docs via Context7 for symbol/API lookups; injects excerpts with sources into reasoning
- code_reasoning: Planning utility to produce bounded SRP steps with success checks
- desktop_commander (optional): Local notifications and guarded desktop utilities (off by default)

### Control and Safety

- Budgets: Per-iteration time and step budgets; restart heuristics on oscillation/timeout
- Lint/Pre-commit: Fail-closed before re-testing; no `--no-verify`
- File Allowlist: Minimal edit applier restricted to allowlisted paths; rollback on conflict
- Sandbox Policy: No network for sandboxed execution; CPU/mem/time caps

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

### Model Provider Abstraction

- Default provider: Cerebral Server (private cluster). Configure via environment variables and provider selector.
- Local fallback: run locally when cluster is unavailable; maintain identical interfaces for portability.
- Cloud providers: not required. AWS-specific MCPs are not part of the default stack in this environment.

