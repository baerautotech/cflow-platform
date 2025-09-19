from __future__ import annotations

import os
# CAEF agent_loop removed - test disabled as it was testing removed functionality
# from cflow_platform.core.agent_loop import loop


def test_budget_stop_on_steps(monkeypatch):
    # Test disabled - CAEF agent_loop removed, replaced with BMAD workflow engine
    # Ensure tests are skipped to avoid running pytest inside pytest
    monkeypatch.setenv("CFLOW_SKIP_TESTS_IN_LOOP", "1")
    # Force a non-green iteration so budget check triggers post-iteration
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "fail")
    # res = loop(profile_name="quick", max_iterations=5, step_budget=1)
    # assert res.get("stop", {}).get("reason") == "budget_exhausted"
    # assert res.get("stop", {}).get("budget_kind") == "steps"
    pass  # Placeholder test


def test_lint_fail_blocks_success(monkeypatch):
    # Test disabled - CAEF agent_loop removed, replaced with BMAD workflow engine
    monkeypatch.setenv("CFLOW_SKIP_TESTS_IN_LOOP", "1")
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "fail")
    # res = loop(profile_name="quick", max_iterations=1)
    # hist = res.get("history") or []
    # assert hist, "history should not be empty"
    # verify = hist[0].get("verify", {})
    # assert verify.get("lint", {}).get("status") == "error"
    # assert res.get("status") == "error"
    pass  # Placeholder test


