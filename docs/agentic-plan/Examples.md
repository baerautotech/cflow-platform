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


