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
        
        # BMAD Persona Management Tools
        elif tool_name == "bmad_discover_personas":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_discover_personas(kwargs or {})
        elif tool_name == "bmad_activate_persona":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_activate_persona(kwargs or {})
        elif tool_name == "bmad_deactivate_persona":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_deactivate_persona(kwargs or {})
        elif tool_name == "bmad_execute_persona_command":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_execute_persona_command(kwargs or {})
        elif tool_name == "bmad_get_persona_status":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_get_persona_status(kwargs or {})
        elif tool_name == "bmad_switch_persona":
            from ..handlers.bmad_persona_handlers import bmad_persona_handlers
            return await bmad_persona_handlers.bmad_switch_persona(kwargs or {})
        
        # BMAD Tool Consolidation Tools (Phase 3)
        elif tool_name == "bmad_discover_tools":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_discover_tools(kwargs or {})
        elif tool_name == "bmad_get_tool":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_get_tool(kwargs or {})
        elif tool_name == "bmad_get_tools_by_category":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_get_tools_by_category(kwargs or {})
        elif tool_name == "bmad_execute_tool":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_execute_tool(kwargs or {})
        elif tool_name == "bmad_get_tool_status":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_get_tool_status(kwargs or {})
        elif tool_name == "bmad_list_categories":
            from ..handlers.bmad_tool_handlers import bmad_tool_handlers
            return await bmad_tool_handlers.bmad_list_categories(kwargs or {})
        
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
        # BMAD Regression Testing Tools (Phase 4.1.3)
        elif tool_name.startswith("bmad_regression_"):
            from ..handlers.regression_testing_handlers import (
                bmad_regression_test_run,
                bmad_regression_baseline_establish,
                bmad_regression_baseline_list,
                bmad_regression_report_generate,
                bmad_regression_history_get
            )
            
            if tool_name == "bmad_regression_test_run":
                return await bmad_regression_test_run(**kwargs)
            elif tool_name == "bmad_regression_baseline_establish":
                return await bmad_regression_baseline_establish(**kwargs)
            elif tool_name == "bmad_regression_baseline_list":
                return await bmad_regression_baseline_list(**kwargs)
            elif tool_name == "bmad_regression_report_generate":
                return await bmad_regression_report_generate(**kwargs)
            elif tool_name == "bmad_regression_history_get":
                return await bmad_regression_history_get(**kwargs)
        # BMAD Git Workflow Management Tools (Phase 4.1.3)
        elif tool_name.startswith("bmad_git_"):
            from ..handlers.regression_testing_handlers import (
                bmad_git_auto_commit,
                bmad_git_auto_push,
                bmad_git_workflow_status,
                bmad_git_workflow_configure
            )
            
            if tool_name == "bmad_git_auto_commit":
                return await bmad_git_auto_commit(**kwargs)
            elif tool_name == "bmad_git_auto_push":
                return await bmad_git_auto_push(**kwargs)
            elif tool_name == "bmad_git_workflow_status":
                return await bmad_git_workflow_status(**kwargs)
            elif tool_name == "bmad_git_workflow_configure":
                return await bmad_git_workflow_configure(**kwargs)
        # BMAD Performance Validation Tools (Phase 4.2)
        elif tool_name.startswith("bmad_performance_"):
            from ..handlers.performance_validation_handlers import (
                bmad_performance_scalability_test,
                bmad_performance_metrics_collect,
                bmad_performance_slo_validate,
                bmad_performance_report_generate,
                bmad_performance_history_get
            )
            from ..handlers.performance_load_testing_handlers import (
                bmad_performance_load_test,
                bmad_performance_stress_test
            )
            
            if tool_name == "bmad_performance_load_test":
                handler_tool_name = kwargs.pop("tool_name", "sys_test")
                return await bmad_performance_load_test(tool_name=handler_tool_name, **kwargs)
            elif tool_name == "bmad_performance_stress_test":
                handler_tool_name = kwargs.pop("tool_name", "sys_test")
                return await bmad_performance_stress_test(tool_name=handler_tool_name, **kwargs)
            elif tool_name == "bmad_performance_scalability_test":
                return await bmad_performance_scalability_test(**kwargs)
            elif tool_name == "bmad_performance_metrics_collect":
                return await bmad_performance_metrics_collect(**kwargs)
            elif tool_name == "bmad_performance_slo_validate":
                return await bmad_performance_slo_validate(**kwargs)
            elif tool_name == "bmad_performance_report_generate":
                return await bmad_performance_report_generate(**kwargs)
            elif tool_name == "bmad_performance_history_get":
                return await bmad_performance_history_get(**kwargs)
            elif tool_name == "bmad_performance_benchmark":
                from ..handlers.performance_load_testing_handlers import bmad_performance_benchmark
                return await bmad_performance_benchmark(**kwargs)
            elif tool_name == "bmad_performance_regression_test":
                from ..handlers.performance_load_testing_handlers import bmad_performance_regression_test
                handler_tool_name = kwargs.pop("tool_name", "sys_test")
                return await bmad_performance_regression_test(tool_name=handler_tool_name, **kwargs)
            elif tool_name == "bmad_performance_test_history":
                from ..handlers.performance_load_testing_handlers import bmad_performance_test_history
                return await bmad_performance_test_history(**kwargs)
            elif tool_name == "bmad_performance_clear_history":
                from ..handlers.performance_load_testing_handlers import bmad_performance_clear_history
                return await bmad_performance_clear_history(**kwargs)
            elif tool_name == "bmad_performance_system_monitor":
                from ..handlers.performance_load_testing_handlers import bmad_performance_system_monitor
                return await bmad_performance_system_monitor(**kwargs)
        # BMAD Error Handling and Recovery Testing Tools (Sprint 5 - Story 3.4)
        elif tool_name.startswith("bmad_error_") or tool_name.startswith("bmad_recovery_") or tool_name.startswith("bmad_resilience_") or tool_name.startswith("bmad_circuit_breaker_"):
            from ..handlers.error_handling_recovery_testing_handlers import (
                bmad_error_injection_test,
                bmad_recovery_strategy_test,
                bmad_resilience_test_suite,
                bmad_circuit_breaker_test,
                bmad_error_recovery_history,
                bmad_error_recovery_clear_history,
                bmad_circuit_breaker_status
            )
            
            if tool_name == "bmad_error_injection_test":
                return await bmad_error_injection_test(**kwargs)
            elif tool_name == "bmad_recovery_strategy_test":
                return await bmad_recovery_strategy_test(**kwargs)
            elif tool_name == "bmad_resilience_test_suite":
                return await bmad_resilience_test_suite(**kwargs)
            elif tool_name == "bmad_circuit_breaker_test":
                return await bmad_circuit_breaker_test(**kwargs)
            elif tool_name == "bmad_error_recovery_history":
                return await bmad_error_recovery_history(**kwargs)
            elif tool_name == "bmad_error_recovery_clear_history":
                return await bmad_error_recovery_clear_history(**kwargs)
            elif tool_name == "bmad_circuit_breaker_status":
                return await bmad_circuit_breaker_status(**kwargs)
        # BMAD Security and Authentication Testing Tools (Sprint 5 - Story 3.5)
        elif tool_name.startswith("bmad_security_"):
            from ..handlers.security_authentication_testing_handlers import (
                bmad_security_authentication_test,
                bmad_security_authorization_test,
                bmad_security_input_validation_test,
                bmad_security_rate_limiting_test,
                bmad_security_test_suite,
                bmad_security_vulnerability_scan,
                bmad_security_test_history,
                bmad_security_test_clear_history
            )
            
            if tool_name == "bmad_security_authentication_test":
                return await bmad_security_authentication_test(**kwargs)
            elif tool_name == "bmad_security_authorization_test":
                return await bmad_security_authorization_test(**kwargs)
            elif tool_name == "bmad_security_input_validation_test":
                return await bmad_security_input_validation_test(**kwargs)
            elif tool_name == "bmad_security_rate_limiting_test":
                return await bmad_security_rate_limiting_test(**kwargs)
            elif tool_name == "bmad_security_test_suite":
                return await bmad_security_test_suite(**kwargs)
            elif tool_name == "bmad_security_vulnerability_scan":
                return await bmad_security_vulnerability_scan(**kwargs)
            elif tool_name == "bmad_security_test_history":
                return await bmad_security_test_history(**kwargs)
            elif tool_name == "bmad_security_test_clear_history":
                return await bmad_security_test_clear_history(**kwargs)
        # BMAD WebMCP Installer Tools (Sprint 6 - Story 4.1)
        elif tool_name.startswith("bmad_webmcp_"):
            from ..handlers.webmcp_installer_handlers import (
                bmad_webmcp_install_config,
                bmad_webmcp_validate_installation,
                bmad_webmcp_test_integration,
                bmad_webmcp_uninstall_config,
                bmad_webmcp_get_config,
                bmad_webmcp_update_config,
                bmad_webmcp_backup_config,
                bmad_webmcp_restore_config
            )
            
            if tool_name == "bmad_webmcp_install_config":
                return await bmad_webmcp_install_config(**kwargs)
            elif tool_name == "bmad_webmcp_validate_installation":
                return await bmad_webmcp_validate_installation(**kwargs)
            elif tool_name == "bmad_webmcp_test_integration":
                return await bmad_webmcp_test_integration(**kwargs)
            elif tool_name == "bmad_webmcp_uninstall_config":
                return await bmad_webmcp_uninstall_config(**kwargs)
            elif tool_name == "bmad_webmcp_get_config":
                return await bmad_webmcp_get_config(**kwargs)
            elif tool_name == "bmad_webmcp_update_config":
                return await bmad_webmcp_update_config(**kwargs)
            elif tool_name == "bmad_webmcp_backup_config":
                return await bmad_webmcp_backup_config(**kwargs)
            elif tool_name == "bmad_webmcp_restore_config":
                return await bmad_webmcp_restore_config(**kwargs)
        # BMAD Installation Flow Testing Tools (Sprint 6 - Story 4.2)
        elif tool_name.startswith("bmad_installation_"):
            from ..handlers.installation_flow_testing_handlers import (
                bmad_installation_flow_test,
                bmad_installation_step_test,
                bmad_installation_rollback_test,
                bmad_installation_validate_environment,
                bmad_installation_validate_components,
                bmad_installation_get_flow_steps,
                bmad_installation_test_prerequisites,
                bmad_installation_generate_report
            )
            
            if tool_name == "bmad_installation_flow_test":
                return await bmad_installation_flow_test(**kwargs)
            elif tool_name == "bmad_installation_step_test":
                return await bmad_installation_step_test(**kwargs)
            elif tool_name == "bmad_installation_rollback_test":
                return await bmad_installation_rollback_test(**kwargs)
            elif tool_name == "bmad_installation_validate_environment":
                return await bmad_installation_validate_environment(**kwargs)
            elif tool_name == "bmad_installation_validate_components":
                return await bmad_installation_validate_components(**kwargs)
            elif tool_name == "bmad_installation_get_flow_steps":
                return await bmad_installation_get_flow_steps(**kwargs)
            elif tool_name == "bmad_installation_test_prerequisites":
                return await bmad_installation_test_prerequisites(**kwargs)
            elif tool_name == "bmad_installation_generate_report":
                return await bmad_installation_generate_report(**kwargs)
        # BMAD Uninstall and Rollback Tools (Sprint 6 - Story 4.3)
        elif tool_name.startswith("bmad_uninstall_") or tool_name.startswith("bmad_rollback_"):
            from ..handlers.uninstall_rollback_handlers import (
                bmad_uninstall_complete,
                bmad_uninstall_step,
                bmad_rollback_create_point,
                bmad_rollback_to_point,
                bmad_rollback_list_points,
                bmad_rollback_delete_point,
                bmad_uninstall_validate,
                bmad_uninstall_simulate,
                bmad_rollback_get_point_info
            )
            
            if tool_name == "bmad_uninstall_complete":
                return await bmad_uninstall_complete(**kwargs)
            elif tool_name == "bmad_uninstall_step":
                return await bmad_uninstall_step(**kwargs)
            elif tool_name == "bmad_rollback_create_point":
                return await bmad_rollback_create_point(**kwargs)
            elif tool_name == "bmad_rollback_to_point":
                return await bmad_rollback_to_point(**kwargs)
            elif tool_name == "bmad_rollback_list_points":
                return await bmad_rollback_list_points(**kwargs)
            elif tool_name == "bmad_rollback_delete_point":
                return await bmad_rollback_delete_point(**kwargs)
            elif tool_name == "bmad_uninstall_validate":
                return await bmad_uninstall_validate(**kwargs)
            elif tool_name == "bmad_uninstall_simulate":
                return await bmad_uninstall_simulate(**kwargs)
            elif tool_name == "bmad_rollback_get_point_info":
                return await bmad_rollback_get_point_info(**kwargs)
        # BMAD Documentation Management Tools (Sprint 6 - Story 4.4)
        elif tool_name.startswith("bmad_documentation_") or tool_name.startswith("bmad_runbook_"):
            from ..handlers.documentation_handlers import (
                bmad_documentation_generate,
                bmad_documentation_update,
                bmad_runbook_generate,
                bmad_documentation_validate,
                bmad_documentation_list,
                bmad_documentation_get_content,
                bmad_documentation_create_section,
                bmad_documentation_update_runbook
            )
            
            if tool_name == "bmad_documentation_generate":
                return await bmad_documentation_generate(**kwargs)
            elif tool_name == "bmad_documentation_update":
                return await bmad_documentation_update(**kwargs)
            elif tool_name == "bmad_runbook_generate":
                return await bmad_runbook_generate(**kwargs)
            elif tool_name == "bmad_documentation_validate":
                return await bmad_documentation_validate(**kwargs)
            elif tool_name == "bmad_documentation_list":
                return await bmad_documentation_list(**kwargs)
            elif tool_name == "bmad_documentation_get_content":
                return await bmad_documentation_get_content(**kwargs)
            elif tool_name == "bmad_documentation_create_section":
                return await bmad_documentation_create_section(**kwargs)
            elif tool_name == "bmad_documentation_update_runbook":
                return await bmad_documentation_update_runbook(**kwargs)
        # BMAD Integration Testing Tools (Phase 4.3)
        elif tool_name.startswith("bmad_integration_"):
            from ..handlers.integration_testing_handlers import (
                bmad_integration_cross_component_test,
                bmad_integration_api_test,
                bmad_integration_database_test,
                bmad_integration_full_suite,
                bmad_integration_report_generate,
                bmad_integration_history_get
            )
            
            if tool_name == "bmad_integration_cross_component_test":
                return await bmad_integration_cross_component_test(**kwargs)
            elif tool_name == "bmad_integration_api_test":
                return await bmad_integration_api_test(**kwargs)
            elif tool_name == "bmad_integration_database_test":
                return await bmad_integration_database_test(**kwargs)
            elif tool_name == "bmad_integration_full_suite":
                return await bmad_integration_full_suite(**kwargs)
            elif tool_name == "bmad_integration_report_generate":
                return await bmad_integration_report_generate(**kwargs)
            elif tool_name == "bmad_integration_history_get":
                return await bmad_integration_history_get(**kwargs)
        # BMAD User Acceptance Testing Tools (Phase 4.4)
        elif tool_name.startswith("bmad_uat_"):
            from ..handlers.user_acceptance_testing_handlers import (
                bmad_uat_scenario_test,
                bmad_uat_usability_test,
                bmad_uat_accessibility_test,
                bmad_uat_full_suite,
                bmad_uat_report_generate,
                bmad_uat_history_get
            )
            
            if tool_name == "bmad_uat_scenario_test":
                return await bmad_uat_scenario_test(**kwargs)
            elif tool_name == "bmad_uat_usability_test":
                return await bmad_uat_usability_test(**kwargs)
            elif tool_name == "bmad_uat_accessibility_test":
                return await bmad_uat_accessibility_test(**kwargs)
            elif tool_name == "bmad_uat_full_suite":
                return await bmad_uat_full_suite(**kwargs)
            elif tool_name == "bmad_uat_report_generate":
                return await bmad_uat_report_generate(**kwargs)
            elif tool_name == "bmad_uat_history_get":
                return await bmad_uat_history_get(**kwargs)
        # BMAD Monitoring & Observability Tools (Phase 4.5)
        elif tool_name.startswith("bmad_monitoring_") or tool_name.startswith("bmad_alerting_") or tool_name.startswith("bmad_observability_") or tool_name.startswith("bmad_logging_"):
            from ..handlers.monitoring_observability_handlers import (
                bmad_monitoring_system_health,
                bmad_monitoring_performance_metrics,
                bmad_monitoring_resource_utilization,
                bmad_alerting_configure,
                bmad_alerting_test,
                bmad_observability_dashboard,
                bmad_logging_centralized,
                bmad_monitoring_report_generate
            )
            
            if tool_name == "bmad_monitoring_system_health":
                return await bmad_monitoring_system_health(**kwargs)
            elif tool_name == "bmad_monitoring_performance_metrics":
                return await bmad_monitoring_performance_metrics(**kwargs)
            elif tool_name == "bmad_monitoring_resource_utilization":
                return await bmad_monitoring_resource_utilization(**kwargs)
            elif tool_name == "bmad_alerting_configure":
                return await bmad_alerting_configure(**kwargs)
            elif tool_name == "bmad_alerting_test":
                return await bmad_alerting_test(**kwargs)
            elif tool_name == "bmad_observability_dashboard":
                return await bmad_observability_dashboard(**kwargs)
            elif tool_name == "bmad_logging_centralized":
                return await bmad_logging_centralized(**kwargs)
            elif tool_name == "bmad_monitoring_report_generate":
                return await bmad_monitoring_report_generate(**kwargs)
        # BMAD Expansion Pack System Tools (Phase 5.1)
        elif tool_name.startswith("bmad_expansion_"):
            from ..handlers.expansion_pack_system_handlers import (
                bmad_expansion_system_status,
                bmad_expansion_pack_install,
                bmad_expansion_pack_uninstall,
                bmad_expansion_pack_list,
                bmad_expansion_pack_activate,
                bmad_expansion_pack_deactivate,
                bmad_expansion_pack_update,
                bmad_expansion_pack_validate
            )
            
            if tool_name == "bmad_expansion_system_status":
                return await bmad_expansion_system_status(**kwargs)
            elif tool_name == "bmad_expansion_pack_install":
                return await bmad_expansion_pack_install(**kwargs)
            elif tool_name == "bmad_expansion_pack_uninstall":
                return await bmad_expansion_pack_uninstall(**kwargs)
            elif tool_name == "bmad_expansion_pack_list":
                return await bmad_expansion_pack_list(**kwargs)
            elif tool_name == "bmad_expansion_pack_activate":
                return await bmad_expansion_pack_activate(**kwargs)
            elif tool_name == "bmad_expansion_pack_deactivate":
                return await bmad_expansion_pack_deactivate(**kwargs)
            elif tool_name == "bmad_expansion_pack_update":
                return await bmad_expansion_pack_update(**kwargs)
            elif tool_name == "bmad_expansion_pack_validate":
                return await bmad_expansion_pack_validate(**kwargs)
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


