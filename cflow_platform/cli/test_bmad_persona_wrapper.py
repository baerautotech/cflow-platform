#!/usr/bin/env python3
"""Test script for BMAD-Method persona wrapper"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.bmad_persona_wrapper import bmad_persona_wrapper

async def test_bmad_persona_wrapper():
    print('🧪 Testing BMAD-Method Persona Wrapper')
    print('=' * 50)
    
    # Test 1: Discover personas
    print('\n1. Discovering BMAD-Method personas...')
    personas = await bmad_persona_wrapper.discover_bmad_personas()
    
    if personas:
        print(f'✅ Discovered {len(personas)} personas:')
        for persona_id, persona in personas.items():
            print(f'   • {persona.name} ({persona_id}) - {persona.title}')
    else:
        print('❌ No personas discovered')
        return False
    
    # Test 2: Get status
    print('\n2. Getting persona status...')
    status = await bmad_persona_wrapper.get_persona_status()
    print(f'✅ Status: {status}')
    
    # Test 3: Activate a persona (try bmad-master first)
    print('\n3. Activating BMAD Master persona...')
    if 'bmad-master' in personas:
        result = await bmad_persona_wrapper.activate_persona('bmad-master')
        if result['success']:
            print(f'✅ Activated: {result["persona"]["name"]}')
            print(f'   Role: {result["persona"]["role"]}')
            print(f'   Cerebral Extensions: {result["cerebral_extensions"]}')
        else:
            print(f'❌ Activation failed: {result["error"]}')
    else:
        print('❌ BMAD Master persona not found')
    
    # Test 4: Execute a command
    print('\n4. Testing persona command execution...')
    if bmad_persona_wrapper.active_persona:
        cmd_result = await bmad_persona_wrapper.execute_persona_command('help')
        if cmd_result['success']:
            print(f'✅ Command executed: {cmd_result["result"]}')
        else:
            print(f'❌ Command failed: {cmd_result["error"]}')
    
    # Test 5: Switch persona (try pm if available)
    print('\n5. Testing persona switching...')
    if 'pm' in personas:
        switch_result = await bmad_persona_wrapper.switch_persona('pm')
        if switch_result['success']:
            print(f'✅ Switched to: {switch_result["persona"]["name"]}')
        else:
            print(f'❌ Switch failed: {switch_result["error"]}')
    else:
        print('❌ PM persona not found')
    
    # Test 6: Final status
    print('\n6. Final status...')
    final_status = await bmad_persona_wrapper.get_persona_status()
    print(f'✅ Final status: {final_status}')
    
    print('\n🎯 BMAD-Method Persona Wrapper Test Complete!')
    return True

if __name__ == '__main__':
    success = asyncio.run(test_bmad_persona_wrapper())
    sys.exit(0 if success else 1)
