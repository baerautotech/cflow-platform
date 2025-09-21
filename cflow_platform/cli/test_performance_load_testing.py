#!/usr/bin/env python3
"""
Test script for Performance and Load Testing functionality.

This script validates the performance and load testing capabilities
for BMAD integration.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.direct_client import execute_mcp_tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_performance_load_test():
    """Test the performance load test functionality."""
    logger.info("Testing performance load test...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_performance_load_test",
            concurrent_users=5,
            duration_seconds=10,
            ramp_up_seconds=2,
            tool_name="sys_test"
        )
        
        logger.info(f"Load test result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "total_requests" in result, "Result should contain 'total_requests' field"
        assert "successful_requests" in result, "Result should contain 'successful_requests' field"
        assert "average_response_time" in result, "Result should contain 'average_response_time' field"
        
        logger.info("✅ Performance load test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance load test failed: {e}")
        return False


async def test_performance_stress_test():
    """Test the performance stress test functionality."""
    logger.info("Testing performance stress test...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_performance_stress_test",
            tool_name="sys_test",
            max_concurrent_users=20,
            increment=5,
            duration_per_level=5
        )
        
        logger.info(f"Stress test result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "max_concurrent_users" in result, "Result should contain 'max_concurrent_users' field"
        assert "recommendations" in result, "Result should contain 'recommendations' field"
        
        logger.info("✅ Performance stress test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance stress test failed: {e}")
        return False


async def test_performance_benchmark():
    """Test the performance benchmark functionality."""
    logger.info("Testing performance benchmark...")
    
    try:
        # Create tools configuration
        tools_config = json.dumps([
            {"tool_name": "sys_test", "tool_args": {}},
            {"tool_name": "sys_stats", "tool_args": {}}
        ])
        
        result = await execute_mcp_tool(
            "bmad_performance_benchmark",
            tools_config=tools_config,
            iterations=3
        )
        
        logger.info(f"Benchmark result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "benchmark_results" in result, "Result should contain 'benchmark_results' field"
        assert "tools_tested" in result, "Result should contain 'tools_tested' field"
        
        logger.info("✅ Performance benchmark passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance benchmark failed: {e}")
        return False


async def test_performance_regression_test():
    """Test the performance regression test functionality."""
    logger.info("Testing performance regression test...")
    
    try:
        # Create baseline metrics
        baseline_metrics = json.dumps({
            "average_execution_time": 0.1,
            "average_memory_usage": 1.0,
            "average_cpu_usage": 5.0
        })
        
        result = await execute_mcp_tool(
            "bmad_performance_regression_test",
            tool_name="sys_test",
            baseline_metrics=baseline_metrics,
            threshold_percentage=20.0
        )
        
        logger.info(f"Regression test result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "regression_detected" in result, "Result should contain 'regression_detected' field"
        assert "regression_details" in result, "Result should contain 'regression_details' field"
        
        logger.info("✅ Performance regression test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance regression test failed: {e}")
        return False


async def test_performance_test_history():
    """Test the performance test history functionality."""
    logger.info("Testing performance test history...")
    
    try:
        result = await execute_mcp_tool("bmad_performance_test_history")
        
        logger.info(f"Test history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "history" in result, "Result should contain 'history' field"
        assert "load_tests_count" in result, "Result should contain 'load_tests_count' field"
        
        logger.info("✅ Performance test history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test history failed: {e}")
        return False


async def test_performance_clear_history():
    """Test the performance clear history functionality."""
    logger.info("Testing performance clear history...")
    
    try:
        result = await execute_mcp_tool("bmad_performance_clear_history")
        
        logger.info(f"Clear history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ Performance clear history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance clear history failed: {e}")
        return False


async def test_performance_system_monitor():
    """Test the performance system monitor functionality."""
    logger.info("Testing performance system monitor...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_performance_system_monitor",
            duration_seconds=5
        )
        
        logger.info(f"System monitor result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "monitoring_duration" in result, "Result should contain 'monitoring_duration' field"
        assert "peak_metrics" in result, "Result should contain 'peak_metrics' field"
        
        logger.info("✅ Performance system monitor passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance system monitor failed: {e}")
        return False


async def run_all_tests():
    """Run all performance and load testing tests."""
    logger.info("Starting Performance and Load Testing validation...")
    
    tests = [
        ("Performance Load Test", test_performance_load_test),
        ("Performance Stress Test", test_performance_stress_test),
        ("Performance Benchmark", test_performance_benchmark),
        ("Performance Regression Test", test_performance_regression_test),
        ("Performance Test History", test_performance_test_history),
        ("Performance Clear History", test_performance_clear_history),
        ("Performance System Monitor", test_performance_system_monitor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        start_time = time.time()
        success = await test_func()
        duration = time.time() - start_time
        
        results.append({
            "test": test_name,
            "success": success,
            "duration": duration
        })
        
        if success:
            logger.info(f"✅ {test_name} completed successfully in {duration:.2f}s")
        else:
            logger.error(f"❌ {test_name} failed after {duration:.2f}s")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("PERFORMANCE AND LOAD TESTING VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Performance and Load Testing tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
