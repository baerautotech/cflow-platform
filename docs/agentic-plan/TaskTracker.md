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
  - [ ] 1.3 Minimal edit applier (file‑scoped, SRP)
    - [ ] 1.3.1 Safety checks (allowlist, rollback)
  - [ ] 1.4 Lint/pre‑commit integration
    - [ ] 1.4.1 Fail‑closed before re‑testing; honor hooks
  - [ ] 1.5 Dry‑run edits + diff presentation
  - [ ] 1.6 E2E on a seeded failing test (turns suite green)

- [ ] Phase 2: Reasoning + Instruction Profiles
  - [ ] 2.1 Instruction profiles loader
    - [ ] 2.1.1 Schema + discovery
    - [ ] 2.1.2 Loader + precedence (project > defaults)
    - [ ] 2.1.3 Unit tests
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

- [ ] Phase 4: Optional Packs (Off by default)
  - [ ] 4.1 Provider portability (document non-default cloud packs)
    - [ ] 4.1.1 Document AWS MCP profile as non-default (not used on Cerebral cluster)
    - [ ] 4.1.2 Safeguards and documentation for portability only
  - [ ] 4.2 Desktop notifications bridge (desktop_commander)
    - [ ] 4.2.1 Minimal notifier wiring
    - [ ] 4.2.2 Usage docs

- [ ] Phase 5: Platform Integration & Documentation
  - [ ] 5.1 Dev workflow integration (no duplication)
  - [ ] 5.2 Documentation (examples, governance)
  - [ ] 5.3 Telemetry and guardrails (opt‑in)

### Validation Gates
- [x] Gate A: tests runner + failure parser validated
- [ ] Gate B: end‑to‑end fix via minimal edit + lint + re‑run → green
- [ ] Gate C: reasoning profiles + bounded plans with success checks
- [ ] Gate D: sandbox policy enforced (limits; no network)
- [ ] Gate E: docs/search integration shows sources; pre‑commit green; telemetry opt‑in
- [ ] Gate P: provider configured for Cerebral Server cluster; local fallback validated

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

