"""
BMAD Persona Management API Endpoints

This module provides HTTP API endpoints for the Phase 2:
Unified Persona Activation system, including session management,
persona switching, and task checkpointing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from cflow_platform.core.bmad_unified_persona_system import (
    BMADUnifiedPersonaSystem,
    UnifiedPersonaConfig,
    create_unified_persona_system
)
from cflow_platform.core.bmad_persona_context import PersonaType
from cflow_platform.core.bmad_task_checkpoint import CheckpointType, CheckpointScope

logger = logging.getLogger(__name__)

# Create router for persona endpoints
router = APIRouter(prefix="/bmad/persona", tags=["BMAD Persona Management"])

# Global persona system instance (will be initialized on startup)
persona_system: Optional[BMADUnifiedPersonaSystem] = None


# Pydantic models for request/response
class SessionCreateRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    project_id: str = Field(..., description="Project identifier")
    initial_persona: str = Field(default="bmad-orchestrator", description="Initial persona type")


class PersonaSwitchRequest(BaseModel):
    target_persona: str = Field(..., description="Target persona to switch to")
    context_preservation: bool = Field(default=True, description="Whether to preserve context")
    checkpoint_before_switch: bool = Field(default=True, description="Whether to checkpoint before switching")


class TaskStartRequest(BaseModel):
    task_name: str = Field(..., description="Human-readable task name")
    input_data: Dict[str, Any] = Field(default={}, description="Initial input data")
    dependencies: Optional[list] = Field(default=None, description="List of task dependencies")


class TaskUpdateRequest(BaseModel):
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress value (0.0 to 1.0)")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="New output data")
    intermediate_results: Optional[Dict[str, Any]] = Field(default=None, description="New intermediate results")
    status: Optional[str] = Field(default=None, description="New status")


class TaskCompleteRequest(BaseModel):
    final_output: Dict[str, Any] = Field(..., description="Final output data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Completion metadata")


class CheckpointCreateRequest(BaseModel):
    checkpoint_type: str = Field(default="manual", description="Type of checkpoint")
    checkpoint_name: Optional[str] = Field(default=None, description="Optional checkpoint name")
    include_active_tasks: bool = Field(default=True, description="Whether to include active task states")


class CheckpointRestoreRequest(BaseModel):
    checkpoint_id: str = Field(..., description="Checkpoint identifier to restore from")
    restore_tasks: bool = Field(default=True, description="Whether to restore task states")


# Dependency to get current user (placeholder)
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request (placeholder implementation)."""
    # This would typically extract user info from JWT token or session
    return {
        "user_id": "user_123",  # Placeholder
        "project_id": "project_456"  # Placeholder
    }


# Initialize persona system on startup
@router.on_event("startup")
async def startup_persona_system():
    """Initialize the persona system on startup."""
    global persona_system
    
    try:
        # This would use the actual database client in production
        # For now, we'll use a mock client
        from unittest.mock import AsyncMock
        mock_db_client = AsyncMock()
        
        config = UnifiedPersonaConfig(
            session_timeout=3600,
            idle_timeout=900,
            auto_checkpoint_interval=300,
            enable_auto_checkpointing=True,
            enable_session_cleanup=True
        )
        
        persona_system = await create_unified_persona_system(mock_db_client, config)
        logger.info("BMAD Persona System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize persona system: {e}")
        raise


@router.on_event("shutdown")
async def shutdown_persona_system():
    """Shutdown the persona system on shutdown."""
    global persona_system
    
    if persona_system:
        await persona_system.shutdown()
        logger.info("BMAD Persona System shutdown complete")


# Session Management Endpoints

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new BMAD session with persona management.
    
    This endpoint creates a new session with the specified initial persona
    and sets up context preservation and task checkpointing capabilities.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        # Validate persona type
        try:
            initial_persona = PersonaType(request.initial_persona)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid persona type: {request.initial_persona}"
            )
        
        # Create session
        result = await persona_system.create_session(
            user_id=request.user_id,
            project_id=request.project_id,
            initial_persona=initial_persona
        )
        
        return {
            "success": True,
            "message": "Session created successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get comprehensive status of a BMAD session.
    
    Returns detailed information about the session, active personas,
    running tasks, and recent checkpoints.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        status_info = await persona_system.get_comprehensive_status(session_id)
        
        return {
            "success": True,
            "data": status_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    reason: str = "user_requested",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Terminate a BMAD session.
    
    Permanently terminates the session and cleans up all associated
    contexts, tasks, and checkpoints.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        success = await persona_system.session_manager.terminate_session(session_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} terminated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to terminate session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Persona Management Endpoints

@router.post("/sessions/{session_id}/switch-persona")
async def switch_persona(
    session_id: str,
    request: PersonaSwitchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Switch to a different BMAD persona.
    
    Switches the active persona while preserving context and optionally
    creating a checkpoint before the switch.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        # Validate persona type
        try:
            target_persona = PersonaType(request.target_persona)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid persona type: {request.target_persona}"
            )
        
        # Switch persona
        result = await persona_system.switch_persona(
            session_id=session_id,
            target_persona=target_persona,
            context_preservation=request.context_preservation,
            checkpoint_before_switch=request.checkpoint_before_switch
        )
        
        return {
            "success": True,
            "message": f"Switched to persona {target_persona.value} successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to switch persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personas")
async def list_available_personas():
    """
    List all available BMAD personas.
    
    Returns a list of all persona types that can be activated.
    """
    return {
        "success": True,
        "data": {
            "personas": [
                {
                    "type": persona.value,
                    "description": _get_persona_description(persona)
                }
                for persona in PersonaType
            ]
        }
    }


# Task Management Endpoints

@router.post("/sessions/{session_id}/tasks")
async def start_task(
    session_id: str,
    request: TaskStartRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start a new task with automatic tracking.
    
    Creates a new task with automatic state tracking and checkpointing
    capabilities.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        result = await persona_system.start_task(
            session_id=session_id,
            task_name=request.task_name,
            input_data=request.input_data,
            dependencies=request.dependencies
        )
        
        return {
            "success": True,
            "message": f"Task '{request.task_name}' started successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to start task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update task progress with automatic checkpointing.
    
    Updates the progress of a task and optionally creates automatic
    checkpoints at significant milestones.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        result = await persona_system.update_task_progress(
            task_id=task_id,
            progress=request.progress,
            output_data=request.output_data,
            intermediate_results=request.intermediate_results,
            status=request.status
        )
        
        return {
            "success": True,
            "message": f"Task {task_id} progress updated to {request.progress:.1%}",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to update task progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    request: TaskCompleteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Complete a task with final checkpointing.
    
    Marks a task as completed and creates a final checkpoint with
    the task's output data.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        result = await persona_system.complete_task(
            task_id=task_id,
            final_output=request.final_output,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "message": f"Task {task_id} completed successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current status of a task.
    
    Returns detailed information about a task's current state,
    progress, and recent checkpoints.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        task_state = await persona_system.task_checkpointer.get_task_state(task_id)
        
        if not task_state:
            raise HTTPException(status_code=404, detail="Task not found")
        
        checkpoints = await persona_system.task_checkpointer.get_task_checkpoints(task_id)
        
        return {
            "success": True,
            "data": {
                "task_state": {
                    "task_id": task_state.task_id,
                    "task_name": task_state.task_name,
                    "status": task_state.status,
                    "progress": task_state.progress,
                    "persona_type": task_state.persona_type,
                    "created_at": task_state.metadata.get("start_time"),
                    "last_modified": task_state.metadata.get("last_modified")
                },
                "checkpoints": [
                    {
                        "checkpoint_id": cp.checkpoint_id,
                        "checkpoint_name": cp.checkpoint_name,
                        "timestamp": cp.timestamp.isoformat(),
                        "type": cp.checkpoint_type.value
                    }
                    for cp in checkpoints
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Checkpoint Management Endpoints

@router.post("/sessions/{session_id}/checkpoints")
async def create_checkpoint(
    session_id: str,
    request: CheckpointCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a checkpoint of session state.
    
    Creates a comprehensive checkpoint of the current session state,
    including persona contexts and active task states.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        # Validate checkpoint type
        try:
            checkpoint_type = CheckpointType(request.checkpoint_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid checkpoint type: {request.checkpoint_type}"
            )
        
        result = await persona_system.checkpoint_session_state(
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            checkpoint_name=request.checkpoint_name,
            include_active_tasks=request.include_active_tasks
        )
        
        return {
            "success": True,
            "message": "Checkpoint created successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/restore")
async def restore_from_checkpoint(
    session_id: str,
    request: CheckpointRestoreRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Restore session state from a checkpoint.
    
    Restores the session state from a previously created checkpoint,
    including persona contexts and task states.
    """
    if not persona_system:
        raise HTTPException(status_code=500, detail="Persona system not initialized")
    
    try:
        result = await persona_system.restore_session_state(
            session_id=session_id,
            checkpoint_id=request.checkpoint_id,
            restore_tasks=request.restore_tasks
        )
        
        return {
            "success": True,
            "message": "Session restored from checkpoint successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore from checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and System Endpoints

@router.get("/health")
async def persona_system_health():
    """
    Check the health of the persona system.
    
    Returns the current status and health information of the
    unified persona system.
    """
    if not persona_system:
        return {
            "success": False,
            "status": "unhealthy",
            "message": "Persona system not initialized"
        }
    
    try:
        # Check if system is initialized
        health_info = {
            "success": True,
            "status": "healthy",
            "initialized": persona_system._initialized,
            "config": {
                "session_timeout": persona_system.config.session_timeout,
                "idle_timeout": persona_system.config.idle_timeout,
                "auto_checkpoint_interval": persona_system.config.auto_checkpoint_interval,
                "enable_auto_checkpointing": persona_system.config.enable_auto_checkpointing
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "message": str(e)
        }


def _get_persona_description(persona: PersonaType) -> str:
    """Get a human-readable description for a persona type."""
    descriptions = {
        PersonaType.ORCHESTRATOR: "Master orchestrator and BMAD method expert",
        PersonaType.PROJECT_MANAGER: "Product management and requirements specialist",
        PersonaType.ARCHITECT: "System architecture and technical design expert",
        PersonaType.DEVELOPER: "Software development and implementation specialist",
        PersonaType.SCRUM_MASTER: "Agile process and story management expert",
        PersonaType.ANALYST: "Business analysis and requirements expert",
        PersonaType.UX_EXPERT: "User experience and interface design specialist",
        PersonaType.TESTER: "Quality assurance and testing specialist",
        PersonaType.MASTER: "Universal BMAD master with all capabilities"
    }
    return descriptions.get(persona, "Specialized BMAD persona")
