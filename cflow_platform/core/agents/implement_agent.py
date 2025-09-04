from __future__ import annotations

from typing import Any, Dict
import json
import os
from pathlib import Path

from cflow_platform.core.agent_loop import apply_edits_if_present


class ImplementAgent:
    def __init__(self) -> None:
        pass

    def run(self, edits_file: str | None = None, apply: bool | None = None) -> Dict[str, Any]:
        if edits_file:
            os.environ["CFLOW_EDIT_PLANS_FILE"] = edits_file
        if apply is not None:
            os.environ["CFLOW_APPLY_EDITS"] = "1" if apply else "0"
        result = apply_edits_if_present()
        return result


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run ImplementAgent to apply minimal edits if present")
    parser.add_argument("--edits", default=None, help="Path to edits JSON file (default .cerebraflow/edits.json)")
    parser.add_argument("--apply", action="store_true", help="Actually apply edits (otherwise dry-run)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    agent = ImplementAgent()
    result = agent.run(edits_file=args.edits, apply=args.apply)
    if args.json:
        print(json.dumps(result))
    else:
        print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(cli())


