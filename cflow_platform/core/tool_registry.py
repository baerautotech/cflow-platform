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
            tool("sys_health", "Get system health status"),
        ]

        # Task management tools
        tools += [
            tool("task_list", "List tasks"),
            tool("task_get", "Get task details"),
            tool("task_next", "Get next task"),
            tool("task_add", "Add new task"),
            tool("task_update", "Update task"),
            tool("task_status", "Update task status"),
            tool("task_sub_add", "Add subtask"),
            tool("task_sub_upd", "Update subtask"),
            tool("task_multi", "Multi-task operations"),
            tool("task_remove", "Remove task"),
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
            tool("enh_pattern", "Enhanced pattern learning"),
            tool("enh_autofix", "Enhanced autofix"),
            tool("enh_perf", "Enhanced performance protection"),
            tool("enh_rag", "Enhanced RAG integration"),
            tool("enh_mon_start", "Start enhanced monitoring"),
            tool("enh_mon_stop", "Stop enhanced monitoring"),
            tool("enh_status", "Enhanced status check"),
        ]

        # Testing tools
        tools += [
            tool("test_analyze", "Analyze test suite"),
            tool("test_delete_flaky", "Delete flaky tests"),
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
            tool("memory_store_procedure", "Store procedure in memory"),
            tool("memory_store_episode", "Store episode in memory"),
            tool("memory_stats", "Get memory statistics"),
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
            tool("codegen.generate_edits", "Generate code edits"),
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

        # BMAD Persona Management Tools
        tools += [
            tool("bmad_discover_personas", "Discover all available BMAD-Method personas"),
            tool("bmad_activate_persona", "Activate a BMAD-Method persona"),
            tool("bmad_deactivate_persona", "Deactivate current persona"),
            tool("bmad_execute_persona_command", "Execute a command on the active persona"),
            tool("bmad_get_persona_status", "Get current persona status"),
            tool("bmad_switch_persona", "Switch to a different persona"),
        ]

        # BMAD Tool Consolidation Tools (Phase 3)
        tools += [
            tool("bmad_discover_tools", "Discover all BMAD-Method tools from vendor/bmad"),
            tool("bmad_get_tool", "Get a specific BMAD tool by ID"),
            tool("bmad_get_tools_by_category", "Get all tools in a specific category"),
            tool("bmad_execute_tool", "Execute a BMAD-Method tool"),
            tool("bmad_get_tool_status", "Get BMAD tool wrapper status"),
            tool("bmad_list_categories", "List all available tool categories"),
        ]

        # BMAD Advanced Features Tools (Phase 5)
        tools += [
            # Expansion Pack Tools
            tool("bmad_expansion_discover_packs", "Discover all BMAD-Method expansion packs"),
            tool("bmad_expansion_install_pack", "Install a BMAD-Method expansion pack"),
            tool("bmad_expansion_activate_pack", "Activate a BMAD-Method expansion pack"),
            tool("bmad_expansion_deactivate_pack", "Deactivate a BMAD-Method expansion pack"),
            tool("bmad_expansion_remove_pack", "Remove a BMAD-Method expansion pack"),
            tool("bmad_expansion_get_pack_status", "Get expansion pack manager status"),
            
            # HIL Integration Tools
            tool("bmad_hil_create_session", "Create a new HIL session"),
            tool("bmad_hil_update_session", "Update a HIL session"),
            tool("bmad_hil_complete_session", "Complete a HIL session"),
            tool("bmad_hil_cancel_session", "Cancel a HIL session"),
            tool("bmad_hil_get_status", "Get HIL integration system status"),
            
            # Workflow Engine Tools
            tool("bmad_workflow_discover", "Discover all BMAD-Method workflows"),
            tool("bmad_workflow_start", "Start a BMAD-Method workflow"),
            tool("bmad_workflow_execute_step", "Execute a workflow step"),
            tool("bmad_workflow_complete", "Complete a BMAD-Method workflow"),
            tool("bmad_workflow_get_status", "Get workflow engine status"),
            
            # Monitoring & Analytics Tools
            tool("bmad_monitoring_collect_metric", "Collect a monitoring metric"),
            tool("bmad_monitoring_generate_report", "Generate an analytics report"),
            tool("bmad_monitoring_get_alerts", "Get monitoring alerts"),
            tool("bmad_monitoring_get_status", "Get monitoring system status"),
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

        # BMAD Security and Authentication Testing tools (Sprint 5 - Story 3.5)
        tools += [
            tool("bmad_security_authentication_test", "Test authentication mechanisms for an endpoint", {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API endpoint to test"},
                    "auth_method": {"type": "string", "description": "Authentication method (jwt, basic, bearer, etc.)", "default": "jwt"},
                    "test_credentials": {"type": "object", "description": "Test credentials to use", "default": {}}
                },
                "required": ["endpoint"]
            }),
            tool("bmad_security_authorization_test", "Test authorization mechanisms for an endpoint", {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API endpoint to test"},
                    "user_roles": {"type": "string", "description": "JSON string with list of user roles to test"},
                    "required_permissions": {"type": "string", "description": "JSON string with list of required permissions"}
                },
                "required": ["endpoint", "user_roles", "required_permissions"]
            }),
            tool("bmad_security_input_validation_test", "Test input validation and sanitization for an endpoint", {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API endpoint to test"},
                    "input_fields": {"type": "string", "description": "JSON string with list of input fields to test"},
                    "malicious_inputs": {"type": "string", "description": "JSON string with list of malicious inputs to test"}
                },
                "required": ["endpoint", "input_fields"]
            }),
            tool("bmad_security_rate_limiting_test", "Test rate limiting mechanisms for an endpoint", {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API endpoint to test"},
                    "rate_limit": {"type": "integer", "description": "Expected rate limit (requests per time window)", "default": 100},
                    "time_window": {"type": "integer", "description": "Time window in seconds", "default": 60}
                },
                "required": ["endpoint"]
            }),
            tool("bmad_security_test_suite", "Run comprehensive security test suite", {
                "type": "object",
                "properties": {
                    "endpoints": {"type": "string", "description": "JSON string with list of endpoints to test"},
                    "test_types": {"type": "string", "description": "JSON string with list of security test types to perform"},
                    "user_roles": {"type": "string", "description": "JSON string with list of user roles to test with"}
                },
                "required": ["endpoints", "test_types"]
            }),
            tool("bmad_security_vulnerability_scan", "Perform comprehensive vulnerability scan on an endpoint", {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API endpoint to scan"},
                    "scan_types": {"type": "string", "description": "JSON string with list of vulnerability scan types"}
                },
                "required": ["endpoint", "scan_types"]
            }),
            tool("bmad_security_test_history", "Get history of all security and authentication tests", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_security_test_clear_history", "Clear all security and authentication test history", {
                "type": "object",
                "properties": {},
                "required": []
            })
        ]

        # BMAD WebMCP Installer tools (Sprint 6 - Story 4.1)
        tools += [
            tool("bmad_webmcp_install_config", "Install WebMCP configuration", {
                "type": "object",
                "properties": {
                    "server_url": {"type": "string", "description": "WebMCP server URL", "default": "http://localhost:8000"},
                    "api_key": {"type": "string", "description": "API key for authentication"},
                    "timeout_seconds": {"type": "integer", "description": "Request timeout in seconds", "default": 30},
                    "retry_attempts": {"type": "integer", "description": "Number of retry attempts", "default": 3},
                    "enable_health_check": {"type": "boolean", "description": "Enable health checking", "default": True},
                    "enable_feature_flags": {"type": "boolean", "description": "Enable feature flags", "default": True},
                    "enable_performance_monitoring": {"type": "boolean", "description": "Enable performance monitoring", "default": True},
                    "enable_security_testing": {"type": "boolean", "description": "Enable security testing", "default": True},
                    "bmad_integration_enabled": {"type": "boolean", "description": "Enable BMAD integration", "default": True},
                    "bmad_api_url": {"type": "string", "description": "BMAD API service URL", "default": "http://localhost:8001"},
                    "bmad_auth_token": {"type": "string", "description": "BMAD authentication token"},
                    "circuit_breaker_enabled": {"type": "boolean", "description": "Enable circuit breaker", "default": True},
                    "rate_limiting_enabled": {"type": "boolean", "description": "Enable rate limiting", "default": True},
                    "logging_level": {"type": "string", "description": "Logging level", "default": "INFO"},
                    "overwrite": {"type": "boolean", "description": "Whether to overwrite existing configuration", "default": False}
                },
                "required": []
            }),
            tool("bmad_webmcp_validate_installation", "Validate WebMCP installation", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_webmcp_test_integration", "Test WebMCP integration", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_webmcp_uninstall_config", "Uninstall WebMCP configuration", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_webmcp_get_config", "Get current WebMCP configuration", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_webmcp_update_config", "Update WebMCP configuration", {
                "type": "object",
                "properties": {
                    "config_updates": {"type": "string", "description": "JSON string with configuration updates"}
                },
                "required": ["config_updates"]
            }),
            tool("bmad_webmcp_backup_config", "Backup WebMCP configuration", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_webmcp_restore_config", "Restore WebMCP configuration from backup", {
                "type": "object",
                "properties": {
                    "backup_file_path": {"type": "string", "description": "Path to backup file"}
                },
                "required": ["backup_file_path"]
            })
        ]

        # BMAD Installation Flow Testing tools (Sprint 6 - Story 4.2)
        tools += [
            tool("bmad_installation_flow_test", "Test the complete installation flow", {
                "type": "object",
                "properties": {
                    "test_environment": {"type": "boolean", "description": "Whether to test in a temporary environment", "default": True},
                    "skip_optional_steps": {"type": "boolean", "description": "Whether to skip optional installation steps", "default": False}
                },
                "required": []
            }),
            tool("bmad_installation_step_test", "Test a specific installation step", {
                "type": "object",
                "properties": {
                    "step_name": {"type": "string", "description": "Name of the installation step to test"},
                    "custom_command": {"type": "string", "description": "Custom command to execute (JSON string)"}
                },
                "required": ["step_name"]
            }),
            tool("bmad_installation_rollback_test", "Test the rollback flow after installation", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_installation_validate_environment", "Validate the installation environment", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_installation_validate_components", "Validate all installation components", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_installation_get_flow_steps", "Get the list of installation flow steps", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_installation_test_prerequisites", "Test installation prerequisites", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_installation_generate_report", "Generate installation flow test report", {
                "type": "object",
                "properties": {},
                "required": []
            })
        ]

        # BMAD Uninstall and Rollback tools (Sprint 6 - Story 4.3)
        tools += [
            tool("bmad_uninstall_complete", "Uninstall BMAD integration completely", {
                "type": "object",
                "properties": {
                    "create_backup": {"type": "boolean", "description": "Whether to create backup before uninstall", "default": True},
                    "remove_vendor_bmad": {"type": "boolean", "description": "Whether to remove vendor BMAD directory", "default": False},
                    "force": {"type": "boolean", "description": "Whether to force uninstall even if some steps fail", "default": False}
                },
                "required": []
            }),
            tool("bmad_uninstall_step", "Execute a specific uninstall step", {
                "type": "object",
                "properties": {
                    "step_name": {"type": "string", "description": "Name of the uninstall step to execute"},
                    "force": {"type": "boolean", "description": "Whether to force execution even if step fails", "default": False}
                },
                "required": ["step_name"]
            }),
            tool("bmad_rollback_create_point", "Create a rollback point for future restoration", {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the rollback point"},
                    "description": {"type": "string", "description": "Description of the rollback point", "default": ""}
                },
                "required": ["name"]
            }),
            tool("bmad_rollback_to_point", "Rollback to a specific rollback point", {
                "type": "object",
                "properties": {
                    "rollback_point_name": {"type": "string", "description": "Name of the rollback point to restore"},
                    "force": {"type": "boolean", "description": "Whether to force rollback even if some steps fail", "default": False}
                },
                "required": ["rollback_point_name"]
            }),
            tool("bmad_rollback_list_points", "List all available rollback points", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_rollback_delete_point", "Delete a specific rollback point", {
                "type": "object",
                "properties": {
                    "rollback_point_name": {"type": "string", "description": "Name of the rollback point to delete"}
                },
                "required": ["rollback_point_name"]
            }),
            tool("bmad_uninstall_validate", "Validate uninstall prerequisites and current state", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_uninstall_simulate", "Simulate uninstall process without actually performing it", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_rollback_get_point_info", "Get detailed information about a specific rollback point", {
                "type": "object",
                "properties": {
                    "rollback_point_name": {"type": "string", "description": "Name of the rollback point"}
                },
                "required": ["rollback_point_name"]
            })
        ]

        # BMAD Documentation Management tools (Sprint 6 - Story 4.4)
        tools += [
            tool("bmad_documentation_generate", "Generate comprehensive BMAD documentation", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_documentation_update", "Update specific documentation section", {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "Documentation section to update (integration, installation, troubleshooting, api, configuration)"},
                    "content": {"type": "string", "description": "New content for the section"}
                },
                "required": ["section", "content"]
            }),
            tool("bmad_runbook_generate", "Generate a specific runbook", {
                "type": "object",
                "properties": {
                    "runbook_type": {"type": "string", "description": "Type of runbook to generate"},
                    "steps": {"type": "string", "description": "JSON string with runbook steps"}
                },
                "required": ["runbook_type", "steps"]
            }),
            tool("bmad_documentation_validate", "Validate existing documentation", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_documentation_list", "List all documentation files", {
                "type": "object",
                "properties": {},
                "required": []
            }),
            tool("bmad_documentation_get_content", "Get content of a specific documentation file", {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the documentation file"}
                },
                "required": ["file_path"]
            }),
            tool("bmad_documentation_create_section", "Create a new documentation section", {
                "type": "object",
                "properties": {
                    "section_name": {"type": "string", "description": "Name of the section"},
                    "title": {"type": "string", "description": "Title of the section"},
                    "content": {"type": "string", "description": "Content of the section"},
                    "parent_section": {"type": "string", "description": "Parent section (optional)"}
                },
                "required": ["section_name", "title", "content"]
            }),
            tool("bmad_documentation_update_runbook", "Update a specific runbook", {
                "type": "object",
                "properties": {
                    "runbook_name": {"type": "string", "description": "Name of the runbook to update"},
                    "content": {"type": "string", "description": "New content for the runbook"}
                },
                "required": ["runbook_name", "content"]
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

        # BMAD Orchestration Tools (Background Agents & Master Orchestration)
        tools += [
            # Background Agent Orchestration Tools
            tool("bmad_activate_background_agents", "Activate background agents for parallel processing"),
            tool("bmad_get_background_agent_status", "Get background agent orchestration status"),
            tool("bmad_distribute_task", "Distribute a task to background agents"),
            tool("bmad_deactivate_background_agents", "Deactivate background agents"),
            
            # BMAD Master Orchestration Tools
            tool("bmad_activate_master_orchestration", "Activate BMAD Master orchestration"),
            tool("bmad_begin_story_implementation", "Begin implementation of a specific story"),
            tool("bmad_get_master_orchestration_status", "Get BMAD Master orchestration status"),
            tool("bmad_deactivate_master_orchestration", "Deactivate BMAD Master orchestration"),
        ]

        # BMAD Brownfield Support Tools
        tools += [
            tool("bmad_project_type_detect", "Detect if project is greenfield or brownfield"),
            tool("bmad_brownfield_document_project", "Document existing project for brownfield development"),
            tool("bmad_brownfield_prd_create", "Create PRD for brownfield project enhancement"),
            tool("bmad_brownfield_arch_create", "Create architecture for brownfield project enhancement"),
            tool("bmad_brownfield_story_create", "Create user stories for brownfield project enhancement"),
        ]

        # BMAD Expansion Pack Management Tools
        tools += [
            tool("bmad_expansion_packs_list_available", "List all available BMAD expansion packs"),
            tool("bmad_expansion_packs_get_details", "Get details about a specific expansion pack"),
            tool("bmad_expansion_packs_install", "Install a BMAD expansion pack"),
            tool("bmad_expansion_packs_enable", "Enable an installed expansion pack for a project"),
            tool("bmad_expansion_packs_uninstall", "Uninstall a BMAD expansion pack"),
            tool("bmad_expansion_packs_list_installed", "List all installed expansion packs"),
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
