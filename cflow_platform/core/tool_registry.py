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

        # System
        tools += [
            tool("sys_test", "Test stdio server connection"),
            tool("sys_stats", "Project statistics overview"),
            tool("sys_debug", "Debug environment"),
            tool("sys_version", "MCP version info"),
        ]

        # Tasks (read)
        tools += [
            tool("task_list", "List/filter tasks", {"type": "object", "properties": {"status": {"type": "string"}, "includeSubtasks": {"type": "boolean"}}, "required": []}),
            tool("task_get", "Get task by ID", {"type": "object", "properties": {"taskId": {"type": "string"}}, "required": ["taskId"]}),
            tool("task_next", "Next recommended task"),
        ]

        # Task modifications
        tools += [
            tool("task_add", "Create task", {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string"}}, "required": ["title", "description"]}),
            tool("task_update", "Update task", {"type": "object", "properties": {"taskId": {"type": "string"}, "updates": {"type": "object"}}, "required": ["taskId", "updates"]}),
            tool("task_status", "Change task status", {"type": "object", "properties": {"taskId": {"type": "string"}, "status": {"type": "string"}}, "required": ["taskId", "status"]}),
            tool("task_sub_add", "Add subtask", {"type": "object", "properties": {"parentId": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}}, "required": ["parentId", "title", "description"]}),
            tool("task_sub_upd", "Append subtask notes", {"type": "object", "properties": {"taskId": {"type": "string"}, "notes": {"type": "string"}}, "required": ["taskId", "notes"]}),
            tool("task_multi", "Batch update starting from ID", {"type": "object", "properties": {"fromId": {"type": "string"}, "updates": {"type": "object"}}, "required": ["fromId", "updates"]}),
            tool("task_remove", "Delete task", {"type": "object", "properties": {"taskId": {"type": "string"}}, "required": ["taskId"]}),
        ]

        # Docs
        tools += [
            tool("doc_generate", "Generate task documentation", {"type": "object", "properties": {"taskId": {"type": "string"}, "content": {"type": "string"}}, "required": ["taskId"]}),
            tool("doc_quality", "Score doc quality", {"type": "object", "properties": {"taskId": {"type": "string"}}, "required": ["taskId"]}),
            tool("doc_refs", "List doc references", {"type": "object", "properties": {"taskId": {"type": "string"}}, "required": ["taskId"]}),
            tool("doc_research", "Doc research (basic)", {"type": "object", "properties": {"taskId": {"type": "string"}, "query": {"type": "string"}}, "required": ["taskId"]}),
            tool("doc_comply", "Doc compliance check", {"type": "object", "properties": {"taskId": {"type": "string"}, "framework": {"type": "string"}}, "required": ["taskId"]}),
        ]

        # Enhanced Research
        tools += [
            tool("research", "Enhanced research (package)", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        ]

        # Plan parser
        tools += [
            tool("plan_parse", "Parse atomic plan", {"type": "object", "properties": {"plan_file": {"type": "string"}, "dry_run": {"type": "boolean"}}, "required": ["plan_file"]}),
            tool("plan_list", "List plans", {"type": "object", "properties": {"search_path": {"type": "string"}}, "required": []}),
            tool("plan_validate", "Validate plan format", {"type": "object", "properties": {"plan_file": {"type": "string"}}, "required": ["plan_file"]}),
        ]

        # Linting (basic + enhanced)
        tools += [
            tool("lint_full", "Run full lint"),
            tool("lint_bg", "Run lint in background"),
            tool("lint_supa", "Run Supabase-specific lint"),
            tool("lint_status", "Lint status"),
            tool("lint_trigger", "Trigger lint", {"type": "object", "properties": {"reason": {"type": "string"}}, "required": []}),
            tool("watch_start", "Start rules watcher"),
            tool("watch_status", "Rules watcher status"),
            tool("enh_full_lint", "Run enhanced lint"),
            tool("enh_pattern", "Enhanced pattern learning"),
            tool("enh_autofix", "Enhanced autofix", {"type": "object", "properties": {"target_files": {"type": "array", "items": {"type": "string"}}}, "required": []}),
            tool("enh_perf", "Enhanced performance protection"),
            tool("enh_rag", "Enhanced RAG compliance"),
            tool("enh_mon_start", "Start enhanced monitoring"),
            tool("enh_mon_stop", "Stop enhanced monitoring"),
            tool("enh_status", "Enhanced status"),
        ]

        # Testing
        tools += [
            tool("test_analyze", "Analyze test suite"),
            tool("test_delete_flaky", "Delete flaky tests", {"type": "object", "properties": {"confirmation": {"type": "boolean"}}, "required": []}),
            tool("test_confidence", "Test confidence report"),
        ]

        # Sandbox execution
        tools += [
            tool(
                "sandbox.run_python",
                "Execute Python in a sandbox with CPU/mem/time caps, FS allowlist, and no network",
                {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "time_limit_sec": {"type": "integer"},
                        "cpu_limit_sec": {"type": "integer"},
                        "mem_limit_mb": {"type": "integer"},
                        "fs_allowlist": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["code"],
                },
            )
        ]

        # Reasoning / planning
        tools += [
            tool(
                "code_reasoning.plan",
                "Produce a bounded minimal-edit plan with success checks",
                {
                    "type": "object",
                    "properties": {
                        "parsed_failures": {"type": "array", "items": {"type": "object"}},
                        "suspect_files": {"type": "array", "items": {"type": "string"}},
                        "max_steps": {"type": "integer"},
                        "profile_name": {"type": "string"},
                    },
                    "required": [],
                },
            )
        ]

        # Memory (CerebralMemory)
        tools += [
            tool("memory_add", "Add a memory to CerebralMemory", {"type": "object", "properties": {"content": {"type": "string"}, "userId": {"type": "string"}, "metadata": {"type": "object"}}, "required": ["content"]}),
            tool("memory_search", "Search memories from CerebralMemory", {"type": "object", "properties": {"query": {"type": "string"}, "userId": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}),
            tool("memory_store_procedure", "Store/update a procedure in CerebralMemory", {"type": "object", "properties": {"title": {"type": "string"}, "steps": {"type": "array", "items": {"type": "object"}}, "justification": {"type": "string"}, "source": {"type": "string"}}, "required": ["title", "steps", "justification"]}),
            tool("memory_store_episode", "Store an episodic iteration log in CerebralMemory", {"type": "object", "properties": {"runId": {"type": "string"}, "taskId": {"type": "string"}, "content": {"type": "string"}, "metadata": {"type": "object"}}, "required": ["runId", "content"]}),
            tool("memory_stats", "Get memory system stats"),
        ]

        # BMAD Planning Tools
        tools += [
            tool("bmad_prd_create", "Create Product Requirements Document", {"type": "object", "properties": {"project_name": {"type": "string"}, "goals": {"type": "array", "items": {"type": "string"}}, "background": {"type": "string"}}, "required": ["project_name"]}),
            tool("bmad_prd_update", "Update PRD document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "updates": {"type": "object"}}, "required": ["doc_id", "updates"]}),
            tool("bmad_prd_get", "Get PRD document", {"type": "object", "properties": {"doc_id": {"type": "string"}}, "required": ["doc_id"]}),
            tool("bmad_arch_create", "Create Architecture Document", {"type": "object", "properties": {"project_name": {"type": "string"}, "prd_id": {"type": "string"}, "tech_stack": {"type": "array", "items": {"type": "string"}}}, "required": ["project_name", "prd_id"]}),
            tool("bmad_arch_update", "Update Architecture document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "updates": {"type": "object"}}, "required": ["doc_id", "updates"]}),
            tool("bmad_arch_get", "Get Architecture document", {"type": "object", "properties": {"doc_id": {"type": "string"}}, "required": ["doc_id"]}),
            tool("bmad_story_create", "Create User Story Document", {"type": "object", "properties": {"project_name": {"type": "string"}, "prd_id": {"type": "string"}, "arch_id": {"type": "string"}, "user_stories": {"type": "array", "items": {"type": "string"}}}, "required": ["project_name", "prd_id", "arch_id"]}),
            tool("bmad_story_update", "Update Story document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "updates": {"type": "object"}}, "required": ["doc_id", "updates"]}),
            tool("bmad_story_get", "Get Story document", {"type": "object", "properties": {"doc_id": {"type": "string"}}, "required": ["doc_id"]}),
            tool("bmad_doc_list", "List BMAD documents", {"type": "object", "properties": {"project_id": {"type": "string"}, "doc_type": {"type": "string", "enum": ["PRD", "ARCH", "STORY", "EPIC"]}, "status": {"type": "string", "enum": ["draft", "review", "approved", "archived"]}}, "required": []}),
            tool("bmad_doc_approve", "Approve BMAD document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "approver": {"type": "string"}}, "required": ["doc_id", "approver"]}),
            tool("bmad_doc_reject", "Reject BMAD document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "reason": {"type": "string"}, "reviewer": {"type": "string"}}, "required": ["doc_id", "reason", "reviewer"]}),
        ]

        # BMAD Orchestration & Workflow Gates
        tools += [
            tool("bmad_master_checklist", "Run PO master checklist to validate PRD/Architecture alignment", {"type": "object", "properties": {"prd_id": {"type": "string"}, "arch_id": {"type": "string"}}, "required": ["prd_id", "arch_id"]}),
            tool("bmad_epic_create", "Create epics from PRD and Architecture", {"type": "object", "properties": {"project_name": {"type": "string"}, "prd_id": {"type": "string"}, "arch_id": {"type": "string"}}, "required": ["project_name", "prd_id", "arch_id"]}),
            tool("bmad_epic_update", "Update epic document", {"type": "object", "properties": {"doc_id": {"type": "string"}, "updates": {"type": "object"}}, "required": ["doc_id", "updates"]}),
            tool("bmad_epic_get", "Get epic document", {"type": "object", "properties": {"doc_id": {"type": "string"}}, "required": ["doc_id"]}),
            tool("bmad_epic_list", "List epics for project", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": []}),
            tool("bmad_workflow_start", "Start specific BMAD workflow", {"type": "object", "properties": {"workflow_id": {"type": "string"}, "project_name": {"type": "string"}}, "required": ["workflow_id", "project_name"]}),
            tool("bmad_workflow_next", "Get next recommended action in workflow", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": []}),
        ]

        # BMAD Expansion Packs
        tools += [
            tool("bmad_expansion_packs_list", "List available BMAD expansion packs", {"type": "object", "properties": {}, "required": []}),
            tool("bmad_expansion_packs_install", "Install BMAD expansion pack", {"type": "object", "properties": {"pack_id": {"type": "string"}}, "required": ["pack_id"]}),
            tool("bmad_expansion_packs_enable", "Enable expansion pack for project", {"type": "object", "properties": {"project_id": {"type": "string"}, "pack_id": {"type": "string"}}, "required": ["project_id", "pack_id"]}),
        ]

        # BMAD Basic Workflow Tools (Story 1.5)
        tools += [
            tool("bmad_basic_prd_workflow", "Create basic PRD using BMAD templates and Cerebral storage", {"type": "object", "properties": {"project_name": {"type": "string"}, "goals": {"type": "array", "items": {"type": "string"}}, "background": {"type": "string"}}, "required": ["project_name"]}),
            tool("bmad_basic_architecture_workflow", "Create basic Architecture using BMAD templates and Cerebral storage", {"type": "object", "properties": {"project_name": {"type": "string"}, "prd_id": {"type": "string"}, "tech_stack": {"type": "array", "items": {"type": "string"}}}, "required": ["project_name", "prd_id"]}),
            tool("bmad_basic_story_workflow", "Create basic Story using BMAD templates and Cerebral storage", {"type": "object", "properties": {"project_name": {"type": "string"}, "prd_id": {"type": "string"}, "arch_id": {"type": "string"}, "user_stories": {"type": "array", "items": {"type": "string"}}}, "required": ["project_name", "prd_id", "arch_id"]}),
            tool("bmad_basic_complete_workflow", "Run complete basic workflow: PRD → Architecture → Story", {"type": "object", "properties": {"project_name": {"type": "string"}, "goals": {"type": "array", "items": {"type": "string"}}, "background": {"type": "string"}, "tech_stack": {"type": "array", "items": {"type": "string"}}, "user_stories": {"type": "array", "items": {"type": "string"}}}, "required": ["project_name"]}),
            tool("bmad_basic_workflow_status", "Get current status of basic BMAD workflows for a project", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]}),
        ]

        # BMAD Human-in-the-Loop (HIL) Interactive Sessions
        tools += [
            tool("bmad_hil_start_session", "Start BMAD-style HIL interactive session for document completion", {"type": "object", "properties": {"doc_id": {"type": "string"}, "doc_type": {"type": "string", "enum": ["PRD", "ARCH", "STORY"]}, "session_type": {"type": "string", "enum": ["elicitation", "review", "approval"]}}, "required": ["doc_id", "doc_type", "session_type"]}),
            tool("bmad_hil_continue_session", "Continue BMAD-style HIL interactive session with user response", {"type": "object", "properties": {"session_id": {"type": "string"}, "user_response": {"type": "string"}}, "required": ["session_id", "user_response"]}),
            tool("bmad_hil_end_session", "End BMAD-style HIL interactive session and update document", {"type": "object", "properties": {"session_id": {"type": "string"}, "finalize": {"type": "boolean"}}, "required": ["session_id"]}),
            tool("bmad_hil_session_status", "Get status of BMAD-style HIL interactive session", {"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]}),
            tool("bmad_workflow_status", "Check BMAD workflow status and HIL session state", {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": []}),
        ]

        # Internet search (DuckDuckGo)
        tools += [
            tool(
                "internet_search",
                "Perform internet search with DuckDuckGo and return a summary with sources",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "region": {"type": "string"},
                        "safe": {"type": "boolean"},
                    },
                    "required": ["query"]
                },
            ),
        ]

        # Desktop notifications (optional, off by default)
        tools += [
            tool(
                "desktop.notify",
                "Send a local desktop notification (macOS only; disabled by default)",
                {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "subtitle": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                },
            )
        ]
        # LLM provider
        tools += [
            tool(
                "llm_provider.probe",
                "Verify LLM provider connectivity and model readiness",
                {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "prompt": {"type": "string"},
                    },
                    "required": [],
                },
            )
        ]

        # Codegen
        tools += [
            tool(
                "codegen.generate_edits",
                "Generate minimal EditPlan[] for the task and write .cerebraflow/edits.json",
                {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "context_files": {"type": "array", "items": {"type": "string"}},
                        "apis": {"type": "array", "items": {"type": "object"}},
                        "tests": {"type": "array", "items": {"type": "string"}},
                        "constraints": {"type": "object"},
                        "success_criteria": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": ["task"],
                },
            )
        ]

        # Code Intelligence
        tools += [
            tool(
                "code.search_functions",
                "Semantic search for functions by natural-language description",
                {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "topK": {"type": "integer"},
                    },
                    "required": ["description"],
                },
            ),
            tool(
                "code.index_functions",
                "Index functions in the repository to build/update embeddings",
                {
                    "type": "object",
                    "properties": {
                        "files": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [],
                },
            ),
            tool(
                "code.call_paths",
                "Compute call paths to a target function",
                {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "maxDepth": {"type": "integer"},
                    },
                    "required": ["to"],
                },
            ),
        ]

        # BMAD Workflow Engine
        tools += [
            tool("bmad_workflow_list", "List available BMAD workflows"),
            tool("bmad_workflow_get", "Get BMAD workflow details", {"type": "object", "properties": {"workflow_id": {"type": "string"}}, "required": ["workflow_id"]}),
            tool("bmad_workflow_execute", "Execute BMAD workflow", {"type": "object", "properties": {"workflow_id": {"type": "string"}, "project_context": {"type": "object"}, "profile_name": {"type": "string"}, "max_iterations": {"type": "integer"}, "wallclock_limit_sec": {"type": "integer"}, "step_budget": {"type": "integer"}}, "required": ["workflow_id"]}),
            tool("bmad_agent_execute", "Execute BMAD agent step", {"type": "object", "properties": {"agent": {"type": "string"}, "action": {"type": "string"}, "creates": {"type": "string"}, "requires": {"type": "array", "items": {"type": "string"}}, "project_context": {"type": "object"}, "agent_content": {"type": "string"}, "notes": {"type": "string"}}, "required": ["agent", "action"]}),
            tool("bmad_action_execute", "Execute BMAD action step", {"type": "object", "properties": {"action": {"type": "string"}, "project_context": {"type": "object"}, "notes": {"type": "string"}}, "required": ["action"]}),
        ]
        
        # BMAD Git Workflow Tools
        tools += [
            tool("bmad_git_commit_changes", "Commit BMAD workflow changes with validation and tracking", {"type": "object", "properties": {"workflow_id": {"type": "string"}, "project_id": {"type": "string"}, "changes_summary": {"type": "string"}, "document_ids": {"type": "array", "items": {"type": "string"}}, "validate": {"type": "boolean"}}, "required": ["workflow_id", "project_id", "changes_summary"]}),
            tool("bmad_git_push_changes", "Push BMAD workflow changes to remote repository", {"type": "object", "properties": {"tracking_id": {"type": "string"}, "remote": {"type": "string"}, "branch": {"type": "string"}}, "required": ["tracking_id"]}),
            tool("bmad_git_validate_changes", "Validate BMAD workflow changes before commit", {"type": "object", "properties": {"workflow_id": {"type": "string"}, "project_id": {"type": "string"}, "validation_type": {"type": "string"}}, "required": ["workflow_id", "project_id"]}),
            tool("bmad_git_get_history", "Get BMAD commit history for a project", {"type": "object", "properties": {"project_id": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["project_id"]}),
        ]

        # BMAD Vault Integration Tools (Phase 2.1)
        tools += [
            tool("bmad_vault_store_secret", "Store secret in HashiCorp Vault", {"type": "object", "properties": {"path": {"type": "string"}, "secret_data": {"type": "object"}, "metadata": {"type": "object"}}, "required": ["path", "secret_data"]}),
            tool("bmad_vault_retrieve_secret", "Retrieve secret from HashiCorp Vault", {"type": "object", "properties": {"path": {"type": "string"}, "version": {"type": "string"}}, "required": ["path"]}),
            tool("bmad_vault_list_secrets", "List secrets in HashiCorp Vault", {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}),
            tool("bmad_vault_delete_secret", "Delete secret from HashiCorp Vault", {"type": "object", "properties": {"path": {"type": "string"}, "versions": {"type": "array", "items": {"type": "string"}}}, "required": ["path"]}),
            tool("bmad_vault_migrate_secrets", "Migrate all local secrets to HashiCorp Vault", {"type": "object", "properties": {}}, "required": []}),
            tool("bmad_vault_health_check", "Check HashiCorp Vault health status", {"type": "object", "properties": {}}, "required": []}),
            tool("bmad_vault_get_config", "Get configuration from HashiCorp Vault", {"type": "object", "properties": {"category": {"type": "string"}}, "required": ["category"]}),
        ]

        return tools

    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get available tools for compatibility with gap analysis."""
        return ToolRegistry.get_tools_for_mcp()

    @staticmethod
    def get_tools_by_group(group_name: str) -> List[Dict[str, Any]]:
        """Get tools filtered by group name"""
        all_tools = ToolRegistry.get_tools_for_mcp()
        return [tool for tool in all_tools if tool.get("group") == group_name]
    
    @staticmethod
    def get_tools_by_client_type(client_type: str) -> List[Dict[str, Any]]:
        """Get tools available for a specific client type"""
        all_tools = ToolRegistry.get_tools_for_mcp()
        available_groups = ToolGroupManager.get_groups_for_client_type(client_type)
        group_names = [group.value for group in available_groups]
        
        return [tool for tool in all_tools if tool.get("group") in group_names]
    
    @staticmethod
    def get_tools_by_project_type(project_type: str) -> List[Dict[str, Any]]:
        """Get tools available for a specific project type"""
        all_tools = ToolRegistry.get_tools_for_mcp()
        available_groups = ToolGroupManager.get_groups_for_project_type(project_type)
        group_names = [group.value for group in available_groups]
        
        return [tool for tool in all_tools if tool.get("group") in group_names]
    
    @staticmethod
    def get_required_tools() -> List[Dict[str, Any]]:
        """Get all required tools"""
        all_tools = ToolRegistry.get_tools_for_mcp()
        return [tool for tool in all_tools if tool.get("metadata", {}).get("required", False)]
    
    @staticmethod
    def validate_tool_grouping() -> Dict[str, Any]:
        """Validate that all tools are properly grouped"""
        all_tools = ToolRegistry.get_tools_for_mcp()
        tool_names = [tool["name"] for tool in all_tools]
        return ToolGroupManager.validate_tool_grouping(tool_names)

    @staticmethod
    def get_version_info() -> Dict[str, Any]:
        total = len(ToolRegistry.get_tools_for_mcp())
        grouping_validation = ToolRegistry.validate_tool_grouping()
        
        return {
            "mcp_server_version": "1.0.0",
            "api_version": "1.0.0",
            "supported_versions": ["1.0.0"],
            "next_version": "2.0.0",
            "deprecation_date": "2025-12-31T23:59:59Z",
            "versioning_standard": "CEREBRAL_191_INTEGRATION_API_VERSIONING_STANDARDS.md",
            "total_tools": total,
            "tool_grouping": {
                "coverage_percentage": grouping_validation["coverage_percentage"],
                "missing_from_groups": grouping_validation["missing_from_groups"],
                "extra_in_groups": grouping_validation["extra_in_groups"]
            },
            "version_metadata": {
                "semantic_versioning": True,
                "backward_compatibility": True,
                "migration_support": True,
                "enterprise_grade": True,
                "tool_management": True
            },
        }


