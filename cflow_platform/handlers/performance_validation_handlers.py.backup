"""
MCP Handlers for Performance Validation

This module provides MCP tool handlers for performance validation functionality
including load testing, stress testing, scalability testing, and SLO validation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.performance_validation_engine import (
    PerformanceValidationEngine,
    PerformanceTestType,
    PerformanceTestStatus,
    get_performance_engine
)
from ..core.git_workflow_manager import get_git_workflow_manager

logger = logging.getLogger(__name__)


async def bmad_performance_load_test(
    target_users: int = 10,
    ramp_up_duration: int = 30,
    test_duration: int = 60,
    ramp_down_duration: int = 30,
    concurrent_requests: int = 5,
    request_timeout: float = 5.0,
    think_time: float = 1.0
) -> Dict[str, Any]:
    """
    Run load testing for multi-agent system under load.
    
    Args:
        target_users: Number of concurrent users to simulate
        ramp_up_duration: Time in seconds to ramp up to target users
        test_duration: Duration of the load test in seconds
        ramp_down_duration: Time in seconds to ramp down from target users
        concurrent_requests: Number of concurrent requests per user
        request_timeout: Timeout for individual requests in seconds
        think_time: Time between requests in seconds
        
    Returns:
        Dict containing load test results
    """
    try:
        engine = get_performance_engine()
        
        # Run load test
        result = await engine.run_load_test(
            target_users=target_users,
            ramp_up_duration=ramp_up_duration,
            test_duration=test_duration,
            ramp_down_duration=ramp_down_duration,
            concurrent_requests=concurrent_requests,
            request_timeout=request_timeout,
            think_time=think_time
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="load_testing",
            test_results={
                "test_id": result.test_id,
                "target_users": target_users,
                "test_duration": test_duration,
                "success_rate": result.summary.get("success_rate", 0.0),
                "avg_response_time": result.summary.get("avg_response_time", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == PerformanceTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "slo_results": result.slo_results,
            "metrics_count": len(result.metrics),
            "git_workflow_result": result.git_workflow_result,
            "message": f"Load test {'completed successfully' if result.status == PerformanceTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run load test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run load test: {e}"
        }


async def bmad_performance_stress_test(
    start_users: int = 5,
    max_users: int = 50,
    increment_users: int = 5,
    increment_interval: int = 10,
    test_duration: int = 30,
    failure_threshold: float = 5.0,
    resource_threshold: float = 90.0
) -> Dict[str, Any]:
    """
    Run stress testing for system limits.
    
    Args:
        start_users: Initial number of users
        max_users: Maximum number of users to test
        increment_users: Number of users to increment each step
        increment_interval: Time between user increments in seconds
        test_duration: Duration of test at each user level in seconds
        failure_threshold: Failure rate threshold percentage
        resource_threshold: Resource usage threshold percentage
        
    Returns:
        Dict containing stress test results
    """
    try:
        engine = get_performance_engine()
        
        # Run stress test
        result = await engine.run_stress_test(
            start_users=start_users,
            max_users=max_users,
            increment_users=increment_users,
            increment_interval=increment_interval,
            test_duration=test_duration,
            failure_threshold=failure_threshold,
            resource_threshold=resource_threshold
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="stress_testing",
            test_results={
                "test_id": result.test_id,
                "max_users_tested": result.summary.get("max_users_tested", 0),
                "success_rate": result.summary.get("success_rate", 0.0),
                "avg_response_time": result.summary.get("avg_response_time", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == PerformanceTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "slo_results": result.slo_results,
            "metrics_count": len(result.metrics),
            "git_workflow_result": result.git_workflow_result,
            "message": f"Stress test {'completed successfully' if result.status == PerformanceTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run stress test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run stress test: {e}"
        }


async def bmad_performance_scalability_test(
    min_users: int = 5,
    max_users: int = 25,
    user_increment: int = 5,
    test_duration_per_level: int = 30,
    performance_degradation_threshold: float = 50.0,
    resource_scaling_threshold: float = 80.0
) -> Dict[str, Any]:
    """
    Run scalability testing for multi-user scenarios.
    
    Args:
        min_users: Minimum number of users to test
        max_users: Maximum number of users to test
        user_increment: Number of users to increment each level
        test_duration_per_level: Duration of test at each user level in seconds
        performance_degradation_threshold: Performance degradation threshold percentage
        resource_scaling_threshold: Resource scaling threshold percentage
        
    Returns:
        Dict containing scalability test results
    """
    try:
        engine = get_performance_engine()
        
        # Run scalability test
        result = await engine.run_scalability_test(
            min_users=min_users,
            max_users=max_users,
            user_increment=user_increment,
            test_duration_per_level=test_duration_per_level,
            performance_degradation_threshold=performance_degradation_threshold,
            resource_scaling_threshold=resource_scaling_threshold
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="scalability_testing",
            test_results={
                "test_id": result.test_id,
                "user_levels_tested": result.summary.get("user_levels_tested", 0),
                "max_users_tested": result.summary.get("max_users_tested", 0),
                "response_time_trend": result.summary.get("response_time_trend", {}),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == PerformanceTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "slo_results": result.slo_results,
            "metrics_count": len(result.metrics),
            "git_workflow_result": result.git_workflow_result,
            "message": f"Scalability test {'completed successfully' if result.status == PerformanceTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run scalability test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run scalability test: {e}"
        }


async def bmad_performance_metrics_collect(
    duration_seconds: int = 60,
    interval_seconds: float = 1.0
) -> Dict[str, Any]:
    """
    Collect performance metrics for specified duration.
    
    Args:
        duration_seconds: Duration to collect metrics in seconds
        interval_seconds: Interval between metric collections in seconds
        
    Returns:
        Dict containing collected metrics
    """
    try:
        engine = get_performance_engine()
        
        # Start metrics collection
        test_id = f"metrics_collection_{int(datetime.now().timestamp())}"
        await engine.load_test_engine.metrics_collector.start_collection(test_id, interval_seconds)
        
        # Wait for specified duration
        await asyncio.sleep(duration_seconds)
        
        # Stop collection and get metrics
        metrics = await engine.load_test_engine.metrics_collector.stop_collection()
        
        # Get summary
        summary = engine.load_test_engine.metrics_collector.get_metric_summary(test_id)
        
        return {
            "success": True,
            "test_id": test_id,
            "duration_seconds": duration_seconds,
            "interval_seconds": interval_seconds,
            "metrics_collected": len(metrics),
            "summary": summary,
            "message": f"Collected {len(metrics)} performance metrics over {duration_seconds} seconds"
        }
        
    except Exception as e:
        logger.error(f"Failed to collect performance metrics: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to collect performance metrics: {e}"
        }


async def bmad_performance_slo_validate(
    test_id: Optional[str] = None,
    custom_thresholds: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate performance against Service Level Objectives.
    
    Args:
        test_id: Specific test ID to validate (optional)
        custom_thresholds: Custom SLO thresholds (optional)
        
    Returns:
        Dict containing SLO validation results
    """
    try:
        engine = get_performance_engine()
        
        # Get test history
        history = engine.get_test_history(test_type=None, limit=1)
        
        if not history:
            return {
                "success": False,
                "error": "No performance tests found",
                "message": "No performance tests found for SLO validation"
            }
        
        # Use specified test or most recent
        test_result = None
        if test_id:
            test_result = next((r for r in history if r.test_id == test_id), None)
            if not test_result:
                return {
                    "success": False,
                    "error": "Test not found",
                    "message": f"Test {test_id} not found"
                }
        else:
            test_result = history[0]
        
        # Validate SLOs
        slo_results = test_result.slo_results
        
        # Calculate overall SLO status
        passed_slos = len([r for r in slo_results if r.get("passed", False)])
        total_slos = len(slo_results)
        slo_pass_rate = (passed_slos / total_slos) * 100 if total_slos > 0 else 0
        
        # Determine overall status
        critical_failures = len([r for r in slo_results if r.get("severity") == "critical" and not r.get("passed", False)])
        overall_status = "PASSED" if critical_failures == 0 else "FAILED"
        
        return {
            "success": True,
            "test_id": test_result.test_id,
            "test_type": test_result.test_type.value,
            "overall_status": overall_status,
            "slo_pass_rate": slo_pass_rate,
            "passed_slos": passed_slos,
            "total_slos": total_slos,
            "critical_failures": critical_failures,
            "slo_results": slo_results,
            "message": f"SLO validation {'passed' if overall_status == 'PASSED' else 'failed'} with {slo_pass_rate:.1f}% pass rate"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate SLOs: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to validate SLOs: {e}"
        }


async def bmad_performance_report_generate(
    test_type: Optional[str] = None,
    days_back: int = 7,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Generate comprehensive performance testing report.
    
    Args:
        test_type: Filter by test type (load, stress, scalability)
        days_back: Number of days to include in report
        format: Report format (json, markdown)
        
    Returns:
        Dict containing performance report
    """
    try:
        engine = get_performance_engine()
        
        # Get test history
        history = engine.get_test_history(test_type=None, limit=100)
        
        # Filter by test type if specified
        if test_type:
            test_type_enum = PerformanceTestType(test_type)
            history = [r for r in history if r.test_type == test_type_enum]
        
        # Filter by date if needed
        if days_back > 0:
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
            history = [r for r in history if r.start_time.timestamp() >= cutoff_date]
        
        # Generate report
        report = {
            "report_generated_at": datetime.now().isoformat(),
            "report_period_days": days_back,
            "filters": {
                "test_type": test_type,
                "days_back": days_back
            },
            "statistics": engine.get_statistics(),
            "test_summary": {
                "total_tests": len(history),
                "load_tests": len([r for r in history if r.test_type == PerformanceTestType.LOAD]),
                "stress_tests": len([r for r in history if r.test_type == PerformanceTestType.STRESS]),
                "scalability_tests": len([r for r in history if r.test_type == PerformanceTestType.SCALABILITY]),
                "successful_tests": len([r for r in history if r.status == PerformanceTestStatus.COMPLETED]),
                "failed_tests": len([r for r in history if r.status == PerformanceTestStatus.FAILED])
            },
            "recent_tests": [
                {
                    "test_id": r.test_id,
                    "test_type": r.test_type.value,
                    "status": r.status.value,
                    "start_time": r.start_time.isoformat(),
                    "duration_seconds": r.duration_seconds,
                    "summary": r.summary
                }
                for r in history[:10]  # Last 10 tests
            ],
            "recommendations": []
        }
        
        # Add recommendations based on statistics
        stats = engine.get_statistics()
        if stats["success_rate"] < 80.0:
            report["recommendations"].append("Success rate is below 80% - review failing tests")
        
        if stats["avg_duration"] > 300.0:
            report["recommendations"].append("Average test duration is high - optimize test efficiency")
        
        if len(history) == 0:
            report["recommendations"].append("No recent tests found - run performance tests regularly")
        
        if format == "markdown":
            # Generate markdown report
            markdown_content = f"""# Performance Testing Report

**Generated**: {report["report_generated_at"]}  
**Period**: {days_back} days  
**Test Type Filter**: {test_type or "All"}

## Summary

- **Total Tests**: {report["test_summary"]["total_tests"]}
- **Load Tests**: {report["test_summary"]["load_tests"]}
- **Stress Tests**: {report["test_summary"]["stress_tests"]}
- **Scalability Tests**: {report["test_summary"]["scalability_tests"]}
- **Success Rate**: {(report["test_summary"]["successful_tests"] / report["test_summary"]["total_tests"]) * 100 if report["test_summary"]["total_tests"] > 0 else 0:.1f}%

## Recent Tests

"""
            
            for test in report["recent_tests"]:
                markdown_content += f"""### {test["test_type"].title()} Test - {test["test_id"]}

- **Status**: {test["status"]}
- **Duration**: {test["duration_seconds"]:.1f} seconds
- **Started**: {test["start_time"]}

"""
            
            return {
                "success": True,
                "report_format": "markdown",
                "report_content": markdown_content,
                "message": "Markdown performance report generated"
            }
        else:
            return {
                "success": True,
                "report_format": "json",
                "report_data": report,
                "message": "JSON performance report generated"
            }
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate performance report: {e}"
        }


async def bmad_performance_history_get(
    test_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get performance testing execution history.
    
    Args:
        test_type: Filter by test type (load, stress, scalability)
        limit: Maximum number of tests to return
        
    Returns:
        Dict containing execution history
    """
    try:
        engine = get_performance_engine()
        
        # Get test history
        test_type_enum = None
        if test_type:
            test_type_enum = PerformanceTestType(test_type)
        
        history = engine.get_test_history(test_type=test_type_enum, limit=limit)
        
        # Convert to serializable format
        history_list = []
        for test in history:
            history_list.append({
                "test_id": test.test_id,
                "test_type": test.test_type.value,
                "status": test.status.value,
                "start_time": test.start_time.isoformat(),
                "end_time": test.end_time.isoformat() if test.end_time else None,
                "duration_seconds": test.duration_seconds,
                "summary": test.summary,
                "metrics_count": len(test.metrics),
                "slo_results_count": len(test.slo_results)
            })
        
        return {
            "success": True,
            "execution_history": history_list,
            "total_count": len(history_list),
            "test_type": test_type,
            "limit": limit,
            "message": f"Retrieved {len(history_list)} performance test executions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get performance history: {e}"
        }
