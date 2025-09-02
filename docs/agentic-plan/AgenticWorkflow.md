## Agentic Workflow Definition

1) Pull local context and recent memory items
2) Run tests (pytest via `test_runner`)
3) Parse failures → structured list
4) Plan minimal edits (bounded steps) with success checks
5) Apply edits (dry‑run or write) using minimal edit applier
6) Lint/pre‑commit; bail on violations
7) Re‑run tests; if green, checkpoint and optionally auto‑commit

Outputs: concise plan, diffs, final status; checkpoints to `.cerebraflow/` and CerebralMemory.

