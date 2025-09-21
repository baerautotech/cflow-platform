#!/usr/bin/env python3
"""
Test script for BMAD Expansion Pack System

This script validates the expansion pack system and MCP tools
for Game Dev, DevOps, and Technical Research expansion packs.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.direct_client import execute_mcp_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_expansion_pack_system():
    """Test the expansion pack system"""
    
    print("🎮 BMAD Expansion Pack System Test")
    print("=" * 60)
    
    try:
        # Test 1: Expansion System Status
        print("\n📊 Testing Expansion System Status...")
        status_result = await execute_mcp_tool('bmad_expansion_system_status')
        
        print(f"✅ Expansion System Status: {status_result.get('success', False)}")
        if status_result.get('system_status'):
            status = status_result['system_status']
            print(f"   System Active: {status.get('system_active', False)}")
            manager_status = status.get('manager_status', {})
            print(f"   Total Available: {manager_status.get('total_available', 0)}")
            print(f"   Total Installed: {manager_status.get('total_installed', 0)}")
            print(f"   Total Active: {manager_status.get('total_active', 0)}")
        
        # Test 2: List Expansion Packs
        print("\n📋 Testing Expansion Pack List...")
        list_result = await execute_mcp_tool('bmad_expansion_pack_list')
        
        print(f"✅ Expansion Pack List: {list_result.get('success', False)}")
        if list_result.get('packs_data'):
            packs_data = list_result['packs_data']
            summary = packs_data.get('summary', {})
            print(f"   Available Packs: {summary.get('total_available', 0)}")
            print(f"   Installed Packs: {summary.get('total_installed', 0)}")
            print(f"   Active Packs: {summary.get('total_active', 0)}")
            
            # Show available packs
            available_packs = packs_data.get('available_packs', [])
            print("   Available Expansion Packs:")
            for pack in available_packs:
                print(f"     - {pack.get('name', 'Unknown')} ({pack.get('pack_id', 'unknown')})")
                print(f"       Type: {pack.get('pack_type', 'unknown')}")
                print(f"       Agents: {pack.get('agents_count', 0)}, Tools: {pack.get('tools_count', 0)}")
        
        # Test 3: Install Game Dev Expansion Pack (may already be installed)
        print("\n🎮 Testing Game Dev Expansion Pack Installation...")
        install_result = await execute_mcp_tool('bmad_expansion_pack_install', pack_id='game_dev')
        
        install_success = install_result.get('success', False)
        install_message = install_result.get('install_result', {}).get('message', 'No message')
        print(f"✅ Game Dev Installation: {install_success}")
        print(f"   Message: {install_message}")
        
        # Test 4: Activate Game Dev Expansion Pack (may already be active)
        print("\n🚀 Testing Game Dev Expansion Pack Activation...")
        activate_result = await execute_mcp_tool('bmad_expansion_pack_activate', pack_id='game_dev')
        
        activate_success = activate_result.get('success', False)
        activate_message = activate_result.get('activate_result', {}).get('message', 'No message')
        print(f"✅ Game Dev Activation: {activate_success}")
        print(f"   Message: {activate_message}")
        
        # Test 5: Install DevOps Expansion Pack (may already be installed)
        print("\n🔧 Testing DevOps Expansion Pack Installation...")
        devops_install_result = await execute_mcp_tool('bmad_expansion_pack_install', pack_id='devops')
        
        devops_success = devops_install_result.get('success', False)
        devops_message = devops_install_result.get('install_result', {}).get('message', 'No message')
        print(f"✅ DevOps Installation: {devops_success}")
        print(f"   Message: {devops_message}")
        
        # Test 6: Install Technical Research Expansion Pack (may already be installed)
        print("\n🔬 Testing Technical Research Expansion Pack Installation...")
        research_install_result = await execute_mcp_tool('bmad_expansion_pack_install', pack_id='technical_research')
        
        research_success = research_install_result.get('success', False)
        research_message = research_install_result.get('install_result', {}).get('message', 'No message')
        print(f"✅ Technical Research Installation: {research_success}")
        print(f"   Message: {research_message}")
        
        # Test 7: Validate Expansion Packs
        print("\n✅ Testing Expansion Pack Validation...")
        validation_results = []
        
        for pack_id in ['game_dev', 'devops', 'technical_research']:
            validate_result = await execute_mcp_tool('bmad_expansion_pack_validate', pack_id=pack_id)
            validation_results.append((pack_id, validate_result.get('success', False)))
            print(f"   {pack_id}: {'✅ PASS' if validate_result.get('success', False) else '❌ FAIL'}")
        
        # Test 8: List Installed Packs
        print("\n📦 Testing Installed Expansion Packs List...")
        installed_list_result = await execute_mcp_tool('bmad_expansion_pack_list')
        
        print(f"✅ Installed Packs List: {installed_list_result.get('success', False)}")
        if installed_list_result.get('packs_data'):
            packs_data = installed_list_result['packs_data']
            summary = packs_data.get('summary', {})
            print(f"   Installed Packs: {summary.get('total_installed', 0)}")
            print(f"   Active Packs: {summary.get('total_active', 0)}")
            
            # Show installed packs
            installed_packs = packs_data.get('installed_packs', [])
            print("   Installed Expansion Packs:")
            for pack in installed_packs:
                print(f"     - {pack.get('name', 'Unknown')} ({pack.get('pack_id', 'unknown')})")
                print(f"       Version: {pack.get('version', 'unknown')}")
                print(f"       Agents: {pack.get('agents_count', 0)}, Tools: {pack.get('tools_count', 0)}")
        
        # Test 9: Deactivate Game Dev Pack
        print("\n⏸️ Testing Game Dev Expansion Pack Deactivation...")
        deactivate_result = await execute_mcp_tool('bmad_expansion_pack_deactivate', pack_id='game_dev')
        
        print(f"✅ Game Dev Deactivation: {deactivate_result.get('success', False)}")
        if deactivate_result.get('deactivate_result'):
            deactivate_data = deactivate_result['deactivate_result']
            print(f"   Success: {deactivate_data.get('success', False)}")
            print(f"   Message: {deactivate_data.get('message', 'No message')}")
        
        # Test 10: Update Expansion Pack
        print("\n🔄 Testing Expansion Pack Update...")
        update_result = await execute_mcp_tool('bmad_expansion_pack_update', pack_id='game_dev')
        
        print(f"✅ Expansion Pack Update: {update_result.get('success', False)}")
        if update_result.get('update_result'):
            update_data = update_result['update_result']
            print(f"   Update Success: {update_data.get('install_success', False)}")
            print(f"   Message: {update_result.get('message', 'No message')}")
        
        # Summary
        print("\n🎉 Expansion Pack System Test Summary")
        print("=" * 60)
        
        # Consider "already installed" as success for installation tests
        install_success = install_result.get('success', False) or "already installed" in install_message.lower()
        activate_success = activate_result.get('success', False) or "already active" in activate_message.lower()
        devops_success = devops_install_result.get('success', False) or "already installed" in devops_message.lower()
        research_success = research_install_result.get('success', False) or "already installed" in research_message.lower()
        
        test_results = [
            ("Expansion System Status", status_result.get('success', False)),
            ("Expansion Pack List", list_result.get('success', False)),
            ("Game Dev Installation", install_success),
            ("Game Dev Activation", activate_success),
            ("DevOps Installation", devops_success),
            ("Technical Research Installation", research_success),
            ("Expansion Pack Validation", all(success for _, success in validation_results)),
            ("Installed Packs List", installed_list_result.get('success', False)),
            ("Game Dev Deactivation", deactivate_result.get('success', False)),
            ("Expansion Pack Update", update_result.get('success', False))
        ]
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All expansion pack system tests passed!")
            return True
        else:
            print("⚠️  Some expansion pack system tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    
    print("Starting BMAD Expansion Pack System Test...")
    
    success = await test_expansion_pack_system()
    
    if success:
        print("\n✅ Expansion Pack System is ready!")
        sys.exit(0)
    else:
        print("\n❌ Expansion Pack System has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
