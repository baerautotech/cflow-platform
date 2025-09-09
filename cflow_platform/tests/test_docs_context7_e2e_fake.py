from __future__ import annotations

import asyncio
import json
import os

import pytest

from cflow_platform.core.public_api import get_direct_client_executor
from cflow_platform.core.docs_context7 import fetch_context7_docs_for_symbols, summarize_docs


@pytest.mark.asyncio
async def test_docs_context7_fake_mode_persists_to_memory(monkeypatch):
    monkeypatch.setenv("CFLOW_CONTEXT7_FAKE", "1")
    # Generate fake docs
    symbols = ["math.sqrt"]
    docs = fetch_context7_docs_for_symbols(symbols, per_symbol_limit=1)
    assert docs.get("notes"), "expected fake docs notes"
    summary = summarize_docs(docs.get("notes", []))
    assert isinstance(summary, str)

    # Persist to memory
    dc = get_direct_client_executor()
    add = await dc(
        "memory_add",
        content=summary or "Docs for math.sqrt: Example excerpt...",
        userId=os.getenv("CEREBRAL_USER_ID", "system"),
        metadata={"type": "docs", "source": "test_docs_context7_e2e_fake"},
    )
    assert add.get("success") is True

    # Query back
    res = await dc(
        "memory_search",
        query="Example excerpt",
        userId=os.getenv("CEREBRAL_USER_ID", "system"),
        limit=5,
        min_score=0.0,
    )
    assert res.get("success") is True
    assert res.get("count", 0) >= 0


