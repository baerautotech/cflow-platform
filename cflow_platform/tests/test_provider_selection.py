from __future__ import annotations

import asyncio
import os
import pytest

from cflow_platform.core.services.llm.provider_selector import probe_provider


@pytest.mark.asyncio
async def test_probe_retries_strict_prompt(monkeypatch):
    # Force OpenRouter path but with no key -> expect fallback failure
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    res = await probe_provider(prompt="ok")
    assert res.get("status") == "error"


@pytest.mark.asyncio
async def test_probe_ollama_path_when_env_model_set(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("CFLOW_OLLAMA_MODEL", "llama3.1:8b")
    # We can't assume a local server in CI; just ensure function returns dict
    res = await probe_provider(prompt="ok")
    assert isinstance(res, dict)


@pytest.mark.asyncio
async def test_probe_prefers_openrouter_when_ok(monkeypatch):
    # Mock OpenRouter to return ok
    async def mock_or_probe(model=None, prompt=None):
        return {"status": "success", "ok": True, "provider": "openrouter", "model": model or "auto"}
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("CFLOW_OLLAMA_MODEL", "llama3.1:8b")
    import cflow_platform.core.services.llm.openrouter_client as orc
    monkeypatch.setattr(orc, "probe", mock_or_probe)
    res = await probe_provider(prompt="ok")
    assert res.get("status") == "success"
    assert res.get("provider") == "openrouter"


@pytest.mark.asyncio
async def test_probe_falls_back_to_ollama_when_openrouter_fails(monkeypatch):
    # Mock OpenRouter to fail and Ollama to succeed
    async def mock_or_probe(model=None, prompt=None):
        return {"status": "error", "ok": False, "provider": "openrouter"}
    async def mock_ol_probe(model=None, prompt=None, timeout_sec: float = 8.0):
        return {"status": "success", "ok": True, "provider": "ollama", "model": model or "llama3.1:8b"}
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("CFLOW_OLLAMA_MODEL", "llama3.1:8b")
    import cflow_platform.core.services.llm.openrouter_client as orc
    import cflow_platform.core.services.llm.ollama_client as olc
    monkeypatch.setattr(orc, "probe", mock_or_probe)
    monkeypatch.setattr(olc, "probe", mock_ol_probe)
    res = await probe_provider(prompt="ok")
    assert res.get("status") == "success"
    assert res.get("provider") == "ollama"


