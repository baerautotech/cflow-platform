from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

from cflow_platform.core.profiles import resolve_profile


class ReasoningHandlers:
    """Implements code_reasoning.plan MCP tool.

    Emits a bounded, SRP plan with minimal-edit constraints and explicit success checks.
    """

    async def handle_code_reasoning_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Inputs
        parsed_failures: List[Dict[str, Any]] = list(arguments.get("parsed_failures", []) or [])
        suspect_files: List[str] = [str(p) for p in (arguments.get("suspect_files") or [])]
        max_steps: int = int(arguments.get("max_steps", 5) or 5)
        profile_name: str = str(arguments.get("profile_name", "quick") or "quick")

        profile = resolve_profile(profile_name)
        if profile is None:
            return {"status": "error", "message": f"Unknown profile {profile_name}"}

        # Derive edit targets from suspects; keep to minimal scope
        unique_targets: List[str] = []
        for p in suspect_files:
            if p not in unique_targets:
                unique_targets.append(p)

        # Build bounded steps with minimal-edit constraints
        steps: List[Dict[str, Any]] = []

        # Step 1: propose minimal edits for suspect files (placeholder, SRP-friendly)
        if unique_targets:
            steps.append(
                {
                    "step": 1,
                    "action": "propose-edits",
                    "targets": unique_targets[: max(1, max_steps - 2)],
                    "constraints": {
                        "minimal_edits": True,
                        "strict_single_match": True,
                        "atomic": True,
                    },
                }
            )

        # Step 2: apply edits if present (no-ops allowed)
        if len(steps) < max_steps:
            steps.append(
                {
                    "step": len(steps) + 1,
                    "action": "apply-edits-if-present",
                    "constraints": {
                        "allowlist": [Path.cwd().resolve().as_posix()],
                        "backup_dir": ".cerebraflow/backups",
                    },
                }
            )

        # Step 3: lint/pre-commit gate (fail-closed)
        if len(steps) < max_steps:
            steps.append(
                {
                    "step": len(steps) + 1,
                    "action": "lint-precommit",
                    "constraints": {"fail_closed": True},
                }
            )

        # Step 4: verify via tests per profile
        if len(steps) < max_steps:
            steps.append(
                {
                    "step": len(steps) + 1,
                    "action": "run-tests",
                    "paths": list(profile.test_paths),
                }
            )

        # Enforce max steps cap
        steps = steps[:max_steps]

        success_checks = [
            {"type": "tests_green", "paths": list(profile.test_paths)},
            {"type": "no_lint_errors"},
        ]

        return {
            "status": "success",
            "profile": profile.name,
            "verify_paths": list(profile.test_paths),
            "max_steps_enforced": True,
            "plan": {
                "steps": steps,
                "success_checks": success_checks,
                "suspect_scope": unique_targets,
            },
        }


