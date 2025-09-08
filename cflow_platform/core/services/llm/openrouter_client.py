from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import re

import httpx


_OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
_ALLOWED_HOST = "openrouter.ai"


def _host_allowed(url: str) -> bool:
    m = re.match(r"^https?://([^/]+)(/|$)", url)
    if not m:
        return False
    host = m.group(1).lower()
    return host == _ALLOWED_HOST or host.endswith("." + _ALLOWED_HOST)


def _headers() -> Dict[str, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    ref = os.environ.get("OPENROUTER_APP_URL", "https://example.com").strip() or "https://example.com"
    title = os.environ.get("OPENROUTER_APP_NAME", "CFlow").strip() or "CFlow"
    return {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": ref,
        "X-Title": title,
        "Content-Type": "application/json",
    }


async def chat_completion(
    messages: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    seed: Optional[int] = None,
    timeout_sec: float = 15.0,
) -> Dict[str, Any]:
    """Call OpenRouter chat completions API.

    Enforces host allowlist and reasonable timeouts. Raises on transport errors.
    """
    url = _OPENROUTER_ENDPOINT
    if not _host_allowed(url):
        raise RuntimeError("Destination host not allowed by policy")

    payload: Dict[str, Any] = {
        "model": model or os.environ.get("CFLOW_LLM_MODEL", "deepseek/deepseek-coder-v2"),
        "messages": messages,
    }
    if temperature is None:
        try:
            temperature = float(os.environ.get("CFLOW_CODEGEN_TEMP", "0.15") or "0.15")
        except Exception:
            temperature = 0.15
    if top_p is None:
        try:
            top_p = float(os.environ.get("CFLOW_CODEGEN_TOP_P", "0.9") or "0.9")
        except Exception:
            top_p = 0.9
    if max_tokens is None:
        try:
            max_tokens = int(os.environ.get("CFLOW_CODEGEN_MAX_TOKENS", "2000") or "2000")
        except Exception:
            max_tokens = 2000

    payload["temperature"] = temperature
    payload["top_p"] = top_p
    payload["max_tokens"] = max_tokens
    if seed is None:
        try:
            seed = int(os.environ.get("CFLOW_CODEGEN_SEED", "0") or "0")
        except Exception:
            seed = 0
    payload["seed"] = seed

    headers = _headers()

    timeout = httpx.Timeout(timeout=timeout_sec, connect=min(5.0, timeout_sec))
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data


async def probe(model: Optional[str] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
    """Simple provider probe: asks model to reply with 'ok' and checks response.

    Returns a structured status with provider/model and the raw content.
    """
    sys_msg = {
        "role": "system",
        "content": "You are a concise assistant. Reply strictly with the assistant content only.",
    }
    user_msg = {"role": "user", "content": (prompt or "Reply with exactly: ok").strip()}

    data = await chat_completion([sys_msg, user_msg], model=model)
    content: str = ""
    try:
        content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    except Exception:
        content = ""
    ok = content.lower() == "ok"
    return {
        "status": "success" if ok else "error",
        "provider": "openrouter",
        "model": model or os.environ.get("CFLOW_LLM_MODEL", "deepseek/deepseek-coder-v2"),
        "content": content,
        "ok": ok,
        "raw": {k: v for k, v in data.items() if k in {"id", "model", "usage"}},
    }


