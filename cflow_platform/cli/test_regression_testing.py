#!/usr/bin/env python3
"""
Regression Testing Validation Script

Tests the regression testing framework functionality including:
- Regression test discovery and management
- Regression test execution
- MCP integration
- Cerebral extensions
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.direct_client import execute_mcp_tool

async def test_regression_discovery():
    """Test regression test discovery functionality"""
    print("🔍 Testing Regression Test Discovery")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_regression_discover_tests')
        if result['success']:
            print(f"✅ Regression discovery: {result.get('total_count', 0)} tests found")
            return True
        else:
            print(f"❌ Regression discovery failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Regression discovery error: {e}")
        return False

async def test_regression_execution():
    """Test regression test execution functionality"""
    print("\n⚡ Testing Regression Test Execution")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_regression_execute_test', test_id='test-regression')
        if result['success']:
            print(f"✅ Regression execution: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Regression execution failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Regression execution error: {e}")
        return False

async def test_regression_management():
    """Test regression test management functionality"""
    print("\n📊 Testing Regression Test Management")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_regression_get_test_status')
        if result['success']:
            print(f"✅ Regression management: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Regression management failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Regression management error: {e}")
        return False

async def test_regression_test_suite():
    """Test regression test suite functionality"""
    print("\n🧪 Testing Regression Test Suite")
    print("-" * 40)
    
    try:
        result = await execute_mcp_tool('bmad_regression_test_run_complete')
        if result['success']:
            print(f"✅ Regression test suite: {result.get('message', 'Working')}")
            return True
        else:
            print(f"❌ Regression test suite failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Regression test suite error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive regression testing validation"""
    print("🧪 Regression Testing Comprehensive Validation")
    print("=" * 60)
    
    tests = [
        ("Regression Discovery", test_regression_discovery),
        ("Regression Execution", test_regression_execution),
        ("Regression Management", test_regression_management),
        ("Regression Test Suite", test_regression_test_suite),
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
        print("🎉 All regression testing tests passed!")
        return True
    else:
        print("⚠️ Some regression testing tests failed.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Regression testing validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
