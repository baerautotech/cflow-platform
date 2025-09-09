from __future__ import annotations

import json
from pathlib import Path

from cflow_platform.hooks import pre_commit_runner as runner


def test_gate_registry_blocks_commit(tmp_path: Path, monkeypatch):
    repo_root = tmp_path
    gates_dir = repo_root / ".cerebraflow" / "validation"
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "gates.json").write_text(json.dumps({"gates": {"GateP": True, "GateRDB": False}}))

    # Patch runner.get_repo_root to point at temp repo
    monkeypatch.setattr(runner, "get_repo_root", lambda: repo_root)

    # No staged files
    monkeypatch.setattr(runner, "get_staged_files", lambda _flags: [])

    rc = runner.main()
    assert rc == 5


