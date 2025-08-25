"""Wrapper to install enhanced git hooks via the monorepo script."""

from __future__ import annotations

import subprocess
from pathlib import Path


def install() -> int:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "install-enhanced-git-hooks.sh"
    proc = subprocess.run(["bash", str(script)], cwd=root)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(install())


