from __future__ import annotations

import asyncio
from pathlib import Path

from cflow_platform.core.direct_client import execute_mcp_tool


def test_sandbox_runs_basic_code():
    result = asyncio.run(
        execute_mcp_tool(
            "sandbox.run_python",
            code="print('hello')",
        )
    )
    assert result["status"] == "success"
    assert "hello" in (result.get("stdout") or "")


def test_sandbox_denies_network():
    # Attempt to create a socket should fail
    code = """
import socket
try:
    s = socket.socket()
    print('socket ok')
except Exception as e:
    print('denied:', type(e).__name__)
"""
    result = asyncio.run(execute_mcp_tool("sandbox.run_python", code=code))
    assert result["status"] == "success"
    stdout = result.get("stdout") or ""
    assert "denied:" in stdout


def test_sandbox_fs_allowlist_blocks_outside_access(tmp_path: Path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    code = f"""
from pathlib import Path
try:
    print(Path({repr(str(outside))}).read_text())
except Exception as e:
    print('fsdenied:', type(e).__name__)
"""
    result = asyncio.run(
        execute_mcp_tool(
            "sandbox.run_python",
            code=code,
            fs_allowlist=[],  # exclude tmp_path
        )
    )
    assert result["status"] in {"success", "error"}
    stdout = (result.get("stdout") or "") + (result.get("stderr") or "")
    assert "fsdenied:" in stdout or "File access denied" in stdout


def test_sandbox_time_limit_enforced():
    code = """
import time
time.sleep(10)
print('done')
"""
    result = asyncio.run(
        execute_mcp_tool(
            "sandbox.run_python",
            code=code,
            time_limit_sec=1,
        )
    )
    assert result["status"] == "error"
    assert result.get("error") in {"timeout", None}

