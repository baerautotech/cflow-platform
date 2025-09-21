"""
Installation Flow Testing Handlers

This module provides MCP handlers for installation flow testing functionality,
including complete installation flow testing, step-by-step testing, and rollback testing.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from cflow_platform.core.installation_flow_testing_engine import (
    InstallationFlowTestingEngine,
    InstallationFlowResult
)

logger = logging.getLogger(__name__)


async def bmad_installation_flow_test(
    test_environment: bool = True,
    skip_optional_steps: bool = False
) -> Dict[str, Any]:
    """
    Test the complete installation flow.
    
    Args:
        test_environment: Whether to test in a temporary environment
        skip_optional_steps: Whether to skip optional installation steps
        
    Returns:
        Dictionary with installation flow test results
    """
    try:
        logger.info("Testing complete installation flow...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Run complete installation flow test
        result = await engine.test_complete_installation_flow(
            test_environment=test_environment,
            skip_optional_steps=skip_optional_steps
        )
        
        return {
            "success": result.success,
            "message": result.message,
            "total_steps": result.total_steps,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "step_results": result.step_results,
            "installation_time": result.installation_time,
            "validation_time": result.validation_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test installation flow: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_step_test(
    step_name: str,
    custom_command: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test a specific installation step.
    
    Args:
        step_name: Name of the installation step to test
        custom_command: Custom command to execute (JSON string)
        
    Returns:
        Dictionary with step test results
    """
    try:
        logger.info(f"Testing installation step: {step_name}")
        
        # Parse custom command if provided
        parsed_command = None
        if custom_command:
            try:
                parsed_command = json.loads(custom_command)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in custom_command: {e}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Test the specific step
        result = await engine.test_installation_step(
            step_name=step_name,
            custom_command=parsed_command
        )
        
        return {
            "success": result["success"],
            "step_name": step_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test installation step {step_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "step_name": step_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_rollback_test() -> Dict[str, Any]:
    """
    Test the rollback flow after installation.
    
    Returns:
        Dictionary with rollback test results
    """
    try:
        logger.info("Testing installation rollback flow...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Test rollback flow
        result = await engine.test_rollback_flow()
        
        return {
            "success": result.success,
            "message": result.message,
            "total_steps": result.total_steps,
            "completed_steps": result.completed_steps,
            "installation_time": result.installation_time,
            "validation_time": result.validation_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test installation rollback: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_validate_environment() -> Dict[str, Any]:
    """
    Validate the installation environment.
    
    Returns:
        Dictionary with environment validation results
    """
    try:
        logger.info("Validating installation environment...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Get installation flow steps
        steps = engine.create_installation_flow()
        
        # Find environment validation step
        env_step = next((s for s in steps if s.name == "environment_validation"), None)
        
        if not env_step:
            return {
                "success": False,
                "error": "Environment validation step not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Execute environment validation
        result = await engine._execute_installation_step(env_step)
        
        return {
            "success": result["success"],
            "step": "environment_validation",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate installation environment: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_validate_components() -> Dict[str, Any]:
    """
    Validate all installation components.
    
    Returns:
        Dictionary with component validation results
    """
    try:
        logger.info("Validating installation components...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Validate complete installation
        validation_result = await engine._validate_complete_installation()
        
        return {
            "success": validation_result["success"],
            "checks": validation_result.get("checks", {}),
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate installation components: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_get_flow_steps() -> Dict[str, Any]:
    """
    Get the list of installation flow steps.
    
    Returns:
        Dictionary with installation flow steps
    """
    try:
        logger.info("Getting installation flow steps...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Get installation flow steps
        steps = engine.create_installation_flow()
        
        # Convert steps to serializable format
        steps_data = []
        for step in steps:
            steps_data.append({
                "name": step.name,
                "description": step.description,
                "command": step.command,
                "expected_exit_code": step.expected_exit_code,
                "timeout_seconds": step.timeout_seconds,
                "required_files": step.required_files,
                "required_directories": step.required_directories,
                "environment_variables": step.environment_variables,
                "validation_checks": step.validation_checks
            })
        
        return {
            "success": True,
            "steps": steps_data,
            "total_steps": len(steps_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get installation flow steps: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_test_prerequisites() -> Dict[str, Any]:
    """
    Test installation prerequisites.
    
    Returns:
        Dictionary with prerequisites test results
    """
    try:
        logger.info("Testing installation prerequisites...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Test various prerequisites
        prerequisites = {
            "python_available": engine._check_dependencies(),
            "project_root_exists": Path.cwd().exists(),
            "git_repository": (Path.cwd() / ".git").exists(),
            "vendor_bmad_exists": (Path.cwd() / "vendor" / "bmad").exists(),
            "cerebraflow_dir_exists": (Path.cwd() / ".cerebraflow").exists()
        }
        
        # Run async checks
        async_results = {}
        for name, check in prerequisites.items():
            if asyncio.iscoroutine(check):
                async_results[name] = await check
            else:
                async_results[name] = check
        
        success = all(async_results.values())
        
        return {
            "success": success,
            "prerequisites": async_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test installation prerequisites: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_installation_generate_report() -> Dict[str, Any]:
    """
    Generate installation flow test report.
    
    Returns:
        Dictionary with installation test report
    """
    try:
        logger.info("Generating installation flow test report...")
        
        # Create testing engine
        engine = InstallationFlowTestingEngine()
        
        # Get installation flow steps
        steps = engine.create_installation_flow()
        
        # Generate report data
        report_data = {
            "installation_flow": {
                "total_steps": len(steps),
                "steps": [
                    {
                        "name": step.name,
                        "description": step.description,
                        "command": " ".join(step.command),
                        "timeout": step.timeout_seconds
                    }
                    for step in steps
                ]
            },
            "prerequisites": {
                "python_available": await engine._check_dependencies(),
                "project_root_exists": Path.cwd().exists(),
                "git_repository": (Path.cwd() / ".git").exists(),
                "vendor_bmad_exists": (Path.cwd() / "vendor" / "bmad").exists()
            },
            "validation_checks": {
                "webmcp_config": await engine._check_webmcp_config(),
                "bmad_handlers": await engine._check_bmad_handlers(),
                "git_hooks": await engine._check_git_hooks(),
                "cursor_config": await engine._check_cursor_config()
            }
        }
        
        return {
            "success": True,
            "report": report_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate installation test report: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
