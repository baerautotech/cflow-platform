"""
MCP Handlers for Regression Testing and Git Workflow Management

This module provides MCP tool handlers for regression testing functionality
and automated git workflow management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.regression_testing_engine import (
    RegressionTestingEngine,
    RegressionStatus,
    get_regression_engine
)
from ..core.git_workflow_manager import (
    GitWorkflowManager,
    GitWorkflowStatus,
    get_git_workflow_manager
)

logger = logging.getLogger(__name__)


# Regression Testing Handlers

async def bmad_regression_test_run(
    test_suite_id: Optional[str] = None,
    baseline_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run comprehensive regression tests.
    
    Args:
        test_suite_id: Specific test suite to run (optional)
        baseline_id: Specific baseline to compare against (optional)
        
    Returns:
        Dict containing regression test results
    """
    try:
        engine = get_regression_engine()
        
        # Run regression tests
        result = await engine.run_regression_tests(
            test_suite_id=test_suite_id,
            baseline_id=baseline_id
        )
        
        return {
            "success": result.status == RegressionStatus.PASSED,
            "execution_id": result.execution_id,
            "test_suite_id": result.test_suite_id,
            "baseline_id": result.baseline_id,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "regressions_found": result.regressions_found,
            "regressions": [
                {
                    "issue_id": r.issue_id,
                    "test_name": r.test_name,
                    "severity": r.severity,
                    "description": r.description,
                    "impact_assessment": r.impact_assessment,
                    "recommended_action": r.recommended_action
                }
                for r in result.regressions
            ],
            "comparison_result": result.comparison_result,
            "report": result.report,
            "git_workflow_result": result.git_workflow_result,
            "message": f"Regression tests {'passed' if result.status == RegressionStatus.PASSED else 'detected regressions'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to run regression tests: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to run regression tests: {e}"
        }


async def bmad_regression_baseline_establish(
    test_suite_id: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Establish a new baseline for regression testing.
    
    Args:
        test_suite_id: ID of the test suite
        description: Description of the baseline
        metadata: Additional metadata for the baseline
        
    Returns:
        Dict containing baseline establishment result
    """
    try:
        engine = get_regression_engine()
        
        # Establish baseline
        result = await engine.establish_baseline(
            test_suite_id=test_suite_id,
            description=description,
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "baseline_id": result.baseline_id,
            "test_suite_id": result.test_suite_id,
            "description": result.description,
            "test_count": result.test_count,
            "created_at": result.created_at.isoformat(),
            "git_workflow_result": result.git_workflow_result,
            "message": f"Baseline '{result.baseline_id}' established successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to establish baseline: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to establish baseline: {e}"
        }


async def bmad_regression_baseline_list(
    test_suite_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available baselines for regression testing.
    
    Args:
        test_suite_id: Filter by test suite ID (optional)
        status: Filter by status (optional)
        
    Returns:
        Dict containing list of baselines
    """
    try:
        engine = get_regression_engine()
        
        # List baselines
        baselines = engine.baseline_manager.list_baselines(
            test_suite_id=test_suite_id,
            status=status
        )
        
        # Convert to serializable format
        baseline_list = []
        for baseline in baselines:
            baseline_list.append({
                "baseline_id": baseline.baseline_id,
                "test_suite_id": baseline.test_suite_id,
                "description": baseline.description,
                "created_at": baseline.created_at.isoformat(),
                "status": baseline.status.value,
                "test_count": len(baseline.test_results.get("tests", [])),
                "metadata": baseline.metadata
            })
        
        return {
            "success": True,
            "baselines": baseline_list,
            "total_count": len(baseline_list),
            "filters": {
                "test_suite_id": test_suite_id,
                "status": status
            },
            "message": f"Found {len(baseline_list)} baselines"
        }
        
    except Exception as e:
        logger.error(f"Failed to list baselines: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list baselines: {e}"
        }


async def bmad_regression_report_generate(
    execution_id: Optional[str] = None,
    test_suite_id: Optional[str] = None,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Generate detailed regression reports.
    
    Args:
        execution_id: Specific execution ID (optional)
        test_suite_id: Filter by test suite ID (optional)
        format: Report format (json, markdown)
        
    Returns:
        Dict containing regression report
    """
    try:
        engine = get_regression_engine()
        
        # Get execution history
        history = engine.get_execution_history(test_suite_id=test_suite_id)
        
        if not history:
            return {
                "success": False,
                "error": "No regression test executions found",
                "message": "No regression test executions found"
            }
        
        # If specific execution ID provided, filter to that execution
        if execution_id:
            history = [r for r in history if r.execution_id == execution_id]
            if not history:
                return {
                    "success": False,
                    "error": "Execution not found",
                    "message": f"Execution {execution_id} not found"
                }
        
        # Get the most recent execution
        latest_execution = history[0]
        
        # Generate report
        report_data = latest_execution.report
        
        if format == "markdown":
            # Generate markdown report
            from ..core.regression_testing_engine import ReportTemplateEngine
            template_engine = ReportTemplateEngine()
            report_content = template_engine.generate_markdown_report(report_data)
            
            return {
                "success": True,
                "report_format": "markdown",
                "report_content": report_content,
                "execution_id": latest_execution.execution_id,
                "message": "Markdown regression report generated"
            }
        else:
            # Return JSON report
            return {
                "success": True,
                "report_format": "json",
                "report_data": report_data,
                "execution_id": latest_execution.execution_id,
                "message": "JSON regression report generated"
            }
        
    except Exception as e:
        logger.error(f"Failed to generate regression report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate regression report: {e}"
        }


async def bmad_regression_history_get(
    test_suite_id: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get regression testing execution history.
    
    Args:
        test_suite_id: Filter by test suite ID (optional)
        limit: Maximum number of executions to return
        
    Returns:
        Dict containing execution history
    """
    try:
        engine = get_regression_engine()
        
        # Get execution history
        history = engine.get_execution_history(test_suite_id=test_suite_id, limit=limit)
        
        # Convert to serializable format
        history_list = []
        for execution in history:
            history_list.append({
                "execution_id": execution.execution_id,
                "test_suite_id": execution.test_suite_id,
                "baseline_id": execution.baseline_id,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "duration_seconds": execution.duration_seconds,
                "regressions_found": execution.regressions_found,
                "regression_count": len(execution.regressions)
            })
        
        return {
            "success": True,
            "execution_history": history_list,
            "total_count": len(history_list),
            "test_suite_id": test_suite_id,
            "limit": limit,
            "message": f"Retrieved {len(history_list)} regression test executions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get regression history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get regression history: {e}"
        }


# Git Workflow Management Handlers

async def bmad_git_auto_commit(
    test_type: str,
    test_results: Dict[str, Any],
    include_untracked: bool = True,
    custom_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically commit changes after testing.
    
    Args:
        test_type: Type of test (workflow_testing, scenario_testing, etc.)
        test_results: Test results to include in commit message
        include_untracked: Whether to include untracked files
        custom_message: Custom commit message (optional)
        
    Returns:
        Dict containing commit result
    """
    try:
        git_manager = get_git_workflow_manager()
        
        # Commit changes
        result = await git_manager.commit_only(
            test_type=test_type,
            test_results=test_results,
            include_untracked=include_untracked,
            custom_message=custom_message
        )
        
        return {
            "success": result.status == GitWorkflowStatus.SUCCESS,
            "status": result.status.value,
            "commit_hash": result.commit_hash,
            "branch": result.branch,
            "message": result.message,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "git_result": {
                "commit_hash": result.commit_hash,
                "branch": result.branch,
                "message": result.message
            },
            "message": f"Git commit {'successful' if result.status == GitWorkflowStatus.SUCCESS else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-commit: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to auto-commit: {e}"
        }


async def bmad_git_auto_push(
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically push committed changes.
    
    Args:
        branch: Branch to push (optional, defaults to current)
        
    Returns:
        Dict containing push result
    """
    try:
        git_manager = get_git_workflow_manager()
        
        # Push changes
        result = await git_manager.push_only(branch=branch)
        
        return {
            "success": result.status == GitWorkflowStatus.SUCCESS,
            "status": result.status.value,
            "push_result": result.push_result,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "message": f"Git push {'successful' if result.status == GitWorkflowStatus.SUCCESS else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-push: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to auto-push: {e}"
        }


async def bmad_git_workflow_status() -> Dict[str, Any]:
    """
    Get status of automated git workflows.
    
    Returns:
        Dict containing git workflow status
    """
    try:
        git_manager = get_git_workflow_manager()
        
        # Get status
        status = git_manager.get_status()
        
        return {
            "success": True,
            "status": status,
            "message": "Git workflow status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get git workflow status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get git workflow status: {e}"
        }


async def bmad_git_workflow_configure(
    auto_push_enabled: Optional[bool] = None,
    commit_message_max_length: Optional[int] = None,
    push_retry_count: Optional[int] = None,
    push_retry_delay: Optional[float] = None,
    conflict_resolution_enabled: Optional[bool] = None,
    branch_protection_enabled: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Configure automated git workflow settings.
    
    Args:
        auto_push_enabled: Enable/disable auto-push
        commit_message_max_length: Maximum commit message length
        push_retry_count: Number of push retries
        push_retry_delay: Delay between push retries
        conflict_resolution_enabled: Enable/disable conflict resolution
        branch_protection_enabled: Enable/disable branch protection
        
    Returns:
        Dict containing configuration result
    """
    try:
        git_manager = get_git_workflow_manager()
        
        # Prepare configuration updates
        updates = {}
        
        if auto_push_enabled is not None:
            updates["auto_push_enabled"] = auto_push_enabled
        if commit_message_max_length is not None:
            updates["commit_message_max_length"] = commit_message_max_length
        if push_retry_count is not None:
            updates["push_retry_count"] = push_retry_count
        if push_retry_delay is not None:
            updates["push_retry_delay"] = push_retry_delay
        if conflict_resolution_enabled is not None:
            updates["conflict_resolution_enabled"] = conflict_resolution_enabled
        if branch_protection_enabled is not None:
            updates["branch_protection_enabled"] = branch_protection_enabled
        
        # Update configuration
        git_manager.config_manager.update_config(updates)
        
        # Get updated configuration
        current_config = git_manager.config_manager.get_config()
        
        return {
            "success": True,
            "configuration": current_config,
            "updates_applied": updates,
            "message": f"Git workflow configuration updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to configure git workflow: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to configure git workflow: {e}"
        }
