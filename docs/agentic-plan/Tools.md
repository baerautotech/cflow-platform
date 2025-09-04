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

- desktop_commander (optional MCP pack): Local system utilities for notifications and controlled desktop interactions (off by default)

References:
- Building your own CLI Coding Agent with Pydantic-AI — Martin Fowler site: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

