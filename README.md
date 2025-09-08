# CFlow Platform (Phase 1 Wrapper)

This package provides Phase 1 wrappers to allow early consumption of CFlow APIs before the full repo split.

- Public API: `cflow_platform.public_api` (proxies to monorepo `.cerebraflow/core/mcp/core/public_api.py`)
- SDK: `cflow_platform.sdk.CFlowClient` to execute MCP tools
- CLI:
  - `cflow-install-hooks` → installs enterprise git hooks (delegates to repo script when present)
  - `cflow-verify-env` → verifies required env keys per operation via the monorepo verifier
  - `cflow-test-runner` → runs pytest and returns structured JSON (supports uv)
  - `cflow-agent-loop` → unified CLI agent loop with planning/verify cycle
  - `cflow-codegen` → runs codegen.generate_edits to write `.cerebraflow/edits.json`
  - `cflow-provider-probe` → probes LLM provider connectivity (Gate P)
  - `cflow-provider-aws` → optional AWS provider/profile MCP tools (off by default)
  - `cflow-sync` → manage vendored unified realtime sync service (Supabase/MinIO/ChromaDB/SQLite)
  - `cflow-caef` → basic CAEF orchestrator wrapper

## SDK Example

```python
import asyncio
from cflow_platform.sdk import CFlowClient

async def main():
    client = CFlowClient()
    result = await client.execute_tool("sys_test")
    print(result)

asyncio.run(main())
```

## Core API (Phase 2)

```python
from cflow_platform.core.public_api import get_stdio_server, get_direct_client_executor, safe_get_version_info
```

## CLI Examples

```bash
# Verify environment for migrations + ragkg + llm
cflow-verify-env --mode migrations --mode ragkg --mode llm --scope both

# Install enterprise git hooks (delegates to scripts/install-enhanced-git-hooks.sh)
cflow-install-hooks

# Structured test runner
cflow-test-runner --verbose --no-in-process cflow_platform/tests

# Agent loop
cflow-agent-loop --profile quick --max-iter 1 --json

# Optional: insert codegen before implement (M3)
OPENROUTER_API_KEY=... CFLOW_ENABLE_CODEGEN=1 cflow-agent-loop --profile quick --max-iter 1 --json

# Unified realtime sync (Supabase/MinIO/ChromaDB/SQLite)
# Required env:
#   SUPABASE_URL, SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
#   MINIO_ENDPOINT (or S3_ENDPOINT), MINIO_ACCESS_KEY, MINIO_SECRET_KEY
# Optional env:
#   CEREBRAL_PROJECT_ROOT (defaults to current directory)
# Start daemon
cflow-sync start --project-root /path/to/Cerebral
# Check status + DB report
cflow-sync status --project-root /path/to/Cerebral
# Stop daemon
cflow-sync stop --project-root /path/to/Cerebral

# CAEF orchestrator (vendored)
cflow-caef status
```

Notes: In Phase 1, this wrapper delegates to the monorepo implementations. After the split, these entry points will target packaged CFlow modules directly.
