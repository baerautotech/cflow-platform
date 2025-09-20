"""
Client Tool Configuration for BMAD WebMCP Server

This module provides client-specific tool configuration capabilities to manage
tool exposure based on client type, capabilities, and legal compliance.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class ClientType(Enum):
    """Supported client types"""
    CURSOR = "cursor"
    MOBILE = "mobile"
    WEB = "web"
    IDE = "ide"
    CLI = "cli"


@dataclass
class ClientCapabilities:
    """Client capabilities and limitations"""
    max_tools: int
    supports_interactive: bool
    supports_file_operations: bool
    supports_network_operations: bool
    supports_desktop_notifications: bool
    supports_sandbox_execution: bool
    supports_git_operations: bool
    supports_expansion_packs: bool


@dataclass
class ClientToolConfig:
    """Configuration for a specific client type"""
    client_type: ClientType
    capabilities: ClientCapabilities
    enabled_groups: List[str]
    disabled_tools: List[str]
    project_specific: bool
    legal_compliance_required: bool
    description: str


class ClientToolConfigManager:
    """Manages client-specific tool configurations"""
    
    # Master tool configurations for each client type
    MASTER_TOOL_CONFIGS = {
        "cursor": {
            "enabled_groups": ["core", "advanced"],
            "disabled_tools": [],
            "max_tools": 50,
            "master_tools": {
                "bmad_task": {"enabled": True, "operations": ["create", "get", "update", "delete", "list"]},
                "bmad_plan": {"enabled": True, "operations": ["create", "get", "update", "list", "execute"]},
                "bmad_doc": {"enabled": True, "operations": ["create", "get", "update", "approve", "list"]},
                "bmad_workflow": {"enabled": True, "operations": ["create", "execute", "status", "list"]},
                "bmad_hil": {"enabled": True, "operations": ["request", "status", "approve"]},
                "bmad_git": {"enabled": True, "operations": ["commit", "push", "pull", "create_branch", "merge"]},
                "bmad_orchestrator": {"enabled": True, "operations": ["start", "stop", "status"]},
                "bmad_expansion": {"enabled": False, "operations": []}
            }
        },
        "mobile": {
            "enabled_groups": ["core"],
            "disabled_tools": [],
            "max_tools": 25,
            "master_tools": {
                "bmad_task": {"enabled": True, "operations": ["create", "get", "update", "list"]},
                "bmad_plan": {"enabled": True, "operations": ["create", "get", "list"]},
                "bmad_doc": {"enabled": True, "operations": ["create", "get", "list"]},
                "bmad_workflow": {"enabled": True, "operations": ["create", "status", "list"]},
                "bmad_hil": {"enabled": True, "operations": ["request", "status"]},
                "bmad_git": {"enabled": False, "operations": []},
                "bmad_orchestrator": {"enabled": False, "operations": []},
                "bmad_expansion": {"enabled": False, "operations": []}
            }
        },
        "web": {
            "enabled_groups": ["core", "advanced", "expansion"],
            "disabled_tools": [],
            "max_tools": 100,
            "master_tools": {
                "bmad_task": {"enabled": True, "operations": ["create", "get", "update", "delete", "list", "search"]},
                "bmad_plan": {"enabled": True, "operations": ["create", "get", "update", "list", "execute"]},
                "bmad_doc": {"enabled": True, "operations": ["create", "get", "update", "approve", "list"]},
                "bmad_workflow": {"enabled": True, "operations": ["create", "execute", "status", "list"]},
                "bmad_hil": {"enabled": True, "operations": ["request", "status", "approve", "list"]},
                "bmad_git": {"enabled": True, "operations": ["commit", "push", "pull", "create_branch", "merge", "status"]},
                "bmad_orchestrator": {"enabled": True, "operations": ["start", "stop", "status", "list"]},
                "bmad_expansion": {"enabled": True, "operations": ["install", "uninstall", "list", "update", "info"]},
                "bmad_gamedev": {"enabled": True, "operations": ["create_project", "generate_assets", "optimize_performance", "test_build", "deploy"]},
                "bmad_devops": {"enabled": True, "operations": ["deploy", "monitor", "scale", "backup", "rollback"]},
                "bmad_creative": {"enabled": True, "operations": ["generate_content", "edit_content", "analyze_content", "generate_ideas", "translate"]}
            }
        },
        "ide": {
            "enabled_groups": ["core", "advanced"],
            "disabled_tools": [],
            "max_tools": 60,
            "master_tools": {
                "bmad_task": {"enabled": True, "operations": ["create", "get", "update", "delete", "list", "search"]},
                "bmad_plan": {"enabled": True, "operations": ["create", "get", "update", "list", "execute"]},
                "bmad_doc": {"enabled": True, "operations": ["create", "get", "update", "approve", "list"]},
                "bmad_workflow": {"enabled": True, "operations": ["create", "execute", "status", "list"]},
                "bmad_hil": {"enabled": True, "operations": ["request", "status", "approve", "list"]},
                "bmad_git": {"enabled": True, "operations": ["commit", "push", "pull", "create_branch", "merge", "status"]},
                "bmad_orchestrator": {"enabled": True, "operations": ["start", "stop", "status", "list"]},
                "bmad_expansion": {"enabled": True, "operations": ["install", "uninstall", "list", "update", "info"]}
            }
        },
        "cli": {
            "enabled_groups": ["core"],
            "disabled_tools": [],
            "max_tools": 20,
            "master_tools": {
                "bmad_task": {"enabled": True, "operations": ["create", "get", "list"]},
                "bmad_plan": {"enabled": True, "operations": ["create", "get", "list"]},
                "bmad_doc": {"enabled": True, "operations": ["create", "get", "list"]},
                "bmad_workflow": {"enabled": True, "operations": ["create", "status", "list"]},
                "bmad_hil": {"enabled": False, "operations": []},
                "bmad_git": {"enabled": True, "operations": ["commit", "push", "pull"]},
                "bmad_orchestrator": {"enabled": False, "operations": []},
                "bmad_expansion": {"enabled": False, "operations": []}
            }
        }
    }
    
    CLIENT_CONFIGS: Dict[ClientType, ClientToolConfig] = {
        ClientType.CURSOR: ClientToolConfig(
            client_type=ClientType.CURSOR,
            capabilities=ClientCapabilities(
                max_tools=50,
                supports_interactive=True,
                supports_file_operations=True,
                supports_network_operations=True,
                supports_desktop_notifications=False,
                supports_sandbox_execution=True,
                supports_git_operations=True,
                supports_expansion_packs=False
            ),
            enabled_groups=["core", "planning", "development", "git", "sandbox", "reasoning"],
            disabled_tools=["desktop.notify", "sys_debug", "bmad_expansion_packs_*"],
            project_specific=True,
            legal_compliance_required=True,
            description="Cursor IDE integration with focused development tools"
        ),
        
        ClientType.MOBILE: ClientToolConfig(
            client_type=ClientType.MOBILE,
            capabilities=ClientCapabilities(
                max_tools=30,
                supports_interactive=True,
                supports_file_operations=False,
                supports_network_operations=True,
                supports_desktop_notifications=True,
                supports_sandbox_execution=False,
                supports_git_operations=False,
                supports_expansion_packs=False
            ),
            enabled_groups=["core", "hil"],
            disabled_tools=["codegen.*", "lint_*", "test_*", "sandbox.*", "git.*"],
            project_specific=False,
            legal_compliance_required=True,
            description="Mobile app with HIL and core BMAD functionality"
        ),
        
        ClientType.WEB: ClientToolConfig(
            client_type=ClientType.WEB,
            capabilities=ClientCapabilities(
                max_tools=100,
                supports_interactive=True,
                supports_file_operations=True,
                supports_network_operations=True,
                supports_desktop_notifications=False,
                supports_sandbox_execution=True,
                supports_git_operations=True,
                supports_expansion_packs=True
            ),
            enabled_groups=["core", "planning", "hil", "expansion", "development", "research", "system", "git", "memory"],
            disabled_tools=[],
            project_specific=True,
            legal_compliance_required=False,
            description="Full web client with complete BMAD functionality"
        ),
        
        ClientType.IDE: ClientToolConfig(
            client_type=ClientType.IDE,
            capabilities=ClientCapabilities(
                max_tools=75,
                supports_interactive=True,
                supports_file_operations=True,
                supports_network_operations=True,
                supports_desktop_notifications=True,
                supports_sandbox_execution=True,
                supports_git_operations=True,
                supports_expansion_packs=True
            ),
            enabled_groups=["core", "planning", "development", "git", "sandbox", "reasoning", "memory"],
            disabled_tools=["desktop.notify"],
            project_specific=True,
            legal_compliance_required=True,
            description="Generic IDE integration with development-focused tools"
        ),
        
        ClientType.CLI: ClientToolConfig(
            client_type=ClientType.CLI,
            capabilities=ClientCapabilities(
                max_tools=40,
                supports_interactive=False,
                supports_file_operations=True,
                supports_network_operations=True,
                supports_desktop_notifications=False,
                supports_sandbox_execution=False,
                supports_git_operations=True,
                supports_expansion_packs=False
            ),
            enabled_groups=["core", "planning", "git"],
            disabled_tools=["bmad_hil_*", "desktop.notify", "sandbox.*", "enh_*"],
            project_specific=True,
            legal_compliance_required=True,
            description="Command-line interface with essential BMAD tools"
        )
    }
    
    @classmethod
    def get_config_for_client(cls, client_type: str) -> Optional[ClientToolConfig]:
        """Get configuration for a specific client type"""
        try:
            client_enum = ClientType(client_type.lower())
            return cls.CLIENT_CONFIGS.get(client_enum)
        except ValueError:
            return None
    
    @classmethod
    def get_max_tools_for_client(cls, client_type: str) -> int:
        """Get maximum tools allowed for a client type"""
        config = cls.get_config_for_client(client_type)
        return config.capabilities.max_tools if config else 100
    
    @classmethod
    def get_enabled_groups_for_client(cls, client_type: str) -> List[str]:
        """Get enabled tool groups for a client type"""
        config = cls.get_config_for_client(client_type)
        return config.enabled_groups if config else []
    
    @classmethod
    def get_disabled_tools_for_client(cls, client_type: str) -> List[str]:
        """Get disabled tools for a client type"""
        config = cls.get_config_for_client(client_type)
        return config.disabled_tools if config else []
    
    @classmethod
    def is_project_specific_for_client(cls, client_type: str) -> bool:
        """Check if client supports project-specific tool filtering"""
        config = cls.get_config_for_client(client_type)
        return config.project_specific if config else False
    
    @classmethod
    def requires_legal_compliance(cls, client_type: str) -> bool:
        """Check if client requires legal compliance filtering"""
        config = cls.get_config_for_client(client_type)
        return config.legal_compliance_required if config else False
    
    @classmethod
    def supports_capability(cls, client_type: str, capability: str) -> bool:
        """Check if client supports a specific capability"""
        config = cls.get_config_for_client(client_type)
        if not config:
            return False
        
        capabilities = config.capabilities
        capability_map = {
            "interactive": capabilities.supports_interactive,
            "file_operations": capabilities.supports_file_operations,
            "network_operations": capabilities.supports_network_operations,
            "desktop_notifications": capabilities.supports_desktop_notifications,
            "sandbox_execution": capabilities.supports_sandbox_execution,
            "git_operations": capabilities.supports_git_operations,
            "expansion_packs": capabilities.supports_expansion_packs
        }
        
        return capability_map.get(capability, False)
    
    @classmethod
    def get_all_client_types(cls) -> List[str]:
        """Get all supported client types"""
        return [client_type.value for client_type in ClientType]
    
    @classmethod
    def validate_client_config(cls, client_type: str) -> Dict[str, Any]:
        """Validate client configuration"""
        config = cls.get_config_for_client(client_type)
        
        if not config:
            return {
                "valid": False,
                "error": f"Unknown client type: {client_type}",
                "supported_types": cls.get_all_client_types()
            }
        
        return {
            "valid": True,
            "client_type": client_type,
            "max_tools": config.capabilities.max_tools,
            "enabled_groups": config.enabled_groups,
            "disabled_tools": config.disabled_tools,
            "project_specific": config.project_specific,
            "legal_compliance_required": config.legal_compliance_required,
            "description": config.description
        }
    
    # Master Tool Configuration Methods
    
    @classmethod
    def get_master_tool_config_for_client(cls, client_type: str) -> Optional[Dict[str, Any]]:
        """Get master tool configuration for a specific client type"""
        return cls.MASTER_TOOL_CONFIGS.get(client_type.lower())
    
    @classmethod
    def get_enabled_master_tools_for_client(cls, client_type: str) -> List[str]:
        """Get enabled master tools for a client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        if not config:
            return []
        
        enabled_tools = []
        for tool_name, tool_config in config["master_tools"].items():
            if tool_config["enabled"]:
                enabled_tools.append(tool_name)
        
        return enabled_tools
    
    @classmethod
    def get_enabled_operations_for_master_tool(cls, client_type: str, master_tool_name: str) -> List[str]:
        """Get enabled operations for a specific master tool and client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        if not config or master_tool_name not in config["master_tools"]:
            return []
        
        tool_config = config["master_tools"][master_tool_name]
        return tool_config["operations"] if tool_config["enabled"] else []
    
    @classmethod
    def get_master_tool_count_for_client(cls, client_type: str) -> int:
        """Get total number of master tool operations available for a client"""
        config = cls.get_master_tool_config_for_client(client_type)
        if not config:
            return 0
        
        total_operations = 0
        for tool_config in config["master_tools"].values():
            if tool_config["enabled"]:
                total_operations += len(tool_config["operations"])
        
        return total_operations
    
    @classmethod
    def is_master_tool_enabled_for_client(cls, client_type: str, master_tool_name: str) -> bool:
        """Check if a master tool is enabled for a client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        if not config or master_tool_name not in config["master_tools"]:
            return False
        
        return config["master_tools"][master_tool_name]["enabled"]
    
    @classmethod
    def is_master_tool_operation_enabled(cls, client_type: str, master_tool_name: str, operation_name: str) -> bool:
        """Check if a master tool operation is enabled for a client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        if not config or master_tool_name not in config["master_tools"]:
            return False
        
        tool_config = config["master_tools"][master_tool_name]
        return tool_config["enabled"] and operation_name in tool_config["operations"]
    
    @classmethod
    def get_master_tool_groups_for_client(cls, client_type: str) -> List[str]:
        """Get enabled master tool groups for a client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        return config["enabled_groups"] if config else []
    
    @classmethod
    def validate_master_tool_config(cls, client_type: str) -> Dict[str, Any]:
        """Validate master tool configuration for a client type"""
        config = cls.get_master_tool_config_for_client(client_type)
        
        if not config:
            return {
                "valid": False,
                "error": f"No master tool configuration found for client type: {client_type}",
                "supported_clients": list(cls.MASTER_TOOL_CONFIGS.keys())
            }
        
        enabled_tools = cls.get_enabled_master_tools_for_client(client_type)
        total_operations = cls.get_master_tool_count_for_client(client_type)
        
        return {
            "valid": True,
            "client_type": client_type,
            "enabled_groups": config["enabled_groups"],
            "enabled_master_tools": enabled_tools,
            "total_master_tools": len(enabled_tools),
            "total_operations": total_operations,
            "max_tools": config["max_tools"],
            "within_limits": total_operations <= config["max_tools"]
        }
