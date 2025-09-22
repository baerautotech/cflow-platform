#!/usr/bin/env python3
"""
BMAD Master Background Agent Orchestrator

Manages background agents for parallel processing of BMAD workflows.
This orchestrator coordinates multiple agents working on different aspects
of the BMAD Master system simultaneously.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class AgentType(Enum):
    """Agent type enumeration"""
    PERSONA_MANAGER = "persona_manager"
    TOOL_COORDINATOR = "tool_coordinator"
    TESTING_ORCHESTRATOR = "testing_orchestrator"
    EXPANSION_MANAGER = "expansion_manager"
    MONITORING_AGENT = "monitoring_agent"
    DEPLOYMENT_AGENT = "deployment_agent"

@dataclass
class BackgroundAgent:
    """Represents a background agent"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    status: AgentStatus
    last_activity: datetime
    current_task: Optional[str] = None
    task_queue: List[str] = None
    capabilities: List[str] = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.task_queue is None:
            self.task_queue = []
        if self.capabilities is None:
            self.capabilities = []
        if self.performance_metrics is None:
            self.performance_metrics = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'average_response_time': 0.0,
                'uptime': 0.0
            }

class BackgroundAgentOrchestrator:
    """Orchestrates background agents for parallel BMAD processing"""
    
    def __init__(self):
        self.agents: Dict[str, BackgroundAgent] = {}
        self.task_distribution_queue: List[Dict[str, Any]] = []
        self.orchestration_active = False
        self.parallel_processing_enabled = True
        self.max_concurrent_agents = 6
        self.agent_coordination_lock = asyncio.Lock()
        
        # Initialize default agents
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default background agents"""
        default_agents = [
            {
                'agent_id': 'persona_manager_001',
                'agent_type': AgentType.PERSONA_MANAGER,
                'name': 'Persona Management Agent',
                'description': 'Manages BMAD-Method persona discovery, activation, and coordination',
                'capabilities': ['persona_discovery', 'persona_activation', 'context_management', 'session_coordination']
            },
            {
                'agent_id': 'tool_coordinator_001',
                'agent_type': AgentType.TOOL_COORDINATOR,
                'name': 'Tool Coordination Agent',
                'description': 'Coordinates BMAD-Method tool discovery, execution, and management',
                'capabilities': ['tool_discovery', 'tool_execution', 'tool_categorization', 'mcp_integration']
            },
            {
                'agent_id': 'testing_orchestrator_001',
                'agent_type': AgentType.TESTING_ORCHESTRATOR,
                'name': 'Testing Orchestration Agent',
                'description': 'Orchestrates testing workflows and validation processes',
                'capabilities': ['workflow_testing', 'scenario_testing', 'regression_testing', 'performance_validation']
            },
            {
                'agent_id': 'expansion_manager_001',
                'agent_type': AgentType.EXPANSION_MANAGER,
                'name': 'Expansion Pack Manager Agent',
                'description': 'Manages BMAD-Method expansion packs and advanced features',
                'capabilities': ['expansion_discovery', 'pack_installation', 'hil_coordination', 'workflow_management']
            },
            {
                'agent_id': 'monitoring_agent_001',
                'agent_type': AgentType.MONITORING_AGENT,
                'name': 'Monitoring & Analytics Agent',
                'description': 'Monitors system health and collects analytics data',
                'capabilities': ['health_monitoring', 'metrics_collection', 'alert_management', 'performance_analysis']
            },
            {
                'agent_id': 'deployment_agent_001',
                'agent_type': AgentType.DEPLOYMENT_AGENT,
                'name': 'Deployment Coordination Agent',
                'description': 'Coordinates production deployments and environment management',
                'capabilities': ['deployment_orchestration', 'environment_management', 'rollback_coordination', 'status_tracking']
            }
        ]
        
        for agent_config in default_agents:
            agent = BackgroundAgent(
                agent_id=agent_config['agent_id'],
                agent_type=agent_config['agent_type'],
                name=agent_config['name'],
                description=agent_config['description'],
                status=AgentStatus.IDLE,
                last_activity=datetime.now(),
                capabilities=agent_config['capabilities']
            )
            self.agents[agent.agent_id] = agent
    
    async def activate_orchestration(self) -> Dict[str, Any]:
        """Activate background agent orchestration"""
        try:
            logger.info("🚀 BMAD Master: Activating background agent orchestration...")
            
            async with self.agent_coordination_lock:
                self.orchestration_active = True
                
                # Activate all agents
                activation_results = {}
                for agent_id, agent in self.agents.items():
                    try:
                        await self._activate_agent(agent)
                        activation_results[agent_id] = {
                            'status': 'activated',
                            'agent_type': agent.agent_type.value,
                            'capabilities': agent.capabilities
                        }
                        logger.info(f"   ✅ Activated agent: {agent.name}")
                    except Exception as e:
                        activation_results[agent_id] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        logger.error(f"   ❌ Failed to activate agent {agent.name}: {e}")
                
                # Start parallel processing coordination
                if self.parallel_processing_enabled:
                    await self._start_parallel_processing_coordination()
                
                logger.info("🎯 BMAD Master: Background agent orchestration activated!")
                
                return {
                    'success': True,
                    'orchestration_active': self.orchestration_active,
                    'total_agents': len(self.agents),
                    'activated_agents': len([r for r in activation_results.values() if r['status'] == 'activated']),
                    'agent_results': activation_results,
                    'parallel_processing': self.parallel_processing_enabled,
                    'max_concurrent_agents': self.max_concurrent_agents
                }
                
        except Exception as e:
            logger.error(f"❌ BMAD Master: Orchestration activation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'orchestration_active': False
            }
    
    async def _activate_agent(self, agent: BackgroundAgent):
        """Activate an individual agent"""
        agent.status = AgentStatus.ACTIVE
        agent.last_activity = datetime.now()
        
        # Initialize agent-specific capabilities
        if agent.agent_type == AgentType.PERSONA_MANAGER:
            await self._initialize_persona_manager(agent)
        elif agent.agent_type == AgentType.TOOL_COORDINATOR:
            await self._initialize_tool_coordinator(agent)
        elif agent.agent_type == AgentType.TESTING_ORCHESTRATOR:
            await self._initialize_testing_orchestrator(agent)
        elif agent.agent_type == AgentType.EXPANSION_MANAGER:
            await self._initialize_expansion_manager(agent)
        elif agent.agent_type == AgentType.MONITORING_AGENT:
            await self._initialize_monitoring_agent(agent)
        elif agent.agent_type == AgentType.DEPLOYMENT_AGENT:
            await self._initialize_deployment_agent(agent)
    
    async def _initialize_persona_manager(self, agent: BackgroundAgent):
        """Initialize persona management agent"""
        # Import and initialize persona wrapper
        from cflow_platform.core.bmad_persona_wrapper import bmad_persona_wrapper
        await bmad_persona_wrapper.discover_bmad_personas()
        agent.current_task = "persona_discovery_complete"
    
    async def _initialize_tool_coordinator(self, agent: BackgroundAgent):
        """Initialize tool coordination agent"""
        # Import and initialize tool wrapper
        from cflow_platform.core.bmad_tool_wrapper import bmad_tool_wrapper
        await bmad_tool_wrapper.discover_bmad_tools()
        agent.current_task = "tool_discovery_complete"
    
    async def _initialize_testing_orchestrator(self, agent: BackgroundAgent):
        """Initialize testing orchestration agent"""
        # Initialize testing engines
        agent.current_task = "testing_framework_ready"
    
    async def _initialize_expansion_manager(self, agent: BackgroundAgent):
        """Initialize expansion management agent"""
        # Initialize expansion pack manager
        from cflow_platform.core.expansion_pack_manager import bmad_expansion_pack_manager
        await bmad_expansion_pack_manager.discover_expansion_packs()
        agent.current_task = "expansion_packs_discovered"
    
    async def _initialize_monitoring_agent(self, agent: BackgroundAgent):
        """Initialize monitoring agent"""
        # Initialize health monitoring
        from cflow_platform.core.health_monitoring import bmad_master_health_monitoring
        await bmad_master_health_monitoring.start_monitoring()
        agent.current_task = "monitoring_active"
    
    async def _initialize_deployment_agent(self, agent: BackgroundAgent):
        """Initialize deployment agent"""
        # Initialize production deployment
        from cflow_platform.core.production_deployment import bmad_master_production_deployment
        agent.current_task = "deployment_ready"
    
    async def _start_parallel_processing_coordination(self):
        """Start parallel processing coordination"""
        logger.info("🔄 BMAD Master: Starting parallel processing coordination...")
        
        # Create coordination tasks for parallel execution
        coordination_tasks = [
            self._coordinate_persona_management(),
            self._coordinate_tool_execution(),
            self._coordinate_testing_workflows(),
            self._coordinate_expansion_management(),
            self._coordinate_monitoring_analytics(),
            self._coordinate_deployment_management()
        ]
        
        # Start all coordination tasks in parallel
        await asyncio.gather(*coordination_tasks, return_exceptions=True)
    
    async def _coordinate_persona_management(self):
        """Coordinate persona management activities"""
        try:
            persona_agent = self.agents['persona_manager_001']
            if persona_agent.status == AgentStatus.ACTIVE:
                logger.info("   📋 Coordinating persona management...")
                # Continuous persona management coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    persona_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Persona management coordination error: {e}")
    
    async def _coordinate_tool_execution(self):
        """Coordinate tool execution activities"""
        try:
            tool_agent = self.agents['tool_coordinator_001']
            if tool_agent.status == AgentStatus.ACTIVE:
                logger.info("   🔧 Coordinating tool execution...")
                # Continuous tool execution coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    tool_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Tool execution coordination error: {e}")
    
    async def _coordinate_testing_workflows(self):
        """Coordinate testing workflow activities"""
        try:
            testing_agent = self.agents['testing_orchestrator_001']
            if testing_agent.status == AgentStatus.ACTIVE:
                logger.info("   🧪 Coordinating testing workflows...")
                # Continuous testing coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    testing_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Testing workflow coordination error: {e}")
    
    async def _coordinate_expansion_management(self):
        """Coordinate expansion management activities"""
        try:
            expansion_agent = self.agents['expansion_manager_001']
            if expansion_agent.status == AgentStatus.ACTIVE:
                logger.info("   🚀 Coordinating expansion management...")
                # Continuous expansion management coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    expansion_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Expansion management coordination error: {e}")
    
    async def _coordinate_monitoring_analytics(self):
        """Coordinate monitoring and analytics activities"""
        try:
            monitoring_agent = self.agents['monitoring_agent_001']
            if monitoring_agent.status == AgentStatus.ACTIVE:
                logger.info("   📊 Coordinating monitoring and analytics...")
                # Continuous monitoring coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    monitoring_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Monitoring coordination error: {e}")
    
    async def _coordinate_deployment_management(self):
        """Coordinate deployment management activities"""
        try:
            deployment_agent = self.agents['deployment_agent_001']
            if deployment_agent.status == AgentStatus.ACTIVE:
                logger.info("   🚀 Coordinating deployment management...")
                # Continuous deployment coordination
                while self.orchestration_active:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    deployment_agent.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"   ❌ Deployment coordination error: {e}")
    
    async def distribute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Distribute a task to the most appropriate agent"""
        try:
            task_type = task.get('type', 'general')
            task_priority = task.get('priority', 'normal')
            
            # Find the best agent for this task
            best_agent = await self._find_best_agent_for_task(task_type)
            
            if best_agent:
                # Add task to agent's queue
                best_agent.task_queue.append(task)
                best_agent.status = AgentStatus.BUSY
                best_agent.current_task = task.get('name', 'unknown_task')
                
                logger.info(f"   📋 Task '{task.get('name', 'unknown')}' distributed to {best_agent.name}")
                
                return {
                    'success': True,
                    'task_id': task.get('id'),
                    'assigned_agent': best_agent.agent_id,
                    'agent_name': best_agent.name,
                    'queue_position': len(best_agent.task_queue)
                }
            else:
                # Add to general distribution queue
                self.task_distribution_queue.append(task)
                return {
                    'success': True,
                    'task_id': task.get('id'),
                    'assigned_agent': 'queued',
                    'message': 'Task queued for distribution'
                }
                
        except Exception as e:
            logger.error(f"❌ Task distribution error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _find_best_agent_for_task(self, task_type: str) -> Optional[BackgroundAgent]:
        """Find the best agent for a specific task type"""
        # Map task types to agent types
        task_agent_mapping = {
            'persona_management': AgentType.PERSONA_MANAGER,
            'tool_execution': AgentType.TOOL_COORDINATOR,
            'testing': AgentType.TESTING_ORCHESTRATOR,
            'expansion_management': AgentType.EXPANSION_MANAGER,
            'monitoring': AgentType.MONITORING_AGENT,
            'deployment': AgentType.DEPLOYMENT_AGENT
        }
        
        target_agent_type = task_agent_mapping.get(task_type, AgentType.TOOL_COORDINATOR)
        
        # Find available agents of the target type
        available_agents = [
            agent for agent in self.agents.values()
            if agent.agent_type == target_agent_type and agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]
        ]
        
        if available_agents:
            # Return the agent with the least tasks in queue
            return min(available_agents, key=lambda a: len(a.task_queue))
        
        return None
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        try:
            active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            busy_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
            total_tasks_queued = sum(len(a.task_queue) for a in self.agents.values())
            
            return {
                'success': True,
                'orchestration_active': self.orchestration_active,
                'total_agents': len(self.agents),
                'active_agents': active_agents,
                'busy_agents': busy_agents,
                'idle_agents': len(self.agents) - active_agents - busy_agents,
                'total_tasks_queued': total_tasks_queued,
                'parallel_processing_enabled': self.parallel_processing_enabled,
                'max_concurrent_agents': self.max_concurrent_agents,
                'agents': [
                    {
                        'agent_id': agent.agent_id,
                        'name': agent.name,
                        'type': agent.agent_type.value,
                        'status': agent.status.value,
                        'current_task': agent.current_task,
                        'tasks_queued': len(agent.task_queue),
                        'last_activity': agent.last_activity.isoformat(),
                        'capabilities': agent.capabilities
                    }
                    for agent in self.agents.values()
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deactivate_orchestration(self) -> Dict[str, Any]:
        """Deactivate background agent orchestration"""
        try:
            logger.info("🛑 BMAD Master: Deactivating background agent orchestration...")
            
            async with self.agent_coordination_lock:
                self.orchestration_active = False
                
                # Deactivate all agents
                for agent in self.agents.values():
                    agent.status = AgentStatus.OFFLINE
                    agent.current_task = None
                
                logger.info("✅ BMAD Master: Background agent orchestration deactivated")
                
                return {
                    'success': True,
                    'orchestration_active': False,
                    'message': 'Background agent orchestration deactivated'
                }
                
        except Exception as e:
            logger.error(f"❌ BMAD Master: Orchestration deactivation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global background agent orchestrator instance
background_agent_orchestrator = BackgroundAgentOrchestrator()
