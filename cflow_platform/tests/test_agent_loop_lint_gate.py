from __future__ import annotations

import os

# CAEF agent_loop removed - test disabled as it was testing removed functionality
# from cflow_platform.core.agent_loop import loop


def test_agent_loop_respects_pre_commit_gate_success(monkeypatch) -> None:
    # Test disabled - CAEF agent_loop removed, replaced with BMAD workflow engine
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "pass")
    # result = loop("quick", max_iterations=1)
    # assert result.get("status") == "success"
    pass  # Placeholder test


def test_agent_loop_respects_pre_commit_gate_failure(monkeypatch) -> None:
    # Test disabled - CAEF agent_loop removed, replaced with BMAD workflow engine
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "fail")
    # result = loop("quick", max_iterations=1)
    # assert result.get("status") == "error"
    pass  # Placeholder test

