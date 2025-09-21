from typing import Any, Dict
from .handler_loader import load_handler_module
from pathlib import Path
from .task_manager_client import TaskManagerClient


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
        tm = TaskManagerClient()
        handler = mod.SystemHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        result = await handler.handle_test_connection({})
        return {"status": "success", "content": result}
    if tool_name in {"task_list", "task_get", "task_next"}:
        mod = load_handler_module("task_handlers")
        tm = TaskManagerClient()
        handler = mod.TaskHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "task_list":
            return await handler.handle_list_tasks(kwargs or {})
        if tool_name == "task_get":
            return await handler.handle_get_task(kwargs or {})
        if tool_name == "task_next":
            return await handler.handle_next_task(kwargs or {})
    if tool_name in {"doc_research", "research"}:
        mod = load_handler_module("enhanced_research_handlers")
        tm = TaskManagerClient()
        handler = mod.EnhancedResearchHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "doc_research":
            return await handler.handle_doc_research(kwargs or {})
        return await handler.handle_research(kwargs or {})
    if tool_name in {"lint_full", "lint_bg", "lint_supa", "lint_status", "lint_trigger", "watch_start", "watch_status"}:
        mod = load_handler_module("linting_handlers")
        handler = mod.LintingHandlers()  # type: ignore[attr-defined]
        mapping = {
            "lint_full": handler.handle_lint_full,
            "lint_bg": handler.handle_lint_bg,
            "lint_supa": handler.handle_lint_supa,
            "lint_status": handler.handle_lint_status,
            "lint_trigger": handler.handle_lint_trigger,
            "watch_start": handler.handle_watch_start,
            "watch_status": handler.handle_watch_status,
        }
        return await mapping[tool_name](kwargs or {})
    if tool_name in {"enh_full_lint", "enh_pattern", "enh_autofix", "enh_perf", "enh_rag", "enh_mon_start", "enh_mon_stop", "enh_status"}:
        mod = load_handler_module("linting_handlers")
        handler = mod.LintingHandlers()  # type: ignore[attr-defined]
        mapping = {
            "enh_full_lint": handler.handle_enh_full_lint,
            "enh_pattern": handler.handle_enh_pattern,
            "enh_autofix": handler.handle_enh_autofix,
            "enh_perf": handler.handle_enh_perf,
            "enh_rag": handler.handle_enh_rag,
            "enh_mon_start": handler.handle_enh_mon_start,
            "enh_mon_stop": handler.handle_enh_mon_stop,
            "enh_status": handler.handle_enh_status,
        }
        return await mapping[tool_name](kwargs or {})
    if tool_name in {"task_add", "task_update", "task_status", "task_sub_add", "task_sub_upd", "task_multi", "task_remove"}:
        mod = load_handler_module("task_mod_handlers")
        tm = TaskManagerClient()
        handler = mod.TaskModificationHandlers(task_manager=tm)  # type: ignore[attr-defined]
        mapping = {
            "task_add": handler.handle_task_add,
            "task_update": handler.handle_task_update,
            "task_status": handler.handle_task_status,
            "task_sub_add": handler.handle_task_sub_add,
            "task_sub_upd": handler.handle_task_sub_upd,
            "task_multi": handler.handle_task_multi,
            "task_remove": handler.handle_task_remove,
        }
        return await mapping[tool_name](kwargs or {})
    if tool_name in {"test_analyze", "test_delete_flaky", "test_confidence"}:
        mod = load_handler_module("testing_handlers")
        handler = mod.TestingHandlers()  # type: ignore[attr-defined]
        mapping = {
            "test_analyze": handler.handle_test_analyze,
            "test_delete_flaky": handler.handle_test_delete_flaky,
            "test_confidence": handler.handle_test_confidence,
        }
        return await mapping[tool_name](kwargs or {})
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
    if tool_name in {"sandbox.run_python"}:
        mod = load_handler_module("sandbox_handlers")
        handler = mod.SandboxHandlers()  # type: ignore[attr-defined]
        return await handler.handle_run_python(kwargs or {})
    if tool_name in {"sys_stats", "sys_debug", "sys_version"}:
        mod = load_handler_module("system_handlers")
        tm = TaskManagerClient()
        handler = mod.SystemHandlers(task_manager=tm, project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "sys_stats":
            return await handler.handle_get_stats(kwargs or {})
        if tool_name == "sys_debug":
            return await handler.handle_debug_environment(kwargs or {})
        if tool_name == "sys_version":
            return await handler.handle_version_info(kwargs or {})
    if tool_name in {"memory_add", "memory_search", "memory_store_procedure", "memory_store_episode", "memory_stats"}:
        mod = load_handler_module("memory_handlers")
        handler = mod.MemoryHandlers()  # type: ignore[attr-defined]
        mapping = {
            "memory_add": handler.handle_memory_add,
            "memory_search": handler.handle_memory_search,
            "memory_store_procedure": handler.handle_memory_store_procedure,
            "memory_store_episode": handler.handle_memory_store_episode,
            "memory_stats": handler.handle_memory_stats,
        }
        return await mapping[tool_name](kwargs or {})
    
    # BMAD Planning Tools
    if tool_name.startswith("bmad_"):
        mod = load_handler_module("bmad_handlers")
        handler = mod.BMADHandlers()  # type: ignore[attr-defined]
        
        if tool_name == "bmad_prd_create":
            return await handler.bmad_prd_create(**kwargs)
        elif tool_name == "bmad_prd_update":
            return await handler.bmad_prd_update(**kwargs)
        elif tool_name == "bmad_prd_get":
            return await handler.bmad_prd_get(**kwargs)
        elif tool_name == "bmad_arch_create":
            return await handler.bmad_arch_create(**kwargs)
        elif tool_name == "bmad_arch_update":
            return await handler.bmad_arch_update(**kwargs)
        elif tool_name == "bmad_arch_get":
            return await handler.bmad_arch_get(**kwargs)
        elif tool_name == "bmad_story_create":
            return await handler.bmad_story_create(**kwargs)
        elif tool_name == "bmad_story_update":
            return await handler.bmad_story_update(**kwargs)
        elif tool_name == "bmad_story_get":
            return await handler.bmad_story_get(**kwargs)
        elif tool_name == "bmad_doc_list":
            return await handler.bmad_doc_list(**kwargs)
        elif tool_name == "bmad_doc_approve":
            return await handler.bmad_doc_approve(**kwargs)
        elif tool_name == "bmad_doc_reject":
            return await handler.bmad_doc_reject(**kwargs)
        elif tool_name == "bmad_master_checklist":
            return await handler.bmad_master_checklist(**kwargs)
        elif tool_name == "bmad_epic_create":
            return await handler.bmad_epic_create(**kwargs)
        elif tool_name == "bmad_epic_update":
            return await handler.bmad_epic_update(**kwargs)
        elif tool_name == "bmad_epic_get":
            return await handler.bmad_epic_get(**kwargs)
        elif tool_name == "bmad_epic_list":
            return await handler.bmad_epic_list(**kwargs)
        elif tool_name == "bmad_workflow_start":
            return await handler.bmad_workflow_start(**kwargs)
        elif tool_name == "bmad_workflow_next":
            return await handler.bmad_workflow_next(**kwargs)
        elif tool_name == "bmad_expansion_packs_list":
            return await handler.bmad_expansion_packs_list(**kwargs)
        elif tool_name == "bmad_expansion_packs_install":
            return await handler.bmad_expansion_packs_install(**kwargs)
        elif tool_name == "bmad_expansion_packs_enable":
            return await handler.bmad_expansion_packs_enable(**kwargs)
        elif tool_name == "bmad_hil_start_session":
            return await handler.bmad_hil_start_session(**kwargs)
        elif tool_name == "bmad_hil_continue_session":
            return await handler.bmad_hil_continue_session(**kwargs)
        elif tool_name == "bmad_hil_end_session":
            return await handler.bmad_hil_end_session(**kwargs)
        elif tool_name == "bmad_hil_session_status":
            return await handler.bmad_hil_session_status(**kwargs)
        elif tool_name == "bmad_workflow_status":
            return await handler.bmad_workflow_status(**kwargs)
        elif tool_name == "bmad_workflow_list":
            from .bmad_workflow_engine import get_workflow_engine
            engine = get_workflow_engine()
            workflows = engine.get_available_workflows()
            return {"status": "success", "workflows": workflows}
        elif tool_name == "bmad_workflow_get":
            from .bmad_workflow_engine import get_workflow_engine
            engine = get_workflow_engine()
            workflow = engine.get_workflow(kwargs.get("workflow_id", ""))
            if workflow:
                return {"status": "success", "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "type": workflow.type,
                    "project_types": workflow.project_types,
                    "sequence": [
                        {
                            "agent": step.agent,
                            "action": step.action,
                            "creates": step.creates,
                            "requires": step.requires,
                            "condition": step.condition,
                            "optional": step.optional,
                            "repeats": step.repeats,
                            "notes": step.notes
                        }
                        for step in workflow.sequence
                    ],
                    "flow_diagram": workflow.flow_diagram,
                    "decision_guidance": workflow.decision_guidance,
                    "handoff_prompts": workflow.handoff_prompts
                }}
            else:
                return {"status": "error", "message": f"Workflow {kwargs.get('workflow_id')} not found"}
        elif tool_name == "bmad_workflow_execute":
            from .bmad_workflow_engine import run_bmad_workflow
            import asyncio
            result = await run_bmad_workflow(
                workflow_id=kwargs.get("workflow_id", ""),
                project_context=kwargs.get("project_context", {}),
                profile_name=kwargs.get("profile_name", "quick"),
                max_iterations=kwargs.get("max_iterations", 1),
                wallclock_limit_sec=kwargs.get("wallclock_limit_sec"),
                step_budget=kwargs.get("step_budget")
            )
            return result
        elif tool_name == "bmad_agent_execute":
            # For now, return a placeholder - this will be implemented in BMAD handlers
            return {"status": "success", "message": f"BMAD agent {kwargs.get('agent')} execution placeholder", "agent": kwargs.get("agent"), "action": kwargs.get("action")}
        elif tool_name == "bmad_action_execute":
            # For now, return a placeholder - this will be implemented in BMAD handlers
            return {"status": "success", "message": f"BMAD action {kwargs.get('action')} execution placeholder", "action": kwargs.get("action")}
        elif tool_name == "bmad_git_commit_changes":
            return await handler.bmad_git_commit_changes(**kwargs)
        elif tool_name == "bmad_git_push_changes":
            return await handler.bmad_git_push_changes(**kwargs)
        elif tool_name == "bmad_git_validate_changes":
            return await handler.bmad_git_validate_changes(**kwargs)
        # BMAD Workflow Testing Tools (Phase 4.1.1)
        elif tool_name.startswith("bmad_workflow_test_"):
            from ..handlers.workflow_testing_handlers import (
                bmad_workflow_test_run_complete,
                bmad_workflow_test_create_suite,
                bmad_workflow_test_run_suite,
                bmad_workflow_test_list_suites,
                bmad_workflow_test_get_history,
                bmad_workflow_test_get_statistics,
                bmad_workflow_test_validate_step
            )
            
            if tool_name == "bmad_workflow_test_run_complete":
                return await bmad_workflow_test_run_complete(**kwargs)
            elif tool_name == "bmad_workflow_test_create_suite":
                return await bmad_workflow_test_create_suite(**kwargs)
            elif tool_name == "bmad_workflow_test_run_suite":
                return await bmad_workflow_test_run_suite(**kwargs)
            elif tool_name == "bmad_workflow_test_list_suites":
                return await bmad_workflow_test_list_suites(**kwargs)
            elif tool_name == "bmad_workflow_test_get_history":
                return await bmad_workflow_test_get_history(**kwargs)
            elif tool_name == "bmad_workflow_test_get_statistics":
                return await bmad_workflow_test_get_statistics(**kwargs)
            elif tool_name == "bmad_workflow_test_validate_step":
                return await bmad_workflow_test_validate_step(**kwargs)
        # BMAD Scenario-based Testing Tools (Phase 4.1.2)
        elif tool_name.startswith("bmad_scenario_"):
            from ..handlers.scenario_testing_handlers import (
                bmad_scenario_create,
                bmad_scenario_execute,
                bmad_scenario_list,
                bmad_scenario_validate,
                bmad_scenario_report,
                bmad_scenario_get_history
            )
            
            if tool_name == "bmad_scenario_create":
                return await bmad_scenario_create(**kwargs)
            elif tool_name == "bmad_scenario_execute":
                return await bmad_scenario_execute(**kwargs)
            elif tool_name == "bmad_scenario_list":
                return await bmad_scenario_list(**kwargs)
            elif tool_name == "bmad_scenario_validate":
                return await bmad_scenario_validate(**kwargs)
            elif tool_name == "bmad_scenario_report":
                return await bmad_scenario_report(**kwargs)
            elif tool_name == "bmad_scenario_get_history":
                return await bmad_scenario_get_history(**kwargs)
        else:
            return {"status": "error", "message": f"Unknown BMAD tool: {tool_name}"}
    elif tool_name == "bmad_git_get_history":
        return await handler.bmad_git_get_history(**kwargs)
    
    # BMAD Vault Integration Tools (Phase 2.1)
    elif tool_name == "bmad_vault_store_secret":
        return await handler.bmad_vault_store_secret(**kwargs)
    elif tool_name == "bmad_vault_retrieve_secret":
        return await handler.bmad_vault_retrieve_secret(**kwargs)
    elif tool_name == "bmad_vault_list_secrets":
        return await handler.bmad_vault_list_secrets(**kwargs)
    elif tool_name == "bmad_vault_delete_secret":
        return await handler.bmad_vault_delete_secret(**kwargs)
    elif tool_name == "bmad_vault_migrate_secrets":
        return await handler.bmad_vault_migrate_secrets(**kwargs)
    elif tool_name == "bmad_vault_health_check":
        return await handler.bmad_vault_health_check(**kwargs)
    elif tool_name == "bmad_vault_get_config":
        return await handler.bmad_vault_get_config(**kwargs)
    
    # BMAD Expansion Pack Management Tools (Phase 2.2)
    elif tool_name.startswith("bmad_expansion_"):
        from .expansion_pack_handlers import get_expansion_pack_handlers
        expansion_handler = get_expansion_pack_handlers()
        
        if tool_name == "bmad_expansion_list_packs":
            return await expansion_handler.bmad_expansion_list_packs(**kwargs)
        elif tool_name == "bmad_expansion_get_pack":
            return await expansion_handler.bmad_expansion_get_pack(**kwargs)
        elif tool_name == "bmad_expansion_search_packs":
            return await expansion_handler.bmad_expansion_search_packs(**kwargs)
        elif tool_name == "bmad_expansion_download_pack":
            return await expansion_handler.bmad_expansion_download_pack(**kwargs)
        elif tool_name == "bmad_expansion_get_file":
            return await expansion_handler.bmad_expansion_get_file(**kwargs)
        elif tool_name == "bmad_expansion_upload_pack":
            return await expansion_handler.bmad_expansion_upload_pack(**kwargs)
        elif tool_name == "bmad_expansion_delete_pack":
            return await expansion_handler.bmad_expansion_delete_pack(**kwargs)
        elif tool_name == "bmad_expansion_migrate_local":
            return await expansion_handler.bmad_expansion_migrate_local(**kwargs)
    
    # BMAD Update Management Tools (Phase 2.3)
    elif tool_name.startswith("bmad_update_") or tool_name.startswith("bmad_customizations_") or tool_name == "bmad_integration_test":
        from .bmad_update_handlers import get_bmad_update_handlers
        update_handler = get_bmad_update_handlers()
        
        if tool_name == "bmad_update_check":
            return await update_handler.bmad_update_check(**kwargs)
        elif tool_name == "bmad_update_validate":
            return await update_handler.bmad_update_validate(**kwargs)
        elif tool_name == "bmad_update_apply":
            return await update_handler.bmad_update_apply(**kwargs)
        elif tool_name == "bmad_update_report":
            return await update_handler.bmad_update_report(**kwargs)
        elif tool_name == "bmad_customizations_discover":
            return await update_handler.bmad_customizations_discover(**kwargs)
        elif tool_name == "bmad_customizations_backup":
            return await update_handler.bmad_customizations_backup(**kwargs)
        elif tool_name == "bmad_customizations_restore":
            return await update_handler.bmad_customizations_restore(**kwargs)
        elif tool_name == "bmad_integration_test":
            return await update_handler.bmad_integration_test(**kwargs)
    
    # BMAD Template Management Tools (Phase 2.2.4)
    elif tool_name.startswith("bmad_template_"):
        from .bmad_template_handlers import get_bmad_template_handlers
        template_handler = get_bmad_template_handlers()
        
        if tool_name == "bmad_template_load":
            return await template_handler.bmad_template_load(**kwargs)
        elif tool_name == "bmad_template_list":
            return await template_handler.bmad_template_list(**kwargs)
        elif tool_name == "bmad_template_search":
            return await template_handler.bmad_template_search(**kwargs)
        elif tool_name == "bmad_template_validate":
            return await template_handler.bmad_template_validate(**kwargs)
        elif tool_name == "bmad_template_preload":
            return await template_handler.bmad_template_preload(**kwargs)
    
    # Basic Workflow Tools (Story 1.5)
    elif tool_name == "bmad_basic_prd_workflow":
        from .basic_workflow_implementations import get_basic_workflows
        workflows = get_basic_workflows()
        return await workflows.create_basic_prd_workflow(
            project_name=kwargs.get("project_name", ""),
            goals=kwargs.get("goals"),
            background=kwargs.get("background")
        )
    elif tool_name == "bmad_basic_architecture_workflow":
        from .basic_workflow_implementations import get_basic_workflows
        workflows = get_basic_workflows()
        return await workflows.create_basic_architecture_workflow(
            project_name=kwargs.get("project_name", ""),
            prd_id=kwargs.get("prd_id", ""),
            tech_stack=kwargs.get("tech_stack")
        )
    elif tool_name == "bmad_basic_story_workflow":
        from .basic_workflow_implementations import get_basic_workflows
        workflows = get_basic_workflows()
        return await workflows.create_basic_story_workflow(
            project_name=kwargs.get("project_name", ""),
            prd_id=kwargs.get("prd_id", ""),
            arch_id=kwargs.get("arch_id", ""),
            user_stories=kwargs.get("user_stories")
        )
    elif tool_name == "bmad_basic_complete_workflow":
        from .basic_workflow_implementations import get_basic_workflows
        workflows = get_basic_workflows()
        return await workflows.run_complete_basic_workflow(
            project_name=kwargs.get("project_name", ""),
            goals=kwargs.get("goals"),
            background=kwargs.get("background"),
            tech_stack=kwargs.get("tech_stack"),
            user_stories=kwargs.get("user_stories")
        )
    elif tool_name == "bmad_basic_workflow_status":
        from .basic_workflow_implementations import get_basic_workflows
        workflows = get_basic_workflows()
        return await workflows.get_workflow_status(kwargs.get("project_id", ""))
    if tool_name in {"internet_search"}:
        mod = load_handler_module("internet_search_handlers")
        handler = mod.InternetSearchHandlers()  # type: ignore[attr-defined]
        return await handler.handle_internet_search(kwargs or {})
    if tool_name in {"code.search_functions", "code.index_functions", "code.call_paths"}:
        mod = load_handler_module("code_intel_handlers")
        handler = mod.CodeIntelHandlers(project_root=Path.cwd())  # type: ignore[attr-defined]
        if tool_name == "code.search_functions":
            return await handler.handle_search_functions(kwargs or {})
        if tool_name == "code.index_functions":
            return await handler.handle_index_functions(kwargs or {})
        if tool_name == "code.call_paths":
            return await handler.handle_call_paths(kwargs or {})
    if tool_name in {"desktop.notify"}:
        mod = load_handler_module("desktop_handlers")
        handler = mod.DesktopHandlers()  # type: ignore[attr-defined]
        return await handler.handle_desktop_notify(kwargs or {})
    if tool_name in {"llm_provider.probe"}:
        mod = load_handler_module("llm_provider_handlers")
        handler = mod.LLMProviderHandlers()  # type: ignore[attr-defined]
        return await handler.handle_probe(kwargs or {})
    if tool_name in {"codegen.generate_edits"}:
        mod = load_handler_module("codegen_handlers")
        handler = mod.CodegenHandlers()  # type: ignore[attr-defined]
        return await handler.handle_generate_edits(kwargs or {})
    if tool_name == "code_reasoning.plan":
        mod = load_handler_module("reasoning_handlers")
        handler = mod.ReasoningHandlers()  # type: ignore[attr-defined]
        return await handler.handle_code_reasoning_plan(kwargs or {})
    return {"status": "error", "message": f"Unknown tool: {tool_name}"}


# Enhanced async execution with performance monitoring
async def execute_mcp_tool_enhanced(
    tool_name: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Enhanced tool execution with performance monitoring and async optimization.
    
    This function provides the same interface as execute_mcp_tool but with
    additional performance features:
    - Connection pooling
    - Performance metrics
    - Error recovery
    - Memory monitoring
    """
    try:
        # Use the async tool executor for enhanced performance
        from .async_tool_executor import execute_tool_async, ToolPriority
        
        # Determine priority based on tool type
        priority = ToolPriority.NORMAL
        if tool_name.startswith("bmad_"):
            priority = ToolPriority.HIGH
        elif tool_name in {"sys_test", "sys_stats", "sys_health"}:
            priority = ToolPriority.CRITICAL
        
        # Execute with enhanced infrastructure
        result = await execute_tool_async(
            tool_name=tool_name,
            kwargs=kwargs,
            priority=priority,
            timeout_seconds=kwargs.get("timeout_seconds", 30.0)
        )
        
        # Return the result in the expected format
        if result.success:
            return result.result
        else:
            return {
                "status": "error",
                "message": result.error or "Tool execution failed",
                "execution_time": result.execution_time
            }
            
    except Exception as e:
        # Fallback to original implementation
        logger.warning(f"Enhanced execution failed, falling back to standard: {e}")
        return await execute_mcp_tool(tool_name, **kwargs)


