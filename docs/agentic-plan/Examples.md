## Examples: Using CFlow Platform

### SDK

```python
import asyncio
from cflow_platform.sdk import CFlowClient

async def main():
    client = CFlowClient()
    # Execute a simple system test tool
    result = await client.execute_tool("sys_test")
    print("sys_test:", result)

    # Run pytest via the structured runner tool (see Tools.md)
    result = await client.execute_tool(
        "testing.run_pytest",
        {
            "path": "cflow_platform/tests",
            "verbose": True,
            "in_process": False
        },
    )
    print("pytest result:", result)

asyncio.run(main())
```

### Core API (direct client and stdio server)

```python
from cflow_platform.core.public_api import (
    get_stdio_server,
    get_direct_client_executor,
    safe_get_version_info,
)

server = get_stdio_server()
executor = get_direct_client_executor()
print("version:", safe_get_version_info())
```

### CLI

```bash
# Verify environment for migrations + ragkg + llm
cflow-verify-env --mode migrations --mode ragkg --mode llm --scope both

# Install enterprise git hooks (delegates to scripts/install-enhanced-git-hooks.sh)
cflow-install-hooks

# Structured test runner
cflow-test-runner --verbose --no-in-process cflow_platform/tests

# Agent loop (quick profile, single iteration)
cflow-agent-loop --profile quick --max-iter 1 --json
```

### Knowledge Graph (KG) quick queries

```bash
# Search plan summaries or docs excerpts with low similarity threshold
uv run python -m cflow_platform.cli.kg_query "PLAN SUMMARY" --limit 5 --min-score 0.0
uv run python -m cflow_platform.cli.kg_query "type:procedure" --limit 5 --min-score 0.0
uv run python -m cflow_platform.cli.kg_query "Example excerpt" --limit 5 --min-score 0.0
```

```python
# Programmatic KG query
import asyncio, json
from cflow_platform.core.public_api import get_direct_client_executor

async def main():
    dc = get_direct_client_executor()
    res = await dc("memory_search", query="PLAN SUMMARY", userId="system", limit=5, min_score=0.0)
    print(json.dumps(res, indent=2))

asyncio.run(main())
```

### stdio-MCP LLM adapter (optional, offline)

- Prepare a local command that prints the content of a prompt file (or integrates with your local LLM). Example shell script:
  ```bash
  #!/bin/sh
  # naive example: echo the prompt file content
  cat "$1"
  ```
- Configure environment:
  - `CFLOW_STDIO_MCP_CMD="/path/to/your/script {prompt_file}"`
  - (Optional) `CFLOW_STDIO_MCP_MODEL=offline-stdio`
- Probe (strict):
  ```bash
  uv run python - << 'PY'
  import asyncio, json, os
  from cflow_platform.core.public_api import get_direct_client_executor
  os.environ["CFLOW_STDIO_MCP_CMD"]="/path/to/your/script {prompt_file}"
  async def main():
    dc = get_direct_client_executor()
    res = await dc("llm_provider.probe", prompt="Reply with exactly: ok")
    print(json.dumps(res, indent=2))
  asyncio.run(main())
  PY
  ```

### Context7 (real mode via WebMCP)

- Ensure `.env` contains:
  - `CONTEXT7_WEBMCP_URL` (e.g., `https://your-webmcp-host/mcp/tools/call`)
  - Either `CONTEXT7_BEARER_TOKEN` or a custom header pair:
    - `CONTEXT7_HEADER_NAME`, `CONTEXT7_HEADER_VALUE`
- Example programmatic call:
  ```python
  import os
  from cflow_platform.core.docs_context7 import fetch_context7_docs_for_symbols, summarize_docs

  os.environ["CONTEXT7_WEBMCP_URL"] = "https://your-webmcp-host/mcp/tools/call"
  os.environ["CONTEXT7_BEARER_TOKEN"] = "<token>"

  docs = fetch_context7_docs_for_symbols(["pandas.DataFrame"], per_symbol_limit=2)
  print(summarize_docs(docs.get("notes", [])))
  print(docs.get("sources", []))
  ```

### Memory & Sync (Supabase/MinIO/ChromaDB/SQLite)

See `./MemoryAndSync.md` for full details. Minimal examples:

```bash
# Required env
export SUPABASE_URL=...           # or configure in .env
export SUPABASE_ANON_KEY=...

# Optional storage if using object sync
export MINIO_ENDPOINT=...
export MINIO_ACCESS_KEY=...
export MINIO_SECRET_KEY=...

# Start daemon
cflow-sync start --project-root /path/to/Cerebral

# Status and DB report
cflow-sync status --project-root /path/to/Cerebral

# Stop
cflow-sync stop --project-root /path/to/Cerebral
```

### Sandbox policy example

```python
from cflow_platform.core.public_api import get_direct_client_executor

executor = get_direct_client_executor()
result = executor.run_tool(
    "sandbox.run_python",
    {"code": "print('hello from sandbox')"}
)
print(result)
```

### Notes

- Follow `./CodeStyle.md` for code examples and formatting.
- For docs/search behavior and sources, see `./Tools.md` and `./LoggingAndObservability.md`.
- Validation gates for end-to-end flows are in `./ValidationGates.md`.


