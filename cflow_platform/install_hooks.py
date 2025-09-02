"""Wrapper to install enhanced git hooks via the monorepo script."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def install() -> int:
    # Repo root is the parent of the cflow_platform package
    root = Path(__file__).resolve().parents[1]
    hooks_dir = root / "git-hooks"
    script = root / "scripts" / "install-enhanced-git-hooks.sh"

    if script.exists():
        proc = subprocess.run(["bash", str(script)], cwd=root)
        return proc.returncode

    # Install direct .git/hooks when repo script not present
    # Resolve actual git dir (worktrees/submodules supported)
    try:
        git_dir = subprocess.check_output(["git", "rev-parse", "--git-dir"], cwd=root, text=True).strip()
        git_dir_path = (root / git_dir).resolve()
    except Exception:
        git_dir_path = (root / ".git").resolve()
    git_hooks_dir = git_dir_path / "hooks"
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_path = git_hooks_dir / "pre-commit"
    post_commit_path = git_hooks_dir / "post-commit"

    # Prefer uv; fallback to project venv python
    uv_path = shutil.which("uv")
    venv_python = str((root / ".venv" / "bin" / "python").resolve())
    pre_exec = f"{uv_path} run -q python" if uv_path else venv_python

    pre_commit_content = f"""#!/bin/bash
set -euo pipefail

# Fast, non-ML pre-commit: file org + RAG guard + emoji guard
exec {pre_exec} -m cflow_platform.hooks.pre_commit_runner
"""

    post_commit_content = f"""#!/bin/bash
set -euo pipefail

# Post-commit embedding and ingestion (run in background)
(
  LOG_DIR="${{PWD}}/.cerebraflow/logs"
  mkdir -p "$LOG_DIR"
  LOG_FILE="$LOG_DIR/post-commit.log"
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "$TS starting post-commit tasks" >> "$LOG_FILE"
  export CFLOW_SKIP_APPLE_MPS=0
  export TOKENIZERS_PARALLELISM=false
  VENV_BIN="${{PWD}}/.venv/bin"
  if command -v uv >/dev/null 2>&1; then
    RUN_CLI="uv run -q"
  else
    RUN_CLI=""
  fi
  # Ingest Cursor artifacts
  if [ -n "$RUN_CLI" ]; then
    $RUN_CLI cflow-memory-watch --json >> "$LOG_FILE" 2>&1 || true
  elif [ -x "$VENV_BIN/cflow-memory-watch" ]; then
    "$VENV_BIN/cflow-memory-watch" --json >> "$LOG_FILE" 2>&1 || true
  fi
  # Vectorize latest commit into local Chroma
  COMMIT=$(git rev-parse HEAD)
  if [ -n "$RUN_CLI" ]; then
    $RUN_CLI cflow-codebase-vectorize --commit "$COMMIT" --json >> "$LOG_FILE" 2>&1 || true
  elif [ -x "$VENV_BIN/cflow-codebase-vectorize" ]; then
    "$VENV_BIN/cflow-codebase-vectorize" --commit "$COMMIT" --json >> "$LOG_FILE" 2>&1 || true
  fi
  TS_END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "$TS_END completed post-commit tasks" >> "$LOG_FILE"
) &>/dev/null &
"""

    pre_commit_path.write_text(pre_commit_content, encoding="utf-8")
    os.chmod(pre_commit_path, 0o755)

    post_commit_path.write_text(post_commit_content, encoding="utf-8")
    os.chmod(post_commit_path, 0o755)

    print("[cflow-platform] Installed direct .git/hooks pre-commit and post-commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(install())


