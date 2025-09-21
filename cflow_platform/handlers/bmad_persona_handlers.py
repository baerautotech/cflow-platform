# BMAD Persona Management MCP Handlers

import asyncio
from typing import Dict, Any
from cflow_platform.core.bmad_persona_wrapper import bmad_persona_wrapper

class BMADPersonaHandlers:
    """MCP handlers for BMAD-Method persona management"""
    
    def __init__(self):
        self.persona_wrapper = bmad_persona_wrapper
    
    async def bmad_discover_personas(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Discover all available BMAD-Method personas"""
        try:
            personas = await self.persona_wrapper.discover_bmad_personas()
            
            return {
                'success': True,
                'personas': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'title': p.title,
                        'icon': p.icon,
                        'when_to_use': p.when_to_use,
                        'role': p.role
                    } for p in personas.values()
                ],
                'total_count': len(personas)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_activate_persona(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a BMAD-Method persona"""
        try:
            persona_id = arguments.get('persona_id')
            session_id = arguments.get('session_id')
            
            if not persona_id:
                return {
                    'success': False,
                    'error': 'persona_id is required'
                }
            
            result = await self.persona_wrapper.activate_persona(persona_id, session_id)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_deactivate_persona(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate current persona"""
        try:
            success = await self.persona_wrapper.deactivate_persona()
            return {
                'success': success,
                'message': 'Persona deactivated' if success else 'No active persona to deactivate'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_execute_persona_command(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command on the active persona"""
        try:
            command = arguments.get('command')
            cmd_arguments = arguments.get('arguments', {})
            
            if not command:
                return {
                    'success': False,
                    'error': 'command is required'
                }
            
            result = await self.persona_wrapper.execute_persona_command(command, cmd_arguments)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_get_persona_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get current persona status"""
        try:
            status = await self.persona_wrapper.get_persona_status()
            return {
                'success': True,
                'status': status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bmad_switch_persona(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to a different persona"""
        try:
            persona_id = arguments.get('persona_id')
            session_id = arguments.get('session_id')
            
            if not persona_id:
                return {
                    'success': False,
                    'error': 'persona_id is required'
                }
            
            result = await self.persona_wrapper.switch_persona(persona_id, session_id)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global persona handlers instance
bmad_persona_handlers = BMADPersonaHandlers()
