from __future__ import annotations

import json
import os
from pathlib import Path


CURSOR_DIRS = [
    Path(".cursor/rules"),
    Path("commands"),
    Path("docs"),
    Path(".cerebraflow/progress"),
]


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _seed_files(repo_root: Path) -> None:
    # AGENTS.md
    _write_if_missing(
        repo_root / "AGENTS.md",
        """# Agents

This workspace uses Cursor’s modular configuration.

- Root instructions live here (AGENTS.md)
- Structured rules live under .cursor/rules/
- Iteration/progress docs live as .mdc files under docs/
- Reusable actions live under commands/

All artifacts are mirrored into CerebralMemory for RAG retrieval.

Environment precedence:
- Load .env at repo root first
- Then load .cerebraflow/.env (overrides)
Set SUPABASE_URL, SUPABASE_ANON_KEY for pgvector search and storage.
""".strip(),
    )

    # Rule profile
    _write_if_missing(
        repo_root / ".cursor/rules/cflow.profile.json",
        json.dumps(
            {
                "name": "cflow-default",
                "description": "CFlow default instruction profile",
                "policies": {
                    "minimal_edits": True,
                    "fail_closed_lint": True,
                    "sandbox_python": True,
                },
            },
            indent=2,
        ),
    )

    # Seed command
    _write_if_missing(
        repo_root / "commands/cflow-fix-tests.md",
        """---
name: Fix tests with cflow
command: |
  uv run python - << 'PY'
  import asyncio, json
  from cflow_platform.core.direct_client import get_direct_client_executor
  async def main():
      dc = get_direct_client_executor()
      res = await dc.execute("memory_stats", {})
      print(json.dumps(res, indent=2))
  asyncio.run(main())
  PY
description: Run the autonomous loop to fix failing tests with minimal edits
---
""".strip(),
    )

    # Seed memory commands
    _write_if_missing(
        repo_root / "commands/memory-search.md",
        """---
name: Search project memory
command: |
  uv run python - << 'PY'
  import asyncio, json
  from cflow_platform.sdk import CFlowClient
  async def main():
      client = CFlowClient()
      result = await client.execute_tool("memory_search", query="<replace with query>")
      print(json.dumps(result, indent=2))
  asyncio.run(main())
  PY
description: Search CerebralMemory for relevant context (fast RAG)
---
""".strip(),
    )
    _write_if_missing(
        repo_root / "commands/memory-add.md",
        """---
name: Add memory note
command: |
  uv run python - << 'PY'
  import asyncio
  from cflow_platform.sdk import CFlowClient
  async def main():
      client = CFlowClient()
      await client.execute_tool(
          "memory_add",
          content="<replace with content>",
          metadata={"type": "context", "source": "cursor-command"}
      )
  asyncio.run(main())
  PY
description: Add a context note into CerebralMemory
---
""".strip(),
    )

    # Seed .mdc planning doc
    _write_if_missing(
        repo_root / "docs/cflow_planning.mdc",
        """# CFlow Planning

Use this file for AI-assisted planning. Iteration checkpoints will mirror here.
""".strip(),
    )


def cli() -> int:
    repo_root = Path.cwd()
    for d in CURSOR_DIRS:
        (repo_root / d).mkdir(parents=True, exist_ok=True)
    _seed_files(repo_root)
    print("Cursor workspace scaffolding created/verified.")
    print("- AGENTS.md, .cursor/rules/cflow.profile.json, commands/{cflow-fix-tests,memory-search,memory-add}.md, docs/cflow_planning.mdc")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


