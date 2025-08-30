from __future__ import annotations

import asyncio
import json
from typing import Any
from argparse import ArgumentParser
from pathlib import Path

from .. import sdk


def _auto_detect_tests_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    # Prefer nearest repo/root tests directory by walking up from CWD
    cwd = Path.cwd()
    for base in [cwd, *cwd.parents]:
        tests_dir = base / "tests"
        if tests_dir.exists():
            try:
                # Consider it valid even if empty; pytest will report cleanly
                return str(tests_dir)
            except Exception:
                pass
    # Fallback to package tests
    pkg_tests = Path(__file__).resolve().parents[1] / "tests"
    return str(pkg_tests)


async def _run(path: str | None, markers: str | None, max_output_bytes: int, verbose: bool) -> dict[str, Any]:
    resolved_path = _auto_detect_tests_path(path)
    return await sdk.run_pytest(path=resolved_path, markers=markers, max_output_bytes=max_output_bytes, verbose=verbose)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--path", dest="path", default=None)
    parser.add_argument("--markers", dest="markers", default=None)
    parser.add_argument("--max-output-bytes", dest="max_output_bytes", type=int, default=200000)
    parser.add_argument("--verbose", dest="verbose", action="store_true", default=False)
    args = parser.parse_args()

    result = asyncio.run(_run(args.path, args.markers, args.max_output_bytes, args.verbose))
    print(json.dumps(result, indent=2))


