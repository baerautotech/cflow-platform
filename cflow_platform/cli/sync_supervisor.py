from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _python_executable() -> str:
    return sys.executable


def _service_paths() -> dict[str, str]:
    base = Path(__file__).resolve().parents[2] / "vendor" / "cerebral" / "services"
    return {
        "unified": str(base / "unified_realtime_sync_service.py"),
        "core": str(base / "chromadb_supabase_sync_service.py"),
    }


def run_command(args: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def start(project_root: str | None) -> int:
    paths = _service_paths()
    if not Path(paths["unified"]).exists():
        print(json.dumps({"success": False, "error": "unified_realtime_sync_service.py not found"}))
        return 1
    code, out, err = run_command([_python_executable(), paths["unified"], "daemon", "--project-root", project_root or str(Path.cwd())])
    print(out or err)
    return 0 if code == 0 else 1


def status(project_root: str | None) -> int:
    paths = _service_paths()
    code, out, err = run_command([_python_executable(), paths["unified"], "status", "--project-root", project_root or str(Path.cwd())])
    print(out or err)
    return 0 if code == 0 else 1


def stop(project_root: str | None) -> int:
    paths = _service_paths()
    code, out, err = run_command([_python_executable(), paths["unified"], "stop", "--project-root", project_root or str(Path.cwd())])
    print(out or err)
    return 0 if code == 0 else 1


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow sync supervisor (vendored Cerebral sync service)")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Supervisor command")
    parser.add_argument("--project-root", dest="project_root", help="Project root for underlying service")
    args = parser.parse_args()
    if args.command == "start":
        return start(args.project_root)
    if args.command == "stop":
        return stop(args.project_root)
    return status(args.project_root)


if __name__ == "__main__":
    raise SystemExit(cli())


