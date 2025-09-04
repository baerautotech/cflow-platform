from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import difflib
from pathlib import Path
import fnmatch


@dataclass
class EditPlan:
    file: str
    original_snippet: str
    replacement_snippet: str


@dataclass
class ApplyOptions:
    dry_run: bool = True
    allowlist: Optional[List[str]] = None  # directories or file globs
    backup_dir: Optional[str] = None
    atomic: bool = True  # if True, rollback all edits on any failure
    strict_single_match: bool = True  # if True, abort when original matches > 1 times


def _normalize_rule(rule: str) -> str:
    # Normalize to POSIX-like string for consistent matching
    return rule.replace("\\", "/").rstrip("/")


def _is_allowed(path: Path, allowlist: Optional[List[str]]) -> bool:
    if not allowlist:
        return True
    # Compare against absolute and repo-relative like strings
    path_str = path.resolve().as_posix()
    rel_str = path.as_posix()
    for raw_rule in allowlist:
        rule = _normalize_rule(raw_rule)
        has_glob = any(ch in rule for ch in ["*", "?", "["])
        # Glob match against absolute and relative
        if has_glob:
            if fnmatch.fnmatch(path_str, rule) or fnmatch.fnmatch(rel_str, rule):
                return True
            continue
        # Directory or exact file prefix checks (absolute and relative)
        # Accept if exact file match
        if rule == path_str or rule == rel_str:
            return True
        # Accept if path is under the directory rule
        if path_str.startswith(rule + "/") or rel_str.startswith(rule + "/"):
            return True
    return False


def _apply_single_edit(content: str, original: str, replacement: str, strict_single_match: bool) -> Tuple[str, str]:
    # Returns (after, status)
    if original not in content:
        return content, "noop"
    # Count occurrences to detect ambiguity/conflict
    occurrences = content.count(original)
    if strict_single_match and occurrences > 1:
        return content, "conflict"
    after = content.replace(original, replacement, 1)
    return after, "applied"


def _diff_text(before: str, after: str, file: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"a/{file}",
            tofile=f"b/{file}",
            lineterm="",
        )
    )


def apply_minimal_edits(edits: List[EditPlan], options: Optional[ApplyOptions] = None) -> Dict[str, Any]:
    options = options or ApplyOptions()
    results: List[Dict[str, Any]] = []
    backups: List[str] = []
    wrote_any = False
    # Prepare backup root if needed
    backup_root: Optional[Path] = None
    if not options.dry_run and (options.atomic or options.backup_dir):
        backup_root = Path(options.backup_dir or ".cflow_backups").resolve()
        backup_root.mkdir(parents=True, exist_ok=True)
    # First pass: compute all diffs and statuses without writing when atomic
    staged_changes: List[Tuple[Path, str, str, str]] = []  # (path, before, after, diff)
    for ep in edits:
        path = Path(ep.file)
        if not _is_allowed(path, options.allowlist):
            results.append({"file": ep.file, "status": "skipped", "reason": "not allowed"})
            continue
        if not path.exists():
            results.append({"file": ep.file, "status": "error", "reason": "missing file"})
            continue
        before = path.read_text()
        after, apply_status = _apply_single_edit(
            before,
            ep.original_snippet,
            ep.replacement_snippet,
            options.strict_single_match,
        )
        diff = _diff_text(before, after, ep.file)
        if apply_status == "noop":
            results.append({"file": ep.file, "status": "noop", "diff": diff})
            continue
        if apply_status == "conflict":
            results.append({"file": ep.file, "status": "conflict", "reason": "multiple matches", "diff": diff})
            # If atomic, abort the whole batch (no writes yet)
            if options.atomic and not options.dry_run:
                return {"status": "error", "results": results, "backups": backups, "reason": "conflict"}
            continue
        # applied candidate
        if options.dry_run:
            results.append({"file": ep.file, "status": "dry-run", "diff": diff})
        else:
            staged_changes.append((path, before, after, diff))
    # Write changes if not dry-run
    if not options.dry_run:
        for path, before, after, diff in staged_changes:
            # Backups: keep relative structure under backup_root
            if backup_root is not None:
                try:
                    rel = path.resolve().relative_to(Path.cwd().resolve())
                except Exception:
                    rel = Path(path.name)
                backup_path = (backup_root / rel).with_suffix(rel.suffix + ".bak")
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(before)
                backups.append(str(backup_path))
            try:
                path.write_text(after)
                wrote_any = True
                results.append({"file": str(path), "status": "applied", "diff": diff})
            except Exception as e:
                results.append({"file": str(path), "status": "error", "reason": str(e)})
                if options.atomic and backups:
                    rb = rollback(backups)
                    return {"status": "error", "results": results, "backups": backups, "rolled_back": rb}
    overall = "success"
    if any(r.get("status") in {"error", "conflict"} for r in results):
        overall = "error"
    if wrote_any and overall == "error" and options.atomic and backups:
        rb = rollback(backups)
        return {"status": "error", "results": results, "backups": backups, "rolled_back": rb}
    return {"status": overall, "results": results, "backups": backups}


def rollback(backups: List[str]) -> Dict[str, Any]:
    restored: List[str] = []
    for b in backups:
        bp = Path(b)
        if not bp.exists():
            continue
        # Replace target file with backup content
        target = bp.with_suffix("")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bp.read_text())
        restored.append(str(target))
    return {"status": "success", "restored": restored}


