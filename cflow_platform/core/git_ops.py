from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
import subprocess


@dataclass
class GitCommandResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int


def _run_git(args: List[str], cwd: Optional[Path] = None) -> GitCommandResult:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return GitCommandResult(proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip(), proc.returncode)
    except Exception as e:
        return GitCommandResult(False, "", str(e), 1)


def _repo_root(start: Optional[Path] = None) -> Optional[Path]:
    start_dir = start or Path.cwd()
    res = _run_git(["rev-parse", "--show-toplevel"], cwd=start_dir)
    if not res.success:
        return None
    try:
        return Path(res.stdout).resolve()
    except Exception:
        return None


def _has_uncommitted_changes(repo_root: Path) -> bool:
    # Detect any tracked file changes (staged or unstaged)
    res = _run_git(["status", "--porcelain"], cwd=repo_root)
    if not res.success:
        return False
    return any(line.strip() for line in res.stdout.splitlines())


def _stage_all(repo_root: Path) -> GitCommandResult:
    return _run_git(["add", "-A"], cwd=repo_root)


def _has_staged_changes(repo_root: Path) -> bool:
    # --quiet exits with 1 when there are differences; 0 when none
    res = _run_git(["diff", "--cached", "--quiet"], cwd=repo_root)
    return res.exit_code == 1


def _current_branch(repo_root: Path) -> str:
    res = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    return res.stdout if res.success else ""


def _head_hash(repo_root: Path) -> str:
    res = _run_git(["rev-parse", "HEAD"], cwd=repo_root)
    return res.stdout if res.success else ""


def attempt_auto_commit(
    *,
    message: Optional[str] = None,
    include_untracked: bool = True,
) -> Dict[str, str]:
    """
    Atomically stage and commit repository changes.

    Preconditions:
    - Must be inside a git repository
    - Pre-commit/lint should already be validated by caller

    Returns a dict with keys: status, commit, branch, message, error
    """
    repo = _repo_root()
    if not repo:
        return {"status": "skipped", "error": "not_a_git_repo"}

    if not _has_uncommitted_changes(repo):
        return {"status": "skipped", "error": "no_changes"}

    stage_res = _stage_all(repo) if include_untracked else _run_git(["add", "-u"], cwd=repo)
    if not stage_res.success:
        return {"status": "error", "error": f"stage_failed: {stage_res.stderr}"}

    if not _has_staged_changes(repo):
        return {"status": "skipped", "error": "nothing_staged"}

    commit_message = (message or "cflow:auto-commit")[:300]
    commit_res = _run_git(["commit", "-m", commit_message], cwd=repo)
    if not commit_res.success:
        return {"status": "error", "error": f"commit_failed: {commit_res.stderr}"}

    return {
        "status": "success",
        "commit": _head_hash(repo),
        "branch": _current_branch(repo),
        "message": commit_message,
    }


