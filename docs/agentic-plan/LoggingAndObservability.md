## Logging and Observability

- Structured JSON outputs from test runner and agent loop
- Iteration checkpoints persisted locally and to CerebralMemory
- CLI flags for verbosity; truncation markers for large outputs

### Budgets and Restarts

- Log per-iteration time budget, step count, and restart reasons
- Emit explicit events for: plan oscillation, timeout, sandbox policy violation

### Source Citations

- When using docs/search MCPs, record source URLs along with summaries in the run log

### Provider Diagnostics

- Log selected model provider (Cerebral Server vs local fallback) and endpoint/version
- Emit health checks for provider readiness at start of each run

### Telemetry (Opt-in)

- Disabled by default. Enable explicitly via environment:
  - `CFLOW_TELEMETRY=1` (accepted truthy: `1`, `true`, `yes`, `on`)
  - Optional output override: `CFLOW_TELEMETRY_FILE=/abs/path/to/telemetry.jsonl`
- Events recorded as JSONL to `.cerebraflow/logs/telemetry.jsonl` by default.
- Examples of emitted events: `agent_loop.start`, `agent_loop.iteration.begin`, `agent_loop.stop.oscillation`, `tests.completed`.
- Guardrails: no sensitive payloads; best-effort logging only; failures never affect run outcome.

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

