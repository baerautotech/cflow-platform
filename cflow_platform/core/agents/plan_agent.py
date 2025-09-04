from __future__ import annotations

from typing import Any, Dict, List
import json

from cflow_platform.core.profiles import InstructionProfile, resolve_profile
from cflow_platform.handlers.reasoning_handlers import ReasoningHandlers


class PlanAgent:
    def __init__(self, profile_name: str = "quick") -> None:
        profile = resolve_profile(profile_name)
        if profile is None:
            raise ValueError(f"Unknown profile {profile_name}")
        self.profile: InstructionProfile = profile
        self.reasoning = ReasoningHandlers()

    def run(self, parsed_failures: List[Dict[str, Any]] | None = None, suspect_files: List[str] | None = None, max_steps: int = 5) -> Dict[str, Any]:
        args: Dict[str, Any] = {
            "parsed_failures": list(parsed_failures or []),
            "suspect_files": list(suspect_files or []),
            "max_steps": int(max_steps),
            "profile_name": self.profile.name,
        }
        # Handlers are async; run synchronously via asyncio loop
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            self.reasoning.handle_code_reasoning_plan(args)  # type: ignore[arg-type]
        )
        return result


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run PlanAgent to produce a bounded minimal-edit plan")
    parser.add_argument("--profile", default="quick")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--suspect", nargs="*", default=None, help="Suspect files to focus edits on")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    agent = PlanAgent(profile_name=args.profile)
    result = agent.run(parsed_failures=None, suspect_files=args.suspect, max_steps=args.max_steps)
    if args.json:
        print(json.dumps(result))
    else:
        print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(cli())


