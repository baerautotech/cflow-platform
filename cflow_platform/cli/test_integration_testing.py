#!/usr/bin/env python3
"""
Test script for BMAD Integration Testing Framework

This script validates the integration testing engine and MCP tools
for cross-component testing, API integration testing, and database integration testing.
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


async def test_integration_testing():
    """Test the integration testing framework"""
    
    print("🔗 BMAD Integration Testing Framework Test")
    print("=" * 60)
    
    try:
        # Test 1: Cross-Component Integration Testing
        print("\n🧩 Testing Cross-Component Integration...")
        cross_component_result = await execute_mcp_tool(
            'bmad_integration_cross_component_test',
            components=['direct_client', 'tool_registry', 'handlers'],
            timeout_seconds=15.0,
            retry_attempts=2,
            parallel_execution=True
        )
        
        print(f"✅ Cross-Component Test Result: {cross_component_result.get('success', False)}")
        print(f"   Test ID: {cross_component_result.get('test_id', 'N/A')}")
        print(f"   Status: {cross_component_result.get('status', 'unknown')}")
        print(f"   Duration: {cross_component_result.get('duration_seconds', 0):.1f}s")
        if cross_component_result.get('summary'):
            summary = cross_component_result['summary']
            print(f"   Components Tested: {summary.get('total_component_tests', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 2: API Integration Testing
        print("\n🌐 Testing API Integration...")
        api_result = await execute_mcp_tool(
            'bmad_integration_api_test',
            base_url='http://localhost:8000',
            endpoints=['/health', '/api/v1/status'],
            timeout_seconds=5.0,
            retry_attempts=2,
            validate_response_schema=True
        )
        
        print(f"✅ API Integration Test Result: {api_result.get('success', False)}")
        print(f"   Test ID: {api_result.get('test_id', 'N/A')}")
        print(f"   Status: {api_result.get('status', 'unknown')}")
        print(f"   Duration: {api_result.get('duration_seconds', 0):.1f}s")
        if api_result.get('summary'):
            summary = api_result['summary']
            print(f"   Endpoints Tested: {summary.get('total_api_tests', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 3: Database Integration Testing
        print("\n🗄️ Testing Database Integration...")
        database_result = await execute_mcp_tool(
            'bmad_integration_database_test',
            connection_string='postgresql://localhost:5432/cflow_platform',
            test_operations=['connection_test', 'table_access_test'],
            timeout_seconds=10.0,
            retry_attempts=2,
            validate_data_consistency=True
        )
        
        print(f"✅ Database Integration Test Result: {database_result.get('success', False)}")
        print(f"   Test ID: {database_result.get('test_id', 'N/A')}")
        print(f"   Status: {database_result.get('status', 'unknown')}")
        print(f"   Duration: {database_result.get('duration_seconds', 0):.1f}s")
        if database_result.get('summary'):
            summary = database_result['summary']
            print(f"   Operations Tested: {summary.get('total_database_tests', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 4: Full Integration Suite
        print("\n🎯 Testing Full Integration Suite...")
        full_suite_result = await execute_mcp_tool(
            'bmad_integration_full_suite',
            include_components=['direct_client', 'tool_registry'],
            include_apis=False,  # Skip API tests for this demo
            include_database=False,  # Skip database tests for this demo
            api_base_url='http://localhost:8000',
            database_connection_string='postgresql://localhost:5432/cflow_platform'
        )
        
        print(f"✅ Full Suite Test Result: {full_suite_result.get('success', False)}")
        print(f"   Test ID: {full_suite_result.get('test_id', 'N/A')}")
        print(f"   Status: {full_suite_result.get('status', 'unknown')}")
        print(f"   Duration: {full_suite_result.get('duration_seconds', 0):.1f}s")
        if full_suite_result.get('summary'):
            summary = full_suite_result['summary']
            print(f"   Test Suites Run: {summary.get('total_test_suites', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 5: Integration Report Generation
        print("\n📋 Testing Integration Report Generation...")
        report_result = await execute_mcp_tool(
            'bmad_integration_report_generate',
            test_type=None,
            days_back=1,
            format='json'
        )
        
        print(f"✅ Integration Report Result: {report_result.get('success', False)}")
        print(f"   Report Format: {report_result.get('report_format', 'unknown')}")
        if report_result.get('report_data'):
            report_data = report_result['report_data']
            test_summary = report_data.get('test_summary', {})
            print(f"   Total Tests: {test_summary.get('total_tests', 0)}")
            print(f"   Cross-Component Tests: {test_summary.get('cross_component_tests', 0)}")
            print(f"   API Integration Tests: {test_summary.get('api_integration_tests', 0)}")
            print(f"   Database Integration Tests: {test_summary.get('database_integration_tests', 0)}")
        
        # Test 6: Integration History
        print("\n📚 Testing Integration History...")
        history_result = await execute_mcp_tool(
            'bmad_integration_history_get',
            test_type=None,
            limit=10
        )
        
        print(f"✅ Integration History Result: {history_result.get('success', False)}")
        print(f"   Total Count: {history_result.get('total_count', 0)}")
        print(f"   Test Type Filter: {history_result.get('test_type', 'None')}")
        
        # Summary
        print("\n🎉 Integration Testing Framework Test Summary")
        print("=" * 60)
        
        test_results = [
            ("Cross-Component Integration", cross_component_result.get('success', False)),
            ("API Integration", api_result.get('success', False)),
            ("Database Integration", database_result.get('success', False)),
            ("Full Integration Suite", full_suite_result.get('success', False)),
            ("Report Generation", report_result.get('success', False)),
            ("History Retrieval", history_result.get('success', False))
        ]
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All integration testing tests passed!")
            return True
        else:
            print("⚠️  Some integration testing tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    
    print("Starting BMAD Integration Testing Framework Test...")
    
    success = await test_integration_testing()
    
    if success:
        print("\n✅ Integration Testing Framework is ready!")
        sys.exit(0)
    else:
        print("\n❌ Integration Testing Framework has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
