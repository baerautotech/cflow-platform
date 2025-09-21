"""
Performance and Load Testing Handlers

This module provides MCP handlers for performance and load testing
of the BMAD integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from cflow_platform.core.performance_load_testing_engine import (
    PerformanceLoadTestingEngine,
    LoadTestResult,
    StressTestResult
)

logger = logging.getLogger(__name__)


async def bmad_performance_load_test(
    tool_name: str,
    concurrent_users: int = 10,
    duration_seconds: int = 60,
    ramp_up_seconds: int = 10,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a load test for a specific BMAD tool.
    
    Args:
        tool_name: Name of the tool to test
        concurrent_users: Number of concurrent users (default: 10)
        duration_seconds: Test duration in seconds (default: 60)
        ramp_up_seconds: Ramp-up time in seconds (default: 10)
        tool_args: Arguments to pass to the tool (default: {})
        
    Returns:
        Dictionary with load test results
    """
    try:
        logger.info(f"Starting load test for {tool_name} with {concurrent_users} concurrent users")
        
        engine = PerformanceLoadTestingEngine()
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Run the load test
        result = await engine.run_load_test(
            tool_name=tool_name,
            tool_args=tool_args,
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=ramp_up_seconds
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "failed_requests": result.failed_requests,
            "success_rate": result.successful_requests / result.total_requests if result.total_requests > 0 else 0,
            "average_response_time": result.average_response_time,
            "min_response_time": result.min_response_time,
            "max_response_time": result.max_response_time,
            "p95_response_time": result.p95_response_time,
            "p99_response_time": result.p99_response_time,
            "requests_per_second": result.requests_per_second,
            "total_duration": result.total_duration,
            "memory_peak": result.memory_peak,
            "cpu_peak": result.cpu_peak,
            "error_count": len(result.errors),
            "errors": result.errors[:10],  # Limit to first 10 errors
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Load test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_stress_test(
    tool_name: str,
    max_concurrent_users: int = 100,
    increment: int = 10,
    duration_per_level: int = 30,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a stress test to find the breaking point for a BMAD tool.
    
    Args:
        tool_name: Name of the tool to test
        max_concurrent_users: Maximum number of concurrent users to test (default: 100)
        increment: Increment for concurrent users (default: 10)
        duration_per_level: Duration for each stress level (default: 30)
        tool_args: Arguments to pass to the tool (default: {})
        
    Returns:
        Dictionary with stress test results
    """
    try:
        logger.info(f"Starting stress test for {tool_name} up to {max_concurrent_users} concurrent users")
        
        engine = PerformanceLoadTestingEngine()
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Run the stress test
        result = await engine.run_stress_test(
            tool_name=tool_name,
            tool_args=tool_args,
            max_concurrent_users=max_concurrent_users,
            increment=increment,
            duration_per_level=duration_per_level
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "max_concurrent_users": result.max_concurrent_users,
            "breaking_point": result.breaking_point,
            "performance_degradation_point": result.performance_degradation_point,
            "error_rate_threshold_reached": result.error_rate_threshold_reached,
            "memory_exhaustion_point": result.memory_exhaustion_point,
            "cpu_saturation_point": result.cpu_saturation_point,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stress test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_benchmark(
    tools_config: str,
    iterations: int = 10
) -> Dict[str, Any]:
    """
    Run performance benchmarks for multiple BMAD tools.
    
    Args:
        tools_config: JSON string with list of tools to benchmark
                     Format: [{"tool_name": "tool1", "tool_args": {...}}, ...]
        iterations: Number of iterations per tool (default: 10)
        
    Returns:
        Dictionary with benchmark results
    """
    try:
        logger.info(f"Starting performance benchmark for {iterations} iterations")
        
        # Parse tools configuration
        try:
            tools_list = json.loads(tools_config)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in tools_config: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(tools_list, list):
            return {
                "success": False,
                "error": "tools_config must be a list of tool configurations",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Convert to tuples for the engine
        tools_to_test = []
        for tool_config in tools_list:
            if not isinstance(tool_config, dict) or "tool_name" not in tool_config:
                return {
                    "success": False,
                    "error": "Each tool config must have 'tool_name' field",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            tool_name = tool_config["tool_name"]
            tool_args = tool_config.get("tool_args", {})
            tools_to_test.append((tool_name, tool_args))
        
        engine = PerformanceLoadTestingEngine()
        
        # Run the benchmark
        benchmark_results = await engine.run_performance_benchmark(
            tools_to_test=tools_to_test,
            iterations=iterations
        )
        
        return {
            "success": True,
            "benchmark_results": benchmark_results,
            "tools_tested": len(tools_to_test),
            "iterations_per_tool": iterations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance benchmark failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_regression_test(
    tool_name: str,
    baseline_metrics: str,
    threshold_percentage: float = 20.0,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Detect performance regression by comparing current metrics to baseline.
    
    Args:
        tool_name: Name of the tool to test
        baseline_metrics: JSON string with baseline performance metrics
        threshold_percentage: Threshold for regression detection (default: 20.0)
        tool_args: Arguments to pass to the tool (default: {})
        
    Returns:
        Dictionary with regression analysis results
    """
    try:
        logger.info(f"Detecting performance regression for {tool_name}")
        
        # Parse baseline metrics
        try:
            baseline = json.loads(baseline_metrics)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in baseline_metrics: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(baseline, dict):
            return {
                "success": False,
                "error": "baseline_metrics must be a dictionary",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        engine = PerformanceLoadTestingEngine()
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Run regression detection
        regression_result = await engine.detect_performance_regression(
            tool_name=tool_name,
            tool_args=tool_args,
            baseline_metrics=baseline,
            threshold_percentage=threshold_percentage
        )
        
        return {
            "success": True,
            "tool_name": tool_name,
            "regression_detected": regression_result["regression_detected"],
            "regression_details": regression_result.get("regression_details", {}),
            "current_metrics": regression_result.get("current_metrics"),
            "baseline_metrics": regression_result.get("baseline_metrics"),
            "threshold_percentage": threshold_percentage,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance regression test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_test_history() -> Dict[str, Any]:
    """
    Get history of all performance and load tests.
    
    Returns:
        Dictionary with test history
    """
    try:
        logger.info("Retrieving performance test history")
        
        engine = PerformanceLoadTestingEngine()
        history = engine.get_test_history()
        
        # Convert datetime objects to ISO format for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            else:
                return obj
        
        converted_history = convert_datetime(history)
        
        return {
            "success": True,
            "history": converted_history,
            "load_tests_count": len(history["load_tests"]),
            "stress_tests_count": len(history["stress_tests"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_clear_history() -> Dict[str, Any]:
    """
    Clear all performance and load test history.
    
    Returns:
        Dictionary with operation result
    """
    try:
        logger.info("Clearing performance test history")
        
        engine = PerformanceLoadTestingEngine()
        engine.clear_test_history()
        
        return {
            "success": True,
            "message": "Performance test history cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_performance_system_monitor(
    duration_seconds: int = 60
) -> Dict[str, Any]:
    """
    Monitor system resources for a specified duration.
    
    Args:
        duration_seconds: Duration to monitor in seconds (default: 60)
        
    Returns:
        Dictionary with system monitoring results
    """
    try:
        logger.info(f"Starting system monitoring for {duration_seconds} seconds")
        
        engine = PerformanceLoadTestingEngine()
        monitor = engine._system_monitor
        
        # Start monitoring
        await monitor.start_monitoring()
        
        # Wait for specified duration
        await asyncio.sleep(duration_seconds)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Get results
        peak_metrics = monitor.get_peak_metrics()
        average_metrics = monitor.get_average_metrics()
        
        return {
            "success": True,
            "monitoring_duration": duration_seconds,
            "peak_metrics": peak_metrics,
            "average_metrics": average_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System monitoring failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
