from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
import json
import os
import datetime as _dt
import re

from ..public_api import get_direct_client_executor


def _ts() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _ensure_dirs(repo_root: Path) -> None:
    (repo_root / ".cerebraflow/progress").mkdir(parents=True, exist_ok=True)
    (repo_root / ".cursor/rules").mkdir(parents=True, exist_ok=True)
    (repo_root / "commands").mkdir(parents=True, exist_ok=True)
    (repo_root / "docs").mkdir(parents=True, exist_ok=True)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _append_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("a", encoding="utf-8") as f:
            f.write("\n\n" + content)
    else:
        path.write_text(content, encoding="utf-8")


def checkpoint_iteration(
    *,
    iteration_index: int,
    plan: Dict[str, Any] | None,
    verify: Dict[str, Any] | None,
    run_id: Optional[str] = None,
    task_id: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write a Cursor-aligned iteration checkpoint and mirror to CerebralMemory.

    Artifacts written:
      - .cerebraflow/progress/iteration_<n>.mdc (primary checkpoint)
      - docs/cflow_planning.mdc (append-only log)
    Mirrored to memory as an episodic entry with metadata.
    """
    repo_root = Path.cwd()
    _ensure_dirs(repo_root)

    run_id = run_id or os.getenv("CFLOW_RUN_ID", "local-run")
    task_id = task_id or os.getenv("CFLOW_TASK_ID", "")

    # Render checkpoint content (Markdown + embedded JSON for machines)
    header = f"# Iteration {iteration_index} — {_ts()}\n"
    plan_block = f"## Plan\n\n```json\n{json.dumps(plan or {}, indent=2)}\n```" if plan is not None else "## Plan\n\n(none)"
    verify_block = f"## Verify\n\n```json\n{json.dumps(verify or {}, indent=2)}\n```" if verify is not None else "## Verify\n\n(none)"
    meta: Dict[str, Any] = {
        "run_id": run_id,
        "task_id": task_id,
        "iteration": iteration_index,
        **(extra_metadata or {}),
    }
    meta_block = f"## Meta\n\n```json\n{json.dumps(meta, indent=2)}\n```"
    content = "\n\n".join([header, plan_block, verify_block, meta_block])

    # Write iteration file
    iter_path = repo_root / ".cerebraflow/progress" / f"iteration_{iteration_index}.mdc"
    _write_file(iter_path, content)

    # Append to planning doc
    plan_doc = repo_root / "docs/cflow_planning.mdc"
    _append_file(plan_doc, content)

    # Mirror to CerebralMemory (best-effort; non-fatal on failure)
    try:
        exec_fn = get_direct_client_executor()
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            exec_fn(
                "memory_store_episode",
                runId=run_id,
                taskId=task_id,
                content=content,
                metadata={
                    "artifact_type": "checkpoint",
                    "cursor_kind": "mdc",
                    "iteration": iteration_index,
                    "artifact_path": str(iter_path),
                },
            )
        )
    except Exception:
        pass

    return {
        "status": "success",
        "iteration": iteration_index,
        "artifact_path": str(iter_path),
        "planning_doc": str(plan_doc),
        "metadata": meta,
    }


# Utilities

_ITER_RE = re.compile(r"^iteration_(\d+)\.mdc$")


def latest_checkpoint_index(repo_root: Optional[Path] = None) -> int:
    """Return the highest iteration_<n>.mdc index, or 0 if none exist.

    This enables roll-forward after a restart by continuing from last + 1.
    """
    root = (repo_root or Path.cwd()).resolve()
    progress_dir = root / ".cerebraflow" / "progress"
    if not progress_dir.exists() or not progress_dir.is_dir():
        return 0
    max_idx = 0
    try:
        for entry in progress_dir.iterdir():
            if not entry.is_file():
                continue
            m = _ITER_RE.match(entry.name)
            if not m:
                continue
            try:
                idx = int(m.group(1))
                if idx > max_idx:
                    max_idx = idx
            except Exception:
                continue
    except Exception:
        return 0
    return max_idx

