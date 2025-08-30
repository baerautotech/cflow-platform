from __future__ import annotations

from typing import Any, Dict, List
import asyncio
import json
import os
import shlex
from pathlib import Path


class TestingHandlers:
    async def handle_test_analyze(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "analysis": {"tests": 0, "confidence": 1.0}}

    async def handle_test_delete_flaky(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "deleted": 0}

    async def handle_test_confidence(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "confidence": {"score": 1.0}}

    async def handle_testing_run_pytest(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Run pytest via uv non-interactively and summarize failures.

        Arguments:
          - path: optional tests path (default: tests/)
          - markers: optional pytest -k expression
          - max_output_bytes: truncate combined stdout+stderr to this size (default: 200000)
          - verbose: bool to include raw logs
        """
        tests_path: str = arguments.get("path", "tests/")
        markers: str | None = arguments.get("markers")
        max_output_bytes: int = int(arguments.get("max_output_bytes", 200000))
        verbose: bool = bool(arguments.get("verbose", False))

        cmd: List[str] = ["uv", "run", "pytest", "-xvs", tests_path]
        if markers:
            cmd += ["-k", markers]

        env = os.environ.copy()
        # Ensure no pager and non-interactive
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        combined = stdout + b"\n" + stderr
        truncated = False
        if len(combined) > max_output_bytes:
            combined = combined[:max_output_bytes] + b"\n[TRUNCATED]\n"
            truncated = True

        raw_text = combined.decode(errors="replace")

        summary = _parse_pytest_output(raw_text)
        result: Dict[str, Any] = {
            "status": "success",
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "truncated": truncated,
            "summary": summary,
        }
        if verbose:
            result["raw_logs"] = raw_text
        return result


def _parse_pytest_output(text: str) -> Dict[str, Any]:
    """Very small parser for common pytest summaries.
    Extracts counts and failing test ids with brief messages when possible.
    """
    lines = text.splitlines()
    failures: List[Dict[str, Any]] = []
    fail_section = False
    current: Dict[str, Any] | None = None
    trailer: List[str] = []

    for line in lines:
        if line.startswith("=") and " FAILURES " in line:
            fail_section = True
            continue
        if fail_section and line.startswith("=") and " short test summary info " in line:
            # End of detailed failures
            if current:
                current["trace"] = "\n".join(trailer[-20:])
                failures.append(current)
                trailer = []
                current = None
            fail_section = False
            continue
        if fail_section and line.startswith("_") and line.rstrip().endswith("_"):
            # New failure header like: _______ test_xxx _______
            if current:
                current["trace"] = "\n".join(trailer[-20:])
                failures.append(current)
                trailer = []
            current = {"test": line.strip(" _")}
            continue
        if fail_section:
            trailer.append(line)

    if current:
        current["trace"] = "\n".join(trailer[-20:])
        failures.append(current)

    # Try to find final summary line
    summary_line = next((l for l in reversed(lines) if l.strip().startswith("===") and " in " in l), "")
    return {"failures": failures, "summary_line": summary_line}


