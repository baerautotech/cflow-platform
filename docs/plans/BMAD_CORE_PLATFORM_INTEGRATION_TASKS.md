# BMAD Core Platform Integration – AEMI SRP Task Breakdown

Document version: 1.0  
Date: 2025-09-14  
Source Plan: `docs/plans/BMAD_CORE_PLATFORM_INTEGRATION_PLAN.md`  
External Context: `docs/external/BMAD-METHOD/gitingest.md` (GitIngest snapshot of BMAD repo)

Notes
- All tasks are SRP-compliant, atomic (15–60 min where possible), with explicit dependencies and acceptance criteria.  
- Use KnowledgeRAG/KnowledgeGraph lookups where marked to retrieve plan excerpts, BMAD repo context, and code references.  
- Gate: Codegen orchestration is blocked until Planning Gate is approved (Story complete).

---

## 1. Compliance & Vendoring

[ ] 1.1 Vendor BMAD (MIT) into platform
- Description: Add BMAD core to `vendor/bmad/` or as a submodule with legal attribution. Include BMAD `LICENSE` and Third-Party Notice entry. Ensure no executable BMAD web UI is enabled.
- Context: Plan → Summary; Licensing; Installer Integration.
- RAG/KG: RAG query for “BMAD LICENSE and structure” using `docs/external/BMAD-METHOD/gitingest.md`.
- Inputs: BMAD repo snapshot; internal vendor policy.
- Outputs: `vendor/bmad/` tree; NOTICE update.
- Acceptance: License headers present; NOTICE updated; build unaffected.
- Dependencies: None.

[ ] 1.2 Define upstream sync policy and contract tests
- Description: Establish monthly upstream sync procedure and contract tests for BMAD planning/story APIs to detect breaking changes before merge.
- Context: Plan → Risks & Mitigations; Timeline.
- RAG/KG: RAG for BMAD API surface references; link to internal testing patterns.
- Outputs: `docs/engineering/bmad_upstream_sync.md`; contract test suite skeleton.
- Acceptance: Doc approved; tests run in CI as pending.
- Dependencies: 1.1.

---

## 2. BMAD Expansion Packs Integration

[ ] 2.1 Inventory available expansion packs
- Description: Catalog all BMAD expansion packs in vendor/bmad/expansion-packs/ and document their capabilities, agents, templates, and workflows.
- Context: Plan → BMAD Expansion Packs Integration; Available Packs.
- RAG/KG: RAG query for expansion pack documentation and capabilities.
- Outputs: `docs/architecture/bmad_expansion_packs_inventory.md`.
- Acceptance: Reviewed by architecture; covers all available packs.
- Dependencies: 1.1.

[ ] 2.2 Design expansion pack registry schema
- Description: Design database schema for expansion pack registry, project associations, and pack metadata storage.
- Context: Plan → Database Schema Design; Expansion Pack Architecture.
- RAG/KG: Query schema docs; link entity relationships.
- Outputs: ERD/DDL for expansion pack tables.
- Acceptance: ERD approved; migration draft ready.
- Dependencies: 2.1.

[ ] 2.3 Implement expansion pack HTTP API endpoints
- Description: Create REST API endpoints for expansion pack management (install, list, enable, execute).
- Context: Plan → API Contracts; Expansion Pack Integration.
- Outputs: HTTP API handlers, OpenAPI spec, deployed to cerebral cluster.
- Acceptance: Contract tests green; accessible via BMAD API facade.
- Dependencies: 2.2, 3.2.

[ ] 2.4 Implement dynamic pack loading system
- Description: Create system to dynamically load expansion packs based on project requirements and tenant configuration.
- Context: Plan → Cerebral Cluster Integration; Dynamic Loading.
- Outputs: Pack loader service, configuration management, deployed to cerebral cluster.
- Acceptance: Packs load on-demand; configuration persisted.
- Dependencies: 2.3.

---

## 3. Gap Analysis (Architecture/Data/UI)

[ ] 3.1 Inventory BMAD planning/story interfaces
- Description: Catalog BMAD agent entrypoints (PRD, Architecture, Story). Capture inputs/outputs for API facade.
- Context: Plan → API Contracts; Process Outline.
- RAG/KG: RAG pull from GitIngest BMAD docs for agent roles and flows.
- Outputs: `docs/architecture/bmad_api_inventory.md`.
- Acceptance: Reviewed by architecture; covers PRD/Architecture/Story.
- Dependencies: 1.1.

[ ] 3.2 Map artifacts to DB schema
- Description: Map PRD/Architecture/Story to `cerebral_documents`, tasks to `cerebral_tasks`, indexes to RAG/KG.
- Context: Plan → Database Schema Design.
- RAG/KG: Query schema docs; link entity relationships.
- Outputs: ERD/DDL deltas.
- Acceptance: ERD approved; migration draft ready.
- Dependencies: 3.1.

[ ] 3.3 UX scope for PRD/Architecture/Story forms
- Description: Define UX flows and approvals in Cerebral Web; mobile/wearable endpoints.
- Context: Plan → Web/mobile/wearable UX.
- Outputs: Wireframes/spec.
- Acceptance: PM sign-off.
- Dependencies: 3.1.

---

## 4. BMAD HTTP API Facade (Cerebral Cluster)

[ ] 4.1 Scaffold BMAD HTTP API service (cerebral-deployment)
- Description: Create Kubernetes manifests (Deployment/Service/Ingress) for BMAD HTTP API facade on cerebral cluster.
- Context: Plan → Installer Integration; Scalability.
- Outputs: `k8s/bmad-api-service.yaml` in cerebral-deployment.
- Acceptance: Pod ready; health endpoint OK; accessible via cluster ingress.
- Dependencies: 1.1.

[ ] 4.2 Implement BMAD HTTP API facade endpoints
- Description: POST `/bmad/planning/prd|architecture|story`, `/bmad/gates/approve`; validations; authz.
- Context: Plan → API Contracts; Security.
- Outputs: HTTP API handlers, OpenAPI spec, deployed to cerebral cluster.
- Acceptance: Contract tests green; accessible via `mcp.cerebral.baerautotech.com`.
- Dependencies: 3.1, 4.1.

[ ] 4.3 WebMCP integration for BMAD tools
- Description: Add BMAD tools to cflow-platform tool registry; update WebMCP server to import and route BMAD calls.
- Context: Plan → MCP Integration; Tool Registry.
- Outputs: Updated `tool_registry.py`; WebMCP server integration.
- Acceptance: BMAD tools available via WebMCP; HTTP routing to BMAD API.
- Dependencies: 4.2.

[ ] 4.4 Provider router integration (hosted LLM only)
- Description: Route BMAD agent calls via provider router; enforce tenant quotas, cost caps, egress allowlist.
- Context: Plan → Security & Compliance; Provider Policy.
- Outputs: Router config; policy checks.
- Acceptance: Quota tests pass; blocked without keys.
- Dependencies: 3.2.

---

## 4. Storage + RAG/KG

[ ] 4.1 DB migrations for artifacts and audit
- Description: Add/alter tables for `cerebral_documents`, task links, activities; RLS policies.
- Context: Plan → Database Schema Design; Security.
- Outputs: SQL migrations; RLS.
- Acceptance: Migrations apply; RLS enforced.
- Dependencies: 2.2.

[ ] 4.2 Persist artifacts and index to RAG
- Description: On PRD/Architecture/Story upsert, write to DB, chunk and embed; add KG edges.
- Context: Plan → Process Outline; RAG/KG.
- Outputs: API + workers; tests.
- Acceptance: Artifacts present; vectors searchable.
- Dependencies: 4.1, 3.2.

[ ] 4.3 KG incremental builder hooks
- Description: Update KG on artifact/code/task changes; ensure link integrity.
- Context: Plan → Process Outline; Scalability.
- Outputs: KG job updates; tests.
- Acceptance: Edges created; no cycles unless intended.
- Dependencies: 4.2.

[ ] 4.4 Centralize AutoDoc processing on server cluster
- Description: Replace local post-commit heavy processing with server-side workers. Implement `/webhooks/git-commit` and `/rag/index` to enqueue jobs; enforce FileLock/ChromaDBWriteLock in workers; use server Apple Silicon/Ollama strictly for embeddings.
- Context: Plan → Centralized AutoDoc Integration; Installer Integration; Security.
- Outputs: API webhook, queue producer, worker deployments, NetworkPolicies.
- Acceptance: Local commits trigger server indexing; audit trails captured; no local mutex lock incidents.
- Dependencies: 3.1, 3.2, 8.1.

[ ] 4.5 Artifact storage and model cache hardening
- Description: Configure MinIO/S3 buckets for chunk artifacts and model caches; set HF/TOKENIZER safe envs; isolate per-tenant prefixes.
- Context: Plan → Centralized AutoDoc Integration; Security & Compliance Plan.
- Outputs: Bucket policies, env templates, validation tests.
- Acceptance: Buckets provisioned; safe envs verified in pods; per-tenant isolation tested.
- Dependencies: 4.4.

---

## 5. CAEF Orchestration (Gates)

[ ] 5.1 Implement Planning Gate enforcement
- Description: Prevent code/test/validation orchestration until Story approved.
- Context: Plan → Process Outline; Acceptance Criteria.
- Outputs: Gate check middleware; audit logs.
- Acceptance: Gate blocks until approval; audit shows action.
- Dependencies: 3.2, 4.2.

[ ] 5.2 Start CAEF jobs post-approval
- Description: Accept gate token to start multi-agent execution; stream status.
- Context: Plan → API Contracts.
- Outputs: `/caef/jobs/start` integration.
- Acceptance: Sample run executes; events logged.
- Dependencies: 5.1.

---

## 6. Web/Mobile/Wearable UX

[ ] 6.1 PRD authoring wizard
- Description: Cerebral Web form with validation, save drafts, submit to BMAD endpoint.
- Context: Plan → UX.
- Outputs: UI + API wiring.
- Acceptance: Draft/save/submit flows work.
- Dependencies: 3.2, 4.2.

[ ] 6.2 Architecture builder
- Description: Create/approve architecture; versioning and diffs.
- Context: Plan → UX.
- Outputs: UI + storage.
- Acceptance: Approvals logged; artifacts versioned.
- Dependencies: 6.1.

[ ] 6.3 Story generator/reviewer
- Description: Generate story, review changes, approve Planning Gate.
- Context: Plan → Process Outline.
- Outputs: UI, approvals, gate call.
- Acceptance: Gate flips; CAEF eligible.
- Dependencies: 6.2, 5.1.

[ ] 6.4 Mobile/wearable endpoints
- Description: Approve gates, monitor runs, notifications; limited authoring.
- Context: Plan → UX.
- Outputs: REST endpoints; mobile views.
- Acceptance: Actions complete; telemetry OK.
- Dependencies: 6.3.

---

## 7. Security & Compliance

[ ] 7.1 Vault-managed secrets for providers (cerebral-deployment)
- Description: Wire Vault secret injection; rotations; no plaintext envs.
- Context: Plan → Security & Compliance.
- Outputs: Secret templates; rotations.
- Acceptance: Pods mount secrets; rotation test passes.
- Dependencies: 3.1.

[ ] 7.2 Egress/DLP policies and allowlists (cerebral-deployment)
- Description: Restrict LLM endpoints; DLP proxy; per-tenant egress policies.
- Context: Plan → Security & Compliance.
- Outputs: NetworkPolicy/proxy config.
- Acceptance: Disallowed egress blocked; logs show attempt.
- Dependencies: 3.3.

[ ] 7.3 Audit logging and SIEM export
- Description: Append-only logs for all actions; SIEM integration; retention.
- Context: Plan → Security & Compliance.
- Outputs: Log schema; exporter.
- Acceptance: Sample audits visible in SIEM.
- Dependencies: 3.2, 5.2.

---

## 8. Scalability & Observability

[ ] 8.1 Queue + worker pools for planning jobs (cerebral-deployment)
- Description: Introduce queue and worker deployments with idempotency and retries.
- Context: Plan → Scalability.
- Outputs: Worker charts; retry policy.
- Acceptance: Load test at target TPS; no backlog growth.
- Dependencies: 3.2.

[ ] 8.1.1 RAG/KG indexer worker pool (cerebral-deployment)
- Description: Dedicated worker Deployment for embeddings+chunking; concurrency controls; dead-letter queue; idempotent job keys by commit/file hash.
- Context: Plan → Centralized AutoDoc Integration; Scalability Plan.
- Outputs: Deployment/Service YAMLs; queue configs; runbooks.
- Acceptance: Sustained load at target QPS; zero duplicate jobs; DLQ handling verified.
- Dependencies: 4.4, 8.1.

[ ] 8.1.2 GPU-enabled indexer images and scheduling (cerebral-deployment)
- Description: Build CUDA images for PyTorch/SentenceTransformers; add GPU requests/limits; install NVIDIA Device Plugin; configure nodeSelectors/taints and fallbacks.
- Context: Plan → GPU Acceleration Strategy; Installer Integration.
- Outputs: Dockerfiles, K8s manifests, device plugin install, HPA tuned for GPU.
- Acceptance: Jobs run on GPU nodes; throughput/latency improvement recorded; CPU fallback tested.
- Dependencies: 8.1.1.

[ ] 8.2 HPA and SLO dashboards (cerebral-deployment)
- Description: HPA for APIs/workers; dashboards for p95 latency, queue depth, token/cost usage.
- Context: Plan → Observability; Scalability.
- Outputs: Grafana/Prometheus configs.
- Acceptance: SLOs displayed; alerts configured.
- Dependencies: 8.1.

---

## 9. Installer Integration (1‑Touch)

[ ] 9.1 Add BMAD to installer (cerebral-deployment)
- Description: Extend 1‑touch scripts to deploy BMAD service, workers, secrets, routes.
- Context: Plan → Installer Integration.
- Outputs: Installer scripts/templates.
- Acceptance: Fresh install brings BMAD up healthy.
- Dependencies: 3.1, 7.1.

[ ] 9.2 Canary/rollback strategy (cerebral-deployment)
- Description: Blue/green or canary rollout; reversible migrations; backups.
- Context: Plan → Rollback Plan.
- Outputs: Release runbook.
- Acceptance: Simulated rollback succeeds.
- Dependencies: 9.1.

---

## 10. Local Development & IDE Integration

[ ] 10.1 `cflow-local bmad` CLI (HTTP client)
- Description: Implement HTTP client for BMAD API facade; login, provider set, prd/arch/story upsert, sync.
- Context: Plan → Local Runner & IDE; API Contracts.
- Outputs: CLI commands + docs; HTTP client library.
- Acceptance: CLI e2e against cerebral cluster BMAD API.
- Dependencies: 3.2, 4.2.

[ ] 10.2 WebMCP tool integration
- Description: Add BMAD tools to WebMCP server; ensure proper HTTP routing to BMAD API facade.
- Context: Plan → MCP Integration; Tool Registry.
- Outputs: WebMCP server updates; tool routing.
- Acceptance: BMAD tools accessible via WebMCP; proper HTTP routing.
- Dependencies: 3.3, 10.1.

[ ] 10.3 Sync engine (bidirectional)
- Description: Cursor-based sync for artifacts and metadata; conflict resolution; audit.
- Context: Plan → API Contracts; Governance.
- Outputs: Sync service + tests.
- Acceptance: Edits converge; conflicts logged.
- Dependencies: 10.1.

---

## 11. Migration & Cleanup

[ ] 11.1 Inventory and tag legacy systems
- Description: Enumerate abandoned TaskMaster/legacy UIs/mocks/duplicated validators; tag `pre-bmad-core`.
- Context: Plan → Migration & Cleanup.
- RAG/KG: Graph search for known paths; report.
- Outputs: Inventory report.
- Acceptance: Reviewed by arch; signed.
- Dependencies: 2.1.

[ ] 11.2 Archive and remove
- Description: Move historical docs to `docs/_archive/`; delete forbidden code; replace entrypoints.
- Context: Plan → Migration & Cleanup.
- Outputs: PRs with deletions/moves; CI green.
- Acceptance: Build/tests pass; no import breaks.
- Dependencies: 11.1.

[ ] 11.3 Post-clean validation
- Description: Lints/tests/security scans; policy checks for forbidden patterns.
- Context: Plan → Acceptance Criteria.
- Outputs: Reports; CI gates.
- Acceptance: All green.
- Dependencies: 11.2.

---

## 12. Pilot & Rollout

[ ] 12.1 Internal pilot project
- Description: Run full PRD→Architecture→Story→CAEF flow with a real initiative; measure quality/cycle time.
- Context: Plan → Timeline; Acceptance Criteria.
- Outputs: Pilot report.
- Acceptance: Metrics improved vs. baseline.
- Dependencies: 6.3, 5.2, 4.2.

[ ] 12.2 Production canary
- Description: Enable BMAD for a subset of tenants/projects; monitor SLOs and costs.
- Context: Plan → Rollout Plan.
- Outputs: Canary config; dashboards.
- Acceptance: No regressions; stakeholder approval.
- Dependencies: 12.1, 9.2.

---

## KnowledgeRAG & KG Usage Index
- PRD/Architecture/Story authoring: retrieve plan excerpts and BMAD agent roles from RAG (GitIngest doc) to enrich prompts.  
- Mapping tasks (schema/ERD): link plan sections to KG nodes (Artifacts↔Tables↔Indexes).  
- Cleanup inventory: KG search for deprecated modules; generate deprecation PRs.  
- Observability and quotas: RAG for provider policy templates; KG for service dependencies.
