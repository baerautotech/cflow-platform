# BMAD Tool Wrapper MCP Handlers

import asyncio
from typing import Dict, Any
from ..core.bmad_tool_wrapper import bmad_tool_wrapper

class BMADToolHandlers:
    """MCP handlers for BMAD tool wrapper functionality"""
    
    def __init__(self):
        self.wrapper = bmad_tool_wrapper
    
    async def bmad_discover_tools(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Discover all BMAD-Method tools via MCP"""
        try:
            tools = await self.wrapper.discover_bmad_tools()
            
            # Convert tools to MCP-friendly format
            tool_list = []
            for tool_id, tool in tools.items():
                tool_list.append({
                    'id': tool_id,
                    'name': tool.name,
                    'description': tool.description,
                    'category': tool.category,
                    'tool_type': tool.tool_type,
                    'file_path': tool.file_path,
                    'dependencies': tool.dependencies,
                    'parameters': tool.parameters,
                    'cerebral_extensions': tool.cerebral_extensions
                })
            
            return {
                'success': True,
                'tools': tool_list,
                'total_count': len(tool_list),
                'categories': self.wrapper.tool_categories
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_get_tool(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific BMAD tool by ID via MCP"""
        try:
            tool_id = kwargs.get('tool_id')
            if not tool_id:
                return {
                    'success': False,
                    'error': 'tool_id parameter required'
                }
            
            tool = await self.wrapper.get_tool_by_id(tool_id)
            if not tool:
                return {
                    'success': False,
                    'error': f'Tool {tool_id} not found'
                }
            
            return {
                'success': True,
                'tool': {
                    'id': tool.id,
                    'name': tool.name,
                    'description': tool.description,
                    'category': tool.category,
                    'tool_type': tool.tool_type,
                    'file_path': tool.file_path,
                    'dependencies': tool.dependencies,
                    'parameters': tool.parameters,
                    'cerebral_extensions': tool.cerebral_extensions
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_get_tools_by_category(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get all tools in a specific category via MCP"""
        try:
            category = kwargs.get('category')
            if not category:
                return {
                    'success': False,
                    'error': 'category parameter required'
                }
            
            tools = await self.wrapper.get_tools_by_category(category)
            
            # Convert tools to MCP-friendly format
            tool_list = []
            for tool in tools:
                tool_list.append({
                    'id': tool.id,
                    'name': tool.name,
                    'description': tool.description,
                    'category': tool.category,
                    'tool_type': tool.tool_type,
                    'file_path': tool.file_path,
                    'dependencies': tool.dependencies,
                    'parameters': tool.parameters,
                    'cerebral_extensions': tool.cerebral_extensions
                })
            
            return {
                'success': True,
                'tools': tool_list,
                'category': category,
                'count': len(tool_list)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_execute_tool(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BMAD tool via MCP"""
        try:
            tool_id = kwargs.get('tool_id')
            if not tool_id:
                return {
                    'success': False,
                    'error': 'tool_id parameter required'
                }
            
            parameters = kwargs.get('parameters', {})
            result = await self.wrapper.execute_tool(tool_id, parameters)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_get_tool_status(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get BMAD tool wrapper status via MCP"""
        try:
            status = await self.wrapper.get_tool_status()
            return {
                'success': True,
                'status': status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_list_categories(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """List all available tool categories via MCP"""
        try:
            categories = {}
            for category, tool_ids in self.wrapper.tool_categories.items():
                categories[category] = {
                    'count': len(tool_ids),
                    'tools': tool_ids
                }
            
            return {
                'success': True,
                'categories': categories,
                'total_categories': len(categories)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global handlers instance
bmad_tool_handlers = BMADToolHandlers()
