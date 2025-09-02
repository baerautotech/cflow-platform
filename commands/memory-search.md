---
name: Search project memory
command: |
  uv run python - << 'PY'
  import asyncio, json
  from cflow_platform.core.direct_client import get_direct_client_executor
  async def main():
      dc = get_direct_client_executor()
      res = await dc.execute("memory_search", {"query":"accelerator", "top_k": 5})
      print(json.dumps(res, indent=2))
  asyncio.run(main())
  PY
description: Search CerebralMemory for relevant context (fast RAG)
---