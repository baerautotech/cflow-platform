"""
Uninstall and Rollback Handlers

This module provides MCP handlers for uninstall and rollback functionality,
including complete uninstall, rollback point management, and restoration capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from cflow_platform.core.uninstall_rollback_engine import (
    UninstallRollbackEngine,
    UninstallResult,
    RollbackResult
)

logger = logging.getLogger(__name__)


async def bmad_uninstall_complete(
    create_backup: bool = True,
    remove_vendor_bmad: bool = False,
    force: bool = False
) -> Dict[str, Any]:
    """
    Uninstall BMAD integration completely.
    
    Args:
        create_backup: Whether to create backup before uninstall
        remove_vendor_bmad: Whether to remove vendor BMAD directory
        force: Whether to force uninstall even if some steps fail
        
    Returns:
        Dictionary with uninstall result
    """
    try:
        logger.info("Starting complete BMAD integration uninstall...")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Perform complete uninstall
        result = await engine.uninstall_bmad_integration(
            create_backup=create_backup,
            remove_vendor_bmad=remove_vendor_bmad,
            force=force
        )
        
        return {
            "success": result.success,
            "message": result.message,
            "total_steps": result.total_steps,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "step_results": result.step_results,
            "uninstall_time": result.uninstall_time,
            "cleanup_time": result.cleanup_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to uninstall BMAD integration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_uninstall_step(
    step_name: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Execute a specific uninstall step.
    
    Args:
        step_name: Name of the uninstall step to execute
        force: Whether to force execution even if step fails
        
    Returns:
        Dictionary with step execution result
    """
    try:
        logger.info(f"Executing uninstall step: {step_name}")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Get uninstall steps
        steps = engine.create_uninstall_steps()
        step = next((s for s in steps if s.name == step_name), None)
        
        if not step:
            return {
                "success": False,
                "error": f"Uninstall step '{step_name}' not found",
                "step_name": step_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Execute the step
        result = await engine._execute_uninstall_step(step)
        
        return {
            "success": result["success"],
            "step_name": step_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute uninstall step {step_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "step_name": step_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_rollback_create_point(
    name: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a rollback point for future restoration.
    
    Args:
        name: Name of the rollback point
        description: Description of the rollback point
        
    Returns:
        Dictionary with rollback point creation result
    """
    try:
        logger.info(f"Creating rollback point: {name}")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Create rollback point
        result = await engine.create_rollback_point(name, description)
        
        return {
            "success": result.success,
            "message": result.message,
            "rollback_point": result.rollback_point,
            "restored_files": result.restored_files,
            "rollback_time": result.rollback_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create rollback point {name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "rollback_point": name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_rollback_to_point(
    rollback_point_name: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Rollback to a specific rollback point.
    
    Args:
        rollback_point_name: Name of the rollback point to restore
        force: Whether to force rollback even if some steps fail
        
    Returns:
        Dictionary with rollback result
    """
    try:
        logger.info(f"Rolling back to point: {rollback_point_name}")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Rollback to point
        result = await engine.rollback_to_point(rollback_point_name, force)
        
        return {
            "success": result.success,
            "message": result.message,
            "rollback_point": result.rollback_point,
            "restored_files": result.restored_files,
            "rollback_time": result.rollback_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to rollback to point {rollback_point_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "rollback_point": rollback_point_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_rollback_list_points() -> Dict[str, Any]:
    """
    List all available rollback points.
    
    Returns:
        Dictionary with rollback points information
    """
    try:
        logger.info("Listing rollback points...")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # List rollback points
        result = await engine.list_rollback_points()
        
        return {
            "success": result["success"],
            "rollback_points": result.get("rollback_points", []),
            "total_points": result.get("total_points", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list rollback points: {e}")
        return {
            "success": False,
            "error": str(e),
            "rollback_points": [],
            "total_points": 0,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_rollback_delete_point(
    rollback_point_name: str
) -> Dict[str, Any]:
    """
    Delete a specific rollback point.
    
    Args:
        rollback_point_name: Name of the rollback point to delete
        
    Returns:
        Dictionary with deletion result
    """
    try:
        logger.info(f"Deleting rollback point: {rollback_point_name}")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Delete rollback point
        result = await engine.delete_rollback_point(rollback_point_name)
        
        return {
            "success": result["success"],
            "message": result.get("message", ""),
            "error": result.get("error", ""),
            "rollback_point": rollback_point_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete rollback point {rollback_point_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "rollback_point": rollback_point_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_uninstall_validate() -> Dict[str, Any]:
    """
    Validate uninstall prerequisites and current state.
    
    Returns:
        Dictionary with validation result
    """
    try:
        logger.info("Validating uninstall prerequisites...")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Get uninstall steps
        steps = engine.create_uninstall_steps()
        
        # Validate each step
        validation_results = {}
        for step in steps:
            validation_results[step.name] = {
                "description": step.description,
                "action": step.action,
                "target_path": step.target_path,
                "required": step.required,
                "validation_checks": step.validation_checks
            }
        
        return {
            "success": True,
            "validation_results": validation_results,
            "total_steps": len(steps),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate uninstall prerequisites: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_uninstall_simulate() -> Dict[str, Any]:
    """
    Simulate uninstall process without actually performing it.
    
    Returns:
        Dictionary with simulation result
    """
    try:
        logger.info("Simulating uninstall process...")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Get uninstall steps
        steps = engine.create_uninstall_steps()
        
        # Simulate each step
        simulation_results = {}
        for step in steps:
            simulation_results[step.name] = {
                "description": step.description,
                "action": step.action,
                "target_path": step.target_path,
                "required": step.required,
                "would_remove": True if step.action in ["remove_file", "remove_directory"] else False,
                "would_execute": True if step.action == "run_command" else False
            }
        
        return {
            "success": True,
            "simulation_results": simulation_results,
            "total_steps": len(steps),
            "message": "Uninstall simulation completed. No actual changes were made.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate uninstall process: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_rollback_get_point_info(
    rollback_point_name: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific rollback point.
    
    Args:
        rollback_point_name: Name of the rollback point
        
    Returns:
        Dictionary with rollback point information
    """
    try:
        logger.info(f"Getting rollback point info: {rollback_point_name}")
        
        # Create uninstall engine
        engine = UninstallRollbackEngine()
        
        # Check if rollback point exists
        rollback_point_dir = engine.rollback_dir / rollback_point_name
        if not rollback_point_dir.exists():
            return {
                "success": False,
                "error": f"Rollback point '{rollback_point_name}' not found",
                "rollback_point": rollback_point_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Load rollback point metadata
        metadata_file = rollback_point_dir / "rollback_metadata.json"
        if not metadata_file.exists():
            return {
                "success": False,
                "error": f"Rollback point metadata not found for '{rollback_point_name}'",
                "rollback_point": rollback_point_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return {
            "success": True,
            "rollback_point": rollback_point_name,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rollback point info for {rollback_point_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "rollback_point": rollback_point_name,
            "timestamp": datetime.utcnow().isoformat()
        }
