#!/usr/bin/env python3
"""
Scenario Testing Validation Script

Tests the scenario testing framework functionality including:
- Scenario discovery and management
- Scenario execution
- MCP integration
- Cerebral extensions
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.direct_client import execute_mcp_tool

async def test_scenario_discovery():
    """Test scenario discovery functionality"""
    print("🔍 Testing Scenario Discovery")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_scenario_discover_scenarios')
        if result['success']:
            print(f"✅ Scenario discovery: {result.get('total_count', 0)} scenarios found")
            return True
        else:
            print(f"❌ Scenario discovery failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Scenario discovery error: {e}")
        return False

async def test_scenario_execution():
    """Test scenario execution functionality"""
    print("\n⚡ Testing Scenario Execution")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_scenario_execute_scenario', scenario_id='test-scenario')
        if result['success']:
            print(f"✅ Scenario execution: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Scenario execution failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Scenario execution error: {e}")
        return False

async def test_scenario_management():
    """Test scenario management functionality"""
    print("\n📊 Testing Scenario Management")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_scenario_get_scenario_status')
        if result['success']:
            print(f"✅ Scenario management: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Scenario management failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Scenario management error: {e}")
        return False

async def test_scenario_test_suite():
    """Test scenario test suite functionality"""
    print("\n🧪 Testing Scenario Test Suite")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_scenario_test_run_complete')
        if result['success']:
            print(f"✅ Scenario test suite: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Scenario test suite failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Scenario test suite error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive scenario testing validation"""
    print("🧪 Scenario Testing Comprehensive Validation")
    print("=" * 60)
    
    tests = [
        ("Scenario Discovery", test_scenario_discovery),
        ("Scenario Execution", test_scenario_execution),
        ("Scenario Management", test_scenario_management),
        ("Scenario Test Suite", test_scenario_test_suite),
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All scenario testing tests passed!")
        return True
    else:
        print("⚠️ Some scenario testing tests failed.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Scenario testing validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
