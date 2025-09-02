## AEMI + VEG Task Tracker (Unified)

- [ ] Phase 1: Cflow Core Agent Loop
  - [x] 1.1 MCP tool: testing.run_pytest
    - [x] 1.1.1 Design spec
    - [x] 1.1.2 Implement executor
    - [x] 1.1.3 Log parser
    - [x] 1.1.4 CLI wiring
    - [x] 1.1.5 Unit tests
  - [x] 1.2 CLI entrypoint: cflow agent
    - [x] 1.2.1 Draft loop + flags
    - [x] 1.2.2 Implement loop shell
    - [ ] 1.2.3 Dry‑run edits + diff presentation
    - [ ] 1.2.4 Pre‑commit integration
    - [ ] 1.2.5 E2E on sample failing test
  - [x] 1.3 Failure parser and report synthesizer
    - [x] 1.3.1 Coverage tests
  - [ ] 1.4 Minimal edit applier (file‑scoped, SRP)
    - [ ] 1.4.1 Safety checks (allowlist, rollback)

- [ ] Phase 2: Reasoning + Instruction Profiles
  - [ ] 2.1 Instruction profiles loader
    - [ ] 2.1.1 Schema + discovery
    - [ ] 2.1.2 Loader + precedence
    - [ ] 2.1.3 Unit tests
  - [ ] 2.2 MCP tool: code_reasoning.plan
    - [ ] 2.2.1 Plan schema
    - [ ] 2.2.2 Implement tool
    - [ ] 2.2.3 Minimal‑edit constraints
    - [ ] 2.2.4 Unit tests
  - [ ] 2.3 Lint and pre‑commit integration step
    - [ ] 2.3.1 Fail‑closed behavior

- [ ] Phase 3: Sandboxed Execution + Docs Auto‑Assist
  - [ ] 3.1 MCP tool: sandbox.run_python
    - [ ] 3.1.1 Sandbox policy
    - [ ] 3.1.2 Executor
    - [ ] 3.1.3 Policy tests
  - [ ] 3.2 Context7 auto‑docs in loop
    - [ ] 3.2.1 Symbol extraction
    - [ ] 3.2.2 Fetch + summarization
    - [ ] 3.2.3 Toggle + tests

- [ ] Phase 4: Optional Packs (Off by default)
  - [ ] 4.1 AWS MCP profile
    - [ ] 4.1.1 Config and env detection
    - [ ] 4.1.2 Safeguards docs
  - [ ] 4.2 Desktop notifications bridge
    - [ ] 4.2.1 Minimal notifier
    - [ ] 4.2.2 Docs

- [ ] Phase 5: Platform Integration & Documentation
  - [ ] 5.1 Dev workflow integration
    - [ ] 5.1.1 Glue (no duplication)
  - [ ] 5.2 Documentation
    - [ ] 5.2.1 Author docs and examples
  - [ ] 5.3 Telemetry and guardrails
    - [ ] 5.3.1 Opt‑in hooks and docs

### Validation Gates
- [x] Gate A: 1.1 + 1.3 pass
- [ ] Gate B: 1.2 e2e (fix failing test via minimal edit + lint + re‑run)
- [ ] Gate C: 2.x reasoning profiles + plan constraints
- [ ] Gate D: 3.x sandbox policy enforced
- [ ] Gate E: Docs complete; pre‑commit green; telemetry opt‑in

