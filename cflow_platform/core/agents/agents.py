from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from pathlib import Path

from cflow_platform.core.minimal_edit_applier import EditPlan, ApplyOptions, apply_minimal_edits
from cflow_platform.core.test_runner import run_tests
from cflow_platform.handlers.reasoning_handlers import ReasoningHandlers


# I/O contracts
@dataclass
class PlanRequest:
    parsed_failures: List[Dict[str, Any]]
    suspect_files: List[str]
    max_steps: int = 5
    profile_name: str = "quick"


@dataclass
class PlanResponse:
    status: str
    plan: Dict[str, Any]
    profile: str
    verify_paths: List[str]


@dataclass
class ImplementRequest:
    edits: List[EditPlan]
    allowlist: Optional[List[str]] = None
    backup_dir: Optional[str] = ".cerebraflow/backups"
    dry_run: bool = False
    atomic: bool = True
    strict_single_match: bool = True


@dataclass
class ImplementResponse:
    status: str
    results: List[Dict[str, Any]]
    backups: List[str]


@dataclass
class TestRequest:
    paths: Optional[List[str]] = None
    k: Optional[str] = None
    m: Optional[str] = None
    maxfail: int = 0
    timeout_sec: Optional[int] = None
    verbose: bool = False


@dataclass
class TestResponse:
    status: str
    summary: Dict[str, Any]
    duration_sec: float
    tests: Optional[List[Dict[str, Any]]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class PlanAgent:
    """Produces a bounded, SRP plan with explicit success checks using existing reasoning handler."""

    def __init__(self) -> None:
        self._handler = ReasoningHandlers()

    async def run(self, request: PlanRequest) -> PlanResponse:
        args: Dict[str, Any] = {
            "parsed_failures": request.parsed_failures,
            "suspect_files": request.suspect_files,
            "max_steps": request.max_steps,
            "profile_name": request.profile_name,
        }
        result = await self._handler.handle_code_reasoning_plan(args)
        status = result.get("status", "error")
        plan = result.get("plan", {})
        profile = result.get("profile", request.profile_name)
        verify_paths = list(result.get("verify_paths", []))
        return PlanResponse(status=status, plan=plan, profile=profile, verify_paths=verify_paths)


class ImplementAgent:
    """Applies minimal, file-scoped edits with allowlist and rollback safeguards."""

    async def run(self, request: ImplementRequest) -> ImplementResponse:
        options = ApplyOptions(
            dry_run=request.dry_run,
            allowlist=request.allowlist,
            backup_dir=request.backup_dir,
            atomic=request.atomic,
            strict_single_match=request.strict_single_match,
        )
        result = apply_minimal_edits(request.edits, options)
        return ImplementResponse(
            status=str(result.get("status", "error")),
            results=list(result.get("results", [])),
            backups=list(result.get("backups", [])),
        )


class TestAgent:
    """Runs pytest with existing runner, returns structured results."""

    async def run(self, request: TestRequest) -> TestResponse:
        rr = run_tests(
            paths=request.paths,
            k=request.k,
            m=request.m,
            maxfail=request.maxfail,
            timeout_sec=request.timeout_sec,
            in_process=True,
            verbose=request.verbose,
        )
        return TestResponse(
            status=str(rr.get("status", "failure")),
            summary=dict(rr.get("summary", {})),
            duration_sec=float(rr.get("duration_sec", 0.0)),
            tests=rr.get("tests"),
            stdout=rr.get("stdout"),
            stderr=rr.get("stderr"),
        )


