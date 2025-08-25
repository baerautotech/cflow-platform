"""Wrapper for scripts/verify_env.py to stabilize import/CLI usage."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _load_monorepo_verifier():
    base = Path(__file__).resolve().parents[2]
    ve = base / "scripts" / "verify_env.py"
    spec = importlib.util.spec_from_file_location("verify_env", str(ve))
    if spec is None or spec.loader is None:
        raise ImportError("Cannot locate scripts/verify_env.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def verify_modes(modes: list[str], scope: str = "both") -> Dict[str, Any]:
    ve = _load_monorepo_verifier()
    # Reuse internal functions for a programmatic API
    paths = []
    if scope in ("root", "both"):
        paths.append(".env")
    if scope in ("cflow", "both"):
        paths.append(".cerebraflow/.env")
    file_env = ve.load_dotenv_files(paths)
    env = ve.merge_env(file_env)
    report = ve.check_modes(env, modes)
    ok = all(not r["missing_all"] and not r["missing_one_of"] for r in report.values())
    return {"ok": ok, "report": report, "modes": modes, "scope": scope, "loaded_paths": paths}


if __name__ == "__main__":
    # Pass-through CLI to monorepo script
    ve = _load_monorepo_verifier()
    sys.exit(ve.main())


def cli() -> int:
    """Console script entrypoint compatible with pyproject scripts."""
    ve = _load_monorepo_verifier()
    return ve.main()


