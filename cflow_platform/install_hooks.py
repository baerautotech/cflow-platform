"""Wrapper to install enhanced git hooks via the monorepo script."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _ensure_hook_block(path: Path, block: str, marker: str) -> None:
    """Append an idempotent integration block to an existing hook script.

    Preserves existing hook behavior and avoids duplication using a marker.
    """
    shebang = "#!/bin/bash\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if marker in existing:
            os.chmod(path, 0o755)
            return
        content = existing.rstrip() + "\n\n" + block
    else:
        content = f"{shebang}set -euo pipefail\n\n{block}"
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o755)


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

    pre_marker = "# >>> cflow-platform:dev-workflow-pre-commit"
    post_marker = "# >>> cflow-platform:dev-workflow-post-commit"

    pre_commit_block = (
        f"{pre_marker}\n"
        f"# Fast, non-ML pre-commit: file org + RAG guard + emoji guard\n"
        f"{pre_exec} -m cflow_platform.hooks.pre_commit_runner\n"
        f"rc=$?\n"
        f"if [ $rc -ne 0 ]; then exit $rc; fi\n"
        f"# <<< cflow-platform:dev-workflow-pre-commit\n"
    )

    post_commit_block = (
        f"{post_marker}\n"
        f"# Post-commit embedding and ingestion (run in background)\n"
        f"(\n"
        f"  LOG_DIR=\"${{PWD}}/.cerebraflow/logs\"\n"
        f"  mkdir -p \"$LOG_DIR\"\n"
        f"  LOG_FILE=\"$LOG_DIR/post-commit.log\"\n"
        f"  TS=$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\n"
        f"  echo \"$TS starting post-commit tasks\" >> \"$LOG_FILE\"\n"
        f"  export CFLOW_SKIP_APPLE_MPS=0\n"
        f"  export TOKENIZERS_PARALLELISM=false\n"
        f"  VENV_BIN=\"${{PWD}}/.venv/bin\"\n"
        f"  if command -v uv >/dev/null 2>&1; then\n"
        f"    RUN_CLI=\"uv run -q\"\n"
        f"  else\n"
        f"    RUN_CLI=\"\"\n"
        f"  fi\n"
        f"  # Ingest Cursor artifacts\n"
        f"  if [ -n \"$RUN_CLI\" ]; then\n"
        f"    $RUN_CLI cflow-memory-watch --json >> \"$LOG_FILE\" 2>&1 || true\n"
        f"  elif [ -x \"$VENV_BIN/cflow-memory-watch\" ]; then\n"
        f"    \"$VENV_BIN/cflow-memory-watch\" --json >> \"$LOG_FILE\" 2>&1 || true\n"
        f"  fi\n"
        f"  # Vectorize latest commit into local Chroma\n"
        f"  COMMIT=$(git rev-parse HEAD)\n"
        f"  if [ -n \"$RUN_CLI\" ]; then\n"
        f"    $RUN_CLI cflow-codebase-vectorize --commit \"$COMMIT\" --json >> \"$LOG_FILE\" 2>&1 || true\n"
        f"  elif [ -x \"$VENV_BIN/cflow-codebase-vectorize\" ]; then\n"
        f"    \"$VENV_BIN/cflow-codebase-vectorize\" --commit \"$COMMIT\" --json >> \"$LOG_FILE\" 2>&1 || true\n"
        f"  fi\n"
        f"  TS_END=$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\n"
        f"  echo \"$TS_END completed post-commit tasks\" >> \"$LOG_FILE\"\n"
        f") &>/dev/null &\n"
        f"# <<< cflow-platform:dev-workflow-post-commit\n"
    )

    _ensure_hook_block(pre_commit_path, pre_commit_block, pre_marker)
    _ensure_hook_block(post_commit_path, post_commit_block, post_marker)

    print("[cflow-platform] Ensured .git/hooks pre-commit and post-commit integration (idempotent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(install())


