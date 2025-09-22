# BMAD-Method Tool Wrapper System

import asyncio
import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

@dataclass
class BMADTool:
    """Represents a BMAD-Method tool loaded from vendor/bmad"""
    name: str
    id: str
    description: str
    category: str
    file_path: str
    tool_type: str  # 'task', 'template', 'workflow', 'checklist', 'agent'
    dependencies: List[str]
    parameters: Dict[str, Any]
    cerebral_extensions: Dict[str, Any] = None

class BMADToolWrapper:
    """Wrapper for BMAD-Method tools with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.discovered_tools: Dict[str, BMADTool] = {}
        self.tool_categories: Dict[str, List[str]] = {}
        self.cerebral_extensions: Dict[str, Any] = {}
        self.last_discovery: Optional[datetime] = None
        self.tools: List[BMADTool] = []
        
        # Tool discovery paths
        self.tool_paths = {
            'tasks': self.bmad_root / 'bmad-core' / 'tasks',
            'templates': self.bmad_root / 'bmad-core' / 'templates',
            'workflows': self.bmad_root / 'bmad-core' / 'workflows',
            'checklists': self.bmad_root / 'bmad-core' / 'checklists',
            'agents': self.bmad_root / 'bmad-core' / 'agents',
            'common_tasks': self.bmad_root / 'common' / 'tasks'
        }
    
    async def discover_bmad_tools(self) -> Dict[str, BMADTool]:
        """Discover all BMAD-Method tools from vendor/bmad"""
        tools = {}
        
        print('🔍 BMAD Master: Discovering BMAD-Method tools...')
        
        for tool_type, tool_path in self.tool_paths.items():
            if tool_path.exists():
                print(f'   📁 Scanning {tool_type}: {tool_path}')
                
                # Discover tools based on type
                if tool_type in ['tasks', 'common_tasks']:
                    discovered = await self._discover_task_tools(tool_path, tool_type)
                elif tool_type == 'templates':
                    discovered = await self._discover_template_tools(tool_path)
                elif tool_type == 'workflows':
                    discovered = await self._discover_workflow_tools(tool_path)
                elif tool_type == 'checklists':
                    discovered = await self._discover_checklist_tools(tool_path)
                elif tool_type == 'agents':
                    discovered = await self._discover_agent_tools(tool_path)
                else:
                    discovered = {}
                
                tools.update(discovered)
                print(f'   ✅ Found {len(discovered)} {tool_type}')
        
        self.discovered_tools = tools
        self.tools = list(tools.values())
        self.last_discovery = datetime.now()
        self._categorize_tools()
        
        print(f'🎯 BMAD Master: Discovered {len(tools)} total BMAD-Method tools')
        return tools
    
    async def _discover_task_tools(self, task_path: Path, tool_type: str) -> Dict[str, BMADTool]:
        """Discover task tools from vendor/bmad"""
        tools = {}
        
        for task_file in task_path.glob('*.md'):
            try:
                tool = await self._load_task_tool(task_file, tool_type)
                if tool:
                    tools[tool.id] = tool
                    print(f'     ✅ Discovered task: {tool.name}')
            except Exception as e:
                print(f'     ❌ Error loading task {task_file}: {e}')
        
        return tools
    
    async def _discover_template_tools(self, template_path: Path) -> Dict[str, BMADTool]:
        """Discover template tools from vendor/bmad"""
        tools = {}
        
        for template_file in template_path.glob('*.yaml'):
            try:
                tool = await self._load_template_tool(template_file)
                if tool:
                    tools[tool.id] = tool
                    print(f'     ✅ Discovered template: {tool.name}')
            except Exception as e:
                print(f'     ❌ Error loading template {template_file}: {e}')
        
        return tools
    
    async def _discover_workflow_tools(self, workflow_path: Path) -> Dict[str, BMADTool]:
        """Discover workflow tools from vendor/bmad"""
        tools = {}
        
        for workflow_file in workflow_path.glob('*.yaml'):
            try:
                tool = await self._load_workflow_tool(workflow_file)
                if tool:
                    tools[tool.id] = tool
                    print(f'     ✅ Discovered workflow: {tool.name}')
            except Exception as e:
                print(f'     ❌ Error loading workflow {workflow_file}: {e}')
        
        return tools
    
    async def _discover_checklist_tools(self, checklist_path: Path) -> Dict[str, BMADTool]:
        """Discover checklist tools from vendor/bmad"""
        tools = {}
        
        for checklist_file in checklist_path.glob('*.md'):
            try:
                tool = await self._load_checklist_tool(checklist_file)
                if tool:
                    tools[tool.id] = tool
                    print(f'     ✅ Discovered checklist: {tool.name}')
            except Exception as e:
                print(f'     ❌ Error loading checklist {checklist_file}: {e}')
        
        return tools
    
    async def _discover_agent_tools(self, agent_path: Path) -> Dict[str, BMADTool]:
        """Discover agent tools from vendor/bmad"""
        tools = {}
        
        for agent_file in agent_path.glob('*.md'):
            try:
                tool = await self._load_agent_tool(agent_file)
                if tool:
                    tools[tool.id] = tool
                    print(f'     ✅ Discovered agent: {tool.name}')
            except Exception as e:
                print(f'     ❌ Error loading agent {agent_file}: {e}')
        
        return tools
    
    async def _load_task_tool(self, task_file: Path, tool_type: str) -> Optional[BMADTool]:
        """Load a task tool from vendor/bmad"""
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract task information from markdown
            lines = content.split('\n')
            name = task_file.stem.replace('-', ' ').title()
            description = ""
            
            # Find description (usually first paragraph after title)
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#'):
                    description = line.strip()
                    break
            
            return BMADTool(
                name=name,
                id=f"{tool_type}_{task_file.stem}",
                description=description,
                category=tool_type,
                file_path=str(task_file),
                tool_type='task',
                dependencies=[],
                parameters={},
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True
                }
            )
        except Exception as e:
            print(f'Error loading task tool {task_file}: {e}')
            return None
    
    async def _load_template_tool(self, template_file: Path) -> Optional[BMADTool]:
        """Load a template tool from vendor/bmad"""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML template
            template_data = yaml.safe_load(content)
            
            name = template_data.get('name', template_file.stem.replace('-', ' ').title())
            description = template_data.get('description', f"Template: {name}")
            
            return BMADTool(
                name=name,
                id=f"template_{template_file.stem}",
                description=description,
                category='template',
                file_path=str(template_file),
                tool_type='template',
                dependencies=template_data.get('dependencies', []),
                parameters=template_data.get('parameters', {}),
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True
                }
            )
        except Exception as e:
            print(f'Error loading template tool {template_file}: {e}')
            return None
    
    async def _load_workflow_tool(self, workflow_file: Path) -> Optional[BMADTool]:
        """Load a workflow tool from vendor/bmad"""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML workflow
            workflow_data = yaml.safe_load(content)
            
            name = workflow_data.get('name', workflow_file.stem.replace('-', ' ').title())
            description = workflow_data.get('description', f"Workflow: {name}")
            
            return BMADTool(
                name=name,
                id=f"workflow_{workflow_file.stem}",
                description=description,
                category='workflow',
                file_path=str(workflow_file),
                tool_type='workflow',
                dependencies=workflow_data.get('dependencies', []),
                parameters=workflow_data.get('parameters', {}),
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True
                }
            )
        except Exception as e:
            print(f'Error loading workflow tool {workflow_file}: {e}')
            return None
    
    async def _load_checklist_tool(self, checklist_file: Path) -> Optional[BMADTool]:
        """Load a checklist tool from vendor/bmad"""
        try:
            with open(checklist_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract checklist information
            name = checklist_file.stem.replace('-', ' ').title()
            description = f"Checklist: {name}"
            
            return BMADTool(
                name=name,
                id=f"checklist_{checklist_file.stem}",
                description=description,
                category='checklist',
                file_path=str(checklist_file),
                tool_type='checklist',
                dependencies=[],
                parameters={},
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True
                }
            )
        except Exception as e:
            print(f'Error loading checklist tool {checklist_file}: {e}')
            return None
    
    async def _load_agent_tool(self, agent_file: Path) -> Optional[BMADTool]:
        """Load an agent tool from vendor/bmad"""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML block
            yaml_start = content.find('```yaml')
            yaml_end = content.find('```', yaml_start + 7)
            
            if yaml_start != -1 and yaml_end != -1:
                yaml_content = content[yaml_start + 7:yaml_end].strip()
                agent_config = yaml.safe_load(yaml_content)
                
                agent_info = agent_config.get('agent', {})
                name = agent_info.get('name', agent_file.stem.replace('-', ' ').title())
                description = agent_info.get('description', f"Agent: {name}")
                
                return BMADTool(
                    name=name,
                    id=f"agent_{agent_file.stem}",
                    description=description,
                    category='agent',
                    file_path=str(agent_file),
                    tool_type='agent',
                    dependencies=agent_config.get('dependencies', []),
                    parameters=agent_config.get('parameters', {}),
                    cerebral_extensions={
                        'mcp_integration': True,
                        'context_preservation': True,
                        'session_management': True,
                        'webmcp_routing': True
                    }
                )
        except Exception as e:
            print(f'Error loading agent tool {agent_file}: {e}')
            return None
    
    def _categorize_tools(self):
        """Categorize discovered tools"""
        self.tool_categories = {}
        
        for tool_id, tool in self.discovered_tools.items():
            category = tool.category
            if category not in self.tool_categories:
                self.tool_categories[category] = []
            self.tool_categories[category].append(tool_id)
    
    async def get_tool_by_id(self, tool_id: str) -> Optional[BMADTool]:
        """Get a specific tool by ID"""
        return self.discovered_tools.get(tool_id)
    
    async def get_tools_by_category(self, category: str) -> List[BMADTool]:
        """Get all tools in a specific category"""
        tool_ids = self.tool_categories.get(category, [])
        return [self.discovered_tools[tool_id] for tool_id in tool_ids if tool_id in self.discovered_tools]
    
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a BMAD-Method tool with Cerebral extensions"""
        try:
            tool = await self.get_tool_by_id(tool_id)
            if not tool:
                return {
                    'success': False,
                    'error': f'Tool {tool_id} not found'
                }
            
            # Add Cerebral extensions to execution context
            execution_context = {
                'tool_id': tool_id,
                'tool_name': tool.name,
                'parameters': parameters or {},
                'cerebral_extensions': tool.cerebral_extensions,
                'timestamp': datetime.now().isoformat(),
                'session_id': None  # Would be provided by session manager
            }
            
            # Execute tool based on type
            if tool.tool_type == 'task':
                result = await self._execute_task_tool(tool, execution_context)
            elif tool.tool_type == 'template':
                result = await self._execute_template_tool(tool, execution_context)
            elif tool.tool_type == 'workflow':
                result = await self._execute_workflow_tool(tool, execution_context)
            elif tool.tool_type == 'checklist':
                result = await self._execute_checklist_tool(tool, execution_context)
            elif tool.tool_type == 'agent':
                result = await self._execute_agent_tool(tool, execution_context)
            else:
                result = {
                    'success': False,
                    'error': f'Unknown tool type: {tool.tool_type}'
                }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_task_tool(self, tool: BMADTool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task tool"""
        # Placeholder for task execution
        return {
            'success': True,
            'tool_id': tool.id,
            'tool_name': tool.name,
            'result': f'Executed task: {tool.name}',
            'context': context
        }
    
    async def _execute_template_tool(self, tool: BMADTool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a template tool"""
        # Placeholder for template execution
        return {
            'success': True,
            'tool_id': tool.id,
            'tool_name': tool.name,
            'result': f'Executed template: {tool.name}',
            'context': context
        }
    
    async def _execute_workflow_tool(self, tool: BMADTool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow tool"""
        # Placeholder for workflow execution
        return {
            'success': True,
            'tool_id': tool.id,
            'tool_name': tool.name,
            'result': f'Executed workflow: {tool.name}',
            'context': context
        }
    
    async def _execute_checklist_tool(self, tool: BMADTool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a checklist tool"""
        # Placeholder for checklist execution
        return {
            'success': True,
            'tool_id': tool.id,
            'tool_name': tool.name,
            'result': f'Executed checklist: {tool.name}',
            'context': context
        }
    
    async def _execute_agent_tool(self, tool: BMADTool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent tool"""
        # Placeholder for agent execution
        return {
            'success': True,
            'tool_id': tool.id,
            'tool_name': tool.name,
            'result': f'Executed agent: {tool.name}',
            'context': context
        }
    
    async def get_tool_status(self) -> Dict[str, Any]:
        """Get current tool wrapper status"""
        return {
            'total_tools': len(self.discovered_tools),
            'categories': {
                category: len(tools) 
                for category, tools in self.tool_categories.items()
            },
            'cerebral_extensions': {
                'mcp_integration': True,
                'context_preservation': True,
                'session_management': True,
                'webmcp_routing': True
            },
            'wrapper_version': '1.0',
            'last_discovery': datetime.now().isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get tool wrapper status for health monitoring"""
        return {
            'total_tools': len(self.discovered_tools),
            'tools_by_category': {
                category: len([t for t in self.discovered_tools.values() if t.category == category])
                for category in ['task', 'template', 'workflow', 'checklist', 'agent', 'common_task']
            },
            'discovered_tools': len(self.discovered_tools),
            'vendor_path': str(self.bmad_root),
            'vendor_path_exists': self.bmad_root.exists(),
            'last_discovery': self.last_discovery.isoformat() if self.last_discovery else None,
            'tools': [
                {
                    'tool_id': t.id,
                    'name': t.name,
                    'category': t.category,
                    'tool_type': t.tool_type
                }
                for t in self.discovered_tools.values()
            ]
        }

# Global BMAD tool wrapper instance
bmad_tool_wrapper = BMADToolWrapper()
