"""
MCP Handlers for Integration Testing

This module provides MCP tool handlers for integration testing functionality
including cross-component testing, API integration testing, and database integration testing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.integration_testing_engine import (
    IntegrationTestingEngine,
    IntegrationTestType,
    IntegrationTestStatus,
    get_integration_engine
)
from ..core.git_workflow_manager import get_git_workflow_manager

logger = logging.getLogger(__name__)


async def bmad_integration_cross_component_test(
    components: Optional[List[str]] = None,
    timeout_seconds: float = 30.0,
    retry_attempts: int = 3,
    parallel_execution: bool = True
) -> Dict[str, Any]:
    """
    Run cross-component integration testing.
    
    Args:
        components: List of components to test (optional, defaults to all)
        timeout_seconds: Timeout for individual component tests
        retry_attempts: Number of retry attempts for failed tests
        parallel_execution: Whether to run tests in parallel
        
    Returns:
        Dict containing cross-component integration test results
    """
    try:
        engine = get_integration_engine()
        
        # Run cross-component integration test
        result = await engine.run_cross_component_integration_test(
            components=components,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            parallel_execution=parallel_execution
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="cross_component_integration",
            test_results={
                "test_id": result.test_id,
                "components_tested": len(result.component_tests),
                "success_rate": result.summary.get("success_rate", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == IntegrationTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "component_tests": result.component_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Cross-component integration test {'completed successfully' if result.status == IntegrationTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run cross-component integration test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run cross-component integration test: {e}"
        }


async def bmad_integration_api_test(
    base_url: str = "http://localhost:8000",
    endpoints: Optional[List[str]] = None,
    timeout_seconds: float = 10.0,
    retry_attempts: int = 3,
    validate_response_schema: bool = True
) -> Dict[str, Any]:
    """
    Run API integration testing for all endpoints.
    
    Args:
        base_url: Base URL for API testing
        endpoints: List of endpoints to test (optional, defaults to common endpoints)
        timeout_seconds: Timeout for individual API requests
        retry_attempts: Number of retry attempts for failed requests
        validate_response_schema: Whether to validate response schemas
        
    Returns:
        Dict containing API integration test results
    """
    try:
        engine = get_integration_engine()
        
        # Run API integration test
        result = await engine.run_api_integration_test(
            base_url=base_url,
            endpoints=endpoints,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            validate_response_schema=validate_response_schema
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="api_integration",
            test_results={
                "test_id": result.test_id,
                "endpoints_tested": len(result.api_tests),
                "success_rate": result.summary.get("success_rate", 0.0),
                "avg_response_time_ms": result.summary.get("avg_response_time_ms", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == IntegrationTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "api_tests": result.api_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"API integration test {'completed successfully' if result.status == IntegrationTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run API integration test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run API integration test: {e}"
        }


async def bmad_integration_database_test(
    connection_string: str = "postgresql://localhost:5432/cflow_platform",
    test_operations: Optional[List[str]] = None,
    timeout_seconds: float = 15.0,
    retry_attempts: int = 3,
    validate_data_consistency: bool = True
) -> Dict[str, Any]:
    """
    Run database integration testing for all operations.
    
    Args:
        connection_string: Database connection string
        test_operations: List of operations to test (optional, defaults to common operations)
        timeout_seconds: Timeout for individual database operations
        retry_attempts: Number of retry attempts for failed operations
        validate_data_consistency: Whether to validate data consistency
        
    Returns:
        Dict containing database integration test results
    """
    try:
        engine = get_integration_engine()
        
        # Run database integration test
        result = await engine.run_database_integration_test(
            connection_string=connection_string,
            test_operations=test_operations,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            validate_data_consistency=validate_data_consistency
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="database_integration",
            test_results={
                "test_id": result.test_id,
                "operations_tested": len(result.database_tests),
                "success_rate": result.summary.get("success_rate", 0.0),
                "avg_duration_seconds": result.summary.get("avg_duration_seconds", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == IntegrationTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "database_tests": result.database_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Database integration test {'completed successfully' if result.status == IntegrationTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run database integration test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run database integration test: {e}"
        }


async def bmad_integration_full_suite(
    include_components: Optional[List[str]] = None,
    include_apis: bool = True,
    include_database: bool = True,
    api_base_url: str = "http://localhost:8000",
    database_connection_string: str = "postgresql://localhost:5432/cflow_platform"
) -> Dict[str, Any]:
    """
    Run complete integration test suite.
    
    Args:
        include_components: List of components to include in cross-component tests
        include_apis: Whether to include API integration tests
        include_database: Whether to include database integration tests
        api_base_url: Base URL for API testing
        database_connection_string: Database connection string
        
    Returns:
        Dict containing full integration test suite results
    """
    try:
        engine = get_integration_engine()
        
        # Run full integration test suite
        result = await engine.run_full_integration_suite(
            include_components=include_components,
            include_apis=include_apis,
            include_database=include_database,
            api_base_url=api_base_url,
            database_connection_string=database_connection_string
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="full_integration_suite",
            test_results={
                "test_id": result.test_id,
                "test_suites_run": result.summary.get("total_test_suites", 0),
                "success_rate": result.summary.get("success_rate", 0.0),
                "total_duration_seconds": result.summary.get("total_duration_seconds", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == IntegrationTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "component_tests": result.component_tests,
            "api_tests": result.api_tests,
            "database_tests": result.database_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Full integration test suite {'completed successfully' if result.status == IntegrationTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run full integration test suite: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run full integration test suite: {e}"
        }


async def bmad_integration_report_generate(
    test_type: Optional[str] = None,
    days_back: int = 7,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Generate comprehensive integration testing report.
    
    Args:
        test_type: Filter by test type (cross_component, api_integration, database_integration, full_suite)
        days_back: Number of days to include in report
        format: Report format (json, markdown)
        
    Returns:
        Dict containing integration testing report
    """
    try:
        engine = get_integration_engine()
        
        # Get test history
        history = engine.get_test_history(test_type=None, limit=100)
        
        # Filter by test type if specified
        if test_type:
            test_type_enum = IntegrationTestType(test_type)
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
                "cross_component_tests": len([r for r in history if r.test_type == IntegrationTestType.CROSS_COMPONENT]),
                "api_integration_tests": len([r for r in history if r.test_type == IntegrationTestType.API_INTEGRATION]),
                "database_integration_tests": len([r for r in history if r.test_type == IntegrationTestType.DATABASE_INTEGRATION]),
                "full_suite_tests": len([r for r in history if r.test_type == IntegrationTestType.FULL_SUITE]),
                "successful_tests": len([r for r in history if r.status == IntegrationTestStatus.COMPLETED]),
                "failed_tests": len([r for r in history if r.status == IntegrationTestStatus.FAILED])
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
            report["recommendations"].append("Success rate is below 80% - review failing integration tests")
        
        if stats["avg_duration"] > 300.0:
            report["recommendations"].append("Average test duration is high - optimize integration test efficiency")
        
        if len(history) == 0:
            report["recommendations"].append("No recent tests found - run integration tests regularly")
        
        if format == "markdown":
            # Generate markdown report
            markdown_content = f"""# Integration Testing Report

**Generated**: {report["report_generated_at"]}  
**Period**: {days_back} days  
**Test Type Filter**: {test_type or "All"}

## Summary

- **Total Tests**: {report["test_summary"]["total_tests"]}
- **Cross-Component Tests**: {report["test_summary"]["cross_component_tests"]}
- **API Integration Tests**: {report["test_summary"]["api_integration_tests"]}
- **Database Integration Tests**: {report["test_summary"]["database_integration_tests"]}
- **Full Suite Tests**: {report["test_summary"]["full_suite_tests"]}
- **Success Rate**: {(report["test_summary"]["successful_tests"] / report["test_summary"]["total_tests"]) * 100 if report["test_summary"]["total_tests"] > 0 else 0:.1f}%

## Recent Tests

"""
            
            for test in report["recent_tests"]:
                markdown_content += f"""### {test["test_type"].replace("_", " ").title()} Test - {test["test_id"]}

- **Status**: {test["status"]}
- **Duration**: {test["duration_seconds"]:.1f} seconds
- **Started**: {test["start_time"]}

"""
            
            return {
                "success": True,
                "report_format": "markdown",
                "report_content": markdown_content,
                "message": "Markdown integration testing report generated"
            }
        else:
            return {
                "success": True,
                "report_format": "json",
                "report_data": report,
                "message": "JSON integration testing report generated"
            }
        
    except Exception as e:
        logger.error(f"Failed to generate integration testing report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate integration testing report: {e}"
        }


async def bmad_integration_history_get(
    test_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get integration testing execution history.
    
    Args:
        test_type: Filter by test type (cross_component, api_integration, database_integration, full_suite)
        limit: Maximum number of tests to return
        
    Returns:
        Dict containing execution history
    """
    try:
        engine = get_integration_engine()
        
        # Get test history
        test_type_enum = None
        if test_type:
            test_type_enum = IntegrationTestType(test_type)
        
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
                "component_tests_count": len(test.component_tests),
                "api_tests_count": len(test.api_tests),
                "database_tests_count": len(test.database_tests)
            })
        
        return {
            "success": True,
            "execution_history": history_list,
            "total_count": len(history_list),
            "test_type": test_type,
            "limit": limit,
            "message": f"Retrieved {len(history_list)} integration test executions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration testing history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get integration testing history: {e}"
        }
