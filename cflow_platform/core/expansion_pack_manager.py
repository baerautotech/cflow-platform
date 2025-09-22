# BMAD-Method Expansion Pack Manager

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
class BMADExpansionPack:
    """Represents a BMAD-Method expansion pack loaded from vendor/bmad"""
    name: str
    id: str
    description: str
    version: str
    category: str
    file_path: str
    config_file: str
    dependencies: List[str]
    requirements: List[str]
    cerebral_extensions: Dict[str, Any] = None
    status: str = 'available'  # available, installed, active, error

class BMADExpansionPackManager:
    """Manager for BMAD-Method expansion packs with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.expansion_packs_path = self.bmad_root / 'expansion-packs'
        self.discovered_packs: Dict[str, BMADExpansionPack] = {}
        self.installed_packs: Dict[str, BMADExpansionPack] = {}
        self.active_packs: Dict[str, BMADExpansionPack] = {}
        self.cerebral_extensions: Dict[str, Any] = {}
        
        # Expansion pack categories
        self.pack_categories = {
            'game-dev': ['bmad-godot-game-dev', 'bmad-2d-unity-game-dev', 'bmad-2d-phaser-game-dev'],
            'business': ['bmad-business', 'bmad-finance', 'bmad-legal'],
            'technical': ['bmad-technical-research', 'bmad-infrastructure-devops'],
            'creative': ['bmad-creative-writing'],
            'healthcare': ['bmad-healthcare']
        }
    
    async def discover_expansion_packs(self) -> Dict[str, BMADExpansionPack]:
        """Discover all BMAD-Method expansion packs from vendor/bmad"""
        packs = {}
        
        print('🔍 BMAD Master: Discovering BMAD-Method expansion packs...')
        
        if not self.expansion_packs_path.exists():
            print(f'   ❌ Expansion packs directory not found: {self.expansion_packs_path}')
            return packs
        
        for pack_dir in self.expansion_packs_path.iterdir():
            if pack_dir.is_dir():
                print(f'   📁 Scanning expansion pack: {pack_dir.name}')
                
                try:
                    pack = await self._load_expansion_pack(pack_dir)
                    if pack:
                        packs[pack.id] = pack
                        print(f'     ✅ Discovered pack: {pack.name} v{pack.version}')
                    else:
                        print(f'     ❌ Failed to load pack: {pack_dir.name}')
                except Exception as e:
                    print(f'     ❌ Error loading pack {pack_dir.name}: {e}')
        
        self.discovered_packs = packs
        print(f'🎯 BMAD Master: Discovered {len(packs)} expansion packs')
        return packs
    
    async def _load_expansion_pack(self, pack_dir: Path) -> Optional[BMADExpansionPack]:
        """Load a BMAD-Method expansion pack from directory"""
        try:
            # Look for config.yaml or README.md
            config_file = None
            config_data = {}
            
            # Try config.yaml first
            config_yaml = pack_dir / 'config.yaml'
            if config_yaml.exists():
                config_file = str(config_yaml)
                with open(config_yaml, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            
            # Try README.md for basic info
            readme_file = pack_dir / 'README.md'
            if readme_file.exists() and not config_data:
                config_file = str(readme_file)
                with open(readme_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract basic info from README
                    config_data = {
                        'name': pack_dir.name.replace('-', ' ').title(),
                        'description': self._extract_description_from_readme(content),
                        'version': '1.0.0'
                    }
            
            if not config_data:
                # Create basic pack info
                config_data = {
                    'name': pack_dir.name.replace('-', ' ').title(),
                    'description': f'Expansion pack: {pack_dir.name}',
                    'version': '1.0.0'
                }
            
            # Determine category
            category = 'other'
            for cat, pack_names in self.pack_categories.items():
                if pack_dir.name in pack_names:
                    category = cat
                    break
            
            return BMADExpansionPack(
                name=config_data.get('name', pack_dir.name.replace('-', ' ').title()),
                id=pack_dir.name,
                description=config_data.get('description', f'Expansion pack: {pack_dir.name}'),
                version=config_data.get('version', '1.0.0'),
                category=category,
                file_path=str(pack_dir),
                config_file=config_file or '',
                dependencies=config_data.get('dependencies', []),
                requirements=config_data.get('requirements', []),
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True,
                    'auto_discovery': True
                }
            )
        except Exception as e:
            print(f'Error loading expansion pack {pack_dir}: {e}')
            return None
    
    def _extract_description_from_readme(self, content: str) -> str:
        """Extract description from README content"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('*'):
                return line[:100] + '...' if len(line) > 100 else line
        return 'Expansion pack description'
    
    async def install_expansion_pack(self, pack_id: str) -> Dict[str, Any]:
        """Install a BMAD-Method expansion pack"""
        try:
            pack = self.discovered_packs.get(pack_id)
            if not pack:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} not found'
                }
            
            if pack_id in self.installed_packs:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} already installed'
                }
            
            # Simulate installation process
            pack.status = 'installed'
            self.installed_packs[pack_id] = pack
            
            return {
                'success': True,
                'pack_id': pack_id,
                'pack_name': pack.name,
                'message': f'Successfully installed expansion pack: {pack.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def activate_expansion_pack(self, pack_id: str) -> Dict[str, Any]:
        """Activate a BMAD-Method expansion pack"""
        try:
            pack = self.installed_packs.get(pack_id)
            if not pack:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} not installed'
                }
            
            if pack_id in self.active_packs:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} already active'
                }
            
            # Simulate activation process
            pack.status = 'active'
            self.active_packs[pack_id] = pack
            
            return {
                'success': True,
                'pack_id': pack_id,
                'pack_name': pack.name,
                'message': f'Successfully activated expansion pack: {pack.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deactivate_expansion_pack(self, pack_id: str) -> Dict[str, Any]:
        """Deactivate a BMAD-Method expansion pack"""
        try:
            if pack_id not in self.active_packs:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} not active'
                }
            
            pack = self.active_packs[pack_id]
            pack.status = 'installed'
            del self.active_packs[pack_id]
            
            return {
                'success': True,
                'pack_id': pack_id,
                'pack_name': pack.name,
                'message': f'Successfully deactivated expansion pack: {pack.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def remove_expansion_pack(self, pack_id: str) -> Dict[str, Any]:
        """Remove a BMAD-Method expansion pack"""
        try:
            if pack_id in self.active_packs:
                await self.deactivate_expansion_pack(pack_id)
            
            if pack_id not in self.installed_packs:
                return {
                    'success': False,
                    'error': f'Expansion pack {pack_id} not installed'
                }
            
            pack = self.installed_packs[pack_id]
            pack.status = 'available'
            del self.installed_packs[pack_id]
            
            return {
                'success': True,
                'pack_id': pack_id,
                'pack_name': pack.name,
                'message': f'Successfully removed expansion pack: {pack.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_expansion_pack(self, pack_id: str) -> Optional[BMADExpansionPack]:
        """Get a specific expansion pack by ID"""
        return self.discovered_packs.get(pack_id)
    
    async def get_expansion_packs_by_category(self, category: str) -> List[BMADExpansionPack]:
        """Get all expansion packs in a specific category"""
        return [pack for pack in self.discovered_packs.values() if pack.category == category]
    
    async def list_installed_packs(self) -> List[BMADExpansionPack]:
        """List all installed expansion packs"""
        return list(self.installed_packs.values())
    
    async def list_active_packs(self) -> List[BMADExpansionPack]:
        """List all active expansion packs"""
        return list(self.active_packs.values())
    
    async def get_expansion_pack_status(self) -> Dict[str, Any]:
        """Get current expansion pack manager status"""
        return {
            'total_packs': len(self.discovered_packs),
            'installed_packs': len(self.installed_packs),
            'active_packs': len(self.active_packs),
            'categories': {
                category: len([pack for pack in self.discovered_packs.values() if pack.category == category])
                for category in self.pack_categories.keys()
            },
            'cerebral_extensions': {
                'mcp_integration': True,
                'context_preservation': True,
                'session_management': True,
                'webmcp_routing': True,
                'auto_discovery': True
            },
            'manager_version': '1.0',
            'last_discovery': datetime.now().isoformat()
        }

# Global expansion pack manager instance
bmad_expansion_pack_manager = BMADExpansionPackManager()
