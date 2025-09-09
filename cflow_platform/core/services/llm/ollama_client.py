from __future__ import annotations

from typing import Any, Dict, Optional
import os

import httpx


async def probe(model: Optional[str] = None, prompt: Optional[str] = None, timeout_sec: float = 8.0) -> Dict[str, Any]:
    """Probe a local Ollama server for strict 'ok' content.

    Requires an Ollama server at http://localhost:11434.
    """
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate").strip()
    model_name = model or os.getenv("CFLOW_OLLAMA_MODEL", "llama3.1:8b")
    payload: Dict[str, Any] = {
        "model": model_name,
        "prompt": (prompt or "Reply with exactly: ok"),
        "stream": False,
        "options": {"temperature": 0.0},
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=timeout_sec, connect=min(3.0, timeout_sec))) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = (data.get("response") or "").strip()
            ok = content.lower() == "ok"
            return {
                "status": "success" if ok else "error",
                "provider": "ollama",
                "model": model_name,
                "content": content,
                "ok": ok,
            }
    except Exception as e:
        return {"status": "error", "provider": "ollama", "error": str(e)}


