---
name: Add memory note
command: |
  uv run python - << 'PY'
  import asyncio
  import json
  from cflow_platform.core.direct_client import get_direct_client_executor
  async def main():
      dc = get_direct_client_executor()
      res = await dc.execute("memory_add", {"type":"rule","content":"Example rule"})
      print(json.dumps(res, indent=2))
  asyncio.run(main())
  PY
description: Add a context note into CerebralMemory
---