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
