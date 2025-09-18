## High‑Level Architecture

### **BMAD Integration Architecture**
- **BMAD Core**: Node v20 headless services vendored into `vendor/bmad/` and exposed via HTTP API facade on cerebral cluster
- **Project Type Detection**: Automatic greenfield vs brownfield detection with workflow routing
- **Brownfield Support**: Comprehensive existing system analysis, documentation generation, and integration strategy planning
- **Greenfield Support**: Standard BMAD workflow for new project development
- **Template Management**: Dynamic template selection based on project type (greenfield vs brownfield templates)
- **Workflow Router**: Routes projects to appropriate greenfield or brownfield workflows

### **Cerebral Platform Integration**
- **CAEF Orchestrator**: Python-based orchestrator for multi-agent code/test/validation after planning gates
- **KnowledgeRAG**: Supabase + pgvector for document indexing and RAG search
- **WebMCP Server**: Runs on cerebral cluster, imports tools from cflow-platform
- **API Gateway**: JWT-based authentication with tenant isolation
- **Storage**: Postgres (Supabase) for documents and tasks, MinIO S3 for artifacts

### **Client Integration**
- **Web/Mobile/Wearable UIs**: React Native + React Native Web for cross-platform development
- **IDE Integration**: Automatic project type detection and context-aware suggestions
- **CLI Tools**: Project type specification and workflow management

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
- Local fallback: OpenRouter (strict probe) then Ollama (local) via unified selector.
- Provider probe: strict "ok" check with prompt retry.
- Cloud providers: not required. AWS-specific MCPs are not part of the default stack in this environment.

