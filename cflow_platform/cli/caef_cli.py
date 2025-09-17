from __future__ import annotations

import argparse
import json
import os
import subprocess
from cflow_platform.core.direct_client import execute_mcp_tool
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


def _truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in {"1", "true", "yes", "on"}


def start() -> int:
    # Optional preflight: provider probe (Gate P)
    if _truthy(os.getenv("CFLOW_PROVIDER_PROBE")):
        try:
            import asyncio
            res = asyncio.get_event_loop().run_until_complete(
                execute_mcp_tool(
                    "llm_provider.probe",
                    model=os.getenv("CFLOW_PROVIDER_MODEL", ""),
                    prompt=os.getenv("CFLOW_PROVIDER_PROMPT", "probe"),
                )
            )
            if (res or {}).get("status") != "success":
                print(json.dumps({"status": "error", "stage": "provider_probe", "result": res}))
                return 2
        except Exception as e:
            print(json.dumps({"status": "error", "stage": "provider_probe", "error": str(e)}))
            return 2

    code, out, err = run_module("caef_unified_orchestrator.py", [])
    if out:
        print(out)
    if err:
        print(err)
    return 0 if code == 0 else 1


def status() -> int:
    """Get CAEF orchestrator status."""
    info = {
        "caef": "vendored",
        "status": "ready",
        "modules": [
            "caef_unified_orchestrator.py",
            "caef_workflow_orchestrator.py", 
            "caef_process_manager.py",
        ],
        "integration": "bmad_gated_execution"
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
