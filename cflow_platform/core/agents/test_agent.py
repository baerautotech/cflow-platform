from __future__ import annotations

from typing import Any, Dict, List
import json

from cflow_platform.core.profiles import InstructionProfile, resolve_profile
from cflow_platform.core.test_runner import run_tests
from cflow_platform.core.agent_loop import run_lint_and_hooks


class TestAgent:
    def __init__(self, profile_name: str = "quick") -> None:
        profile = resolve_profile(profile_name)
        if profile is None:
            raise ValueError(f"Unknown profile {profile_name}")
        self.profile: InstructionProfile = profile

    def run(self, paths: List[str] | None = None, lint_gate: bool = True, in_process: bool | None = None) -> Dict[str, Any]:
        test_paths = paths or list(self.profile.test_paths)
        under_pytest = "PYTEST_CURRENT_TEST" in __import__("os").environ
        in_proc = bool(in_process) if in_process is not None else not under_pytest
        result = run_tests(paths=test_paths, in_process=in_proc)
        if lint_gate:
            lint = run_lint_and_hooks()
            overall = "success" if (result.get("status") == "success" and lint.get("status") == "success") else "error"
            return {"status": overall, "tests": result, "lint": lint}
        return result


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run TestAgent to execute profile tests with optional lint gate")
    parser.add_argument("--profile", default="quick")
    parser.add_argument("paths", nargs="*", default=None)
    parser.add_argument("--no-lint", dest="lint", action="store_false")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--in-process", dest="in_process", action="store_true")
    parser.add_argument("--no-in-process", dest="in_process", action="store_false")
    parser.set_defaults(in_process=None)
    args = parser.parse_args()

    agent = TestAgent(profile_name=args.profile)
    result = agent.run(paths=args.paths or None, lint_gate=args.lint, in_process=args.in_process)
    if args.json:
        print(json.dumps(result))
    else:
        print(json.dumps(result, indent=2))
    return 0 if (result.get("status") == "success" or (isinstance(result.get("tests"), dict) and result.get("tests", {}).get("status") == "success")) else 1


if __name__ == "__main__":
    raise SystemExit(cli())


