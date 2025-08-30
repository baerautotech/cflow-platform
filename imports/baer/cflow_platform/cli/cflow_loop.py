from __future__ import annotations

import asyncio
import json
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .. import sdk


@dataclass
class FailureItem:
    test: str
    trace: str


def _auto_detect_tests_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    cwd = Path.cwd()
    for base in [cwd, *cwd.parents]:
        tests_dir = base / "tests"
        if tests_dir.exists():
            return str(tests_dir)
    return str(cwd / "tests")


def _synthesize_plan(summary: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = summary.get("failures", []) if isinstance(summary, dict) else []
    steps: List[Dict[str, Any]] = []
    for f in failures[:5]:
        test_id = f.get("test", "unknown-test")
        steps.append({
            "action": "inspect_failure",
            "test": test_id,
            "verify": "Re-run pytest after minimal code change",
        })
    return {
        "hypotheses": [
            "Fix implementation first; do not modify tests unless spec-mismatch is confirmed",
            "Apply minimal diffs scoped to impacted module(s)",
        ],
        "steps": steps,
        "success": [
            "pytest exit_code == 0",
            "no new linter errors",
        ],
    }


async def _run_loop(path: str | None, markers: str | None, max_output_bytes: int, verbose: bool, profile: str | None) -> Dict[str, Any]:
    resolved_path = _auto_detect_tests_path(path)
    run = await sdk.run_pytest(path=resolved_path, markers=markers, max_output_bytes=max_output_bytes, verbose=verbose)
    plan = _synthesize_plan(run.get("summary", {}))
    return {
        "tool": "cflow_agent_loop",
        "input": {"path": resolved_path, "markers": markers, "profile": profile},
        "result": run,
        "plan": plan,
    }


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--path", dest="path", default=None)
    parser.add_argument("--markers", dest="markers", default=None)
    parser.add_argument("--max-output-bytes", dest="max_output_bytes", type=int, default=200000)
    parser.add_argument("--verbose", dest="verbose", action="store_true", default=False)
    parser.add_argument("--profile", dest="profile", default=None, help="Instruction profile to apply (e.g., strict)")
    args = parser.parse_args()

    payload = asyncio.run(_run_loop(args.path, args.markers, args.max_output_bytes, args.verbose, args.profile))
    # Ensure output is flushed so CLI prints under all shells
    print(json.dumps(payload, indent=2), flush=True)


