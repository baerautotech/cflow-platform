# BMAD-Method Brownfield/Greenfield Workflow Engine

import asyncio
import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class WorkflowType(Enum):
    BROWNFIELD = "brownfield"
    GREENFIELD = "greenfield"

class WorkflowStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class BMADWorkflow:
    """Represents a BMAD-Method workflow"""
    workflow_id: str
    name: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    file_path: str
    steps: List[Dict[str, Any]]
    dependencies: List[str]
    created_at: datetime
    updated_at: datetime
    cerebral_extensions: Dict[str, Any] = None

class BMADBrownfieldGreenfieldWorkflowEngine:
    """Brownfield/Greenfield Workflow Engine for BMAD-Method with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.workflows_path = self.bmad_root / 'bmad-core' / 'workflows'
        self.discovered_workflows: Dict[str, BMADWorkflow] = {}
        self.active_workflows: Dict[str, BMADWorkflow] = {}
        self.workflow_history: List[BMADWorkflow] = []
        self.cerebral_extensions: Dict[str, Any] = {}
        
        # Workflow types from vendor/bmad
        self.workflow_types = {
            'brownfield-fullstack': 'Brownfield fullstack development workflow',
            'brownfield-service': 'Brownfield service development workflow',
            'brownfield-ui': 'Brownfield UI development workflow',
            'greenfield-fullstack': 'Greenfield fullstack development workflow',
            'greenfield-service': 'Greenfield service development workflow',
            'greenfield-ui': 'Greenfield UI development workflow'
        }
    
    async def discover_workflows(self) -> Dict[str, BMADWorkflow]:
        """Discover all BMAD-Method workflows from vendor/bmad"""
        workflows = {}
        
        print('🔍 BMAD Master: Discovering BMAD-Method workflows...')
        
        if not self.workflows_path.exists():
            print(f'   ❌ Workflows directory not found: {self.workflows_path}')
            return workflows
        
        for workflow_file in self.workflows_path.glob('*.yaml'):
            print(f'   📁 Scanning workflow: {workflow_file.name}')
            
            try:
                workflow = await self._load_workflow(workflow_file)
                if workflow:
                    workflows[workflow.workflow_id] = workflow
                    print(f'     ✅ Discovered workflow: {workflow.name}')
                else:
                    print(f'     ❌ Failed to load workflow: {workflow_file.name}')
            except Exception as e:
                print(f'     ❌ Error loading workflow {workflow_file.name}: {e}')
        
        self.discovered_workflows = workflows
        print(f'🎯 BMAD Master: Discovered {len(workflows)} workflows')
        return workflows
    
    async def _load_workflow(self, workflow_file: Path) -> Optional[BMADWorkflow]:
        """Load a BMAD-Method workflow from YAML file"""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f) or {}
            
            # Determine workflow type
            workflow_type = WorkflowType.BROWNFIELD
            if 'greenfield' in workflow_file.stem:
                workflow_type = WorkflowType.GREENFIELD
            
            # Extract workflow information
            name = workflow_data.get('name', workflow_file.stem.replace('-', ' ').title())
            steps = workflow_data.get('steps', [])
            dependencies = workflow_data.get('dependencies', [])
            
            return BMADWorkflow(
                workflow_id=workflow_file.stem,
                name=name,
                workflow_type=workflow_type,
                status=WorkflowStatus.ACTIVE,
                file_path=str(workflow_file),
                steps=steps,
                dependencies=dependencies,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True,
                    'step_tracking': True
                }
            )
        except Exception as e:
            print(f'Error loading workflow {workflow_file}: {e}')
            return None
    
    async def start_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a BMAD-Method workflow"""
        try:
            workflow = self.discovered_workflows.get(workflow_id)
            if not workflow:
                return {
                    'success': False,
                    'error': f'Workflow {workflow_id} not found'
                }
            
            if workflow_id in self.active_workflows:
                return {
                    'success': False,
                    'error': f'Workflow {workflow_id} already active'
                }
            
            # Add context to workflow
            if context:
                workflow.cerebral_extensions['context'] = context
            
            # Start workflow
            workflow.status = WorkflowStatus.ACTIVE
            workflow.updated_at = datetime.now()
            self.active_workflows[workflow_id] = workflow
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'workflow_name': workflow.name,
                'workflow_type': workflow.workflow_type.value,
                'steps': len(workflow.steps),
                'message': f'Successfully started workflow: {workflow.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_workflow_step(self, workflow_id: str, step_index: int, step_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific step in a workflow"""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    'success': False,
                    'error': f'Workflow {workflow_id} not active'
                }
            
            if step_index >= len(workflow.steps):
                return {
                    'success': False,
                    'error': f'Step index {step_index} out of range'
                }
            
            step = workflow.steps[step_index]
            
            # Simulate step execution
            result = {
                'step_index': step_index,
                'step_name': step.get('name', f'Step {step_index}'),
                'step_type': step.get('type', 'unknown'),
                'execution_time': datetime.now().isoformat(),
                'result': 'success',
                'data': step_data or {}
            }
            
            # Update workflow context
            if 'context' not in workflow.cerebral_extensions:
                workflow.cerebral_extensions['context'] = {}
            workflow.cerebral_extensions['context'][f'step_{step_index}'] = result
            
            workflow.updated_at = datetime.now()
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'step_result': result,
                'message': f'Successfully executed step {step_index}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def complete_workflow(self, workflow_id: str, result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete a BMAD-Method workflow"""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    'success': False,
                    'error': f'Workflow {workflow_id} not active'
                }
            
            # Complete workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.updated_at = datetime.now()
            
            if result:
                workflow.cerebral_extensions['final_result'] = result
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'workflow_name': workflow.name,
                'result': result,
                'message': f'Successfully completed workflow: {workflow.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_workflow(self, workflow_id: str) -> Optional[BMADWorkflow]:
        """Get a specific workflow by ID"""
        return self.discovered_workflows.get(workflow_id)
    
    async def get_workflows_by_type(self, workflow_type: WorkflowType) -> List[BMADWorkflow]:
        """Get all workflows of a specific type"""
        return [workflow for workflow in self.discovered_workflows.values() if workflow.workflow_type == workflow_type]
    
    async def list_active_workflows(self) -> List[BMADWorkflow]:
        """List all active workflows"""
        return list(self.active_workflows.values())
    
    async def list_workflow_history(self) -> List[BMADWorkflow]:
        """List workflow history"""
        return self.workflow_history
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get workflow engine status"""
        return {
            'total_workflows': len(self.discovered_workflows),
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.workflow_history),
            'workflow_types': {
                'brownfield': len([w for w in self.discovered_workflows.values() if w.workflow_type == WorkflowType.BROWNFIELD]),
                'greenfield': len([w for w in self.discovered_workflows.values() if w.workflow_type == WorkflowType.GREENFIELD])
            },
            'cerebral_extensions': {
                'mcp_integration': True,
                'context_preservation': True,
                'session_management': True,
                'webmcp_routing': True,
                'step_tracking': True
            },
            'engine_version': '1.0',
            'last_update': datetime.now().isoformat()
        }

# Global workflow engine instance
bmad_brownfield_greenfield_workflow_engine = BMADBrownfieldGreenfieldWorkflowEngine()
