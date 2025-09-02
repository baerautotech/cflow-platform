## Agentic Workflow Definition

1) Pull local context and recent memory items (prefer CerebralMemory before external RAG)
2) Run tests (pytest via `test_runner`)
3) Parse failures → structured list
4) Plan minimal edits (bounded steps, SRP) with explicit success checks
5) If stack traces mention external APIs/symbols, fetch top relevant docs via Context7 and optionally real-time search
6) Apply edits (dry‑run or write) using minimal edit applier (allowlist + rollback)
7) Lint/pre‑commit; bail on violations
8) Re‑run tests; if green, checkpoint and optionally auto‑commit; otherwise iterate with budgets and restart heuristics

Outputs: concise plan, diffs, final status; checkpoints to `.cerebraflow/` and CerebralMemory.

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`
