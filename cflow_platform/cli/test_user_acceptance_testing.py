#!/usr/bin/env python3
"""
Test script for BMAD User Acceptance Testing Framework

This script validates the user acceptance testing engine and MCP tools
for user scenario testing, usability testing, and accessibility testing.
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


async def test_user_acceptance_testing():
    """Test the user acceptance testing framework"""
    
    print("👥 BMAD User Acceptance Testing Framework Test")
    print("=" * 60)
    
    try:
        # Test 1: User Scenario Testing
        print("\n🎭 Testing User Scenario Testing...")
        scenario_result = await execute_mcp_tool(
            'bmad_uat_scenario_test',
            scenario_name='bmad_workflow_complete',
            user_role='developer',
            timeout_seconds=30.0
        )
        
        print(f"✅ User Scenario Test Result: {scenario_result.get('success', False)}")
        print(f"   Test ID: {scenario_result.get('test_id', 'N/A')}")
        print(f"   Status: {scenario_result.get('status', 'unknown')}")
        print(f"   Duration: {scenario_result.get('duration_seconds', 0):.1f}s")
        if scenario_result.get('summary'):
            summary = scenario_result['summary']
            print(f"   Scenario: {summary.get('scenario_name', 'N/A')}")
            print(f"   User Role: {summary.get('user_role', 'N/A')}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 2: Usability Testing
        print("\n🎨 Testing Usability Testing...")
        usability_result = await execute_mcp_tool(
            'bmad_uat_usability_test',
            interface_component='main_interface',
            user_role='end_user',
            timeout_seconds=15.0
        )
        
        print(f"✅ Usability Test Result: {usability_result.get('success', False)}")
        print(f"   Test ID: {usability_result.get('test_id', 'N/A')}")
        print(f"   Status: {usability_result.get('status', 'unknown')}")
        print(f"   Duration: {usability_result.get('duration_seconds', 0):.1f}s")
        if usability_result.get('summary'):
            summary = usability_result['summary']
            print(f"   Interface: {summary.get('interface_component', 'N/A')}")
            print(f"   Overall Score: {summary.get('overall_score', 0):.1f}%")
            print(f"   Usability Grade: {summary.get('usability_grade', 'N/A')}")
        
        # Test 3: Accessibility Testing
        print("\n♿ Testing Accessibility Testing...")
        accessibility_result = await execute_mcp_tool(
            'bmad_uat_accessibility_test',
            interface_component='main_interface',
            wcag_level='AA',
            timeout_seconds=15.0
        )
        
        print(f"✅ Accessibility Test Result: {accessibility_result.get('success', False)}")
        print(f"   Test ID: {accessibility_result.get('test_id', 'N/A')}")
        print(f"   Status: {accessibility_result.get('status', 'unknown')}")
        print(f"   Duration: {accessibility_result.get('duration_seconds', 0):.1f}s")
        if accessibility_result.get('summary'):
            summary = accessibility_result['summary']
            print(f"   Interface: {summary.get('interface_component', 'N/A')}")
            print(f"   WCAG Level: {summary.get('wcag_level', 'N/A')}")
            print(f"   Overall Score: {summary.get('overall_score', 0):.1f}%")
            print(f"   Accessibility Grade: {summary.get('accessibility_grade', 'N/A')}")
            print(f"   Compliance Status: {summary.get('compliance_status', 'N/A')}")
        
        # Test 4: Full UAT Suite
        print("\n🎯 Testing Full UAT Suite...")
        full_suite_result = await execute_mcp_tool(
            'bmad_uat_full_suite',
            scenarios=['bmad_workflow_complete'],
            interface_components=['main_interface'],
            include_usability=True,
            include_accessibility=True,
            wcag_level='AA'
        )
        
        print(f"✅ Full UAT Suite Result: {full_suite_result.get('success', False)}")
        print(f"   Test ID: {full_suite_result.get('test_id', 'N/A')}")
        print(f"   Status: {full_suite_result.get('status', 'unknown')}")
        print(f"   Duration: {full_suite_result.get('duration_seconds', 0):.1f}s")
        if full_suite_result.get('summary'):
            summary = full_suite_result['summary']
            print(f"   Total Tests: {summary.get('total_tests', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
            print(f"   Scenario Tests: {summary.get('scenario_tests', 0)}")
            print(f"   Usability Tests: {summary.get('usability_tests', 0)}")
            print(f"   Accessibility Tests: {summary.get('accessibility_tests', 0)}")
        
        # Test 5: UAT Report Generation
        print("\n📋 Testing UAT Report Generation...")
        report_result = await execute_mcp_tool(
            'bmad_uat_report_generate',
            test_type=None,
            days_back=1,
            format='json'
        )
        
        print(f"✅ UAT Report Result: {report_result.get('success', False)}")
        print(f"   Report Format: {report_result.get('report_format', 'unknown')}")
        if report_result.get('report_data'):
            report_data = report_result['report_data']
            test_summary = report_data.get('test_summary', {})
            print(f"   Total Tests: {test_summary.get('total_tests', 0)}")
            print(f"   Scenario Tests: {test_summary.get('scenario_tests', 0)}")
            print(f"   Usability Tests: {test_summary.get('usability_tests', 0)}")
            print(f"   Accessibility Tests: {test_summary.get('accessibility_tests', 0)}")
        
        # Test 6: UAT History
        print("\n📚 Testing UAT History...")
        history_result = await execute_mcp_tool(
            'bmad_uat_history_get',
            test_type=None,
            limit=10
        )
        
        print(f"✅ UAT History Result: {history_result.get('success', False)}")
        print(f"   Total Count: {history_result.get('total_count', 0)}")
        print(f"   Test Type Filter: {history_result.get('test_type', 'None')}")
        
        # Summary
        print("\n🎉 User Acceptance Testing Framework Test Summary")
        print("=" * 60)
        
        test_results = [
            ("User Scenario Testing", scenario_result.get('success', False)),
            ("Usability Testing", usability_result.get('success', False)),
            ("Accessibility Testing", accessibility_result.get('success', False)),
            ("Full UAT Suite", full_suite_result.get('success', False)),
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
            print("🎉 All user acceptance testing tests passed!")
            return True
        else:
            print("⚠️  Some user acceptance testing tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    
    print("Starting BMAD User Acceptance Testing Framework Test...")
    
    success = await test_user_acceptance_testing()
    
    if success:
        print("\n✅ User Acceptance Testing Framework is ready!")
        sys.exit(0)
    else:
        print("\n❌ User Acceptance Testing Framework has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
