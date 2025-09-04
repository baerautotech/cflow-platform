from __future__ import annotations

import os

from cflow_platform.core.agent_loop import loop


def test_agent_loop_respects_pre_commit_gate_success(monkeypatch) -> None:
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "pass")
    result = loop("quick", max_iterations=1)
    assert result.get("status") == "success"


def test_agent_loop_respects_pre_commit_gate_failure(monkeypatch) -> None:
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "fail")
    result = loop("quick", max_iterations=1)
    assert result.get("status") == "error"

