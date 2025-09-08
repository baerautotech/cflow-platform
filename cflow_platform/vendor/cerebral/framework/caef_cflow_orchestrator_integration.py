from __future__ import annotations

from typing import Any, Dict, Optional
import os

try:
    from cflow_platform.core.agent_loop import loop as cflow_loop  # type: ignore
except Exception:  # pragma: no cover - defensive
    cflow_loop = None  # type: ignore


class CFlowOrchestratorIntegration:
    """Thin bridge to invoke CFlow agent loop from CAEF when requested.

    This provides a minimal compatibility surface. If CFlow is unavailable,
    calls will no-op with an error dictionary rather than raising exceptions.
    """

    def __init__(self) -> None:
        pass

    def run_cflow_agent_once(self, profile: str = "quick", max_iter: int = 1) -> Dict[str, Any]:
        if cflow_loop is None:
            return {"status": "error", "message": "cflow loop not available"}
        try:
            wallclock = os.getenv("CFLOW_MAX_WALLCLOCK_SEC")
            step_budget = os.getenv("CFLOW_MAX_STEPS")
            res = cflow_loop(
                profile_name=profile,
                max_iterations=int(max_iter),
                wallclock_limit_sec=int(wallclock) if wallclock else None,
                step_budget=int(step_budget) if step_budget else None,
            )
            return res
        except Exception as e:
            return {"status": "error", "message": str(e)}


