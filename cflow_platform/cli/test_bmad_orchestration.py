#!/usr/bin/env python3
"""
BMAD Orchestration System Testing

Tests the BMAD Master orchestration and background agent systems.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.direct_client import execute_mcp_tool

async def test_background_agent_orchestration():
    """Test background agent orchestration"""
    print("🤖 Testing Background Agent Orchestration")
    print("-" * 50)
    
    try:
        # Test 1: Activate background agents
        print("1. Activating background agents...")
        result = await execute_mcp_tool("bmad_activate_background_agents")
        if result.get('success', False):
            print(f"   ✅ Background agents activated: {result['activated_agents']}/{result['total_agents']} agents")
            print(f"   ✅ Parallel processing: {result['parallel_processing']}")
            print(f"   ✅ Max concurrent agents: {result['max_concurrent_agents']}")
        else:
            print(f"   ❌ Activation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test 2: Get background agent status
        print("\n2. Getting background agent status...")
        result = await execute_mcp_tool("bmad_get_background_agent_status")
        if result.get('success', False):
            print(f"   ✅ Orchestration active: {result['orchestration_active']}")
            print(f"   ✅ Total agents: {result['total_agents']}")
            print(f"   ✅ Active agents: {result['active_agents']}")
            print(f"   ✅ Busy agents: {result['busy_agents']}")
            print(f"   ✅ Idle agents: {result['idle_agents']}")
            print(f"   ✅ Total tasks queued: {result['total_tasks_queued']}")
            
            # Show agent details
            print("   Agent Details:")
            for agent in result['agents']:
                print(f"     • {agent['name']}: {agent['status']} ({agent['tasks_queued']} tasks)")
        else:
            print(f"   ❌ Status check failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test 3: Distribute a task
        print("\n3. Distributing a test task...")
        test_task = {
            'id': 'test_task_001',
            'type': 'persona_management',
            'name': 'Test Persona Management Task',
            'priority': 'high',
            'parameters': {
                'test': True,
                'description': 'Test task for orchestration validation'
            }
        }
        
        result = await execute_mcp_tool("bmad_distribute_task", task=test_task)
        if result.get('success', False):
            print(f"   ✅ Task distributed: {result['task_id']}")
            print(f"   ✅ Assigned agent: {result['assigned_agent']}")
            print(f"   ✅ Queue position: {result['queue_position']}")
        else:
            print(f"   ❌ Task distribution failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Background agent orchestration test failed: {e}")
        return False

async def test_bmad_master_orchestration():
    """Test BMAD Master orchestration"""
    print("\n🎯 Testing BMAD Master Orchestration")
    print("-" * 50)
    
    try:
        # Test 1: Activate BMAD Master orchestration
        print("1. Activating BMAD Master orchestration...")
        result = await execute_mcp_tool("bmad_activate_master_orchestration")
        if result.get('success', False):
            print(f"   ✅ BMAD Master active: {result['bmad_master_active']}")
            print(f"   ✅ Session ID: {result['session_id']}")
            print(f"   ✅ Persona activation: {result['persona_activation']['success']}")
            print(f"   ✅ Background orchestration: {result['background_orchestration']['success']}")
        else:
            print(f"   ❌ Activation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test 2: Get BMAD Master orchestration status
        print("\n2. Getting BMAD Master orchestration status...")
        result = await execute_mcp_tool("bmad_get_master_orchestration_status")
        if result.get('success', False):
            print(f"   ✅ BMAD Master active: {result['bmad_master_active']}")
            print(f"   ✅ Session ID: {result['session_id']}")
            print(f"   ✅ Active workflows: {result['active_workflows']}")
            print(f"   ✅ Completed workflows: {result['completed_workflows']}")
            print(f"   ✅ Background orchestration: {result['background_orchestration']['orchestration_active']}")
            
            # Show workflow details
            if result['workflows']:
                print("   Workflow Details:")
                for workflow in result['workflows'][:3]:  # Show first 3
                    print(f"     • {workflow['name']}: {workflow['status']} ({workflow['progress']}%)")
        else:
            print(f"   ❌ Status check failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test 3: Begin story implementation
        print("\n3. Beginning story implementation...")
        test_story_id = "test_story_001"
        implementation_plan = {
            'story_type': 'feature_implementation',
            'complexity': 'medium',
            'estimated_effort': '2-4 hours',
            'dependencies': [],
            'test_requirements': ['unit_tests', 'integration_tests']
        }
        
        result = await execute_mcp_tool("bmad_begin_story_implementation", 
                                      story_id=test_story_id, 
                                      implementation_plan=implementation_plan)
        if result.get('success', False):
            print(f"   ✅ Story implementation started: {result['story_id']}")
            print(f"   ✅ Workflow ID: {result['workflow_id']}")
            print(f"   ✅ Status: {result['status']}")
            print(f"   ✅ Progress: {result['progress']}%")
        else:
            print(f"   ❌ Story implementation failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ BMAD Master orchestration test failed: {e}")
        return False

async def test_orchestration_integration():
    """Test orchestration system integration"""
    print("\n🔗 Testing Orchestration System Integration")
    print("-" * 50)
    
    try:
        # Test 1: Verify both systems are working together
        print("1. Verifying orchestration integration...")
        
        # Check background agents
        bg_result = await execute_mcp_tool("bmad_get_background_agent_status")
        bg_active = bg_result.get('success', False) and bg_result.get('orchestration_active', False)
        
        # Check BMAD Master
        master_result = await execute_mcp_tool("bmad_get_master_orchestration_status")
        master_active = master_result.get('success', False) and master_result.get('bmad_master_active', False)
        
        if bg_active and master_active:
            print("   ✅ Background agents: Active")
            print("   ✅ BMAD Master: Active")
            print("   ✅ Integration: Working")
            
            # Show combined status
            print(f"   ✅ Total agents: {bg_result['total_agents']}")
            print(f"   ✅ Active workflows: {master_result['active_workflows']}")
            print(f"   ✅ Session ID: {master_result['session_id']}")
            
            return True
        else:
            print(f"   ❌ Integration failed:")
            print(f"     Background agents active: {bg_active}")
            print(f"     BMAD Master active: {master_active}")
            return False
        
    except Exception as e:
        print(f"❌ Orchestration integration test failed: {e}")
        return False

async def test_orchestration_cleanup():
    """Test orchestration system cleanup"""
    print("\n🧹 Testing Orchestration System Cleanup")
    print("-" * 50)
    
    try:
        # Test 1: Deactivate BMAD Master orchestration
        print("1. Deactivating BMAD Master orchestration...")
        result = await execute_mcp_tool("bmad_deactivate_master_orchestration")
        if result.get('success', False):
            print(f"   ✅ BMAD Master deactivated: {result['bmad_master_active']}")
            print(f"   ✅ Background deactivation: {result['background_deactivation']['success']}")
            print(f"   ✅ Persona deactivation: {result['persona_deactivation']['success']}")
        else:
            print(f"   ❌ Deactivation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test 2: Deactivate background agents
        print("\n2. Deactivating background agents...")
        result = await execute_mcp_tool("bmad_deactivate_background_agents")
        if result.get('success', False):
            print(f"   ✅ Background agents deactivated: {result['orchestration_active']}")
            print(f"   ✅ Message: {result['message']}")
        else:
            print(f"   ❌ Deactivation failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestration cleanup test failed: {e}")
        return False

async def run_comprehensive_orchestration_test():
    """Run comprehensive orchestration system validation"""
    print("🧪 BMAD Orchestration System - Comprehensive Validation")
    print("=" * 70)
    
    tests = [
        ("Background Agent Orchestration", test_background_agent_orchestration),
        ("BMAD Master Orchestration", test_bmad_master_orchestration),
        ("Orchestration Integration", test_orchestration_integration),
        ("Orchestration Cleanup", test_orchestration_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Orchestration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All orchestration tests passed!")
        print("🚀 BMAD Master orchestration system is ready!")
        return True
    else:
        print("⚠️ Some orchestration tests failed.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_orchestration_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Orchestration validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
