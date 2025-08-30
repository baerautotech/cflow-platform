# CFlow Platform

Core MCP platform library providing:

- Core handlers (system, task, doc, plan, lint, enhanced, test)
- Direct client dispatcher and tool registry
- TaskManagerClient (ChromaDB-backed via lightweight HTTP proxy)
- Web MCP server bindings
- Hook installer and env verifier wrappers

Usage:

```bash
pip install cflow-platform
```

Programmatic:

```python
from cflow_platform.core.direct_client import execute_mcp_tool
# result = await execute_mcp_tool("task_list")
```

Dev notes:
- TaskManagerClient discovers a local proxy at http://localhost:8000/health
- See scripts/run-chromadb-proxy.sh in the monorepo for a convenience runner
