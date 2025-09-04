from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import os
import sys
import time
from pathlib import Path

from .public_api import get_direct_client_executor
from .orchestrator import run_iteration
from .test_runner import run_tests
from .docs_context7 import (
    build_failure_report_from_test_result,
    extract_symbols_from_failure_report,
    fetch_context7_docs_for_symbols,
    summarize_docs,
)
from .memory.checkpointer import checkpoint_iteration
from cflow_platform.hooks.pre_commit_runner import main as run_pre_commit_main  # type: ignore
from .minimal_edit_applier import EditPlan, ApplyOptions, apply_minimal_edits
from .profiles import InstructionProfile, resolve_profile


 # Using InstructionProfile from profiles module


def plan(profile: InstructionProfile) -> Dict[str, Any]:
    return {
        "status": "success",
        "plan": [
            {"step": 1, "action": "run-tests", "paths": profile.test_paths},
            {"step": 2, "action": "apply-edits-if-present"},
            {"step": 3, "action": "lint-precommit"},
        ],
    }


def verify(profile: InstructionProfile) -> Dict[str, Any]:
    if profile.verify_mode == "tests":
        # Avoid invoking pytest from within pytest; default to skip in-loop tests when under pytest
        under_pytest = "PYTEST_CURRENT_TEST" in os.environ
        skip_tests = under_pytest or (os.getenv("CFLOW_SKIP_TESTS_IN_LOOP", "").strip().lower() in {"1", "true", "yes"})
        if skip_tests:
            result = {"status": "success", "summary": {"exit_code": 0}}
        else:
            # Avoid in-process recursion when invoked from pytest-based tests
            in_process_exec = not under_pytest
            result = run_tests(paths=profile.test_paths, use_uv=False, in_process=in_process_exec)
            # Memory-first retrieval when tests fail
            if result.get("status") != "success":
                try:
                    failure_report = build_failure_report_from_test_result(result)
                except Exception:
                    failure_report = ""
                try:
                    symbols = extract_symbols_from_failure_report(failure_report)
                except Exception:
                    symbols = []
                # Prefer CerebralMemory before external RAG
                try:
                    exec_fn = get_direct_client_executor()
                    import asyncio  # local import to avoid global dependency during tests
                    query_parts = []
                    if symbols:
                        query_parts.append(" ".join([str(s) for s in symbols]))
                    if failure_report:
                        # keep report short to avoid excessive payloads
                        query_parts.append(str(failure_report)[:1000])
                    query = "\n".join([p for p in query_parts if p]).strip() or "test failures"
                    mem_limit = int(os.getenv("CFLOW_MEMORY_SEARCH_LIMIT", "20") or "20")
                    mem_res = asyncio.get_event_loop().run_until_complete(
                        exec_fn(
                            "memory_search",
                            query=query,
                            userId=os.getenv("CFLOW_USER_ID", "system"),
                            limit=mem_limit,
                        )
                    )
                    result["memory"] = {
                        "enabled": True,
                        "query": query,
                        "count": mem_res.get("count", 0),
                        "results": mem_res.get("results", []),
                    }
                except Exception:
                    # Non-fatal if memory lookup fails
                    result["memory"] = {"enabled": False}

                # 3.2 Context7 docs integration (toggle via CFLOW_ENABLE_CONTEXT7=1); runs after memory
                enable_docs = os.getenv("CFLOW_ENABLE_CONTEXT7", "").strip().lower() in {"1", "true", "yes"}
                if enable_docs:
                    try:
                        per_symbol_limit = int(os.getenv("CFLOW_CONTEXT7_PER_SYMBOL_LIMIT", "2") or "2")
                        docs = fetch_context7_docs_for_symbols(symbols or [], per_symbol_limit=per_symbol_limit)
                        summary_text = summarize_docs(docs.get("notes", []))
                        result["docs"] = {
                            "enabled": True,
                            "symbols": symbols or [],
                            "notes": docs.get("notes", []),
                            "summary": summary_text,
                            "sources": docs.get("sources", []),
                        }
                    except Exception:
                        result["docs"] = {"enabled": False}
        # After tests, enforce lint/pre-commit gating (fail-closed)
        lint = run_lint_and_hooks()
        overall_status = "success" if (result.get("status") == "success" and lint.get("status") == "success") else "error"
        return {
            "status": overall_status,
            "verification": result,
            "lint": lint,
        }
    return {"status": "error", "message": f"Unknown verify mode {profile.verify_mode}"}


def run_lint_and_hooks() -> Dict[str, Any]:
    """Run lint/pre-commit checks with test-friendly overrides.

    Testing overrides via CFLOW_PRE_COMMIT_MODE:
    - "skip": do not run, return success (used to isolate behavior)
    - "pass": simulate success
    - "fail": simulate failure
    """
    mode = os.getenv("CFLOW_PRE_COMMIT_MODE", "").strip().lower()
    if mode == "skip":
        return {"status": "success", "skipped": True}
    if mode == "pass":
        return {"status": "success", "simulated": True}
    if mode == "fail":
        return {"status": "error", "simulated": True}
    try:
        code = run_pre_commit_main()
        return {"status": "success" if code == 0 else "error", "exit_code": code}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _load_edit_plans_from_file(path: Path) -> list[EditPlan]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return []
    plans: list[EditPlan] = []
    if isinstance(data, list):
        for item in data:
            try:
                plans.append(
                    EditPlan(
                        file=item["file"],
                        original_snippet=item["original_snippet"],
                        replacement_snippet=item["replacement_snippet"],
                    )
                )
            except Exception:
                continue
    return plans


def apply_edits_if_present() -> Dict[str, Any]:
    edits_file_env = os.getenv("CFLOW_EDIT_PLANS_FILE", ".cerebraflow/edits.json")
    path = Path(edits_file_env)
    if not path.exists():
        return {"status": "skipped", "reason": "no edits file"}
    plans = _load_edit_plans_from_file(path)
    if not plans:
        return {"status": "skipped", "reason": "no valid edits"}
    # Options configured by environment with safe defaults
    apply_flag = os.getenv("CFLOW_APPLY_EDITS", "0").strip().lower() in {"1", "true", "yes"}
    allowlist_env = os.getenv("CFLOW_EDIT_ALLOWLIST", "").strip()
    allowlist = [s for s in [p.strip() for p in allowlist_env.replace(";", ",").split(",")] if s]
    if not allowlist:
        # Default to repo root to prevent writes outside workspace
        allowlist = [Path.cwd().resolve().as_posix()]
    options = ApplyOptions(
        dry_run=not apply_flag,
        allowlist=allowlist,
        backup_dir=os.getenv("CFLOW_EDIT_BACKUP_DIR", ".cerebraflow/backups"),
        atomic=True,
        strict_single_match=True,
    )
    result = apply_minimal_edits(plans, options)
    # Optionally persist the result for inspection
    try:
        out_dir = Path(".cerebraflow/logs")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "edit-apply.json").write_text(json.dumps(result, indent=2))
    except Exception:
        pass
    return result


def loop(profile_name: str, max_iterations: int = 1) -> Dict[str, Any]:
    profile = resolve_profile(profile_name)
    if not profile:
        return {"status": "error", "message": f"Unknown profile {profile_name}"}
    executor = get_direct_client_executor()
    history: List[Dict[str, Any]] = []
    for i in range(max_iterations):
        # Run Plan → Implement → Verify with fresh per-stage contexts
        stage_result = run_iteration(
            plan_fn=plan,
            implement_fn=apply_edits_if_present,
            verify_fn=verify,
            profile=profile,
        )
        p = stage_result.get("planning", {})
        history.append({"iteration": i + 1, **{k: v for k, v in stage_result.items() if k != "status"}})
        # Persist procedure definition and a simple planning memory (best-effort)
        try:
            import asyncio
            steps = p.get("plan", []) or []
            proc_steps = []
            for s in steps:
                try:
                    proc_steps.append({
                        "order": int(s.get("step", len(proc_steps) + 1)),
                        "instruction": str(s.get("action", "")).strip(),
                        "notes": None,
                    })
                except Exception:
                    continue
            if proc_steps:
                asyncio.get_event_loop().run_until_complete(
                    executor(
                        "memory_store_procedure",
                        title=f"Agent Loop Procedure (profile {profile.name})",
                        steps=proc_steps,
                        justification="Automated plan capture from agent loop",
                        source="agent_loop.plan",
                    )
                )
            # Lightweight planning snapshot as a general memory
            asyncio.get_event_loop().run_until_complete(
                executor(
                    "memory_add",
                    content=json.dumps({"iteration": i + 1, "plan": steps}, indent=2),
                    userId=os.getenv("CFLOW_USER_ID", "system"),
                    metadata={
                        "type": "plan",
                        "iteration": i + 1,
                        "profile": profile.name,
                    },
                )
            )
        except Exception:
            pass
        v = stage_result.get("verify", {})
        apply_result = stage_result.get("apply", {})
        # Persist checkpoint to Cursor artifacts + CerebralMemory (best-effort)
        try:
            checkpoint_iteration(
                iteration_index=i + 1,
                plan=p,
                verify={**v, "apply": apply_result},
                run_id=os.getenv("CFLOW_RUN_ID", "local-run"),
                task_id=os.getenv("CFLOW_TASK_ID", ""),
                extra_metadata={"profile": profile.name},
            )
        except Exception:
            pass
        if stage_result.get("status") == "success":
            break
    return {"status": history[-1].get("verify", {}).get("status", "error"), "iterations": len(history), "history": history}


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Unified CLI agent loop for cflow-platform")
    parser.add_argument("--profile", default="quick", help="Instruction profile name")
    parser.add_argument("--max-iter", type=int, default=1, help="Maximum loop iterations")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result")
    args = parser.parse_args()
    result = loop(args.profile, max_iterations=args.max_iter)
    if args.json:
        print(json.dumps(result))
    else:
        status = result.get("status")
        print(f"Agent loop finished with status={status} after {result.get('iterations')} iteration(s)")
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(cli())


