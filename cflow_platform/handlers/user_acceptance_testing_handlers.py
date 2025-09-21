"""
MCP Handlers for User Acceptance Testing

This module provides MCP tool handlers for user acceptance testing functionality
including user scenario testing, usability testing, and accessibility testing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.user_acceptance_testing_engine import (
    UserAcceptanceTestingEngine,
    UATTestType,
    UATTestStatus,
    get_uat_engine
)
from ..core.git_workflow_manager import get_git_workflow_manager

logger = logging.getLogger(__name__)


async def bmad_uat_scenario_test(
    scenario_name: str,
    user_role: str = "developer",
    timeout_seconds: float = 60.0
) -> Dict[str, Any]:
    """
    Run user acceptance scenario testing for real-world scenarios.
    
    Args:
        scenario_name: Name of the scenario to test
        user_role: User role for the test (developer, product_manager, architect, qa_engineer, end_user, administrator)
        timeout_seconds: Timeout for the scenario test
        
    Returns:
        Dict containing user scenario test results
    """
    try:
        engine = get_uat_engine()
        
        # Run user scenario test
        result = await engine.run_user_scenario_test(
            scenario_name=scenario_name,
            user_role=user_role,
            timeout_seconds=timeout_seconds
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="user_scenario_testing",
            test_results={
                "test_id": result.test_id,
                "scenario_name": scenario_name,
                "user_role": user_role,
                "success_rate": result.summary.get("success_rate", 0.0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == UATTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "scenario_tests": result.scenario_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"User scenario test {'completed successfully' if result.status == UATTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run user scenario test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run user scenario test: {e}"
        }


async def bmad_uat_usability_test(
    interface_component: str,
    user_role: str = "end_user",
    timeout_seconds: float = 30.0
) -> Dict[str, Any]:
    """
    Run usability testing for user interfaces.
    
    Args:
        interface_component: Interface component to test
        user_role: User role for the test
        timeout_seconds: Timeout for the usability test
        
    Returns:
        Dict containing usability test results
    """
    try:
        engine = get_uat_engine()
        
        # Run usability test
        result = await engine.run_usability_test(
            interface_component=interface_component,
            user_role=user_role,
            timeout_seconds=timeout_seconds
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="usability_testing",
            test_results={
                "test_id": result.test_id,
                "interface_component": interface_component,
                "user_role": user_role,
                "overall_score": result.summary.get("overall_score", 0.0),
                "usability_grade": result.summary.get("usability_grade", "Unknown"),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == UATTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "usability_tests": result.usability_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Usability test {'completed successfully' if result.status == UATTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run usability test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run usability test: {e}"
        }


async def bmad_uat_accessibility_test(
    interface_component: str,
    wcag_level: str = "AA",
    timeout_seconds: float = 30.0
) -> Dict[str, Any]:
    """
    Run accessibility testing for compliance.
    
    Args:
        interface_component: Interface component to test
        wcag_level: WCAG compliance level (AA or AAA)
        timeout_seconds: Timeout for the accessibility test
        
    Returns:
        Dict containing accessibility test results
    """
    try:
        engine = get_uat_engine()
        
        # Run accessibility test
        result = await engine.run_accessibility_test(
            interface_component=interface_component,
            wcag_level=wcag_level,
            timeout_seconds=timeout_seconds
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="accessibility_testing",
            test_results={
                "test_id": result.test_id,
                "interface_component": interface_component,
                "wcag_level": wcag_level,
                "overall_score": result.summary.get("overall_score", 0.0),
                "accessibility_grade": result.summary.get("accessibility_grade", "Unknown"),
                "compliance_status": result.summary.get("compliance_status", "Unknown"),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == UATTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "accessibility_tests": result.accessibility_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Accessibility test {'completed successfully' if result.status == UATTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run accessibility test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run accessibility test: {e}"
        }


async def bmad_uat_full_suite(
    scenarios: Optional[List[str]] = None,
    interface_components: Optional[List[str]] = None,
    include_usability: bool = True,
    include_accessibility: bool = True,
    wcag_level: str = "AA"
) -> Dict[str, Any]:
    """
    Run complete user acceptance test suite.
    
    Args:
        scenarios: List of scenarios to test (optional, defaults to common scenarios)
        interface_components: List of interface components to test (optional, defaults to common components)
        include_usability: Whether to include usability tests
        include_accessibility: Whether to include accessibility tests
        wcag_level: WCAG compliance level for accessibility tests
        
    Returns:
        Dict containing full UAT suite results
    """
    try:
        engine = get_uat_engine()
        
        # Run full UAT suite
        result = await engine.run_full_uat_suite(
            scenarios=scenarios,
            interface_components=interface_components,
            include_usability=include_usability,
            include_accessibility=include_accessibility,
            wcag_level=wcag_level
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="full_uat_suite",
            test_results={
                "test_id": result.test_id,
                "total_tests": result.summary.get("total_tests", 0),
                "success_rate": result.summary.get("success_rate", 0.0),
                "scenario_tests": result.summary.get("scenario_tests", 0),
                "usability_tests": result.summary.get("usability_tests", 0),
                "accessibility_tests": result.summary.get("accessibility_tests", 0),
                "status": result.status.value
            }
        )
        
        result.git_workflow_result = git_result
        
        return {
            "success": result.status == UATTestStatus.COMPLETED,
            "test_id": result.test_id,
            "test_type": result.test_type.value,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary,
            "scenario_tests": result.scenario_tests,
            "usability_tests": result.usability_tests,
            "accessibility_tests": result.accessibility_tests,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Full UAT suite {'completed successfully' if result.status == UATTestStatus.COMPLETED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run full UAT suite: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run full UAT suite: {e}"
        }


async def bmad_uat_report_generate(
    test_type: Optional[str] = None,
    days_back: int = 7,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Generate comprehensive user acceptance testing report.
    
    Args:
        test_type: Filter by test type (user_scenario, usability, accessibility, full_suite)
        days_back: Number of days to include in report
        format: Report format (json, markdown)
        
    Returns:
        Dict containing user acceptance testing report
    """
    try:
        engine = get_uat_engine()
        
        # Get test history
        history = engine.get_test_history(test_type=None, limit=100)
        
        # Filter by test type if specified
        if test_type:
            test_type_enum = UATTestType(test_type)
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
                "scenario_tests": len([r for r in history if r.test_type == UATTestType.USER_SCENARIO]),
                "usability_tests": len([r for r in history if r.test_type == UATTestType.USABILITY]),
                "accessibility_tests": len([r for r in history if r.test_type == UATTestType.ACCESSIBILITY]),
                "full_suite_tests": len([r for r in history if r.test_type == UATTestType.FULL_SUITE]),
                "successful_tests": len([r for r in history if r.status == UATTestStatus.COMPLETED]),
                "failed_tests": len([r for r in history if r.status == UATTestStatus.FAILED])
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
            report["recommendations"].append("Success rate is below 80% - review failing UAT tests")
        
        if stats["avg_duration"] > 300.0:
            report["recommendations"].append("Average test duration is high - optimize UAT test efficiency")
        
        if len(history) == 0:
            report["recommendations"].append("No recent tests found - run UAT tests regularly")
        
        if format == "markdown":
            # Generate markdown report
            markdown_content = f"""# User Acceptance Testing Report

**Generated**: {report["report_generated_at"]}  
**Period**: {days_back} days  
**Test Type Filter**: {test_type or "All"}

## Summary

- **Total Tests**: {report["test_summary"]["total_tests"]}
- **Scenario Tests**: {report["test_summary"]["scenario_tests"]}
- **Usability Tests**: {report["test_summary"]["usability_tests"]}
- **Accessibility Tests**: {report["test_summary"]["accessibility_tests"]}
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
                "message": "Markdown user acceptance testing report generated"
            }
        else:
            return {
                "success": True,
                "report_format": "json",
                "report_data": report,
                "message": "JSON user acceptance testing report generated"
            }
        
    except Exception as e:
        logger.error(f"Failed to generate user acceptance testing report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate user acceptance testing report: {e}"
        }


async def bmad_uat_history_get(
    test_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get user acceptance testing execution history.
    
    Args:
        test_type: Filter by test type (user_scenario, usability, accessibility, full_suite)
        limit: Maximum number of tests to return
        
    Returns:
        Dict containing execution history
    """
    try:
        engine = get_uat_engine()
        
        # Get test history
        test_type_enum = None
        if test_type:
            test_type_enum = UATTestType(test_type)
        
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
                "scenario_tests_count": len(test.scenario_tests),
                "usability_tests_count": len(test.usability_tests),
                "accessibility_tests_count": len(test.accessibility_tests)
            })
        
        return {
            "success": True,
            "execution_history": history_list,
            "total_count": len(history_list),
            "test_type": test_type,
            "limit": limit,
            "message": f"Retrieved {len(history_list)} user acceptance test executions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get user acceptance testing history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get user acceptance testing history: {e}"
        }
