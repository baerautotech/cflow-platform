#!/usr/bin/env python3
"""
Test script for BMAD Performance Validation Framework

This script validates the performance validation engine and MCP tools
for load testing, stress testing, and scalability testing.
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


async def test_performance_validation():
    """Test the performance validation framework"""
    
    print("🚀 BMAD Performance Validation Framework Test")
    print("=" * 60)
    
    try:
        # Test 1: Load Testing
        print("\n📊 Testing Load Testing...")
        load_result = await execute_mcp_tool(
            'bmad_performance_load_test',
            target_users=5,
            ramp_up_duration=10,
            test_duration=20,
            ramp_down_duration=10,
            concurrent_requests=2,
            request_timeout=3.0,
            think_time=0.5
        )
        
        print(f"✅ Load Test Result: {load_result.get('success', False)}")
        print(f"   Test ID: {load_result.get('test_id', 'N/A')}")
        print(f"   Status: {load_result.get('status', 'unknown')}")
        print(f"   Duration: {load_result.get('duration_seconds', 0):.1f}s")
        if load_result.get('summary'):
            summary = load_result['summary']
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
            print(f"   Avg Response Time: {summary.get('avg_response_time', 0):.1f}ms")
        
        # Test 2: Stress Testing
        print("\n⚡ Testing Stress Testing...")
        stress_result = await execute_mcp_tool(
            'bmad_performance_stress_test',
            start_users=2,
            max_users=10,
            increment_users=2,
            increment_interval=5,
            test_duration=10,
            failure_threshold=10.0,
            resource_threshold=85.0
        )
        
        print(f"✅ Stress Test Result: {stress_result.get('success', False)}")
        print(f"   Test ID: {stress_result.get('test_id', 'N/A')}")
        print(f"   Status: {stress_result.get('status', 'unknown')}")
        print(f"   Duration: {stress_result.get('duration_seconds', 0):.1f}s")
        if stress_result.get('summary'):
            summary = stress_result['summary']
            print(f"   Max Users Tested: {summary.get('max_users_tested', 0)}")
            print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Test 3: Scalability Testing
        print("\n📈 Testing Scalability Testing...")
        scalability_result = await execute_mcp_tool(
            'bmad_performance_scalability_test',
            min_users=2,
            max_users=8,
            user_increment=2,
            test_duration_per_level=10,
            performance_degradation_threshold=100.0,
            resource_scaling_threshold=80.0
        )
        
        print(f"✅ Scalability Test Result: {scalability_result.get('success', False)}")
        print(f"   Test ID: {scalability_result.get('test_id', 'N/A')}")
        print(f"   Status: {scalability_result.get('status', 'unknown')}")
        print(f"   Duration: {scalability_result.get('duration_seconds', 0):.1f}s")
        if scalability_result.get('summary'):
            summary = scalability_result['summary']
            print(f"   User Levels Tested: {summary.get('user_levels_tested', 0)}")
            print(f"   Max Users Tested: {summary.get('max_users_tested', 0)}")
        
        # Test 4: Metrics Collection
        print("\n📊 Testing Metrics Collection...")
        metrics_result = await execute_mcp_tool(
            'bmad_performance_metrics_collect',
            duration_seconds=10,
            interval_seconds=1.0
        )
        
        print(f"✅ Metrics Collection Result: {metrics_result.get('success', False)}")
        print(f"   Test ID: {metrics_result.get('test_id', 'N/A')}")
        print(f"   Metrics Collected: {metrics_result.get('metrics_collected', 0)}")
        print(f"   Duration: {metrics_result.get('duration_seconds', 0)}s")
        
        # Test 5: SLO Validation
        print("\n🎯 Testing SLO Validation...")
        slo_result = await execute_mcp_tool('bmad_performance_slo_validate')
        
        print(f"✅ SLO Validation Result: {slo_result.get('success', False)}")
        print(f"   Overall Status: {slo_result.get('overall_status', 'unknown')}")
        print(f"   SLO Pass Rate: {slo_result.get('slo_pass_rate', 0):.1f}%")
        print(f"   Passed SLOs: {slo_result.get('passed_slos', 0)}/{slo_result.get('total_slos', 0)}")
        
        # Test 6: Performance Report Generation
        print("\n📋 Testing Performance Report Generation...")
        report_result = await execute_mcp_tool(
            'bmad_performance_report_generate',
            test_type=None,
            days_back=1,
            format='json'
        )
        
        print(f"✅ Performance Report Result: {report_result.get('success', False)}")
        print(f"   Report Format: {report_result.get('report_format', 'unknown')}")
        if report_result.get('report_data'):
            report_data = report_result['report_data']
            test_summary = report_data.get('test_summary', {})
            print(f"   Total Tests: {test_summary.get('total_tests', 0)}")
            print(f"   Load Tests: {test_summary.get('load_tests', 0)}")
            print(f"   Stress Tests: {test_summary.get('stress_tests', 0)}")
            print(f"   Scalability Tests: {test_summary.get('scalability_tests', 0)}")
        
        # Test 7: Performance History
        print("\n📚 Testing Performance History...")
        history_result = await execute_mcp_tool(
            'bmad_performance_history_get',
            test_type=None,
            limit=10
        )
        
        print(f"✅ Performance History Result: {history_result.get('success', False)}")
        print(f"   Total Count: {history_result.get('total_count', 0)}")
        print(f"   Test Type Filter: {history_result.get('test_type', 'None')}")
        
        # Summary
        print("\n🎉 Performance Validation Framework Test Summary")
        print("=" * 60)
        
        test_results = [
            ("Load Testing", load_result.get('success', False)),
            ("Stress Testing", stress_result.get('success', False)),
            ("Scalability Testing", scalability_result.get('success', False)),
            ("Metrics Collection", metrics_result.get('success', False)),
            ("SLO Validation", slo_result.get('success', False)),
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
            print("🎉 All performance validation tests passed!")
            return True
        else:
            print("⚠️  Some performance validation tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    
    print("Starting BMAD Performance Validation Framework Test...")
    
    success = await test_performance_validation()
    
    if success:
        print("\n✅ Performance Validation Framework is ready!")
        sys.exit(0)
    else:
        print("\n❌ Performance Validation Framework has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
