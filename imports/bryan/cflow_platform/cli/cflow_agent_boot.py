from __future__ import annotations

import subprocess
import sys


def main() -> None:
    # Delegate to module execution to ensure uv-run Python resolves package
    # correctly even when console shim import path is not set up for editable installs.
    cmd = [sys.executable, "-m", "cflow_platform.cli.cflow_agent", *sys.argv[1:]]
    raise SystemExit(subprocess.call(cmd))


