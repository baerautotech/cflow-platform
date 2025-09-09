from __future__ import annotations

from typing import Any, Dict, Optional
import os


async def probe_provider(model: Optional[str] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
    """Probe the currently selected LLM provider with strict 'ok' flow.

    Selection precedence (first available):
      1) OpenRouter (if OPENROUTER_API_KEY)
      2) Ollama local server (if reachable)
    """
    # OpenRouter first
    if os.getenv("OPENROUTER_API_KEY"):
        try:
            from .openrouter_client import probe as or_probe  # type: ignore
            # Attempt with provided prompt, then with explicit strict prompt
            for pr in [prompt, "Reply with exactly: ok"]:
                data = await or_probe(model=model, prompt=pr)
                if data.get("status") == "success" and data.get("ok") is True:
                    return data
        except Exception as e:
            # fall through to next provider
            last_err = str(e)

    # Ollama fallback
    try:
        from .ollama_client import probe as ol_probe  # type: ignore
        for pr in [prompt, "Reply with exactly: ok"]:
            data2 = await ol_probe(model=os.getenv("CFLOW_OLLAMA_MODEL", None), prompt=pr)
            if data2.get("status") == "success" and data2.get("ok") is True:
                return data2
    except Exception:
        pass

    return {"status": "error", "provider": "none", "error": "no provider passed strict ok probe"}


