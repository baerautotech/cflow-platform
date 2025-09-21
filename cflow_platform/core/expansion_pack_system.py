"""
BMAD Expansion Pack System

This module provides the core framework for domain-specific expansion packs
including Game Dev, DevOps, and Technical Research capabilities.
"""

import asyncio
import logging
import time
import uuid
import json
import importlib
import inspect
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class ExpansionPackStatus(Enum):
    """Expansion pack status"""
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPDATING = "updating"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class ExpansionPackType(Enum):
    """Expansion pack types"""
    GAME_DEV = "game_dev"
    DEVOPS = "devops"
    TECHNICAL_RESEARCH = "technical_research"
    CREATIVE_WRITING = "creative_writing"
    DATA_SCIENCE = "data_science"
    WEB_DEVELOPMENT = "web_development"


class AgentCapability(Enum):
    """Agent capabilities"""
    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    RESEARCH = "research"
    OPTIMIZATION = "optimization"


@dataclass
class ExpansionPackMetadata:
    """Expansion pack metadata"""
    pack_id: str
    name: str
    version: str
    description: str
    pack_type: ExpansionPackType
    author: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[AgentCapability] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    templates: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExpansionPackAgent:
    """Expansion pack agent definition"""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    tools: List[str]
    templates: List[str]
    workflows: List[str]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpansionPackTool:
    """Expansion pack tool definition"""
    tool_id: str
    name: str
    description: str
    category: str
    agent_id: str
    handler_function: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


class GameDevExpansionPack:
    """Game Development Expansion Pack"""
    
    def __init__(self):
        self.pack_id = "game_dev"
        self.name = "Game Development Expansion Pack"
        self.version = "1.0.0"
        self.description = "Specialized agents and tools for game development"
        self.pack_type = ExpansionPackType.GAME_DEV
        
        self.agents = self._create_game_dev_agents()
        self.tools = self._create_game_dev_tools()
        self.templates = self._create_game_dev_templates()
        self.workflows = self._create_game_dev_workflows()
    
    def _create_game_dev_agents(self) -> List[ExpansionPackAgent]:
        """Create game development agents"""
        
        return [
            ExpansionPackAgent(
                agent_id="game_designer",
                name="Game Designer",
                description="Specialized agent for game design and mechanics",
                capabilities=[AgentCapability.DESIGN, AgentCapability.ANALYSIS],
                tools=["game_mechanics_design", "level_design", "game_balance_analysis"],
                templates=["game_design_document", "level_design_spec"],
                workflows=["game_design_workflow", "level_creation_workflow"]
            ),
            ExpansionPackAgent(
                agent_id="game_programmer",
                name="Game Programmer",
                description="Specialized agent for game programming and implementation",
                capabilities=[AgentCapability.IMPLEMENTATION, AgentCapability.TESTING],
                tools=["game_code_generation", "performance_optimization", "bug_fixing"],
                templates=["game_code_template", "shader_template"],
                workflows=["game_development_workflow", "performance_optimization_workflow"]
            ),
            ExpansionPackAgent(
                agent_id="game_artist",
                name="Game Artist",
                description="Specialized agent for game art and visual design",
                capabilities=[AgentCapability.DESIGN, AgentCapability.IMPLEMENTATION],
                tools=["asset_generation", "texture_creation", "animation_design"],
                templates=["art_style_guide", "asset_pipeline_template"],
                workflows=["art_creation_workflow", "asset_pipeline_workflow"]
            )
        ]
    
    def _create_game_dev_tools(self) -> List[ExpansionPackTool]:
        """Create game development tools"""
        
        return [
            ExpansionPackTool(
                tool_id="game_mechanics_design",
                name="Game Mechanics Designer",
                description="Design and analyze game mechanics",
                category="design",
                agent_id="game_designer",
                handler_function="design_game_mechanics"
            ),
            ExpansionPackTool(
                tool_id="level_design",
                name="Level Designer",
                description="Create and design game levels",
                category="design",
                agent_id="game_designer",
                handler_function="design_level"
            ),
            ExpansionPackTool(
                tool_id="game_code_generation",
                name="Game Code Generator",
                description="Generate game code and scripts",
                category="implementation",
                agent_id="game_programmer",
                handler_function="generate_game_code"
            ),
            ExpansionPackTool(
                tool_id="asset_generation",
                name="Asset Generator",
                description="Generate game assets and resources",
                category="implementation",
                agent_id="game_artist",
                handler_function="generate_assets"
            )
        ]
    
    def _create_game_dev_templates(self) -> List[str]:
        """Create game development templates"""
        
        return [
            "game_design_document.yaml",
            "level_design_spec.yaml",
            "game_code_template.py",
            "shader_template.glsl",
            "art_style_guide.md",
            "asset_pipeline_template.yaml"
        ]
    
    def _create_game_dev_workflows(self) -> List[str]:
        """Create game development workflows"""
        
        return [
            "game_design_workflow.yaml",
            "level_creation_workflow.yaml",
            "game_development_workflow.yaml",
            "performance_optimization_workflow.yaml",
            "art_creation_workflow.yaml",
            "asset_pipeline_workflow.yaml"
        ]


class DevOpsExpansionPack:
    """DevOps Expansion Pack"""
    
    def __init__(self):
        self.pack_id = "devops"
        self.name = "DevOps Expansion Pack"
        self.version = "1.0.0"
        self.description = "Specialized agents and tools for DevOps operations"
        self.pack_type = ExpansionPackType.DEVOPS
        
        self.agents = self._create_devops_agents()
        self.tools = self._create_devops_tools()
        self.templates = self._create_devops_templates()
        self.workflows = self._create_devops_workflows()
    
    def _create_devops_agents(self) -> List[ExpansionPackAgent]:
        """Create DevOps agents"""
        
        return [
            ExpansionPackAgent(
                agent_id="infrastructure_engineer",
                name="Infrastructure Engineer",
                description="Specialized agent for infrastructure management",
                capabilities=[AgentCapability.DESIGN, AgentCapability.IMPLEMENTATION],
                tools=["infrastructure_provisioning", "config_management", "monitoring_setup"],
                templates=["infrastructure_template", "monitoring_config"],
                workflows=["infrastructure_deployment", "monitoring_setup"]
            ),
            ExpansionPackAgent(
                agent_id="ci_cd_engineer",
                name="CI/CD Engineer",
                description="Specialized agent for CI/CD pipeline management",
                capabilities=[AgentCapability.IMPLEMENTATION, AgentCapability.DEPLOYMENT],
                tools=["pipeline_creation", "deployment_automation", "rollback_management"],
                templates=["pipeline_template", "deployment_config"],
                workflows=["ci_cd_setup", "deployment_automation"]
            ),
            ExpansionPackAgent(
                agent_id="security_engineer",
                name="Security Engineer",
                description="Specialized agent for security and compliance",
                capabilities=[AgentCapability.ANALYSIS, AgentCapability.MONITORING],
                tools=["security_scanning", "compliance_checking", "vulnerability_assessment"],
                templates=["security_policy", "compliance_checklist"],
                workflows=["security_assessment", "compliance_validation"]
            )
        ]
    
    def _create_devops_tools(self) -> List[ExpansionPackTool]:
        """Create DevOps tools"""
        
        return [
            ExpansionPackTool(
                tool_id="infrastructure_provisioning",
                name="Infrastructure Provisioner",
                description="Provision and manage infrastructure resources",
                category="infrastructure",
                agent_id="infrastructure_engineer",
                handler_function="provision_infrastructure"
            ),
            ExpansionPackTool(
                tool_id="pipeline_creation",
                name="Pipeline Creator",
                description="Create and manage CI/CD pipelines",
                category="automation",
                agent_id="ci_cd_engineer",
                handler_function="create_pipeline"
            ),
            ExpansionPackTool(
                tool_id="security_scanning",
                name="Security Scanner",
                description="Scan for security vulnerabilities",
                category="security",
                agent_id="security_engineer",
                handler_function="scan_security"
            )
        ]
    
    def _create_devops_templates(self) -> List[str]:
        """Create DevOps templates"""
        
        return [
            "infrastructure_template.yaml",
            "monitoring_config.yaml",
            "pipeline_template.yaml",
            "deployment_config.yaml",
            "security_policy.yaml",
            "compliance_checklist.yaml"
        ]
    
    def _create_devops_workflows(self) -> List[str]:
        """Create DevOps workflows"""
        
        return [
            "infrastructure_deployment.yaml",
            "monitoring_setup.yaml",
            "ci_cd_setup.yaml",
            "deployment_automation.yaml",
            "security_assessment.yaml",
            "compliance_validation.yaml"
        ]


class TechnicalResearchExpansionPack:
    """Technical Research Expansion Pack"""
    
    def __init__(self):
        self.pack_id = "technical_research"
        self.name = "Technical Research Expansion Pack"
        self.version = "1.0.0"
        self.description = "Advanced research capabilities replacing Enhanced Research"
        self.pack_type = ExpansionPackType.TECHNICAL_RESEARCH
        
        self.agents = self._create_research_agents()
        self.tools = self._create_research_tools()
        self.templates = self._create_research_templates()
        self.workflows = self._create_research_workflows()
    
    def _create_research_agents(self) -> List[ExpansionPackAgent]:
        """Create technical research agents"""
        
        return [
            ExpansionPackAgent(
                agent_id="research_analyst",
                name="Research Analyst",
                description="Specialized agent for technical research and analysis",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
                tools=["literature_review", "technical_analysis", "trend_analysis"],
                templates=["research_proposal", "technical_report"],
                workflows=["research_methodology", "analysis_workflow"]
            ),
            ExpansionPackAgent(
                agent_id="innovation_engineer",
                name="Innovation Engineer",
                description="Specialized agent for innovation and optimization",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.OPTIMIZATION],
                tools=["innovation_assessment", "optimization_analysis", "feasibility_study"],
                templates=["innovation_proposal", "optimization_report"],
                workflows=["innovation_process", "optimization_workflow"]
            ),
            ExpansionPackAgent(
                agent_id="knowledge_synthesizer",
                name="Knowledge Synthesizer",
                description="Specialized agent for knowledge synthesis and documentation",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.DESIGN],
                tools=["knowledge_synthesis", "documentation_generation", "knowledge_graph"],
                templates=["knowledge_base", "synthesis_report"],
                workflows=["knowledge_synthesis", "documentation_workflow"]
            )
        ]
    
    def _create_research_tools(self) -> List[ExpansionPackTool]:
        """Create technical research tools"""
        
        return [
            ExpansionPackTool(
                tool_id="literature_review",
                name="Literature Reviewer",
                description="Conduct comprehensive literature reviews",
                category="research",
                agent_id="research_analyst",
                handler_function="conduct_literature_review"
            ),
            ExpansionPackTool(
                tool_id="innovation_assessment",
                name="Innovation Assessor",
                description="Assess innovation potential and feasibility",
                category="innovation",
                agent_id="innovation_engineer",
                handler_function="assess_innovation"
            ),
            ExpansionPackTool(
                tool_id="knowledge_synthesis",
                name="Knowledge Synthesizer",
                description="Synthesize knowledge from multiple sources",
                category="knowledge",
                agent_id="knowledge_synthesizer",
                handler_function="synthesize_knowledge"
            )
        ]
    
    def _create_research_templates(self) -> List[str]:
        """Create technical research templates"""
        
        return [
            "research_proposal.yaml",
            "technical_report.yaml",
            "innovation_proposal.yaml",
            "optimization_report.yaml",
            "knowledge_base.yaml",
            "synthesis_report.yaml"
        ]
    
    def _create_research_workflows(self) -> List[str]:
        """Create technical research workflows"""
        
        return [
            "research_methodology.yaml",
            "analysis_workflow.yaml",
            "innovation_process.yaml",
            "optimization_workflow.yaml",
            "knowledge_synthesis.yaml",
            "documentation_workflow.yaml"
        ]


class ExpansionPackManager:
    """Manager for expansion packs"""
    
    def __init__(self):
        self.installed_packs: Dict[str, ExpansionPackMetadata] = {}
        self.active_packs: Dict[str, ExpansionPackMetadata] = {}
        self.pack_registry: Dict[str, Type] = {
            "game_dev": GameDevExpansionPack,
            "devops": DevOpsExpansionPack,
            "technical_research": TechnicalResearchExpansionPack
        }
        self.pack_instances: Dict[str, Any] = {}
    
    def get_available_packs(self) -> List[ExpansionPackMetadata]:
        """Get list of available expansion packs"""
        
        available_packs = []
        for pack_id, pack_class in self.pack_registry.items():
            pack_instance = pack_class()
            metadata = ExpansionPackMetadata(
                pack_id=pack_instance.pack_id,
                name=pack_instance.name,
                version=pack_instance.version,
                description=pack_instance.description,
                pack_type=pack_instance.pack_type,
                author="BMAD Team",
                agents=[agent.agent_id for agent in pack_instance.agents],
                tools=[tool.tool_id for tool in pack_instance.tools],
                templates=pack_instance.templates,
                workflows=pack_instance.workflows
            )
            available_packs.append(metadata)
        
        return available_packs
    
    def install_pack(self, pack_id: str) -> Dict[str, Any]:
        """Install an expansion pack"""
        
        if pack_id not in self.pack_registry:
            raise ValueError(f"Unknown expansion pack: {pack_id}")
        
        if pack_id in self.installed_packs:
            return {"success": False, "message": f"Pack {pack_id} already installed"}
        
        try:
            # Create pack instance
            pack_class = self.pack_registry[pack_id]
            pack_instance = pack_class()
            
            # Create metadata
            metadata = ExpansionPackMetadata(
                pack_id=pack_instance.pack_id,
                name=pack_instance.name,
                version=pack_instance.version,
                description=pack_instance.description,
                pack_type=pack_instance.pack_type,
                author="BMAD Team",
                agents=[agent.agent_id for agent in pack_instance.agents],
                tools=[tool.tool_id for tool in pack_instance.tools],
                templates=pack_instance.templates,
                workflows=pack_instance.workflows
            )
            
            # Store pack
            self.installed_packs[pack_id] = metadata
            self.pack_instances[pack_id] = pack_instance
            
            logger.info(f"Installed expansion pack: {pack_id}")
            
            return {
                "success": True,
                "message": f"Successfully installed {pack_id}",
                "pack_metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to install pack {pack_id}: {e}")
            return {"success": False, "message": f"Failed to install {pack_id}: {e}"}
    
    def uninstall_pack(self, pack_id: str) -> Dict[str, Any]:
        """Uninstall an expansion pack"""
        
        if pack_id not in self.installed_packs:
            return {"success": False, "message": f"Pack {pack_id} not installed"}
        
        try:
            # Deactivate if active
            if pack_id in self.active_packs:
                self.deactivate_pack(pack_id)
            
            # Remove from installed packs
            del self.installed_packs[pack_id]
            del self.pack_instances[pack_id]
            
            logger.info(f"Uninstalled expansion pack: {pack_id}")
            
            return {
                "success": True,
                "message": f"Successfully uninstalled {pack_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall pack {pack_id}: {e}")
            return {"success": False, "message": f"Failed to uninstall {pack_id}: {e}"}
    
    def activate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Activate an expansion pack"""
        
        if pack_id not in self.installed_packs:
            return {"success": False, "message": f"Pack {pack_id} not installed"}
        
        if pack_id in self.active_packs:
            return {"success": False, "message": f"Pack {pack_id} already active"}
        
        try:
            # Activate pack
            self.active_packs[pack_id] = self.installed_packs[pack_id]
            
            logger.info(f"Activated expansion pack: {pack_id}")
            
            return {
                "success": True,
                "message": f"Successfully activated {pack_id}",
                "pack_metadata": self.active_packs[pack_id]
            }
            
        except Exception as e:
            logger.error(f"Failed to activate pack {pack_id}: {e}")
            return {"success": False, "message": f"Failed to activate {pack_id}: {e}"}
    
    def deactivate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Deactivate an expansion pack"""
        
        if pack_id not in self.active_packs:
            return {"success": False, "message": f"Pack {pack_id} not active"}
        
        try:
            # Deactivate pack
            del self.active_packs[pack_id]
            
            logger.info(f"Deactivated expansion pack: {pack_id}")
            
            return {
                "success": True,
                "message": f"Successfully deactivated {pack_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to deactivate pack {pack_id}: {e}")
            return {"success": False, "message": f"Failed to deactivate {pack_id}: {e}"}
    
    def get_pack_status(self, pack_id: str) -> Dict[str, Any]:
        """Get expansion pack status"""
        
        status = "uninstalled"
        if pack_id in self.installed_packs:
            status = "installed"
        if pack_id in self.active_packs:
            status = "active"
        
        return {
            "pack_id": pack_id,
            "status": status,
            "installed": pack_id in self.installed_packs,
            "active": pack_id in self.active_packs
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get expansion pack system status"""
        
        return {
            "total_available": len(self.pack_registry),
            "total_installed": len(self.installed_packs),
            "total_active": len(self.active_packs),
            "available_packs": list(self.pack_registry.keys()),
            "installed_packs": list(self.installed_packs.keys()),
            "active_packs": list(self.active_packs.keys())
        }
    
    def validate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Validate expansion pack integrity"""
        
        if pack_id not in self.installed_packs:
            return {"success": False, "message": f"Pack {pack_id} not installed"}
        
        try:
            pack_instance = self.pack_instances[pack_id]
            metadata = self.installed_packs[pack_id]
            
            # Validate pack structure
            validation_results = {
                "agents_count": len(pack_instance.agents),
                "tools_count": len(pack_instance.tools),
                "templates_count": len(pack_instance.templates),
                "workflows_count": len(pack_instance.workflows),
                "metadata_valid": metadata.pack_id == pack_instance.pack_id,
                "version_valid": metadata.version == pack_instance.version
            }
            
            all_valid = all(validation_results.values())
            
            return {
                "success": all_valid,
                "message": f"Pack {pack_id} validation {'passed' if all_valid else 'failed'}",
                "validation_results": validation_results
            }
            
        except Exception as e:
            logger.error(f"Failed to validate pack {pack_id}: {e}")
            return {"success": False, "message": f"Failed to validate {pack_id}: {e}"}


class ExpansionPackSystem:
    """Main expansion pack system"""
    
    def __init__(self):
        self.manager = ExpansionPackManager()
        self.system_active = False
    
    async def initialize_system(self):
        """Initialize the expansion pack system"""
        
        try:
            # Initialize system
            self.system_active = True
            
            # Auto-install core packs
            core_packs = ["game_dev", "devops", "technical_research"]
            for pack_id in core_packs:
                result = self.manager.install_pack(pack_id)
                if result["success"]:
                    # Auto-activate core packs
                    self.manager.activate_pack(pack_id)
            
            logger.info("Expansion pack system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize expansion pack system: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get expansion pack system status"""
        
        return {
            "system_active": self.system_active,
            "manager_status": self.manager.get_system_status(),
            "initialized_at": datetime.now().isoformat()
        }
    
    def list_available_packs(self) -> List[ExpansionPackMetadata]:
        """List available expansion packs"""
        
        return self.manager.get_available_packs()
    
    def list_installed_packs(self) -> List[ExpansionPackMetadata]:
        """List installed expansion packs"""
        
        return list(self.manager.installed_packs.values())
    
    def list_active_packs(self) -> List[ExpansionPackMetadata]:
        """List active expansion packs"""
        
        return list(self.manager.active_packs.values())
    
    def install_pack(self, pack_id: str) -> Dict[str, Any]:
        """Install an expansion pack"""
        
        return self.manager.install_pack(pack_id)
    
    def uninstall_pack(self, pack_id: str) -> Dict[str, Any]:
        """Uninstall an expansion pack"""
        
        return self.manager.uninstall_pack(pack_id)
    
    def activate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Activate an expansion pack"""
        
        return self.manager.activate_pack(pack_id)
    
    def deactivate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Deactivate an expansion pack"""
        
        return self.manager.deactivate_pack(pack_id)
    
    def get_pack_status(self, pack_id: str) -> Dict[str, Any]:
        """Get expansion pack status"""
        
        return self.manager.get_pack_status(pack_id)
    
    def validate_pack(self, pack_id: str) -> Dict[str, Any]:
        """Validate expansion pack integrity"""
        
        return self.manager.validate_pack(pack_id)


# Global instance
_expansion_system: Optional[ExpansionPackSystem] = None


def get_expansion_system() -> ExpansionPackSystem:
    """Get the global expansion pack system instance"""
    global _expansion_system
    if _expansion_system is None:
        _expansion_system = ExpansionPackSystem()
    return _expansion_system
