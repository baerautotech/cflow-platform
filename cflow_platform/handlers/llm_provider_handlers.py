from __future__ import annotations

from typing import Any, Dict, Optional
import os

from cflow_platform.core.services.llm.openrouter_client import probe as or_probe


class LLMProviderHandlers:
    """Handlers for LLM provider operations (e.g., provider probe/gate P)."""

    async def handle_probe(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure required env present
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            return {"status": "error", "message": "OPENROUTER_API_KEY missing"}

        model: Optional[str] = arguments.get("model") or os.environ.get("CFLOW_LLM_MODEL", "deepseek/deepseek-coder-v2")
        prompt: Optional[str] = arguments.get("prompt")

        try:
            res = await or_probe(model=model, prompt=prompt)
            return res
        except Exception as e:
            return {"status": "error", "message": str(e)}

