# BMAD-Method Persona Wrapper System

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
class BMADPersona:
    """Represents a BMAD-Method persona loaded from vendor/bmad"""
    name: str
    id: str
    title: str
    icon: str
    when_to_use: str
    role: str
    identity: str
    style: Optional[str] = None
    focus: Optional[str] = None
    core_principles: List[str] = None
    commands: List[Dict[str, Any]] = None
    dependencies: Dict[str, List[str]] = None
    activation_instructions: List[str] = None
    agent_file_path: Optional[str] = None

class BMADPersonaWrapper:
    """Wrapper for BMAD-Method personas with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.agents_path = self.bmad_root / 'bmad-core' / 'agents'
        self.discovered_personas: Dict[str, BMADPersona] = {}
        self.active_persona: Optional[BMADPersona] = None
        self.persona_contexts: Dict[str, Dict[str, Any]] = {}
        self.session_context: Dict[str, Any] = {}
        
        # Context persistence
        self.context_dir = Path('.cerebraflow/persona_contexts')
        self.context_dir.mkdir(parents=True, exist_ok=True)
    
    async def discover_bmad_personas(self) -> Dict[str, BMADPersona]:
        """Discover all BMAD-Method personas from vendor/bmad"""
        personas = {}
        
        if not self.agents_path.exists():
            print(f'Warning: BMAD agents path not found: {self.agents_path}')
            return personas
        
        for agent_file in self.agents_path.glob('*.md'):
            try:
                persona = await self._load_bmad_persona(agent_file)
                if persona:
                    personas[persona.id] = persona
                    print(f'✅ Discovered BMAD persona: {persona.name} ({persona.id})')
            except Exception as e:
                print(f'Error loading persona from {agent_file}: {e}')
        
        self.discovered_personas = personas
        return personas
    
    async def _load_bmad_persona(self, agent_file: Path) -> Optional[BMADPersona]:
        """Load a BMAD-Method persona from agent file"""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML block
            yaml_start = content.find('```yaml')
            yaml_end = content.find('```', yaml_start + 7)
            
            if yaml_start == -1 or yaml_end == -1:
                print(f'No YAML block found in {agent_file}')
                return None
            
            yaml_content = content[yaml_start + 7:yaml_end].strip()
            agent_config = yaml.safe_load(yaml_content)
            
            # Extract persona information
            agent_info = agent_config.get('agent', {})
            persona_info = agent_config.get('persona', {})
            
            persona = BMADPersona(
                name=agent_info.get('name', 'Unknown'),
                id=agent_info.get('id', 'unknown'),
                title=agent_info.get('title', 'Unknown Role'),
                icon=agent_info.get('icon', '🤖'),
                when_to_use=agent_info.get('whenToUse', ''),
                role=persona_info.get('role', ''),
                identity=persona_info.get('identity', ''),
                style=persona_info.get('style'),
                focus=persona_info.get('focus'),
                core_principles=persona_info.get('core_principles', []),
                commands=agent_config.get('commands', []),
                dependencies=agent_config.get('dependencies', {}),
                activation_instructions=agent_config.get('activation-instructions', []),
                agent_file_path=str(agent_file)
            )
            
            return persona
            
        except Exception as e:
            print(f'Error parsing BMAD persona from {agent_file}: {e}')
            return None
    
    async def activate_persona(self, persona_id: str, session_id: str = None) -> Dict[str, Any]:
        """Activate a BMAD-Method persona with Cerebral extensions"""
        try:
            if persona_id not in self.discovered_personas:
                return {
                    'success': False,
                    'error': f'Persona {persona_id} not found. Available: {list(self.discovered_personas.keys())}'
                }
            
            persona = self.discovered_personas[persona_id]
            
            # Deactivate current persona if any
            if self.active_persona:
                await self.deactivate_persona()
            
            # Set new active persona
            self.active_persona = persona
            
            # Load persona context from persistent storage
            context = await self.load_context(persona_id) or {}
            
            # Add Cerebral extensions to context
            context.update({
                'cerebral_session_id': session_id,
                'activated_at': datetime.now().isoformat(),
                'cerebral_extensions': {
                    'context_preservation': True,
                    'session_management': True,
                    'mcp_integration': True,
                    'webmcp_routing': True
                }
            })
            
            # Save updated context
            await self.save_context(persona_id, context)
            self.persona_contexts[persona_id] = context
            
            return {
                'success': True,
                'persona': {
                    'id': persona.id,
                    'name': persona.name,
                    'title': persona.title,
                    'icon': persona.icon,
                    'role': persona.role
                },
                'context': context,
                'cerebral_extensions': context['cerebral_extensions']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deactivate_persona(self) -> bool:
        """Deactivate current persona with context preservation"""
        try:
            if self.active_persona:
                # Save current context to persistent storage
                await self.save_context(self.active_persona.id, self.session_context.copy())
                self.persona_contexts[self.active_persona.id] = self.session_context.copy()
                
                # Clear active persona
                self.active_persona = None
                self.session_context = {}
                
                return True
            return False
        except Exception as e:
            print(f'Error deactivating persona: {e}')
            return False
    
    async def execute_persona_command(self, command: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a command on the active persona"""
        try:
            if not self.active_persona:
                return {
                    'success': False,
                    'error': 'No active persona'
                }
            
            # Get command definition from persona
            command_def = None
            command_description = None
            
            for cmd in self.active_persona.commands or []:
                if isinstance(cmd, dict):
                    # Handle YAML-parsed command format: {"command-name": "description"}
                    for cmd_name, cmd_desc in cmd.items():
                        if cmd_name == command:
                            command_def = cmd_name
                            command_description = cmd_desc
                            break
                        elif cmd_name.startswith(command):
                            command_def = cmd_name
                            command_description = cmd_desc
                            break
                    if command_def:
                        break
                elif isinstance(cmd, str):
                    # Parse BMAD-Method command format: "command-name: description"
                    if ':' in cmd:
                        cmd_name, cmd_desc = cmd.split(':', 1)
                        cmd_name = cmd_name.strip()
                        cmd_desc = cmd_desc.strip()
                        
                        if cmd_name == command:
                            command_def = cmd_name
                            command_description = cmd_desc
                            break
                        elif cmd_name.startswith(command):
                            command_def = cmd_name
                            command_description = cmd_desc
                            break
                    elif cmd.strip() == command:
                        command_def = cmd.strip()
                        command_description = f"Command: {cmd}"
                        break
            
            if not command_def:
                available_commands = []
                for cmd in self.active_persona.commands or []:
                    if isinstance(cmd, dict):
                        for cmd_name in cmd.keys():
                            available_commands.append(cmd_name)
                    elif isinstance(cmd, str) and ':' in cmd:
                        cmd_name = cmd.split(':', 1)[0].strip()
                        available_commands.append(cmd_name)
                
                return {
                    'success': False,
                    'error': f'Command {command} not found in persona {self.active_persona.name}',
                    'available_commands': available_commands
                }
            
            # Execute command (placeholder - would integrate with BMAD execution)
            return {
                'success': True,
                'command': command_def,
                'description': command_description,
                'persona': self.active_persona.name,
                'result': f'Executed {command_def} on {self.active_persona.name}: {command_description}',
                'arguments': arguments or {}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_persona_status(self) -> Dict[str, Any]:
        """Get current persona status and available personas"""
        return {
            'active_persona': {
                'id': self.active_persona.id,
                'name': self.active_persona.name,
                'title': self.active_persona.title
            } if self.active_persona else None,
            'available_personas': [
                {
                    'id': p.id,
                    'name': p.name,
                    'title': p.title,
                    'icon': p.icon
                } for p in self.discovered_personas.values()
            ],
            'total_personas': len(self.discovered_personas),
            'context_size': len(self.session_context)
        }
    
    async def switch_persona(self, new_persona_id: str, session_id: str = None) -> Dict[str, Any]:
        """Switch to a new persona with context preservation"""
        return await self.activate_persona(new_persona_id, session_id)
    
    async def save_context(self, persona_id: str, context: Dict[str, Any]) -> bool:
        """Save persona context to persistent storage"""
        try:
            context_file = self.context_dir / f'{persona_id}_context.json'
            context_data = {
                'persona_id': persona_id,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f'Error saving context for {persona_id}: {e}')
            return False
    
    async def load_context(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Load persona context from persistent storage"""
        try:
            context_file = self.context_dir / f'{persona_id}_context.json'
            if context_file.exists():
                with open(context_file, 'r', encoding='utf-8') as f:
                    context_data = json.load(f)
                
                return context_data.get('context', {})
            
            return None
        except Exception as e:
            print(f'Error loading context for {persona_id}: {e}')
            return None
    
    async def save_session_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Save session context to persistent storage"""
        try:
            session_file = self.context_dir / f'session_{session_id}.json'
            session_data = {
                'session_id': session_id,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f'Error saving session context for {session_id}: {e}')
            return False
    
    async def load_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session context from persistent storage"""
        try:
            session_file = self.context_dir / f'session_{session_id}.json'
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                return session_data.get('context', {})
            
            return None
        except Exception as e:
            print(f'Error loading session context for {session_id}: {e}')
            return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get persona wrapper status for health monitoring"""
        return {
            'total_personas': len(self.discovered_personas),
            'active_personas': len([p for p in self.discovered_personas.values() if p.status == PersonaStatus.ACTIVE]),
            'discovered_personas': len(self.discovered_personas),
            'context_dir': str(self.context_dir),
            'context_dir_exists': self.context_dir.exists(),
            'last_discovery': self.last_discovery.isoformat() if self.last_discovery else None,
            'personas': [
                {
                    'persona_id': p.persona_id,
                    'name': p.name,
                    'status': p.status.value,
                    'activation_count': p.activation_count
                }
                for p in self.discovered_personas.values()
            ]
        }

# Global BMAD persona wrapper instance
bmad_persona_wrapper = BMADPersonaWrapper()
