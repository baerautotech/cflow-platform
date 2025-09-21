"""
MCP Handlers for Scenario-based Testing

This module provides MCP tool handlers for scenario-based testing functionality,
including scenario creation, execution, validation, and reporting.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.scenario_testing_engine import (
    ScenarioTestingEngine,
    TestScenario,
    ScenarioPriority,
    ScenarioStatus,
    get_scenario_engine
)

logger = logging.getLogger(__name__)


async def bmad_scenario_create(
    name: str,
    description: str,
    priority: str,
    category: str,
    steps: List[Dict[str, Any]],
    prerequisites: Optional[List[str]] = None,
    cleanup_steps: Optional[List[Dict[str, Any]]] = None,
    expected_duration_seconds: float = 60.0,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new test scenario for scenario-based testing.
    
    Args:
        name: Scenario name
        description: Scenario description
        priority: Priority level (P0, P1, P2, P3)
        category: Scenario category (e.g., "user_registration", "payment_flow")
        steps: List of scenario steps
        prerequisites: List of prerequisite scenarios
        cleanup_steps: List of cleanup steps
        expected_duration_seconds: Expected execution duration
        tags: List of tags for categorization
        metadata: Additional metadata
        
    Returns:
        Dict containing scenario creation result
    """
    try:
        engine = get_scenario_engine()
        
        # Convert priority string to enum
        priority_enum = ScenarioPriority(priority)
        
        # Create scenario
        scenario = engine.create_scenario(
            name=name,
            description=description,
            priority=priority_enum,
            category=category,
            steps=steps,
            prerequisites=prerequisites or [],
            cleanup_steps=cleanup_steps or [],
            expected_duration_seconds=expected_duration_seconds,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "description": scenario.description,
            "priority": scenario.priority.value,
            "category": scenario.category,
            "steps_count": len(scenario.steps),
            "cleanup_steps_count": len(scenario.cleanup_steps),
            "expected_duration_seconds": scenario.expected_duration_seconds,
            "tags": scenario.tags,
            "message": f"Scenario '{scenario.name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create scenario: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create scenario: {e}"
        }


async def bmad_scenario_execute(
    scenario_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a test scenario.
    
    Args:
        scenario_id: ID of the scenario to execute
        context: Execution context data
        
    Returns:
        Dict containing execution result
    """
    try:
        engine = get_scenario_engine()
        
        # Execute scenario
        result = await engine.execute_scenario(scenario_id, context or {})
        
        return {
            "success": result.status == ScenarioStatus.PASSED,
            "execution_id": result.execution_id,
            "scenario_id": result.scenario_id,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "overall_score": result.overall_score,
            "error_summary": result.error_summary,
            "step_results": result.step_results,
            "message": f"Scenario execution {'completed successfully' if result.status == ScenarioStatus.PASSED else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to execute scenario: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to execute scenario: {e}"
        }


async def bmad_scenario_list(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    List available test scenarios with optional filtering.
    
    Args:
        category: Filter by category
        priority: Filter by priority (P0, P1, P2, P3)
        tags: Filter by tags
        
    Returns:
        Dict containing list of scenarios
    """
    try:
        engine = get_scenario_engine()
        
        # Convert priority string to enum if provided
        priority_enum = None
        if priority:
            priority_enum = ScenarioPriority(priority)
        
        # List scenarios
        scenarios = engine.list_scenarios(
            category=category,
            priority=priority_enum,
            tags=tags
        )
        
        # Convert scenarios to serializable format
        scenario_list = []
        for scenario in scenarios:
            scenario_list.append({
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "priority": scenario.priority.value,
                "category": scenario.category,
                "steps_count": len(scenario.steps),
                "cleanup_steps_count": len(scenario.cleanup_steps),
                "expected_duration_seconds": scenario.expected_duration_seconds,
                "tags": scenario.tags,
                "prerequisites": scenario.prerequisites,
                "metadata": scenario.metadata
            })
        
        return {
            "success": True,
            "scenarios": scenario_list,
            "total_count": len(scenario_list),
            "filters": {
                "category": category,
                "priority": priority,
                "tags": tags
            },
            "message": f"Found {len(scenario_list)} scenarios"
        }
        
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list scenarios: {e}"
        }


async def bmad_scenario_validate(
    scenario_id: str,
    execution_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate scenario execution results.
    
    Args:
        scenario_id: ID of the scenario to validate
        execution_id: Specific execution ID to validate (optional)
        
    Returns:
        Dict containing validation result
    """
    try:
        engine = get_scenario_engine()
        
        # Get execution history
        history = engine.get_execution_history(scenario_id=scenario_id)
        
        if not history:
            return {
                "success": False,
                "error": "No executions found for scenario",
                "message": f"No executions found for scenario {scenario_id}"
            }
        
        # If specific execution ID provided, filter to that execution
        if execution_id:
            history = [r for r in history if r.execution_id == execution_id]
            if not history:
                return {
                    "success": False,
                    "error": "Execution not found",
                    "message": f"Execution {execution_id} not found for scenario {scenario_id}"
                }
        
        # Get the most recent execution
        latest_execution = history[0]
        
        # Validate the execution
        validation_result = {
            "scenario_id": scenario_id,
            "execution_id": latest_execution.execution_id,
            "status": latest_execution.status.value,
            "overall_score": latest_execution.overall_score,
            "duration_seconds": latest_execution.duration_seconds,
            "step_validation": [],
            "issues": [],
            "recommendations": []
        }
        
        # Validate each step
        for step_result in latest_execution.step_results:
            step_validation = {
                "step_id": step_result.get("step_id"),
                "name": step_result.get("name"),
                "status": step_result.get("status"),
                "score": step_result.get("score", 0.0),
                "validation_results": step_result.get("validation_results", {})
            }
            validation_result["step_validation"].append(step_validation)
            
            # Collect issues and recommendations
            validation_data = step_result.get("validation_results", {})
            if validation_data.get("issues"):
                validation_result["issues"].extend(validation_data["issues"])
            if validation_data.get("recommendations"):
                validation_result["recommendations"].extend(validation_data["recommendations"])
        
        # Overall validation
        validation_result["valid"] = latest_execution.status == ScenarioStatus.PASSED
        validation_result["success"] = validation_result["valid"]
        
        return {
            "success": True,
            "validation_result": validation_result,
            "message": f"Scenario validation {'passed' if validation_result['valid'] else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate scenario: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to validate scenario: {e}"
        }


async def bmad_scenario_report(
    scenario_id: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Generate scenario testing report.
    
    Args:
        scenario_id: Specific scenario ID (optional)
        category: Filter by category (optional)
        priority: Filter by priority (optional)
        days_back: Number of days to include in report
        
    Returns:
        Dict containing scenario testing report
    """
    try:
        engine = get_scenario_engine()
        
        # Get statistics
        stats = engine.get_statistics()
        
        # Get execution history
        history = engine.get_execution_history(scenario_id=scenario_id)
        
        # Filter by date if needed
        if days_back > 0:
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
            history = [r for r in history if r.start_time.timestamp() >= cutoff_date]
        
        # Generate report
        report = {
            "report_generated_at": datetime.now().isoformat(),
            "report_period_days": days_back,
            "filters": {
                "scenario_id": scenario_id,
                "category": category,
                "priority": priority
            },
            "statistics": stats,
            "execution_summary": {
                "total_executions": len(history),
                "successful_executions": len([r for r in history if r.status == ScenarioStatus.PASSED]),
                "failed_executions": len([r for r in history if r.status == ScenarioStatus.FAILED]),
                "error_executions": len([r for r in history if r.status == ScenarioStatus.ERROR]),
                "average_score": sum(r.overall_score for r in history) / len(history) if history else 0.0,
                "average_duration": sum(r.duration_seconds for r in history) / len(history) if history else 0.0
            },
            "recent_executions": [
                {
                    "execution_id": r.execution_id,
                    "scenario_id": r.scenario_id,
                    "status": r.status.value,
                    "start_time": r.start_time.isoformat(),
                    "duration_seconds": r.duration_seconds,
                    "overall_score": r.overall_score,
                    "error_summary": r.error_summary
                }
                for r in history[:10]  # Last 10 executions
            ],
            "scenarios_by_priority": stats.get("scenarios_by_priority", {}),
            "recommendations": []
        }
        
        # Add recommendations based on statistics
        if stats["success_rate"] < 80.0:
            report["recommendations"].append("Success rate is below 80% - review failing scenarios")
        
        if stats["average_score"] < 70.0:
            report["recommendations"].append("Average score is below 70% - improve scenario validation")
        
        if stats["average_duration"] > 120.0:
            report["recommendations"].append("Average duration is high - optimize scenario performance")
        
        return {
            "success": True,
            "report": report,
            "message": f"Scenario testing report generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate scenario report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate scenario report: {e}"
        }


async def bmad_scenario_get_history(
    scenario_id: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get scenario execution history.
    
    Args:
        scenario_id: Specific scenario ID (optional)
        limit: Maximum number of executions to return
        
    Returns:
        Dict containing execution history
    """
    try:
        engine = get_scenario_engine()
        
        # Get execution history
        history = engine.get_execution_history(scenario_id=scenario_id, limit=limit)
        
        # Convert to serializable format
        history_list = []
        for execution in history:
            history_list.append({
                "execution_id": execution.execution_id,
                "scenario_id": execution.scenario_id,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "duration_seconds": execution.duration_seconds,
                "overall_score": execution.overall_score,
                "error_summary": execution.error_summary,
                "step_count": len(execution.step_results)
            })
        
        return {
            "success": True,
            "execution_history": history_list,
            "total_count": len(history_list),
            "scenario_id": scenario_id,
            "limit": limit,
            "message": f"Retrieved {len(history_list)} execution records"
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get execution history: {e}"
        }
