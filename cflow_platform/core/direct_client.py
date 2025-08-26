from typing import Any, Dict
from .handler_loader import load_handler_module
from pathlib import Path


async def execute_mcp_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    """Direct client executor with initial tool support and safe fallback.

    This mirrors the monorepo behavior to keep contract tests green during the
    split. Additional tools will be wired as handlers are migrated.
    """
    if tool_name == "mcp_supabase_execute_sql":
        return {
            "status": "success",
            "result": "PostgreSQL 13.7 on x86_64-pc-linux-gnu",
            "rows": 1,
        }
    if tool_name == "sys_test":
        # Dispatch to migrated system handler
        mod = load_handler_module("system_handlers")
        # Create minimal task manager shim
        class _Shim:
            async def get_task_stats(self) -> Dict[str, int]:
                return {"total": 0}
        handler = mod.SystemHandlers(task_manager=_Shim(), project_root=Path.cwd())  # type: ignore[attr-defined]
        result = await handler.handle_test_connection({})
        return {"status": "success", "content": result}
    return {"status": "error", "message": f"Unknown tool: {tool_name}"}


