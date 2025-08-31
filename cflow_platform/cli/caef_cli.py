from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _python_executable() -> str:
    return sys.executable


def _framework_path(module: str) -> str:
    base = Path(__file__).resolve().parents[2] / "vendor" / "cerebral" / "framework"
    return str(base / module)


def run_module(module: str, args: list[str]) -> tuple[int, str, str]:
    cmd = [_python_executable(), _framework_path(module)] + args
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def start() -> int:
    code, out, err = run_module("caef_unified_orchestrator.py", [])
    if out:
        print(out)
    if err:
        print(err)
    return 0 if code == 0 else 1


def status() -> int:
    # Placeholder status: could wire to orchestrator if it exposes status
    info = {
        "caef": "vendored",
        "modules": [
            "caef_unified_orchestrator.py",
            "caef_workflow_orchestrator.py",
            "caef_process_manager.py",
        ],
    }
    print(json.dumps(info))
    return 0


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow CAEF supervisor")
    parser.add_argument("command", choices=["start", "status"], help="Command")
    args = parser.parse_args()
    if args.command == "start":
        return start()
    return status()


if __name__ == "__main__":
    raise SystemExit(cli())
