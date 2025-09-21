"""
BMAD Workflow Testing Handlers
Phase 4.1.1: Implement complete workflow testing

MCP handlers for workflow testing functionality.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..core.workflow_testing_engine import (
    workflow_testing_engine,
    WorkflowTestSuite,
    WorkflowTestStep,
    WorkflowPhase,
    TestStatus
)

logger = logging.getLogger(__name__)

async def bmad_workflow_test_run_complete(**kwargs) -> Dict[str, Any]:
    """
    Run a complete workflow test from PRD to deployment
    
    Args:
        None required - runs the default complete workflow test
    
    Returns:
        Dict containing test execution results
    """
    try:
        logger.info("Starting complete workflow test")
        
        # Run the complete workflow test
        execution = await workflow_testing_engine.run_complete_workflow_test()
        
        # Format results
        result = {
            "success": True,
            "execution_id": execution.execution_id,
            "suite_id": execution.suite_id,
            "status": execution.status.value,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "duration_seconds": execution.duration_seconds,
            "overall_score": execution.overall_score,
            "error_summary": execution.error_summary,
            "step_results": []
        }
        
        # Add step results
        for step_result in execution.step_results:
            step_data = {
                "step_id": step_result.step_id,
                "status": step_result.status.value,
                "start_time": step_result.start_time.isoformat(),
                "end_time": step_result.end_time.isoformat() if step_result.end_time else None,
                "duration_seconds": step_result.duration_seconds,
                "error_message": step_result.error_message,
                "validation_results": step_result.validation_results
            }
            result["step_results"].append(step_data)
        
        logger.info(f"Complete workflow test completed with status: {execution.status}")
        return result
        
    except Exception as e:
        logger.error(f"Error running complete workflow test: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_id": None,
            "status": "ERROR"
        }

async def bmad_workflow_test_create_suite(**kwargs) -> Dict[str, Any]:
    """
    Create a custom workflow test suite
    
    Args:
        name: Name of the test suite
        description: Description of the test suite
        phases: List of workflow phases to include
        custom_steps: Custom test steps (optional)
    
    Returns:
        Dict containing suite creation results
    """
    try:
        name = kwargs.get("name", "Custom Workflow Test Suite")
        description = kwargs.get("description", "Custom workflow test suite")
        phases_data = kwargs.get("phases", [])
        custom_steps_data = kwargs.get("custom_steps", [])
        
        # Convert phases data to WorkflowPhase enums
        phases = []
        for phase_name in phases_data:
            try:
                phase = WorkflowPhase(phase_name.upper())
                phases.append(phase)
            except ValueError:
                logger.warning(f"Invalid workflow phase: {phase_name}")
        
        # Convert custom steps data to WorkflowTestStep objects
        custom_steps = []
        for step_data in custom_steps_data:
            try:
                step = WorkflowTestStep(
                    step_id=step_data.get("step_id", f"step_{len(custom_steps)}"),
                    step_name=step_data.get("step_name", "Custom Step"),
                    phase=WorkflowPhase(step_data.get("phase", "PRD_CREATION").upper()),
                    description=step_data.get("description", "Custom test step"),
                    expected_output=step_data.get("expected_output", {}),
                    validation_criteria=step_data.get("validation_criteria", {}),
                    dependencies=step_data.get("dependencies", []),
                    timeout_seconds=step_data.get("timeout_seconds", 300),
                    retry_count=step_data.get("retry_count", 3),
                    critical=step_data.get("critical", True)
                )
                custom_steps.append(step)
            except Exception as e:
                logger.warning(f"Invalid custom step data: {e}")
        
        # Create the custom suite
        suite = workflow_testing_engine.suite_builder.create_custom_suite(
            name=name,
            description=description,
            phases=phases,
            custom_steps=custom_steps
        )
        
        result = {
            "success": True,
            "suite_id": suite.suite_id,
            "suite_name": suite.suite_name,
            "description": suite.description,
            "phases": [phase.value for phase in suite.workflow_phases],
            "test_steps": [
                {
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "phase": step.phase.value,
                    "description": step.description,
                    "dependencies": step.dependencies,
                    "timeout_seconds": step.timeout_seconds,
                    "critical": step.critical
                }
                for step in suite.test_steps
            ],
            "created_at": suite.created_at.isoformat()
        }
        
        logger.info(f"Created custom workflow test suite: {suite.suite_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating custom workflow test suite: {e}")
        return {
            "success": False,
            "error": str(e),
            "suite_id": None
        }

async def bmad_workflow_test_run_suite(**kwargs) -> Dict[str, Any]:
    """
    Run a specific workflow test suite
    
    Args:
        suite_id: ID of the test suite to run
    
    Returns:
        Dict containing test execution results
    """
    try:
        suite_id = kwargs.get("suite_id")
        if not suite_id:
            return {
                "success": False,
                "error": "suite_id is required",
                "execution_id": None
            }
        
        logger.info(f"Running workflow test suite: {suite_id}")
        
        # Run the custom test suite
        execution = await workflow_testing_engine.run_custom_workflow_test(suite_id)
        
        # Format results
        result = {
            "success": True,
            "execution_id": execution.execution_id,
            "suite_id": execution.suite_id,
            "status": execution.status.value,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "duration_seconds": execution.duration_seconds,
            "overall_score": execution.overall_score,
            "error_summary": execution.error_summary,
            "step_results": []
        }
        
        # Add step results
        for step_result in execution.step_results:
            step_data = {
                "step_id": step_result.step_id,
                "status": step_result.status.value,
                "start_time": step_result.start_time.isoformat(),
                "end_time": step_result.end_time.isoformat() if step_result.end_time else None,
                "duration_seconds": step_result.duration_seconds,
                "error_message": step_result.error_message,
                "validation_results": step_result.validation_results
            }
            result["step_results"].append(step_data)
        
        logger.info(f"Workflow test suite completed with status: {execution.status}")
        return result
        
    except Exception as e:
        logger.error(f"Error running workflow test suite: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_id": None,
            "status": "ERROR"
        }

async def bmad_workflow_test_list_suites(**kwargs) -> Dict[str, Any]:
    """
    List all available workflow test suites
    
    Args:
        None required
    
    Returns:
        Dict containing list of test suites
    """
    try:
        suites = workflow_testing_engine.suite_builder.list_suites()
        
        result = {
            "success": True,
            "suites": []
        }
        
        for suite in suites:
            suite_data = {
                "suite_id": suite.suite_id,
                "suite_name": suite.suite_name,
                "description": suite.description,
                "phases": [phase.value for phase in suite.workflow_phases],
                "test_steps_count": len(suite.test_steps),
                "created_at": suite.created_at.isoformat(),
                "updated_at": suite.updated_at.isoformat()
            }
            result["suites"].append(suite_data)
        
        logger.info(f"Listed {len(suites)} workflow test suites")
        return result
        
    except Exception as e:
        logger.error(f"Error listing workflow test suites: {e}")
        return {
            "success": False,
            "error": str(e),
            "suites": []
        }

async def bmad_workflow_test_get_history(**kwargs) -> Dict[str, Any]:
    """
    Get workflow test execution history
    
    Args:
        limit: Maximum number of executions to return (default: 50)
    
    Returns:
        Dict containing test execution history
    """
    try:
        limit = kwargs.get("limit", 50)
        history = workflow_testing_engine.get_test_history(limit)
        
        result = {
            "success": True,
            "executions": []
        }
        
        for execution in history:
            execution_data = {
                "execution_id": execution.execution_id,
                "suite_id": execution.suite_id,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "duration_seconds": execution.duration_seconds,
                "overall_score": execution.overall_score,
                "error_summary": execution.error_summary,
                "step_results_count": len(execution.step_results) if execution.step_results else 0
            }
            result["executions"].append(execution_data)
        
        logger.info(f"Retrieved {len(history)} workflow test executions")
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "executions": []
        }

async def bmad_workflow_test_get_statistics(**kwargs) -> Dict[str, Any]:
    """
    Get workflow test execution statistics
    
    Args:
        None required
    
    Returns:
        Dict containing test statistics
    """
    try:
        stats = workflow_testing_engine.get_test_statistics()
        
        result = {
            "success": True,
            "statistics": stats
        }
        
        logger.info("Retrieved workflow test statistics")
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow test statistics: {e}")
        return {
            "success": False,
            "error": str(e),
            "statistics": {}
        }

async def bmad_workflow_test_validate_step(**kwargs) -> Dict[str, Any]:
    """
    Validate a specific workflow test step
    
    Args:
        step_id: ID of the step to validate
        output: Step output to validate
        validation_criteria: Criteria for validation
    
    Returns:
        Dict containing validation results
    """
    try:
        step_id = kwargs.get("step_id")
        output = kwargs.get("output", {})
        validation_criteria = kwargs.get("validation_criteria", {})
        
        if not step_id:
            return {
                "success": False,
                "error": "step_id is required"
            }
        
        # Create a mock step for validation
        step = WorkflowTestStep(
            step_id=step_id,
            step_name="Validation Step",
            phase=WorkflowPhase.PRD_CREATION,  # Default phase
            description="Step validation",
            expected_output=output,
            validation_criteria=validation_criteria,
            dependencies=[]
        )
        
        # Validate the step output
        validator = workflow_testing_engine.test_executor.validator
        validation_results = await validator.validate_step_output(step, output)
        
        result = {
            "success": True,
            "step_id": step_id,
            "validation_results": validation_results
        }
        
        logger.info(f"Validated workflow test step: {step_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error validating workflow test step: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_results": {}
        }
