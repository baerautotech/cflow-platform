"""
Tool Group Manager for BMAD WebMCP Server

This module provides tool grouping and modularization capabilities to manage
tool exposure based on client type, project requirements, and legal compliance.
"""

from typing import Any, Dict, List, Set
from dataclasses import dataclass
from enum import Enum


class ToolGroup(Enum):
    """Tool group categories for BMAD tools"""
    CORE = "core"
    PLANNING = "planning"
    HIL = "hil"
    EXPANSION = "expansion"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    SYSTEM = "system"
    GIT = "git"
    MEMORY = "memory"
    SANDBOX = "sandbox"
    REASONING = "reasoning"


@dataclass
class ToolGroupConfig:
    """Configuration for a tool group"""
    description: str
    tools: List[str]
    required: bool = False
    max_tools: int = None
    client_types: List[str] = None
    project_types: List[str] = None


class ToolGroupManager:
    """Manages tool groups and provides tool filtering capabilities"""
    
    # Master tool groups configuration
    MASTER_TOOL_GROUPS = {
        "bmad_task": {
            "group": "core",
            "operations": ["create", "get", "update", "delete", "list", "search"],
            "description": "Task management operations"
        },
        "bmad_plan": {
            "group": "core", 
            "operations": ["create", "get", "update", "list", "execute"],
            "description": "Plan management operations"
        },
        "bmad_doc": {
            "group": "core",
            "operations": ["create", "get", "update", "approve", "list"],
            "description": "Document management operations"
        },
        "bmad_workflow": {
            "group": "core",
            "operations": ["create", "execute", "status", "list"],
            "description": "Workflow management operations"
        },
        "bmad_hil": {
            "group": "advanced",
            "operations": ["request", "status", "approve", "list"],
            "description": "Human-in-the-Loop operations"
        },
        "bmad_git": {
            "group": "advanced",
            "operations": ["commit", "push", "pull", "create_branch", "merge", "status"],
            "description": "Git operations"
        },
        "bmad_orchestrator": {
            "group": "advanced",
            "operations": ["start", "stop", "status", "list"],
            "description": "Orchestration operations"
        },
        "bmad_expansion": {
            "group": "advanced",
            "operations": ["install", "uninstall", "list", "update", "info"],
            "description": "Expansion pack operations"
        },
        "bmad_gamedev": {
            "group": "expansion",
            "operations": ["create_project", "generate_assets", "optimize_performance", "test_build", "deploy"],
            "description": "Game development operations"
        },
        "bmad_devops": {
            "group": "expansion",
            "operations": ["deploy", "monitor", "scale", "backup", "rollback"],
            "description": "DevOps operations"
        },
        "bmad_creative": {
            "group": "expansion",
            "operations": ["generate_content", "edit_content", "analyze_content", "generate_ideas", "translate"],
            "description": "Creative writing operations"
        }
    }
    
    TOOL_GROUPS: Dict[ToolGroup, ToolGroupConfig] = {
        ToolGroup.CORE: ToolGroupConfig(
            description="Essential BMAD core functionality",
            tools=[
                "bmad_prd_create", "bmad_prd_update", "bmad_prd_get",
                "bmad_arch_create", "bmad_arch_update", "bmad_arch_get",
                "bmad_story_create", "bmad_story_update", "bmad_story_get",
                "bmad_doc_list", "bmad_doc_approve", "bmad_doc_reject"
            ],
            required=True,
            client_types=["cursor", "mobile", "web"],
            project_types=["greenfield", "brownfield", "game_dev", "devops"]
        ),
        
        ToolGroup.PLANNING: ToolGroupConfig(
            description="BMAD planning and orchestration",
            tools=[
                "bmad_master_checklist", "bmad_epic_create", "bmad_epic_update",
                "bmad_epic_get", "bmad_epic_list",
                "bmad_workflow_start", "bmad_workflow_next", "bmad_workflow_list",
                "bmad_workflow_get", "bmad_workflow_execute"
            ],
            required=False,
            client_types=["cursor", "web"],
            project_types=["greenfield", "brownfield"]
        ),
        
        ToolGroup.HIL: ToolGroupConfig(
            description="Human-in-the-Loop interactive sessions",
            tools=[
                "bmad_hil_start_session", "bmad_hil_continue_session",
                "bmad_hil_end_session", "bmad_hil_session_status",
                "bmad_workflow_status"
            ],
            required=False,
            client_types=["mobile", "web"],
            project_types=["greenfield", "brownfield"]
        ),
        
        ToolGroup.EXPANSION: ToolGroupConfig(
            description="BMAD expansion packs",
            tools=[
                "bmad_expansion_packs_list", "bmad_expansion_packs_install",
                "bmad_expansion_packs_enable"
            ],
            required=False,
            client_types=["web"],
            project_types=["game_dev", "devops", "creative_writing"]
        ),
        
        ToolGroup.DEVELOPMENT: ToolGroupConfig(
            description="Development and code tools",
            tools=[
                "code.search_functions", "code.index_functions", "code.call_paths",
                "codegen.generate_edits", "lint_full", "lint_bg", "lint_supa",
                "lint_status", "lint_trigger", "enh_full_lint", "enh_pattern",
                "enh_autofix", "enh_perf", "enh_rag", "test_analyze",
                "test_delete_flaky", "test_confidence"
            ],
            required=False,
            client_types=["cursor", "web"],
            project_types=["greenfield", "brownfield"]
        ),
        
        ToolGroup.RESEARCH: ToolGroupConfig(
            description="Research and documentation",
            tools=[
                "research", "internet_search", "doc_generate", "doc_quality",
                "doc_refs", "doc_research", "doc_comply"
            ],
            required=False,
            client_types=["web"],
            project_types=["brownfield", "research"]
        ),
        
        ToolGroup.SYSTEM: ToolGroupConfig(
            description="System administration",
            tools=[
                "sys_test", "sys_stats", "sys_debug", "sys_version",
                "desktop.notify", "llm_provider.probe"
            ],
            required=False,
            client_types=["web"],
            project_types=["all"]
        ),
        
        ToolGroup.GIT: ToolGroupConfig(
            description="BMAD Git workflow tools",
            tools=[
                "bmad_git_commit_changes", "bmad_git_push_changes",
                "bmad_git_validate_changes", "bmad_git_get_history"
            ],
            required=False,
            client_types=["cursor", "web"],
            project_types=["greenfield", "brownfield"]
        ),
        
        ToolGroup.MEMORY: ToolGroupConfig(
            description="CerebralMemory integration",
            tools=[
                "memory_add", "memory_search", "memory_store_procedure",
                "memory_store_episode", "memory_stats"
            ],
            required=False,
            client_types=["web"],
            project_types=["all"]
        ),
        
        ToolGroup.SANDBOX: ToolGroupConfig(
            description="Sandbox execution environment",
            tools=[
                "sandbox.run_python"
            ],
            required=False,
            client_types=["cursor", "web"],
            project_types=["greenfield", "brownfield"]
        ),
        
        ToolGroup.REASONING: ToolGroupConfig(
            description="Code reasoning and planning",
            tools=[
                "code_reasoning.plan"
            ],
            required=False,
            client_types=["cursor", "web"],
            project_types=["greenfield", "brownfield"]
        )
    }
    
    @classmethod
    def get_tools_for_group(cls, group: ToolGroup) -> List[str]:
        """Get all tools for a specific group"""
        return cls.TOOL_GROUPS[group].tools
    
    @classmethod
    def get_groups_for_client_type(cls, client_type: str) -> List[ToolGroup]:
        """Get tool groups available for a specific client type"""
        available_groups = []
        for group, config in cls.TOOL_GROUPS.items():
            if config.client_types is None or client_type in config.client_types:
                available_groups.append(group)
        return available_groups
    
    @classmethod
    def get_groups_for_project_type(cls, project_type: str) -> List[ToolGroup]:
        """Get tool groups available for a specific project type"""
        available_groups = []
        for group, config in cls.TOOL_GROUPS.items():
            if config.project_types is None or project_type in config.project_types or "all" in config.project_types:
                available_groups.append(group)
        return available_groups
    
    @classmethod
    def get_required_groups(cls) -> List[ToolGroup]:
        """Get all required tool groups"""
        return [group for group, config in cls.TOOL_GROUPS.items() if config.required]
    
    @classmethod
    def is_tool_in_group(cls, tool_name: str, group: ToolGroup) -> bool:
        """Check if a tool belongs to a specific group"""
        return tool_name in cls.TOOL_GROUPS[group].tools
    
    @classmethod
    def get_group_for_tool(cls, tool_name: str) -> ToolGroup:
        """Get the group that contains a specific tool"""
        for group, config in cls.TOOL_GROUPS.items():
            if tool_name in config.tools:
                return group
        return None
    
    @classmethod
    def get_all_tools(cls) -> List[str]:
        """Get all tools across all groups"""
        all_tools = []
        for config in cls.TOOL_GROUPS.values():
            all_tools.extend(config.tools)
        return list(set(all_tools))  # Remove duplicates
    
    @classmethod
    def validate_tool_grouping(cls, tool_registry_tools: List[str]) -> Dict[str, Any]:
        """Validate that all tools in registry are properly grouped"""
        grouped_tools = cls.get_all_tools()
        registry_tools = set(tool_registry_tools)
        grouped_tools_set = set(grouped_tools)
        
        missing_from_groups = registry_tools - grouped_tools_set
        extra_in_groups = grouped_tools_set - registry_tools
        
        return {
            "total_registry_tools": len(registry_tools),
            "total_grouped_tools": len(grouped_tools),
            "missing_from_groups": list(missing_from_groups),
            "extra_in_groups": list(extra_in_groups),
            "coverage_percentage": (len(grouped_tools_set & registry_tools) / len(registry_tools)) * 100 if registry_tools else 0
        }
    
    # Master Tool Management Methods
    
    @classmethod
    def get_master_tools_for_group(cls, group: str) -> List[str]:
        """Get all master tools for a specific group"""
        return [tool_name for tool_name, config in cls.MASTER_TOOL_GROUPS.items() 
                if config["group"] == group]
    
    @classmethod
    def get_operations_for_master_tool(cls, master_tool_name: str) -> List[str]:
        """Get all operations for a specific master tool"""
        if master_tool_name in cls.MASTER_TOOL_GROUPS:
            return cls.MASTER_TOOL_GROUPS[master_tool_name]["operations"]
        return []
    
    @classmethod
    def get_group_for_master_tool(cls, master_tool_name: str) -> str:
        """Get the group for a specific master tool"""
        if master_tool_name in cls.MASTER_TOOL_GROUPS:
            return cls.MASTER_TOOL_GROUPS[master_tool_name]["group"]
        return None
    
    @classmethod
    def get_all_master_tools(cls) -> List[str]:
        """Get all master tool names"""
        return list(cls.MASTER_TOOL_GROUPS.keys())
    
    @classmethod
    def get_all_master_operations(cls) -> List[str]:
        """Get all master tool operations as tool.operation format"""
        operations = []
        for tool_name, config in cls.MASTER_TOOL_GROUPS.items():
            for operation in config["operations"]:
                operations.append(f"{tool_name}.{operation}")
        return operations
    
    @classmethod
    def get_master_tools_for_client_type(cls, client_type: str) -> List[str]:
        """Get master tools available for a specific client type"""
        # Core tools available to all clients
        core_tools = cls.get_master_tools_for_group("core")
        
        # Advanced tools available to cursor and web
        advanced_tools = []
        if client_type in ["cursor", "web"]:
            advanced_tools = cls.get_master_tools_for_group("advanced")
        
        # Expansion tools available to web only
        expansion_tools = []
        if client_type == "web":
            expansion_tools = cls.get_master_tools_for_group("expansion")
        
        return core_tools + advanced_tools + expansion_tools
    
    @classmethod
    def get_master_tools_for_project_type(cls, project_type: str) -> List[str]:
        """Get master tools available for a specific project type"""
        available_tools = []
        
        # Core tools available to all project types
        available_tools.extend(cls.get_master_tools_for_group("core"))
        
        # Advanced tools available to most project types
        if project_type in ["greenfield", "brownfield"]:
            available_tools.extend(cls.get_master_tools_for_group("advanced"))
        
        # Expansion tools based on project type
        if project_type == "game_dev":
            available_tools.append("bmad_gamedev")
        elif project_type == "devops":
            available_tools.append("bmad_devops")
        elif project_type == "creative_writing":
            available_tools.append("bmad_creative")
        
        return list(set(available_tools))  # Remove duplicates
    
    @classmethod
    def get_master_tool_schema(cls, master_tool_name: str) -> Dict[str, Any]:
        """Get complete schema for a master tool"""
        if master_tool_name not in cls.MASTER_TOOL_GROUPS:
            return None
        
        config = cls.MASTER_TOOL_GROUPS[master_tool_name]
        return {
            "name": master_tool_name,
            "group": config["group"],
            "description": config["description"],
            "operations": config["operations"],
            "operation_count": len(config["operations"]),
            "type": "master_tool"
        }
    
    @classmethod
    def get_master_tool_operation_schema(cls, master_tool_name: str, operation_name: str) -> Dict[str, Any]:
        """Get schema for a specific master tool operation"""
        if master_tool_name not in cls.MASTER_TOOL_GROUPS:
            return None
        
        config = cls.MASTER_TOOL_GROUPS[master_tool_name]
        if operation_name not in config["operations"]:
            return None
        
        return {
            "master_tool": master_tool_name,
            "operation": operation_name,
            "full_name": f"{master_tool_name}.{operation_name}",
            "group": config["group"],
            "description": f"{config['description']} - {operation_name} operation",
            "type": "master_tool_operation"
        }
    
    @classmethod
    def validate_master_tool_configuration(cls) -> Dict[str, Any]:
        """Validate master tool configuration"""
        total_master_tools = len(cls.MASTER_TOOL_GROUPS)
        total_operations = sum(len(config["operations"]) for config in cls.MASTER_TOOL_GROUPS.values())
        
        # Check for duplicate operations across master tools
        all_operations = []
        for tool_name, config in cls.MASTER_TOOL_GROUPS.items():
            for operation in config["operations"]:
                all_operations.append(f"{tool_name}.{operation}")
        
        duplicate_operations = []
        operation_counts = {}
        for operation in all_operations:
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
            if operation_counts[operation] > 1:
                duplicate_operations.append(operation)
        
        return {
            "total_master_tools": total_master_tools,
            "total_operations": total_operations,
            "average_operations_per_tool": total_operations / total_master_tools if total_master_tools > 0 else 0,
            "duplicate_operations": duplicate_operations,
            "configuration_valid": len(duplicate_operations) == 0
        }
