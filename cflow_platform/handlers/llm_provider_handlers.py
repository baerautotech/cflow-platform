from __future__ import annotations

from typing import Any, Dict


class LLMProviderHandlers:
    """Handlers for LLM provider operations (e.g., provider probe/gate P)."""

    async def handle_probe(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from cflow_platform.core.services.llm.provider_selector import probe_provider  # type: ignore
            model = (arguments.get("model") or None) if isinstance(arguments, dict) else None
            prompt = (arguments.get("prompt") or None) if isinstance(arguments, dict) else None
            return await probe_provider(model=model, prompt=prompt)
        except Exception as e:
            return {"status": "error", "error": str(e)}

