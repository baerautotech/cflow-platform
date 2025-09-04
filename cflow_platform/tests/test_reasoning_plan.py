from __future__ import annotations

import asyncio
from pathlib import Path

from cflow_platform.core.public_api import get_direct_client_executor


async def _run(tool: str, **kwargs):
    exec_fn = get_direct_client_executor()
    return await exec_fn(tool, **kwargs)


def test_code_reasoning_plan_basic() -> None:
    result = asyncio.run(_run(
        "code_reasoning.plan",
        parsed_failures=[{"nodeid": "tests/test_x.py::test_y", "message": "AssertionError"}],
        suspect_files=["app/mod.py", "app/utils.py", "app/mod.py"],
        max_steps=4,
        profile_name="quick",
    ))
    assert result["status"] == "success"
    plan = result["plan"]
    assert isinstance(plan["steps"], list)
    assert len(plan["steps"]) <= 4
    # Minimal edit constraints present on propose/apply
    assert any(s["action"] == "apply-edits-if-present" for s in plan["steps"]) 
    assert result["verify_paths"]


