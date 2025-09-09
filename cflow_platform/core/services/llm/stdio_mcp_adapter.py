from __future__ import annotations

from typing import Any, Dict, Optional
import os
import shlex
import subprocess
import tempfile


async def probe(model: Optional[str] = None, prompt: Optional[str] = None, timeout_sec: float = 8.0) -> Dict[str, Any]:
    """Probe a local stdio MCP LLM adapter.

    Requires CFLOW_STDIO_MCP_CMD to be set to a runnable command. If the command
    contains the token {prompt_file}, the prompt will be written to a temp file
    and the placeholder replaced with the file path. Otherwise, the command will
    be executed as-is and the prompt ignored.
    """
    cmd_tpl = os.getenv("CFLOW_STDIO_MCP_CMD", "").strip()
    if not cmd_tpl:
        return {"status": "error", "provider": "stdio_mcp", "error": "CFLOW_STDIO_MCP_CMD not set"}

    use_file = "{prompt_file}" in cmd_tpl
    tf: Optional[tempfile.NamedTemporaryFile] = None
    try:
        if use_file:
            tf = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
            tf.write((prompt or "Reply with exactly: ok"))
            tf.flush()
            cmd_str = cmd_tpl.replace("{prompt_file}", tf.name)
        else:
            cmd_str = cmd_tpl
        cmd = shlex.split(cmd_str)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if proc.returncode != 0:
            return {"status": "error", "provider": "stdio_mcp", "error": proc.stderr.strip() or "nonzero exit"}
        content = (proc.stdout or "").strip()
        ok = content.lower() == "ok"
        return {
            "status": "success" if ok else "error",
            "provider": "stdio_mcp",
            "model": model or "stdio-mcp",
            "content": content,
            "ok": ok,
        }
    except Exception as e:
        return {"status": "error", "provider": "stdio_mcp", "error": str(e)}
    finally:
        if tf is not None:
            try:
                os.unlink(tf.name)
            except Exception:
                pass


