from __future__ import annotations

from typing import Any, Callable, Dict


def run_iteration(
    *,
    plan_fn: Callable[..., Dict[str, Any]],
    implement_fn: Callable[..., Dict[str, Any]],
    verify_fn: Callable[..., Dict[str, Any]],
    profile: Any,
) -> Dict[str, Any]:
    """
    Compose Plan → Implement → Test stages with fresh per-stage contexts.

    - plan_fn: produces a plan dictionary for the given profile
    - implement_fn: applies edits if present and returns an application result
    - verify_fn: runs tests/lint per profile and returns verification result
    """
    # Fresh contexts per stage (not shared/mutated across stages)
    plan_context: Dict[str, Any] = {}
    implement_context: Dict[str, Any] = {}
    verify_context: Dict[str, Any] = {}

    planning = plan_fn(profile, **plan_context) if plan_context is not None else plan_fn(profile)
    apply_res = implement_fn(**implement_context) if implement_context is not None else implement_fn()
    verification = verify_fn(profile, **verify_context) if verify_context is not None else verify_fn(profile)

    status = verification.get("status", "error")
    return {
        "status": status,
        "planning": planning,
        "apply": apply_res,
        "verify": verification,
    }


