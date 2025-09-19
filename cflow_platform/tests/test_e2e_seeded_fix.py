from __future__ import annotations

from pathlib import Path

from cflow_platform.core.test_runner import run_tests
from cflow_platform.core.minimal_edit_applier import EditPlan, ApplyOptions, apply_minimal_edits
# CAEF agent_loop removed - using direct linting handler
from cflow_platform.handlers.linting_handlers import LintingHandlers


def test_e2e_seeded_failing_test_turns_green(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path
    pkg_dir = project_root / "pkg"
    tests_dir = project_root / "tests"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Seed a buggy implementation
    mod_path = pkg_dir / "mod.py"
    mod_path.write_text(
        """
def add(a, b):
    # bug: subtraction instead of addition
    return a - b
""".lstrip()
    )

    # Seed a failing test
    test_path = tests_dir / "test_mod.py"
    test_path.write_text(
        """
from pkg.mod import add


def test_add():
    assert add(2, 3) == 5
""".lstrip()
    )

    # 1) Run tests (should fail)
    result_fail = run_tests(paths=["tests"], use_uv=False, in_process=False, cwd=str(project_root))
    assert result_fail["status"] == "failure"
    assert result_fail["summary"]["failed"] >= 1

    # 2) Prepare minimal edit plan and dry-run to present diff
    plan = [
        EditPlan(
            file=str(mod_path),
            original_snippet="return a - b",
            replacement_snippet="return a + b",
        )
    ]
    opts_dry = ApplyOptions(dry_run=True, allowlist=[str(project_root)])
    dry = apply_minimal_edits(plan, opts_dry)
    assert dry["status"] == "success"
    assert dry["results"][0]["status"] == "dry-run"
    diff_text = dry["results"][0]["diff"]
    assert "-    return a - b" in diff_text
    assert "+    return a + b" in diff_text

    # 3) Apply for real
    opts_apply = ApplyOptions(dry_run=False, allowlist=[str(project_root)], atomic=True, strict_single_match=True)
    applied = apply_minimal_edits(plan, opts_apply)
    assert applied["status"] == "success"
    assert any(r.get("status") == "applied" for r in applied["results"]) 

    # 4) Lint gate should pass (simulate pass)
    monkeypatch.setenv("CFLOW_PRE_COMMIT_MODE", "pass")
    # Use linting handler directly instead of removed agent_loop function
    lint_handler = LintingHandlers()
    import asyncio
    lint_result = asyncio.get_event_loop().run_until_complete(lint_handler.handle_lint_full({}))
    lint = {"status": "success" if lint_result.get("status") == "success" else "error"}
    assert lint.get("status") == "success"

    # 5) Re-run tests (should pass)
    result_pass = run_tests(paths=["tests"], use_uv=False, in_process=False, cwd=str(project_root))
    assert result_pass["status"] == "success"


