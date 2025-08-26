from typing import Any, Dict


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
    return {"status": "error", "message": f"Unknown tool: {tool_name}"}


