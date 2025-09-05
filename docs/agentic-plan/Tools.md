## Tool Definitions

- testing.run_pytest: Executes pytest with size caps via `uv`, returns structured JSON (status, summary, optional raw logs)

- code_reasoning.plan (planned): Produces a bounded, SRP plan with steps, file scopes, and explicit success checks

- sandbox.run_python: Sandboxed Python execution with CPU/memory/time limits, filesystem allowlist, no network

- memory_add / memory_search (planned integration): Read/Write CerebralMemory; retrieval should prefer CerebralMemory before external docs

- run_python (MCP server): General Python execution via a sandboxed MCP server (e.g., `@pydantic/mcp-run-python`) for quick, isolated evaluations

- internet_search (MCP server): Real-time search (e.g., `duckduckgo-mcp-server`) to fetch up-to-date information for libraries and APIs

- context7.docs (MCP server): Up-to-date library documentation retrieval (Context7) for symbol/API references; returns excerpts with sources

- awslabs.core (optional MCP pack): AWS capabilities for cloud-native workflows (off by default)

- aws_docs (optional MCP pack): AWS documentation MCP server for authoritative AWS references (off by default)

- desktop_commander (optional MCP pack): Local notifications (off by default). CLI: `cflow-desktop-notify` and MCP tool `desktop.notify`.

References:
- Building your own CLI Coding Agent with Pydantic-AI — Martin Fowler site: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

### Optional: AWS MCP Profile (Off by default)

- Description: For cloud-native teams that need AWS docs/CLI MCPs, an optional profile and MCP config are provided but not enabled by default.
- Activation steps:
  1. Ensure credentials are present via `AWS_PROFILE` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (and `AWS_REGION`).
  2. Write the optional profile and MCP rules:
     - `uv run -m cflow_platform.cli.provider_aws write-profile`
     - `uv run -m cflow_platform.cli.provider_aws write-mcp`
  3. Merge AWS MCP servers into `.cursor/mcp.json` (idempotent):
     - `uv run -m cflow_platform.cli.provider_aws activate`
  4. Run the agent with the profile explicitly:
     - `uv run -m cflow_platform.core.agent_loop --profile aws`

- Safeguards:
  - If credentials are missing, activation cleanly fails without modifying existing config.
  - AWS MCPs are not started unless explicitly merged into `.cursor/mcp.json`.
  - Default project behavior remains provider-agnostic (Cerebral Server primary; no AWS dependency).
