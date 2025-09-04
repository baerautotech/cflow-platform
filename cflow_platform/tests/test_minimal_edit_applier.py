from __future__ import annotations

from pathlib import Path

from cflow_platform.core.minimal_edit_applier import (
    EditPlan,
    ApplyOptions,
    apply_minimal_edits,
    rollback,
)


def test_dry_run_and_diff(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    before = """def greet():\n    return "hello world"\n"""
    target.write_text(before)
    plan = [
        EditPlan(
            file=str(target),
            original_snippet='"hello world"',
            replacement_snippet='"hello there"',
        )
    ]
    opts = ApplyOptions(dry_run=True, allowlist=[str(tmp_path)])
    result = apply_minimal_edits(plan, opts)
    assert result["status"] == "success"
    assert result["results"][0]["status"] == "dry-run"
    diff = result["results"][0]["diff"]
    assert "-    return \"hello world\"" in diff
    assert "+    return \"hello there\"" in diff
    # Ensure file unchanged
    assert target.read_text() == before


def test_allowlist_blocks_edits(tmp_path: Path) -> None:
    target = tmp_path / "blocked.py"
    target.write_text("x = 1\n")
    plan = [EditPlan(file=str(target), original_snippet="x = 1\n", replacement_snippet="x = 2\n")]
    opts = ApplyOptions(dry_run=False, allowlist=[str(tmp_path / "other_dir")])
    result = apply_minimal_edits(plan, opts)
    assert result["results"][0]["status"] == "skipped"
    assert target.read_text() == "x = 1\n"


def test_conflict_detection_multiple_matches(tmp_path: Path) -> None:
    target = tmp_path / "conflict.py"
    target.write_text("import x\nimport x\n")
    plan = [EditPlan(file=str(target), original_snippet="import x", replacement_snippet="import y")]
    opts = ApplyOptions(dry_run=False, allowlist=[str(tmp_path)], strict_single_match=True)
    result = apply_minimal_edits(plan, opts)
    assert result["status"] == "error"
    assert result["results"][0]["status"] == "conflict"
    # No change applied
    assert target.read_text() == "import x\nimport x\n"


def test_atomic_batch_aborts_on_conflict_without_writes(tmp_path: Path) -> None:
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("v = 1\n")
    b.write_text("line\nline\n")
    plans = [
        EditPlan(file=str(a), original_snippet="v = 1\n", replacement_snippet="v = 2\n"),
        EditPlan(file=str(b), original_snippet="line\n", replacement_snippet="row\n"),
    ]
    opts = ApplyOptions(dry_run=False, allowlist=[str(tmp_path)], atomic=True, strict_single_match=True)
    result = apply_minimal_edits(plans, opts)
    assert result["status"] == "error"
    # Neither file should be changed because conflict is detected before writes
    assert a.read_text() == "v = 1\n"
    assert b.read_text() == "line\nline\n"


def test_rollback_restores_from_backups(tmp_path: Path) -> None:
    # Create a fake backup and target
    target = tmp_path / "t.py"
    target.write_text("bad\n")
    backup = tmp_path / "t.py.bak"
    backup.write_text("good\n")
    rb = rollback([str(backup)])
    assert rb["status"] == "success"
    assert target.read_text() == "good\n"

