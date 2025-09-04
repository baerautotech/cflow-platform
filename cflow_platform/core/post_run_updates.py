from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import datetime as _dt
import json
import os


def _repo_root() -> Path:
    # Resolve repository root as the parent of the package root
    return Path(__file__).resolve().parents[2]


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing.endswith("\n") and text.startswith("\n"):
            path.write_text(existing + text, encoding="utf-8")
        else:
            sep = "\n" if not existing.endswith("\n") else ""
            path.write_text(existing + sep + text, encoding="utf-8")
    else:
        path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _ts() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_run_summary(summary: Dict[str, Any]) -> str:
    # Compact, Markdown-friendly summary block
    parts: List[str] = []
    parts.append(f"- **timestamp**: {summary.get('timestamp')}")
    task_id = summary.get("task_id") or ""
    if task_id:
        parts.append(f"- **task_id**: {task_id}")
    profile = summary.get("profile") or ""
    if profile:
        parts.append(f"- **profile**: {profile}")
    iter_count = summary.get("iterations")
    if iter_count is not None:
        parts.append(f"- **iterations**: {iter_count}")
    status = summary.get("status") or "success"
    parts.append(f"- **status**: {status}")
    tests = summary.get("tests", {}) or {}
    if tests:
        try:
            counts = {k: int(v) for k, v in (tests.get("summary") or {}).items()}
        except Exception:
            counts = {}
        if counts:
            parts.append(f"- **tests**: {json.dumps(counts)}")
    apply_info = summary.get("apply") or {}
    if apply_info:
        changed = apply_info.get("changed_files") or apply_info.get("applied_files")
        if changed:
            try:
                n = len(changed) if hasattr(changed, "__len__") else int(changed)
                parts.append(f"- **changed_files**: {n}")
            except Exception:
                pass
    return "\n".join(parts)


def update_cursor_artifacts(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update Cursor workspace artifacts after a successful run.

    Artifacts updated (best-effort):
    - AGENTS.md: append "Last successful run" block
    - docs/cflow_planning.mdc: append compact run summary block
    - .cursor/rules/run_status.mdc: write status snapshot for tools
    """
    root = _repo_root()
    ts = _ts()
    enriched = {**summary, "timestamp": ts}
    updated: List[str] = []

    # 1) Update AGENTS.md
    try:
        agents_md = root / "AGENTS.md"
        header = "\n### Last successful run\n"
        block = _format_run_summary(enriched)
        _append(agents_md, header + block + "\n")
        updated.append(str(agents_md))
    except Exception:
        pass

    # 2) Update docs/cflow_planning.mdc
    try:
        plan_doc = root / "docs" / "cflow_planning.mdc"
        header = "\n### Run summary (auto)\n"
        block = _format_run_summary(enriched)
        _append(plan_doc, header + block + "\n")
        updated.append(str(plan_doc))
    except Exception:
        pass

    # 3) Write .cursor/rules/run_status.mdc snapshot
    try:
        rules_dir = root / ".cursor" / "rules"
        rules_path = rules_dir / "run_status.mdc"
        rules_dir.mkdir(parents=True, exist_ok=True)
        content = ["### Run Status Snapshot", "", _format_run_summary(enriched), ""]
        rules_path.write_text("\n".join(content), encoding="utf-8")
        updated.append(str(rules_path))
    except Exception:
        pass

    return {"status": "success", "updated": updated, "timestamp": ts}


