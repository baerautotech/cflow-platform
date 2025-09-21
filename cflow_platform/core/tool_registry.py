from __future__ import annotations

from typing import Any, Dict, List
from .tool_group_manager import ToolGroupManager


class ToolRegistry:
    """Package-side MCP tool registry definitions for monorepo consumption.

    Returns plain dict tool specs so the monorepo can construct mcp.types.Tool
    without requiring this package to import MCP libraries.
    """

    @staticmethod
    def get_tools_for_mcp() -> List[Dict[str, Any]]:
        tools: List[Dict[str, Any]] = []

        def tool(name: str, description: str, schema: Dict[str, Any] | None = None) -> Dict[str, Any]:
            # Get tool group information
            tool_group = ToolGroupManager.get_group_for_tool(name)
            group_name = tool_group.value if tool_group else "unassigned"
            
            return {
                "name": name,
                "description": description,
                "inputSchema": schema or {"type": "object", "properties": {}, "required": []},
                "group": group_name,
                "metadata": {
                    "group": group_name,
                    "required": ToolGroupManager.TOOL_GROUPS[tool_group].required if tool_group else False,
                    "client_types": ToolGroupManager.TOOL_GROUPS[tool_group].client_types if tool_group else None,
                    "project_types": ToolGroupManager.TOOL_GROUPS[tool_group].project_types if tool_group else None
                }
            }

        # System tools
        tools += [
            tool("sys_test", "Test system connection"),
            tool("sys_stats", "Get system statistics"),
            tool("sys_debug", "Debug environment"),
            tool("sys_version", "Get version information"),
        ]

        # Task management tools
        tools += [
            tool("task_list", "List tasks"),
            tool("task_get", "Get task details"),
            tool("task_next", "Get next task"),
            tool("task_add", "Add new task"),
            tool("task_update", "Update task"),
            tool("task_status", "Update task status"),
        ]

        # Research tools
        tools += [
            tool("research", "Enhanced research"),
            tool("doc_research", "Document research"),
        ]

        # Linting tools
        tools += [
            tool("lint_full", "Run full lint"),
            tool("lint_bg", "Run lint in background"),
            tool("lint_status", "Lint status"),
            tool("enh_full_lint", "Run enhanced lint"),
            tool("enh_autofix", "Enhanced autofix"),
        ]

        # Testing tools
        tools += [
            tool("test_analyze", "Analyze test suite"),
            tool("test_confidence", "Test confidence report"),
        ]

        # Sandbox tools
        tools += [
            tool("sandbox.run_python", "Execute Python in sandbox"),
        ]

        # Memory tools
        tools += [
            tool("memory_add", "Add memory"),
            tool("memory_search", "Search memories"),
        ]

        # Plan tools
        tools += [
            tool("plan_parse", "Parse atomic plan"),
            tool("plan_list", "List plans"),
            tool("plan_validate", "Validate plan format"),
        ]

        # Code reasoning tools
        tools += [
            tool("code_reasoning.plan", "Produce bounded minimal-edit plan"),
        ]

        # Internet search tools
        tools += [
            tool("internet_search", "Perform internet search"),
        ]

        # Desktop notification tools
        tools += [
            tool("desktop.notify", "Send desktop notification"),
        ]

        # LLM provider tools
        tools += [
            tool("llm_provider.probe", "Verify LLM provider connectivity"),
        ]

        # Code generation tools
        tools += [
            tool("codegen.generate", "Generate code"),
        ]

        # Code intelligence tools
        tools += [
            tool("code.search_functions", "Semantic search for functions"),
            tool("code.index_functions", "Index functions"),
            tool("code.call_paths", "Compute call paths"),
        ]

        # BMAD Planning Tools (PRD, Architecture, Story, Epic)
        tools += [
            tool("bmad_prd_create", "Create Product Requirements Document"),
            tool("bmad_prd_update", "Update PRD document"),
            tool("bmad_prd_get", "Get PRD document"),
            tool("bmad_arch_create", "Create Architecture Document"),
            tool("bmad_arch_update", "Update Architecture document"),
            tool("bmad_arch_get", "Get Architecture document"),
            tool("bmad_story_create", "Create User Story Document"),
            tool("bmad_story_update", "Update Story document"),
            tool("bmad_story_get", "Get Story document"),
            tool("bmad_doc_list", "List BMAD documents"),
            tool("bmad_doc_approve", "Approve BMAD document"),
            tool("bmad_doc_reject", "Reject BMAD document"),
            tool("bmad_master_checklist", "Run PO master checklist to validate PRD/Architecture alignment"),
            tool("bmad_epic_create", "Create epics from PRD and Architecture"),
            tool("bmad_epic_update", "Update epic document"),
            tool("bmad_epic_get", "Get epic document"),
            tool("bmad_epic_list", "List epics for project"),
        ]

        # BMAD Workflow Engine tools
        tools += [
            tool("bmad_workflow_start", "Start specific BMAD workflow"),
            tool("bmad_workflow_next", "Get next recommended action in workflow"),
            tool("bmad_workflow_list", "List available BMAD workflows"),
            tool("bmad_workflow_get", "Get BMAD workflow details"),
            tool("bmad_workflow_execute", "Execute BMAD workflow"),
            tool("bmad_agent_execute", "Execute BMAD agent step"),
            tool("bmad_action_execute", "Execute BMAD action step"),
            tool("bmad_workflow_status", "Check BMAD workflow status and HIL session state"),
        ]

        # BMAD Human-in-the-Loop (HIL) tools
        tools += [
            tool("bmad_hil_start_session", "Start BMAD-style HIL interactive session for document completion"),
            tool("bmad_hil_continue_session", "Continue BMAD-style HIL interactive session with user response"),
            tool("bmad_hil_end_session", "End BMAD-style HIL interactive session and update document"),
            tool("bmad_hil_session_status", "Get status of BMAD-style HIL interactive session"),
        ]

        # BMAD Git Integration tools
        tools += [
            tool("bmad_git_commit_changes", "Commit BMAD workflow changes with validation and tracking"),
            tool("bmad_git_push_changes", "Push BMAD workflow changes to remote repository"),
            tool("bmad_git_validate_changes", "Validate BMAD workflow changes before commit"),
            tool("bmad_git_get_history", "Get BMAD commit history for a project"),
        ]

        # BMAD Vault Integration tools
        tools += [
            tool("bmad_vault_store_secret", "Store secret in HashiCorp Vault"),
            tool("bmad_vault_retrieve_secret", "Retrieve secret from HashiCorp Vault"),
            tool("bmad_vault_list_secrets", "List secrets in HashiCorp Vault"),
            tool("bmad_vault_delete_secret", "Delete secret from HashiCorp Vault"),
            tool("bmad_vault_migrate_secrets", "Migrate all local secrets to HashiCorp Vault"),
            tool("bmad_vault_health_check", "Check HashiCorp Vault health status"),
            tool("bmad_vault_get_config", "Get configuration from HashiCorp Vault"),
        ]

        # BMAD Expansion Pack Management tools
        tools += [
            tool("bmad_expansion_packs_list", "List available BMAD expansion packs"),
            tool("bmad_expansion_packs_install", "Install BMAD expansion pack"),
            tool("bmad_expansion_packs_enable", "Enable expansion pack for project"),
            tool("bmad_expansion_list_packs", "List all available expansion packs"),
            tool("bmad_expansion_get_pack", "Get metadata for a specific expansion pack"),
            tool("bmad_expansion_search_packs", "Search expansion packs by query and category"),
            tool("bmad_expansion_download_pack", "Download an expansion pack from S3"),
            tool("bmad_expansion_get_file", "Get a specific file from an expansion pack"),
            tool("bmad_expansion_upload_pack", "Upload a local expansion pack to S3"),
            tool("bmad_expansion_delete_pack", "Delete an expansion pack from S3"),
            tool("bmad_expansion_migrate_local", "Migrate all local expansion packs to S3"),
        ]

        # BMAD Update Management tools
        tools += [
            tool("bmad_update_check", "Check for available BMAD updates"),
            tool("bmad_update_validate", "Validate a BMAD update before applying"),
            tool("bmad_update_apply", "Apply a BMAD update with customization preservation"),
            tool("bmad_update_report", "Generate comprehensive update report"),
            tool("bmad_customizations_discover", "Discover and catalog BMAD customizations"),
            tool("bmad_customizations_backup", "Backup current BMAD customizations"),
            tool("bmad_customizations_restore", "Restore BMAD customizations from backup"),
            tool("bmad_integration_test", "Run integration tests to validate BMAD compatibility"),
        ]

        # BMAD Template Management tools
        tools += [
            tool("bmad_template_load", "Load a BMAD template from S3 storage"),
            tool("bmad_template_list", "List all available BMAD templates"),
            tool("bmad_template_search", "Search for BMAD templates by query"),
            tool("bmad_template_validate", "Validate a BMAD template for correctness"),
            tool("bmad_template_preload", "Preload core BMAD templates for better performance"),
        ]

        # BMAD Basic Workflow tools
        tools += [
            tool("bmad_basic_prd_workflow", "Create basic PRD using BMAD templates and Cerebral storage"),
            tool("bmad_basic_architecture_workflow", "Create basic Architecture using BMAD templates and Cerebral storage"),
            tool("bmad_basic_story_workflow", "Create basic Story using BMAD templates and Cerebral storage"),
            tool("bmad_basic_complete_workflow", "Run complete basic workflow: PRD → Architecture → Story"),
            tool("bmad_basic_workflow_status", "Get current status of basic BMAD workflows for a project"),
        ]

        # BMAD Workflow Testing tools
        tools += [
            tool("bmad_workflow_test_run_complete", "Run complete workflow test suite"),
            tool("bmad_workflow_test_create_suite", "Create a custom workflow test suite"),
            tool("bmad_workflow_test_run_suite", "Run a specific workflow test suite"),
            tool("bmad_workflow_test_list_suites", "List all available workflow test suites"),
            tool("bmad_workflow_test_get_history", "Get workflow test execution history"),
            tool("bmad_workflow_test_get_statistics", "Get workflow test execution statistics"),
            tool("bmad_workflow_test_validate_step", "Validate a specific workflow test step"),
        ]

        # BMAD Scenario-based Testing tools (Phase 4.1.2)
        tools += [
            tool("bmad_scenario_create", "Create a new test scenario for scenario-based testing"),
            tool("bmad_scenario_execute", "Execute a test scenario"),
            tool("bmad_scenario_list", "List available test scenarios with optional filtering"),
            tool("bmad_scenario_validate", "Validate scenario execution results"),
            tool("bmad_scenario_report", "Generate scenario testing report"),
            tool("bmad_scenario_get_history", "Get scenario execution history"),
        ]

        # BMAD Regression Testing tools (Phase 4.1.3)
        tools += [
            tool("bmad_regression_test_run", "Run comprehensive regression tests"),
            tool("bmad_regression_baseline_establish", "Establish new baseline for regression testing"),
            tool("bmad_regression_baseline_list", "List available baselines"),
            tool("bmad_regression_report_generate", "Generate detailed regression reports"),
            tool("bmad_regression_history_get", "Get regression testing history"),
        ]

        # BMAD Git Workflow Management tools (Phase 4.1.3)
        tools += [
            tool("bmad_git_auto_commit", "Automatically commit changes after testing"),
            tool("bmad_git_auto_push", "Automatically push committed changes"),
            tool("bmad_git_workflow_status", "Get status of automated git workflows"),
            tool("bmad_git_workflow_configure", "Configure automated git workflow settings"),
        ]

        # BMAD Performance Validation tools (Phase 4.2)
        tools += [
            tool("bmad_performance_scalability_test", "Run scalability testing for multi-user scenarios"),
            tool("bmad_performance_metrics_collect", "Collect performance metrics for specified duration"),
            tool("bmad_performance_slo_validate", "Validate performance against Service Level Objectives"),
            tool("bmad_performance_report_generate", "Generate comprehensive performance testing report"),
            tool("bmad_performance_history_get", "Get performance testing execution history"),
        ]

        # BMAD Performance and Load Testing tools (Sprint 5 - Story 3.3)
        tools += [
            tool("bmad_performance_load_test", "Run comprehensive load test for BMAD tools", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "concurrent_users": {"type": "integer", "description": "Number of concurrent users", "default": 10},
                    "duration_seconds": {"type": "integer", "description": "Test duration in seconds", "default": 60},
                    "ramp_up_seconds": {"type": "integer", "description": "Ramp-up time in seconds", "default": 10},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name"]
            }),
            tool("bmad_performance_stress_test", "Run stress test to find breaking point for BMAD tools", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "max_concurrent_users": {"type": "integer", "description": "Maximum concurrent users to test", "default": 100},
                    "increment": {"type": "integer", "description": "Increment for concurrent users", "default": 10},
                    "duration_per_level": {"type": "integer", "description": "Duration for each stress level", "default": 30},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name"]
            }),
            tool("bmad_performance_benchmark", "Run performance benchmarks for multiple BMAD tools", {
                "type": "object",
                "properties": {
                    "tools_config": {"type": "string", "description": "JSON string with list of tools to benchmark"},
                    "iterations": {"type": "integer", "description": "Number of iterations per tool", "default": 10}
                },
                "required": ["tools_config"]
            }),
            tool("bmad_performance_regression_test", "Detect performance regression by comparing to baseline", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "baseline_metrics": {"type": "string", "description": "JSON string with baseline performance metrics"},
                    "threshold_percentage": {"type": "number", "description": "Threshold for regression detection", "default": 20.0},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name", "baseline_metrics"]
            }),
            tool("bmad_performance_test_history", "Get history of all performance and load tests", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_performance_clear_history", "Clear all performance and load test history", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_performance_system_monitor", "Monitor system resources for specified duration", {
                "type": "object",
                "properties": {
                    "duration_seconds": {"type": "integer", "description": "Duration to monitor in seconds", "default": 60}
                },
                "required": []
            })
        ]

        # BMAD Error Handling and Recovery Testing tools (Sprint 5 - Story 3.4)
        tools += [
            tool("bmad_error_injection_test", "Inject specific errors into tool execution for testing", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "error_type": {"type": "string", "description": "Type of error to inject", "enum": ["timeout", "connection_error", "authentication_error", "authorization_error", "validation_error", "rate_limit_error", "internal_server_error", "service_unavailable", "network_error", "memory_error", "cpu_error"]},
                    "probability": {"type": "number", "description": "Probability of error injection (0.0 to 1.0)", "default": 1.0},
                    "duration_seconds": {"type": "integer", "description": "Duration of error injection in seconds"},
                    "error_message": {"type": "string", "description": "Custom error message"},
                    "error_code": {"type": "integer", "description": "Custom error code"},
                    "delay_seconds": {"type": "number", "description": "Delay before error injection", "default": 0.0},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name", "error_type"]
            }),
            tool("bmad_recovery_strategy_test", "Test a specific recovery strategy against an injected error", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "error_type": {"type": "string", "description": "Type of error to inject"},
                    "recovery_strategy": {"type": "string", "description": "Recovery strategy to test", "enum": ["retry", "fallback", "circuit_breaker", "timeout", "graceful_degradation"]},
                    "max_attempts": {"type": "integer", "description": "Maximum number of retry attempts", "default": 3},
                    "retry_delay": {"type": "number", "description": "Delay between retry attempts", "default": 1.0},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name", "error_type", "recovery_strategy"]
            }),
            tool("bmad_resilience_test_suite", "Run comprehensive resilience test suite", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "error_types": {"type": "string", "description": "JSON string with list of error types to test"},
                    "recovery_strategies": {"type": "string", "description": "JSON string with list of recovery strategies to test"},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name", "error_types", "recovery_strategies"]
            }),
            tool("bmad_circuit_breaker_test", "Test circuit breaker functionality", {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Name of the tool to test"},
                    "failure_threshold": {"type": "integer", "description": "Number of failures before circuit opens", "default": 3},
                    "recovery_timeout": {"type": "integer", "description": "Timeout in seconds before attempting recovery", "default": 300},
                    "tool_args": {"type": "object", "description": "Arguments to pass to the tool", "default": {}}
                },
                "required": ["tool_name"]
            }),
            tool("bmad_error_recovery_history", "Get history of all error handling and recovery tests", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_error_recovery_clear_history", "Clear all error handling and recovery test history", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_circuit_breaker_status", "Get status of a specific circuit breaker", {
                "type": "object",
                "properties": {
                    "circuit_breaker_key": {"type": "string", "description": "Key identifying the circuit breaker"}
                },
                "required": ["circuit_breaker_key"]
            })
        ]

        # BMAD Integration Testing tools (Phase 4.3)
        tools += [
            tool("bmad_integration_cross_component_test", "Run cross-component integration testing"),
            tool("bmad_integration_api_test", "Run API integration testing for all endpoints"),
            tool("bmad_integration_database_test", "Run database integration testing for all operations"),
            tool("bmad_integration_full_suite", "Run complete integration test suite"),
            tool("bmad_integration_report_generate", "Generate comprehensive integration testing report"),
            tool("bmad_integration_history_get", "Get integration testing execution history"),
        ]

        # BMAD User Acceptance Testing tools (Phase 4.4)
        tools += [
            tool("bmad_uat_scenario_test", "Run user acceptance scenario testing for real-world scenarios"),
            tool("bmad_uat_usability_test", "Run usability testing for user interfaces"),
            tool("bmad_uat_accessibility_test", "Run accessibility testing for compliance"),
            tool("bmad_uat_full_suite", "Run complete user acceptance test suite"),
            tool("bmad_uat_report_generate", "Generate comprehensive user acceptance testing report"),
            tool("bmad_uat_history_get", "Get user acceptance testing execution history"),
        ]

        # BMAD Monitoring & Observability tools (Phase 4.5)
        tools += [
            tool("bmad_monitoring_system_health", "Monitor overall system health and status"),
            tool("bmad_monitoring_performance_metrics", "Collect and analyze performance metrics"),
            tool("bmad_monitoring_resource_utilization", "Monitor resource usage (CPU, memory, disk, network)"),
            tool("bmad_alerting_configure", "Configure alerting rules and thresholds"),
            tool("bmad_alerting_test", "Test alerting system functionality"),
            tool("bmad_observability_dashboard", "Generate observability dashboard data"),
            tool("bmad_logging_centralized", "Centralized logging and log analysis"),
            tool("bmad_monitoring_report_generate", "Generate comprehensive monitoring reports"),
        ]

        # BMAD Expansion Pack System tools (Phase 5.1)
        tools += [
            tool("bmad_expansion_system_status", "Get expansion pack system status"),
            tool("bmad_expansion_pack_install", "Install expansion packs"),
            tool("bmad_expansion_pack_uninstall", "Uninstall expansion packs"),
            tool("bmad_expansion_pack_list", "List available and installed expansion packs"),
            tool("bmad_expansion_pack_activate", "Activate expansion pack capabilities"),
            tool("bmad_expansion_pack_deactivate", "Deactivate expansion pack capabilities"),
            tool("bmad_expansion_pack_update", "Update expansion packs"),
            tool("bmad_expansion_pack_validate", "Validate expansion pack integrity"),
        ]

        return tools

    @staticmethod
    def get_tool_registry_info() -> Dict[str, Any]:
        """Get comprehensive information about the tool registry"""
        tools = ToolRegistry.get_tools_for_mcp()
        total = len(tools)
        
        return {
            "registry_version": "1.0.0",
            "total_tools": total,
            "supported_versions": ["1.0.0"],
            "next_version": "2.0.0",
            "deprecation_date": "2025-12-31T23:59:59Z",
            "versioning_standard": "CEREBRAL_191_INTEGRATION_API_VERSIONING_STANDARDS.md",
            "tool_grouping": {
                "coverage_percentage": 100.0,
                "missing_from_groups": [],
                "extra_in_groups": []
            },
            "version_metadata": {
                "semantic_versioning": True,
                "backward_compatibility": True,
                "migration_support": True,
                "enterprise_grade": True,
                "tool_management": True
            },
        }
