"""
Project Tool Filter for BMAD WebMCP Server

This module provides project-specific tool filtering capabilities to manage
tool exposure based on project type, requirements, and domain-specific needs.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class ProjectType(Enum):
    """Supported project types"""
    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    GAME_DEV = "game_dev"
    DEVOPS = "devops"
    CREATIVE_WRITING = "creative_writing"
    DATA_SCIENCE = "data_science"
    BUSINESS_STRATEGY = "business_strategy"
    HEALTH_WELLNESS = "health_wellness"
    EDUCATION = "education"
    LEGAL_ASSISTANT = "legal_assistant"
    RESEARCH = "research"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class ProjectToolFilter:
    """Tool filtering configuration for a specific project type"""
    project_type: ProjectType
    enabled_groups: List[str]
    disabled_tools: List[str]
    required_expansion_packs: List[str]
    optional_expansion_packs: List[str]
    domain_specific_tools: List[str]
    description: str


class ProjectToolFilterManager:
    """Manages project-specific tool filtering"""
    
    PROJECT_FILTERS: Dict[ProjectType, ProjectToolFilter] = {
        ProjectType.GREENFIELD: ProjectToolFilter(
            project_type=ProjectType.GREENFIELD,
            enabled_groups=["core", "planning", "development", "git", "sandbox", "reasoning"],
            disabled_tools=["bmad_brownfield_*", "research", "doc_research"],
            required_expansion_packs=[],
            optional_expansion_packs=["technical_research"],
            domain_specific_tools=["bmad_prd_create", "bmad_arch_create", "bmad_story_create"],
            description="New project development from scratch"
        ),
        
        ProjectType.BROWNFIELD: ProjectToolFilter(
            project_type=ProjectType.BROWNFIELD,
            enabled_groups=["core", "planning", "development", "research", "git", "sandbox", "reasoning"],
            disabled_tools=["bmad_greenfield_*"],
            required_expansion_packs=["technical_research"],
            optional_expansion_packs=["documentation"],
            domain_specific_tools=["research", "doc_research", "bmad_document_project"],
            description="Enhancement of existing systems"
        ),
        
        ProjectType.GAME_DEV: ProjectToolFilter(
            project_type=ProjectType.GAME_DEV,
            enabled_groups=["core", "planning", "expansion", "development", "git"],
            disabled_tools=["bmad_brownfield_*", "research", "doc_research"],
            required_expansion_packs=["game_dev"],
            optional_expansion_packs=["creative_writing", "technical_research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_game_dev_*"],
            description="Game development with specialized agents"
        ),
        
        ProjectType.DEVOPS: ProjectToolFilter(
            project_type=ProjectType.DEVOPS,
            enabled_groups=["core", "planning", "expansion", "development", "git"],
            disabled_tools=["bmad_brownfield_*", "research", "doc_research"],
            required_expansion_packs=["devops"],
            optional_expansion_packs=["infrastructure", "technical_research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_devops_*"],
            description="DevOps and infrastructure automation"
        ),
        
        ProjectType.CREATIVE_WRITING: ProjectToolFilter(
            project_type=ProjectType.CREATIVE_WRITING,
            enabled_groups=["core", "planning", "expansion", "research"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["creative_writing"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_creative_writing_*"],
            description="Creative writing and content creation"
        ),
        
        ProjectType.DATA_SCIENCE: ProjectToolFilter(
            project_type=ProjectType.DATA_SCIENCE,
            enabled_groups=["core", "planning", "expansion", "development", "research"],
            disabled_tools=["bmad_brownfield_*"],
            required_expansion_packs=["data_science"],
            optional_expansion_packs=["technical_research", "research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_data_science_*"],
            description="Data science and machine learning projects"
        ),
        
        ProjectType.BUSINESS_STRATEGY: ProjectToolFilter(
            project_type=ProjectType.BUSINESS_STRATEGY,
            enabled_groups=["core", "planning", "expansion", "research"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["business_strategy"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_business_strategy_*"],
            description="Business strategy and planning"
        ),
        
        ProjectType.HEALTH_WELLNESS: ProjectToolFilter(
            project_type=ProjectType.HEALTH_WELLNESS,
            enabled_groups=["core", "planning", "expansion", "research"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["health_wellness"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_health_wellness_*"],
            description="Health and wellness applications"
        ),
        
        ProjectType.EDUCATION: ProjectToolFilter(
            project_type=ProjectType.EDUCATION,
            enabled_groups=["core", "planning", "expansion", "research"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["education"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_education_*"],
            description="Educational content and curriculum design"
        ),
        
        ProjectType.LEGAL_ASSISTANT: ProjectToolFilter(
            project_type=ProjectType.LEGAL_ASSISTANT,
            enabled_groups=["core", "planning", "expansion", "research"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["legal_assistant"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_legal_assistant_*"],
            description="Legal research and compliance"
        ),
        
        ProjectType.RESEARCH: ProjectToolFilter(
            project_type=ProjectType.RESEARCH,
            enabled_groups=["core", "planning", "research", "expansion"],
            disabled_tools=["bmad_brownfield_*", "codegen.*", "lint_*", "test_*", "sandbox.*"],
            required_expansion_packs=["technical_research"],
            optional_expansion_packs=["research"],
            domain_specific_tools=["research", "doc_research", "internet_search"],
            description="Technical research and documentation"
        ),
        
        ProjectType.INFRASTRUCTURE: ProjectToolFilter(
            project_type=ProjectType.INFRASTRUCTURE,
            enabled_groups=["core", "planning", "expansion", "development", "git"],
            disabled_tools=["bmad_brownfield_*"],
            required_expansion_packs=["infrastructure"],
            optional_expansion_packs=["devops", "technical_research"],
            domain_specific_tools=["bmad_expansion_packs_enable", "bmad_infrastructure_*"],
            description="Infrastructure and platform engineering"
        )
    }
    
    @classmethod
    def get_filter_for_project_type(cls, project_type: str) -> Optional[ProjectToolFilter]:
        """Get filter configuration for a specific project type"""
        try:
            project_enum = ProjectType(project_type.lower())
            return cls.PROJECT_FILTERS.get(project_enum)
        except ValueError:
            return None
    
    @classmethod
    def get_enabled_groups_for_project(cls, project_type: str) -> List[str]:
        """Get enabled tool groups for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        return filter_config.enabled_groups if filter_config else []
    
    @classmethod
    def get_disabled_tools_for_project(cls, project_type: str) -> List[str]:
        """Get disabled tools for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        return filter_config.disabled_tools if filter_config else []
    
    @classmethod
    def get_required_expansion_packs(cls, project_type: str) -> List[str]:
        """Get required expansion packs for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        return filter_config.required_expansion_packs if filter_config else []
    
    @classmethod
    def get_optional_expansion_packs(cls, project_type: str) -> List[str]:
        """Get optional expansion packs for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        return filter_config.optional_expansion_packs if filter_config else []
    
    @classmethod
    def get_domain_specific_tools(cls, project_type: str) -> List[str]:
        """Get domain-specific tools for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        return filter_config.domain_specific_tools if filter_config else []
    
    @classmethod
    def get_all_project_types(cls) -> List[str]:
        """Get all supported project types"""
        return [project_type.value for project_type in ProjectType]
    
    @classmethod
    def validate_project_filter(cls, project_type: str) -> Dict[str, Any]:
        """Validate project filter configuration"""
        filter_config = cls.get_filter_for_project_type(project_type)
        
        if not filter_config:
            return {
                "valid": False,
                "error": f"Unknown project type: {project_type}",
                "supported_types": cls.get_all_project_types()
            }
        
        return {
            "valid": True,
            "project_type": project_type,
            "enabled_groups": filter_config.enabled_groups,
            "disabled_tools": filter_config.disabled_tools,
            "required_expansion_packs": filter_config.required_expansion_packs,
            "optional_expansion_packs": filter_config.optional_expansion_packs,
            "domain_specific_tools": filter_config.domain_specific_tools,
            "description": filter_config.description
        }
    
    @classmethod
    def get_expansion_pack_requirements(cls, project_type: str) -> Dict[str, List[str]]:
        """Get expansion pack requirements for a project type"""
        filter_config = cls.get_filter_for_project_type(project_type)
        
        if not filter_config:
            return {"required": [], "optional": []}
        
        return {
            "required": filter_config.required_expansion_packs,
            "optional": filter_config.optional_expansion_packs
        }
    
    @classmethod
    def is_tool_disabled_for_project(cls, tool_name: str, project_type: str) -> bool:
        """Check if a tool is disabled for a specific project type"""
        disabled_tools = cls.get_disabled_tools_for_project(project_type)
        
        for disabled_pattern in disabled_tools:
            if disabled_pattern.endswith("*"):
                # Wildcard pattern matching
                if tool_name.startswith(disabled_pattern[:-1]):
                    return True
            elif tool_name == disabled_pattern:
                return True
        
        return False
    
    @classmethod
    def is_tool_domain_specific(cls, tool_name: str, project_type: str) -> bool:
        """Check if a tool is domain-specific for a project type"""
        domain_tools = cls.get_domain_specific_tools(project_type)
        return tool_name in domain_tools
