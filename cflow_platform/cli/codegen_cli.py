from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from cflow_platform.core.public_api import get_direct_client_executor


def cli() -> int:
    parser = argparse.ArgumentParser(description="Run codegen.generate_edits and write edits.json")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--context", action="append", default=[], help="Context file to include (repeatable)")
    parser.add_argument("--tests", action="append", default=[], help="Test file paths (repeatable)")
    parser.add_argument("--max-edits", type=int, default=10)
    args = parser.parse_args()

    constraints = {
        "minimal_edits": True,
        "strict_single_match": True,
        "atomic": True,
        "allowlist": [Path.cwd().resolve().as_posix()],
        "max_edits": args.max_edits,
    }

    exec_fn = get_direct_client_executor()
    result = asyncio.get_event_loop().run_until_complete(
        exec_fn(
            "codegen.generate_edits",
            task=args.task,
            context_files=args.context,
            tests=args.tests,
            constraints=constraints,
        )
    )
    print(json.dumps(result))
    return 0 if str(result.get("status")) == "success" else 2

