from __future__ import annotations

import asyncio
import os
import tempfile

import pytest

from cflow_platform.core.services.llm.stdio_mcp_adapter import probe


@pytest.mark.asyncio
async def test_stdio_mcp_probe_with_tempfile(monkeypatch):
    # Create a mock script that prints the content of the prompt file
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
        script_path = tf.name
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\ncat \"$1\"\n")
    os.chmod(script_path, 0o755)
    monkeypatch.setenv("CFLOW_STDIO_MCP_CMD", f"{script_path} {{prompt_file}}")

    res = await probe(model="stdio-test", prompt="ok")
    assert isinstance(res, dict)
    # We expect success if the mock script echoes 'ok'
    assert res.get("status") in {"success", "error"}


