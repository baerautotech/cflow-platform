from __future__ import annotations

import os
from cflow_platform.core.docs_context7 import (
    extract_symbols_from_failure_report,
    build_failure_report_from_test_result,
    fetch_context7_docs_for_symbols,
)


def test_extract_symbols_from_synthetic_failure_report() -> None:
    report = {
        "failures": [
            {
                "error_type": "ModuleNotFoundError",
                "message": "ModuleNotFoundError: No module named 'fastapi'",
                "top_trace": [
                    "E   ModuleNotFoundError: No module named 'fastapi'",
                ],
            },
            {
                "error_type": "AttributeError",
                "message": "AttributeError: module 'numpy' has no attribute 'ndarrai'",
                "top_trace": [
                    "E   AttributeError: module 'numpy' has no attribute 'ndarrai'",
                ],
            },
        ]
    }
    symbols = extract_symbols_from_failure_report(report)
    assert "fastapi" in symbols
    assert "numpy.ndarrai" in symbols


def test_build_failure_report_from_structured_test_result() -> None:
    structured = {
        "status": "failure",
        "summary": {"exit_code": 1},
        "tests": [
            {
                "nodeid": "tests/test_example.py::test_fails",
                "outcome": "failed",
                "longrepr": "ModuleNotFoundError: No module named 'requests'",
            }
        ],
    }
    report = build_failure_report_from_test_result(structured)
    symbols = extract_symbols_from_failure_report(report)
    assert "requests" in symbols


def test_fetch_context7_docs_fake_mode(monkeypatch) -> None:  # type: ignore[no-redef]
    monkeypatch.setenv("CFLOW_CONTEXT7_FAKE", "1")
    data = fetch_context7_docs_for_symbols(["requests.get"], per_symbol_limit=1)
    assert data.get("notes") and isinstance(data.get("notes"), list)
    assert data.get("sources") and isinstance(data.get("sources"), list)

import asyncio


def test_unified_enterprise_rag_build_index_payload_smoke():
    from cflow_platform.core.services.unified_enterprise_rag import UnifiedEnterpriseRAG

    rag = UnifiedEnterpriseRAG()

    async def _run():
        corpus = [
            {"id": "1", "content": "alpha beta"},
            {"id": "2", "content": "gamma delta"},
        ]
        docs, vecs, metas = await rag.build_index_payload(corpus)
        assert isinstance(docs, list) and len(docs) == 2
        assert isinstance(vecs, list) and len(vecs) == 2
        assert isinstance(vecs[0], list) and len(vecs[0]) > 0
        assert isinstance(metas, list) and len(metas) == 2

    asyncio.run(_run())


