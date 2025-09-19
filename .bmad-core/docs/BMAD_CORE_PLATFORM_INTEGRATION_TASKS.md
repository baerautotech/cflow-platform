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

## 2. BMAD Human-in-the-Loop (HIL) Approval System

### 2.1 Interactive Document Creation System
**2.1.1** Implement interactive PRD creation with Q&A sessions
**2.1.2** Implement interactive Architecture creation with Q&A sessions  
**2.1.3** Implement interactive Story creation with approval workflow
**2.1.4** Create interactive session management database schema
**2.1.5** Implement interactive session APIs and handlers

### 2.2 Approval Gate System
**2.2.1** Implement document approval workflow system
**2.2.2** Create approval tracking database schema
**2.2.3** Implement approval request and confirmation APIs
**2.2.4** Create approval status tracking and notifications
**2.2.5** Implement approval history and audit logging

### 2.3 Workflow Gate Enforcement
**2.3.1** Implement workflow gate enforcement in orchestrator
**2.3.2** Create gate status tracking and validation
**2.3.3** Implement gate blocking logic for unapproved documents
**2.3.4** Create gate status APIs and client integration
**2.3.5** Implement gate transition validation and error handling

### 2.4 Client Integration for HIL
**2.4.1** Create interactive session UI components
**2.4.2** Implement document approval dashboard
**2.4.3** Create workflow gate status display
**2.4.4** Implement approval notification system
**2.4.5** Create CLI commands for interactive sessions and approvals

## 3. BMAD Brownfield vs Greenfield Integration

[ ] 2.1 Implement project type detection system
- Description: Create core service for automatic detection of greenfield vs brownfield projects based on user input and existing codebase analysis.
- Context: Plan → BMAD Brownfield vs Greenfield Integration; Project Type Detection Logic.
- RAG/KG: RAG query for BMAD brownfield documentation and project type detection patterns.
- Outputs: Project type detection service, API endpoints, database schema extensions.
- Acceptance: Service detects project type accurately; API endpoints functional; schema updated.
- Dependencies: 1.1.

[ ] 2.2 Implement brownfield project documentation generation
- Description: Create service to generate comprehensive documentation from existing codebase using BMAD's document-project task.
- Context: Plan → Brownfield Workflow Components; Project Documentation Phase.
- RAG/KG: Query BMAD document-project task documentation and implementation patterns.
- Outputs: Documentation generation service, API endpoints, integration with Knowledge Graph.
- Acceptance: Service generates complete system documentation; indexed in Knowledge Graph.
- Dependencies: 2.1.

[ ] 2.3 Implement brownfield-specific PRD creation
- Description: Create brownfield PRD creation service using brownfield-prd-tmpl.yaml with existing system analysis and integration planning.
- Context: Plan → Brownfield Workflow Components; Enhancement Planning Phase.
- RAG/KG: Query BMAD brownfield PRD template and enhancement planning patterns.
- Outputs: Brownfield PRD creation service, API endpoints, template integration.
- Acceptance: Service creates comprehensive brownfield PRDs; templates properly integrated.
- Dependencies: 2.2.

[ ] 2.4 Implement brownfield-specific architecture creation
- Description: Create brownfield architecture creation service using brownfield-architecture-tmpl.yaml with integration strategy and migration planning.
- Context: Plan → Brownfield Workflow Components; Architecture Planning Phase.
- RAG/KG: Query BMAD brownfield architecture template and integration strategy patterns.
- Outputs: Brownfield architecture creation service, API endpoints, integration strategy planning.
- Acceptance: Service creates comprehensive brownfield architectures; integration strategies included.
- Dependencies: 2.3.

[ ] 2.5 Implement brownfield-specific story creation
- Description: Create brownfield story creation service for isolated changes and focused enhancements.
- Context: Plan → Brownfield Workflow Components; Story Creation.
- RAG/KG: Query BMAD brownfield story creation patterns and isolated change handling.
- Outputs: Brownfield story creation service, API endpoints, isolated change support.
- Acceptance: Service creates focused brownfield stories; isolated changes properly handled.
- Dependencies: 2.4.

[ ] 2.6 Implement workflow routing system
- Description: Create workflow routing system that directs projects to appropriate greenfield or brownfield workflows based on project type detection.
- Context: Plan → Unified Workflow Integration; Server Platform Components.
- RAG/KG: Query BMAD workflow routing patterns and project type handling.
- Outputs: Workflow routing service, API endpoints, project type-based routing.
- Acceptance: Service routes workflows correctly; project type-based routing functional.
- Dependencies: 2.1, 2.5.

[ ] 2.7 Implement enhanced PO master checklist
- Description: Enhance PO master checklist to adapt intelligently based on project type (greenfield vs brownfield) with appropriate validation criteria.
- Context: Plan → Brownfield Workflow Components; Validation Phase.
- RAG/KG: Query BMAD PO master checklist and project type-specific validation patterns.
- Outputs: Enhanced PO master checklist, project type-specific validation, API endpoints.
- Acceptance: Checklist adapts to project type; validation criteria appropriate for each type.
- Dependencies: 2.6.

[ ] 2.8 Implement client integration for project type management
- Description: Create client integration components for web/mobile/wearable UIs, IDE integration, and CLI tools to support project type detection and workflow selection.
- Context: Plan → Client Integration Requirements; Entry Points.
- RAG/KG: Query BMAD client integration patterns and project type management.
- Outputs: Client integration components, UI components, IDE integration, CLI tools.
- Acceptance: All client interfaces support project type management; workflow selection functional.
- Dependencies: 2.7.

---

## 3. BMAD Technical Research Expansion Pack Integration

[ ] 3.1 Create BMAD Technical Research expansion pack structure
- Description: Create complete expansion pack structure with agents, tasks, templates, workflows, and team configuration
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Key Features
- Outputs: Complete `bmad-technical-research` expansion pack in `vendor/bmad/expansion-packs/`
- Acceptance: Expansion pack structure complete with all components
- Dependencies: 1.1

[ ] 3.2 Implement specialized research agents
- Description: Create 6 specialized research agents (Code Analyst, Vector Researcher, Documentation Specialist, Knowledge Graph Navigator, Task Research Coordinator, Technical Writer)
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Key Features
- Outputs: Agent definitions with commands, dependencies, and interactive workflows
- Acceptance: All agents functional with proper command structure
- Dependencies: 3.1

[ ] 3.3 Create YAML template system for document generation
- Description: Create comprehensive YAML template system for TDD, API docs, user guides, specs, README, architecture, deployment, troubleshooting, changelog
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Template System Architecture
- Outputs: YAML templates with metadata, validation, and downstream processing rules
- Acceptance: Templates generate standardized documents with quality validation
- Dependencies: 3.2

[ ] 3.4 Implement template-based document generation workflow
- Description: Create interactive workflow for template selection, information collection, document generation, and downstream processing
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Template Selection Process
- Outputs: Complete document generation workflow with user interaction
- Acceptance: Users can select templates and generate documents through interactive workflow
- Dependencies: 3.3

[ ] 3.5 Implement downstream processing (task/story/epic creation)
- Description: Create automatic task/story/epic creation from documents using standardized templates
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Downstream Processing
- Outputs: Task creation, story generation, and epic planning templates with field mapping
- Acceptance: Documents automatically generate tasks/stories/epics with proper field mapping
- Dependencies: 3.4

[ ] 3.6 Integrate with existing cflow systems
- Description: Connect Technical Research expansion pack to existing embedding service, Knowledge Graph, task management, and database systems
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Integration Benefits
- Outputs: Integration with vector search, KG, task management, and Supabase
- Acceptance: All integrations functional with multi-user cluster support
- Dependencies: 3.5

[ ] 3.7 Deprecate Enhanced Research handlers
- Description: Remove Enhanced Research handlers and replace with BMAD Technical Research expansion pack
- Context: Plan → BMAD Technical Research Expansion Pack Integration; Enhanced Research Deprecation
- Outputs: Enhanced Research handlers removed, client integrations updated
- Acceptance: No Enhanced Research dependencies, all functionality through BMAD expansion pack
- Dependencies: 3.6

---

## 4. Multi-User Cluster Compatibility Fixes

### 4.1 HashiCorp Vault Integration
[ ] 4.1.1 Implement Vault client for secret management
- Description: Replace SecretStore with HashiCorp Vault client for centralized secret management
- Context: Plan → Multi-User Cluster Compatibility Fixes; HashiCorp Vault Integration
- Outputs: Vault client implementation, secret injection, rotation policies
- Acceptance: Secrets managed through Vault, no local file dependencies
- Dependencies: 1.1

[ ] 4.1.2 Migrate existing secrets to Vault
- Description: Migrate all existing secrets from local files to HashiCorp Vault
- Context: Plan → Multi-User Cluster Compatibility Fixes; HashiCorp Vault Integration
- Outputs: All secrets in Vault, local secret files removed
- Acceptance: All secrets accessible through Vault API, local files removed
- Dependencies: 4.1.1

[ ] 4.1.3 Update secret access patterns
- Description: Update all components to use Vault client instead of local SecretStore
- Context: Plan → Multi-User Cluster Compatibility Fixes; HashiCorp Vault Integration
- Outputs: Updated secret access in all components
- Acceptance: All components use Vault for secret access
- Dependencies: 4.1.2

### 4.2 BMAD Expansion Pack Storage Fix
[ ] 4.2.1 Create expansion pack database schema
- Description: Create database schema for expansion pack metadata and content storage
- Context: Plan → Multi-User Cluster Compatibility Fixes; BMAD Expansion Pack Storage Fix
- Outputs: Database schema for bmad_expansion_packs and project_expansion_packs tables
- Acceptance: Schema supports expansion pack metadata and project associations
- Dependencies: 1.1

[ ] 4.2.2 Migrate expansion packs to database/S3 storage
- Description: Move expansion packs from local file system to database metadata and S3 content storage
- Context: Plan → Multi-User Cluster Compatibility Fixes; BMAD Expansion Pack Storage Fix
- Outputs: Expansion packs stored in database and S3, local files removed
- Acceptance: Expansion packs accessible through database/S3, no local file dependencies
- Dependencies: 4.2.1

[ ] 4.2.3 Update expansion pack handlers
- Description: Update expansion pack handlers to use database/S3 instead of local file system
- Context: Plan → Multi-User Cluster Compatibility Fixes; BMAD Expansion Pack Storage Fix
- Outputs: Updated handlers for database/S3 access
- Acceptance: Handlers work with database/S3 storage
- Dependencies: 4.2.2

### 4.3 Memory Storage Fix
[ ] 4.3.1 Migrate memory storage to Supabase
- Description: Replace local JSONL memory storage with Supabase memory_items table
- Context: Plan → Multi-User Cluster Compatibility Fixes; Memory Storage Fix
- Outputs: Memory storage using Supabase, local JSONL removed
- Acceptance: Memory accessible through database, no local file dependencies
- Dependencies: 1.1

[ ] 4.3.2 Update memory handlers
- Description: Update memory handlers to use Supabase instead of local JSONL files
- Context: Plan → Multi-User Cluster Compatibility Fixes; Memory Storage Fix
- Outputs: Updated memory handlers for database access
- Acceptance: Memory handlers work with Supabase storage
- Dependencies: 4.3.1

### 4.4 RAG Document Storage Fix
[ ] 4.4.1 Create TDD document database schema
- Description: Create database schema for TDD documents and object storage references
- Context: Plan → Multi-User Cluster Compatibility Fixes; RAG Document Storage Fix
- Outputs: Database schema for tdd_documents and object_storage_refs tables
- Acceptance: Schema supports TDD document storage and S3 references
- Dependencies: 1.1

[ ] 4.4.2 Migrate TDD documents to database/S3 storage
- Description: Move TDD documents from local files to database storage with S3 for large content
- Context: Plan → Multi-User Cluster Compatibility Fixes; RAG Document Storage Fix
- Outputs: TDD documents stored in database/S3, local files removed
- Acceptance: TDD documents accessible through database/S3, no local file dependencies
- Dependencies: 4.4.1

[ ] 4.4.3 Update RAG handlers
- Description: Update RAG handlers to use database/S3 instead of local file system
- Context: Plan → Multi-User Cluster Compatibility Fixes; RAG Document Storage Fix
- Outputs: Updated RAG handlers for database/S3 access
- Acceptance: RAG handlers work with database/S3 storage
- Dependencies: 4.4.2

### 4.5 Service Integration Fixes
[ ] 4.5.1 Deploy Plan Parser as cluster service
- Description: Deploy plan parser as cluster service, remove local monorepo dependency
- Context: Plan → Multi-User Cluster Compatibility Fixes; Service Integration Fixes
- Outputs: Plan parser service deployed in cluster, API-based integration
- Acceptance: Plan parser accessible through cluster service, no local dependencies
- Dependencies: 1.1

[ ] 4.5.2 Deploy Enhanced Research as cluster service
- Description: Deploy enhanced research handlers as cluster service, remove local monorepo dependency
- Context: Plan → Multi-User Cluster Compatibility Fixes; Service Integration Fixes
- Outputs: Enhanced research service deployed in cluster, API-based integration
- Acceptance: Enhanced research accessible through cluster service, no local dependencies
- Dependencies: 1.1

### 4.6 Multi-User Testing and Validation
[ ] 4.6.1 Test all components with multiple users
- Description: Test all fixed components with multiple users to ensure cluster accessibility
- Context: Plan → Multi-User Cluster Compatibility Fixes; Multi-User Testing
- Outputs: Multi-user test results and validation reports
- Acceptance: All components work correctly with multiple users
- Dependencies: 4.1.3, 4.2.3, 4.3.2, 4.4.3, 4.5.2

[ ] 4.6.2 Validate cluster accessibility
- Description: Validate that all components are accessible from cluster nodes
- Context: Plan → Multi-User Cluster Compatibility Fixes; Multi-User Testing
- Outputs: Cluster accessibility validation report
- Acceptance: All components accessible from all cluster nodes
- Dependencies: 4.6.1

[ ] 4.6.3 Performance testing
- Description: Test performance with multiple users and cluster load
- Context: Plan → Multi-User Cluster Compatibility Fixes; Multi-User Testing
- Outputs: Performance test results and optimization recommendations
- Acceptance: Performance meets SLOs with multiple users
- Dependencies: 4.6.2

---

## 5. BMAD Expansion Packs Integration

[ ] 5.1 Inventory available expansion packs
- Description: Catalog all BMAD expansion packs in vendor/bmad/expansion-packs/ and document their capabilities, agents, templates, and workflows.
- Context: Plan → BMAD Expansion Packs Integration; Available Packs.
- RAG/KG: RAG query for expansion pack documentation and capabilities.
- Outputs: `docs/architecture/bmad_expansion_packs_inventory.md`.
- Acceptance: Reviewed by architecture; covers all available packs.
- Dependencies: 1.1.

[ ] 5.2 Design expansion pack registry schema
- Description: Design database schema for expansion pack registry, project associations, and pack metadata storage.
- Context: Plan → Database Schema Design; Expansion Pack Architecture.
- RAG/KG: Query schema docs; link entity relationships.
- Outputs: ERD/DDL for expansion pack tables.
- Acceptance: ERD approved; migration draft ready.
- Dependencies: 5.1.

[ ] 5.3 Implement expansion pack HTTP API endpoints
- Description: Create REST API endpoints for expansion pack management (install, list, enable, execute).
- Context: Plan → API Contracts; Expansion Pack Integration.
- Outputs: HTTP API handlers, OpenAPI spec, deployed to cerebral cluster.
- Acceptance: Contract tests green; accessible via BMAD API facade.
- Dependencies: 5.2.

[ ] 5.4 Implement dynamic pack loading system
- Description: Create system to dynamically load expansion packs based on project requirements and tenant configuration.
- Context: Plan → Cerebral Cluster Integration; Dynamic Loading.
- Outputs: Pack loader service, configuration management, deployed to cerebral cluster.
- Acceptance: Packs load on-demand; configuration persisted.
- Dependencies: 5.3.

---

## 6. Gap Analysis (Architecture/Data/UI)

[ ] 6.1 Inventory BMAD planning/story interfaces
- Description: Catalog BMAD agent entrypoints (PRD, Architecture, Story). Capture inputs/outputs for API facade.
- Context: Plan → API Contracts; Process Outline.
- RAG/KG: RAG pull from GitIngest BMAD docs for agent roles and flows.
- Outputs: `docs/architecture/bmad_api_inventory.md`.
- Acceptance: Reviewed by architecture; covers PRD/Architecture/Story.
- Dependencies: 1.1.

[ ] 6.2 Map artifacts to DB schema
- Description: Map PRD/Architecture/Story to `cerebral_documents`, tasks to `cerebral_tasks`, indexes to RAG/KG.
- Context: Plan → Database Schema Design.
- RAG/KG: Query schema docs; link entity relationships.
- Outputs: ERD/DDL deltas.
- Acceptance: ERD approved; migration draft ready.
- Dependencies: 6.1.

[ ] 6.3 UX scope for PRD/Architecture/Story forms
- Description: Define UX flows and approvals in Cerebral Web; mobile/wearable endpoints.
- Context: Plan → Web/mobile/wearable UX.
- Outputs: Wireframes/spec.
- Acceptance: PM sign-off.
- Dependencies: 6.1.

---

## 7. BMAD HTTP API Facade (Cerebral Cluster)

[ ] 7.1 Scaffold BMAD HTTP API service (cerebral-deployment)
- Description: Create Kubernetes manifests (Deployment/Service/Ingress) for BMAD HTTP API facade on cerebral cluster.
- Context: Plan → Installer Integration; Scalability.
- Outputs: `k8s/bmad-api-service.yaml` in cerebral-deployment.
- Acceptance: Pod ready; health endpoint OK; accessible via cluster ingress.
- Dependencies: 1.1.

[ ] 7.2 Implement BMAD HTTP API facade endpoints
- Description: POST `/bmad/planning/prd|architecture|story`, `/bmad/gates/approve`; validations; authz.
- Context: Plan → API Contracts; Security.
- Outputs: HTTP API handlers, OpenAPI spec, deployed to cerebral cluster.
- Acceptance: Contract tests green; accessible via `mcp.cerebral.baerautotech.com`.
- Dependencies: 5.1, 6.1.

[ ] 7.3 WebMCP integration for BMAD tools
- Description: Add BMAD tools to cflow-platform tool registry; update WebMCP server to import and route BMAD calls.
- Context: Plan → MCP Integration; Tool Registry.
- Outputs: Updated `tool_registry.py`; WebMCP server integration.
- Acceptance: BMAD tools available via WebMCP; HTTP routing to BMAD API.
- Dependencies: 6.2.

[ ] 7.4 Provider router integration (hosted LLM only)
- Description: Route BMAD agent calls via provider router; enforce tenant quotas, cost caps, egress allowlist.
- Context: Plan → Security & Compliance; Provider Policy.
- Outputs: Router config; policy checks.
- Acceptance: Quota tests pass; blocked without keys.
- Dependencies: 5.2.

---

## 8. Storage + RAG/KG

[ ] 8.1 DB migrations for artifacts and audit
- Description: Add/alter tables for `cerebral_documents`, task links, activities; RLS policies.
- Context: Plan → Database Schema Design; Security.
- Outputs: SQL migrations; RLS.
- Acceptance: Migrations apply; RLS enforced.
- Dependencies: 2.8.

[ ] 8.2 Persist artifacts and index to RAG
- Description: On PRD/Architecture/Story upsert, write to DB, chunk and embed; add KG edges.
- Context: Plan → Process Outline; RAG/KG.
- Outputs: API + workers; tests.
- Acceptance: Artifacts present; vectors searchable.
- Dependencies: 6.1, 5.2.

[ ] 8.3 KG incremental builder hooks
- Description: Update KG on artifact/code/task changes; ensure link integrity.
- Context: Plan → Process Outline; Scalability.
- Outputs: KG job updates; tests.
- Acceptance: Edges created; no cycles unless intended.
- Dependencies: 6.2.

[ ] 8.4 Centralize AutoDoc processing on server cluster
- Description: Replace local post-commit heavy processing with server-side workers. Implement `/webhooks/git-commit` and `/rag/index` to enqueue jobs; enforce FileLock/ChromaDBWriteLock in workers; use server Apple Silicon/Ollama strictly for embeddings.
- Context: Plan → Centralized AutoDoc Integration; Installer Integration; Security.
- Outputs: API webhook, queue producer, worker deployments, NetworkPolicies.
- Acceptance: Local commits trigger server indexing; audit trails captured; no local mutex lock incidents.
- Dependencies: 5.1, 5.2, 8.1.

[ ] 8.5 Artifact storage and model cache hardening
- Description: Configure MinIO/S3 buckets for chunk artifacts and model caches; set HF/TOKENIZER safe envs; isolate per-tenant prefixes.
- Context: Plan → Centralized AutoDoc Integration; Security & Compliance Plan.
- Outputs: Bucket policies, env templates, validation tests.
- Acceptance: Buckets provisioned; safe envs verified in pods; per-tenant isolation tested.
- Dependencies: 8.4.

---

## 9. CAEF Orchestration (Gates)

[ ] 9.1 Implement Planning Gate enforcement
- Description: Prevent code/test/validation orchestration until Story approved.
- Context: Plan → Process Outline; Acceptance Criteria.
- Outputs: Gate check middleware; audit logs.
- Acceptance: Gate blocks until approval; audit shows action.
- Dependencies: 5.2, 6.2.

[ ] 9.2 Start CAEF jobs post-approval
- Description: Accept gate token to start multi-agent execution; stream status.
- Context: Plan → API Contracts.
- Outputs: `/caef/jobs/start` integration.
- Acceptance: Sample run executes; events logged.
- Dependencies: 7.1.

---

## 10. Web/Mobile/Wearable UX

[ ] 10.1 PRD authoring wizard
- Description: Cerebral Web form with validation, save drafts, submit to BMAD endpoint.
- Context: Plan → UX.
- Outputs: UI + API wiring.
- Acceptance: Draft/save/submit flows work.
- Dependencies: 5.2, 6.2.

[ ] 10.2 Architecture builder
- Description: Create/approve architecture; versioning and diffs.
- Context: Plan → UX.
- Outputs: UI + storage.
- Acceptance: Approvals logged; artifacts versioned.
- Dependencies: 8.1.

[ ] 10.3 Story generator/reviewer
- Description: Generate story, review changes, approve Planning Gate.
- Context: Plan → Process Outline.
- Outputs: UI, approvals, gate call.
- Acceptance: Gate flips; CAEF eligible.
- Dependencies: 8.2, 7.1.

[ ] 10.4 Mobile/wearable endpoints
- Description: Approve gates, monitor runs, notifications; limited authoring.
- Context: Plan → UX.
- Outputs: REST endpoints; mobile views.
- Acceptance: Actions complete; telemetry OK.
- Dependencies: 8.3.

---

## 11. Security & Compliance

[ ] 11.1 Vault-managed secrets for providers (cerebral-deployment)
- Description: Wire Vault secret injection; rotations; no plaintext envs.
- Context: Plan → Security & Compliance.
- Outputs: Secret templates; rotations.
- Acceptance: Pods mount secrets; rotation test passes.
- Dependencies: 5.1.

[ ] 11.2 Egress/DLP policies and allowlists (cerebral-deployment)
- Description: Restrict LLM endpoints; DLP proxy; per-tenant egress policies.
- Context: Plan → Security & Compliance.
- Outputs: NetworkPolicy/proxy config.
- Acceptance: Disallowed egress blocked; logs show attempt.
- Dependencies: 5.3.

[ ] 11.3 Audit logging and SIEM export
- Description: Append-only logs for all actions; SIEM integration; retention.
- Context: Plan → Security & Compliance.
- Outputs: Log schema; exporter.
- Acceptance: Sample audits visible in SIEM.
- Dependencies: 5.2, 7.2.

---

## 12. Scalability & Observability

[ ] 12.1 Queue + worker pools for planning jobs (cerebral-deployment)
- Description: Introduce queue and worker deployments with idempotency and retries.
- Context: Plan → Scalability.
- Outputs: Worker charts; retry policy.
- Acceptance: Load test at target TPS; no backlog growth.
- Dependencies: 5.2.

[ ] 12.1.1 RAG/KG indexer worker pool (cerebral-deployment)
- Description: Dedicated worker Deployment for embeddings+chunking; concurrency controls; dead-letter queue; idempotent job keys by commit/file hash.
- Context: Plan → Centralized AutoDoc Integration; Scalability Plan.
- Outputs: Deployment/Service YAMLs; queue configs; runbooks.
- Acceptance: Sustained load at target QPS; zero duplicate jobs; DLQ handling verified.
- Dependencies: 8.4, 8.1.

[ ] 12.1.2 GPU-enabled indexer images and scheduling (cerebral-deployment)
- Description: Build CUDA images for PyTorch/SentenceTransformers; add GPU requests/limits; install NVIDIA Device Plugin; configure nodeSelectors/taints and fallbacks.
- Context: Plan → GPU Acceleration Strategy; Installer Integration.
- Outputs: Dockerfiles, K8s manifests, device plugin install, HPA tuned for GPU.
- Acceptance: Jobs run on GPU nodes; throughput/latency improvement recorded; CPU fallback tested.
- Dependencies: 12.1.1.

[ ] 12.2 HPA and SLO dashboards (cerebral-deployment)
- Description: HPA for APIs/workers; dashboards for p95 latency, queue depth, token/cost usage.
- Context: Plan → Observability; Scalability.
- Outputs: Grafana/Prometheus configs.
- Acceptance: SLOs displayed; alerts configured.
- Dependencies: 12.1.

---

## 13. Installer Integration (1‑Touch)

[ ] 13.1 Add BMAD to installer (cerebral-deployment)
- Description: Extend 1‑touch scripts to deploy BMAD service, workers, secrets, routes.
- Context: Plan → Installer Integration.
- Outputs: Installer scripts/templates.
- Acceptance: Fresh install brings BMAD up healthy.
- Dependencies: 5.1, 9.1.

[ ] 13.2 Canary/rollback strategy (cerebral-deployment)
- Description: Blue/green or canary rollout; reversible migrations; backups.
- Context: Plan → Rollback Plan.
- Outputs: Release runbook.
- Acceptance: Simulated rollback succeeds.
- Dependencies: 11.1.

---

## 14. Local Development & IDE Integration

[ ] 14.1 `cflow-local bmad` CLI (HTTP client)
- Description: Implement HTTP client for BMAD API facade; login, provider set, prd/arch/story upsert, sync.
- Context: Plan → Local Runner & IDE; API Contracts.
- Outputs: CLI commands + docs; HTTP client library.
- Acceptance: CLI e2e against cerebral cluster BMAD API.
- Dependencies: 5.2, 6.2.

[ ] 14.2 WebMCP tool integration
- Description: Add BMAD tools to WebMCP server; ensure proper HTTP routing to BMAD API facade.
- Context: Plan → MCP Integration; Tool Registry.
- Outputs: WebMCP server updates; tool routing.
- Acceptance: BMAD tools accessible via WebMCP; proper HTTP routing.
- Dependencies: 5.3, 12.1.

[ ] 14.3 Sync engine (bidirectional)
- Description: Cursor-based sync for artifacts and metadata; conflict resolution; audit.
- Context: Plan → API Contracts; Governance.
- Outputs: Sync service + tests.
- Acceptance: Edits converge; conflicts logged.
- Dependencies: 12.1.

---

## 15. Migration & Cleanup

[ ] 15.1 Inventory and tag legacy systems
- Description: Enumerate abandoned TaskMaster/legacy UIs/mocks/duplicated validators; tag `pre-bmad-core`.
- Context: Plan → Migration & Cleanup.
- RAG/KG: Graph search for known paths; report.
- Outputs: Inventory report.
- Acceptance: Reviewed by arch; signed.
- Dependencies: 2.1.

[ ] 15.2 Archive and remove
- Description: Move historical docs to `docs/_archive/`; delete forbidden code; replace entrypoints.
- Context: Plan → Migration & Cleanup.
- Outputs: PRs with deletions/moves; CI green.
- Acceptance: Build/tests pass; no import breaks.
- Dependencies: 13.1.

[ ] 15.3 Post-clean validation
- Description: Lints/tests/security scans; policy checks for forbidden patterns.
- Context: Plan → Acceptance Criteria.
- Outputs: Reports; CI gates.
- Acceptance: All green.
- Dependencies: 13.2.

---

## 16. Pilot & Rollout

[ ] 16.1 Internal pilot project
- Description: Run full PRD→Architecture→Story→CAEF flow with a real initiative; measure quality/cycle time.
- Context: Plan → Timeline; Acceptance Criteria.
- Outputs: Pilot report.
- Acceptance: Metrics improved vs. baseline.
- Dependencies: 8.3, 7.2, 6.2.

[ ] 16.2 Production canary
- Description: Enable BMAD for a subset of tenants/projects; monitor SLOs and costs.
- Context: Plan → Rollout Plan.
- Outputs: Canary config; dashboards.
- Acceptance: No regressions; stakeholder approval.
- Dependencies: 14.1, 11.2.

---

## KnowledgeRAG & KG Usage Index
- PRD/Architecture/Story authoring: retrieve plan excerpts and BMAD agent roles from RAG (GitIngest doc) to enrich prompts.  
- Mapping tasks (schema/ERD): link plan sections to KG nodes (Artifacts↔Tables↔Indexes).  
- Cleanup inventory: KG search for deprecated modules; generate deprecation PRs.  
- Observability and quotas: RAG for provider policy templates; KG for service dependencies.
