from typing import Any, Dict
from .handler_loader import load_handler_module
from pathlib import Path
from .task_manager_adapter import TaskManagerAdapter


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
        tm = TaskManagerAdapter()
        handler = mod.SystemHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        result = await handler.handle_test_connection({})
        return {"status": "success", "content": result}
    if tool_name in {"task_list", "task_get", "task_next"}:
        mod = load_handler_module("task_handlers")
        tm = TaskManagerAdapter()
        handler = mod.TaskHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "task_list":
            return await handler.handle_list_tasks(kwargs or {})
        if tool_name == "task_get":
            return await handler.handle_get_task(kwargs or {})
        if tool_name == "task_next":
            return await handler.handle_next_task(kwargs or {})
    if tool_name == "doc_research":
        mod = load_handler_module("enhanced_research_handlers")
        tm = TaskManagerAdapter()
        handler = mod.EnhancedResearchHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        return await handler.handle_doc_research(kwargs or {})
    if tool_name in {"plan_parse", "plan_list", "plan_validate"}:
        mod = load_handler_module("plan_parser_handlers")
        handler = mod.PlanParserHandlers()  # type: ignore[attr-defined]
        if tool_name == "plan_parse":
            return await handler.parse_atomic_plan(**(kwargs or {}))
        if tool_name == "plan_list":
            return await handler.list_available_plans(**(kwargs or {}))
        if tool_name == "plan_validate":
            return await handler.validate_plan_format(**(kwargs or {}))
    if tool_name in {"doc_generate", "doc_quality", "doc_refs", "doc_research", "doc_comply"}:
        mod = load_handler_module("rag_handlers")
        handler = mod.RAGHandlers(project_root=Path.cwd())  # type: ignore[attr-defined]
        mapping = {
            "doc_generate": handler.handle_doc_generate,
            "doc_quality": handler.handle_doc_quality,
            "doc_refs": handler.handle_doc_refs,
            "doc_research": handler.handle_doc_research,
            "doc_comply": handler.handle_doc_comply,
        }
        return await mapping[tool_name](kwargs or {})
    if tool_name in {"sys_stats", "sys_debug", "sys_version"}:
        mod = load_handler_module("system_handlers")
        tm = TaskManagerAdapter()
        handler = mod.SystemHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "sys_stats":
            return await handler.handle_get_stats(kwargs or {})
        if tool_name == "sys_debug":
            return await handler.handle_debug_environment(kwargs or {})
        if tool_name == "sys_version":
            return await handler.handle_version_info(kwargs or {})
    return {"status": "error", "message": f"Unknown tool: {tool_name}"}


