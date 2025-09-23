"""
BMAD Unified Persona System

This module integrates all Phase 2 components to provide a complete
Unified Persona Activation system with context preservation, session
management, and task checkpointing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from .bmad_persona_context import (
    BMADPersonaContextManager, 
    PersonaType, 
    BMADPersonaContextStorage
)
from .bmad_session_manager import (
    BMADSessionManager, 
    SessionEventHandler,
    SessionEvent
)
from .bmad_task_checkpoint import (
    BMADTaskCheckpointer,
    TaskState,
    CheckpointType,
    CheckpointScope,
    TaskCheckpointStorage
)

logger = logging.getLogger(__name__)


@dataclass
class UnifiedPersonaConfig:
    """Configuration for the unified persona system."""
    session_timeout: int = 3600  # 1 hour
    idle_timeout: int = 900      # 15 minutes
    auto_checkpoint_interval: int = 300  # 5 minutes
    max_sessions_per_user: int = 10
    max_checkpoints_per_task: int = 10
    enable_auto_checkpointing: bool = True
    enable_session_cleanup: bool = True


class BMADUnifiedPersonaSystem:
    """
    Unified Persona Activation System for BMAD.
    
    This class integrates all Phase 2 components to provide seamless
    persona switching with context preservation, session management,
    and task checkpointing.
    """
    
    def __init__(self, 
                 db_client: Any,
                 config: Optional[UnifiedPersonaConfig] = None):
        """
        Initialize the unified persona system.
        
        Args:
            db_client: Database client for persistence
            config: Configuration for the system
        """
        self.config = config or UnifiedPersonaConfig()
        self.db_client = db_client
        
        # Initialize storage backends
        self.context_storage = BMADPersonaContextStorage(db_client)
        self.task_storage = TaskCheckpointStorage(db_client)
        
        # Initialize core components
        self.context_manager = BMADPersonaContextManager(self.context_storage)
        self.session_manager = BMADSessionManager(
            context_manager=self.context_manager,
            session_timeout=self.config.session_timeout,
            idle_timeout=self.config.idle_timeout,
            max_sessions_per_user=self.config.max_sessions_per_user,
            cleanup_interval=300  # 5 minutes
        )
        self.task_checkpointer = BMADTaskCheckpointer(
            storage_backend=self.task_storage,
            auto_checkpoint_interval=self.config.auto_checkpoint_interval,
            max_checkpoints_per_task=self.config.max_checkpoints_per_task
        )
        
        # Integration event handlers
        self._setup_event_handlers()
        
        # System state
        self._initialized = False
    
    async def initialize(self):
        """Initialize the unified persona system."""
        if self._initialized:
            return
        
        # Start background tasks
        await self.session_manager.start()
        if self.config.enable_auto_checkpointing:
            await self.task_checkpointer.start()
        
        self._initialized = True
        logger.info("BMAD Unified Persona System initialized")
    
    async def shutdown(self):
        """Shutdown the unified persona system."""
        if not self._initialized:
            return
        
        # Stop background tasks
        await self.session_manager.stop()
        await self.task_checkpointer.stop()
        
        self._initialized = False
        logger.info("BMAD Unified Persona System shutdown")
    
    async def create_session(self, 
                           user_id: str, 
                           project_id: str, 
                           initial_persona: PersonaType = PersonaType.ORCHESTRATOR) -> Dict[str, Any]:
        """
        Create a new session with unified persona capabilities.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            initial_persona: Initial persona to activate
            
        Returns:
            Session creation result
        """
        await self.initialize()
        
        # Create session through session manager
        session_id = await self.session_manager.create_session(
            user_id, project_id, initial_persona
        )
        
        # Get session status
        status = await self.session_manager.get_session_status(session_id)
        
        return {
            "session_id": session_id,
            "status": status,
            "system_initialized": True,
            "available_personas": [persona.value for persona in PersonaType]
        }
    
    async def switch_persona(self, 
                           session_id: str, 
                           target_persona: PersonaType,
                           context_preservation: bool = True,
                           checkpoint_before_switch: bool = True) -> Dict[str, Any]:
        """
        Switch to a different persona with full context preservation.
        
        Args:
            session_id: Session identifier
            target_persona: Target persona to switch to
            context_preservation: Whether to preserve context
            checkpoint_before_switch: Whether to checkpoint before switching
            
        Returns:
            Persona switch result
        """
        # Checkpoint current state if requested
        if checkpoint_before_switch:
            await self.checkpoint_session_state(
                session_id, 
                checkpoint_type=CheckpointType.PERSONA_SWITCH,
                checkpoint_name=f"before_switch_to_{target_persona.value}"
            )
        
        # Switch persona through session manager
        result = await self.session_manager.switch_persona(
            session_id, target_persona, context_preservation
        )
        
        # Update task context for new persona
        await self._update_task_context_for_persona(session_id, target_persona)
        
        return result
    
    async def start_task(self, 
                        session_id: str,
                        task_name: str,
                        input_data: Dict[str, Any],
                        dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a new task with automatic tracking and checkpointing.
        
        Args:
            session_id: Session identifier
            task_name: Human-readable task name
            input_data: Initial input data for the task
            dependencies: List of task dependencies
            
        Returns:
            Task creation result
        """
        # Get current session info
        session_status = await self.session_manager.get_session_status(session_id)
        active_persona = session_status["active_persona"]
        
        # Generate task ID
        task_id = f"{session_id}_{task_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Start task tracking
        task_state = await self.task_checkpointer.start_task(
            task_id=task_id,
            task_name=task_name,
            persona_type=active_persona["type"],
            input_data=input_data,
            dependencies=dependencies
        )
        
        return {
            "task_id": task_id,
            "task_state": task_state,
            "session_id": session_id,
            "active_persona": active_persona["type"]
        }
    
    async def update_task_progress(self, 
                                 task_id: str,
                                 progress: float,
                                 output_data: Optional[Dict[str, Any]] = None,
                                 intermediate_results: Optional[Dict[str, Any]] = None,
                                 status: Optional[str] = None) -> Dict[str, Any]:
        """
        Update task progress with automatic checkpointing.
        
        Args:
            task_id: Task identifier
            progress: Progress value (0.0 to 1.0)
            output_data: New output data
            intermediate_results: New intermediate results
            status: New status
            
        Returns:
            Update result
        """
        # Update task state
        task_state = await self.task_checkpointer.update_task_state(
            task_id=task_id,
            progress=progress,
            output_data=output_data,
            intermediate_results=intermediate_results,
            status=status,
            metadata={"last_update": datetime.utcnow().isoformat()}
        )
        
        # Create automatic checkpoint if significant progress
        if progress > 0.1 and int(progress * 10) % 2 == 0:  # Every 20% progress
            await self.task_checkpointer.create_checkpoint(
                task_ids=[task_id],
                checkpoint_type=CheckpointType.AUTOMATIC,
                checkpoint_name=f"progress_{int(progress * 100)}_percent"
            )
        
        return {
            "task_id": task_id,
            "updated_task_state": task_state,
            "checkpoint_created": progress > 0.1 and int(progress * 10) % 2 == 0
        }
    
    async def complete_task(self, 
                          task_id: str,
                          final_output: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete a task with final checkpointing.
        
        Args:
            task_id: Task identifier
            final_output: Final output data
            metadata: Completion metadata
            
        Returns:
            Task completion result
        """
        # Complete task
        task_state = await self.task_checkpointer.complete_task(
            task_id=task_id,
            final_output=final_output,
            metadata=metadata
        )
        
        return {
            "task_id": task_id,
            "completed_task_state": task_state,
            "completion_timestamp": datetime.utcnow().isoformat()
        }
    
    async def checkpoint_session_state(self, 
                                     session_id: str,
                                     checkpoint_type: CheckpointType = CheckpointType.MANUAL,
                                     checkpoint_name: Optional[str] = None,
                                     include_active_tasks: bool = True) -> Dict[str, Any]:
        """
        Create a comprehensive checkpoint of session state.
        
        Args:
            session_id: Session identifier
            checkpoint_type: Type of checkpoint
            checkpoint_name: Optional checkpoint name
            include_active_tasks: Whether to include active task states
            
        Returns:
            Checkpoint creation result
        """
        # Create session checkpoint
        session_checkpoint_id = await self.session_manager.checkpoint_session(
            session_id, checkpoint_name
        )
        
        # Create task checkpoints if requested
        task_checkpoints = []
        if include_active_tasks:
            # Get all active tasks for the session
            active_tasks = await self._get_session_active_tasks(session_id)
            
            if active_tasks:
                task_checkpoint_id = await self.task_checkpointer.create_checkpoint(
                    task_ids=active_tasks,
                    checkpoint_type=checkpoint_type,
                    scope=CheckpointScope.SESSION,
                    checkpoint_name=f"session_checkpoint_{checkpoint_name or 'manual'}",
                    session_id=session_id
                )
                task_checkpoints.append(task_checkpoint_id)
        
        return {
            "session_checkpoint_id": session_checkpoint_id,
            "task_checkpoint_ids": task_checkpoints,
            "checkpoint_type": checkpoint_type.value,
            "session_id": session_id
        }
    
    async def restore_session_state(self, 
                                  session_id: str,
                                  checkpoint_id: str,
                                  restore_tasks: bool = True) -> Dict[str, Any]:
        """
        Restore session state from a checkpoint.
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
            restore_tasks: Whether to restore task states
            
        Returns:
            Restore result
        """
        # Restore session context
        session_result = await self.session_manager.restore_session(
            session_id, checkpoint_id
        )
        
        # Restore task states if requested
        task_result = None
        if restore_tasks:
            try:
                task_result = await self.task_checkpointer.restore_from_checkpoint(
                    checkpoint_id
                )
            except ValueError:
                # No task checkpoint found, that's okay
                pass
        
        return {
            "session_restored": session_result,
            "tasks_restored": task_result,
            "restore_timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_comprehensive_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status of session, personas, and tasks.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Comprehensive status information
        """
        # Get session status
        session_status = await self.session_manager.get_session_status(session_id)
        
        # Get active tasks
        active_tasks = await self._get_session_active_tasks(session_id)
        task_states = {}
        for task_id in active_tasks:
            task_state = await self.task_checkpointer.get_task_state(task_id)
            if task_state:
                task_states[task_id] = {
                    "task_name": task_state.task_name,
                    "status": task_state.status,
                    "progress": task_state.progress,
                    "persona_type": task_state.persona_type,
                    "last_modified": task_state.metadata.get("last_modified")
                }
        
        # Get recent checkpoints
        recent_checkpoints = []
        for task_id in active_tasks:
            checkpoints = await self.task_checkpointer.get_task_checkpoints(task_id)
            recent_checkpoints.extend([
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "checkpoint_name": cp.checkpoint_name,
                    "timestamp": cp.timestamp.isoformat(),
                    "type": cp.checkpoint_type.value,
                    "task_id": task_id
                }
                for cp in checkpoints[-3:]  # Last 3 checkpoints per task
            ])
        
        # Sort by timestamp
        recent_checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "session_status": session_status,
            "active_tasks": task_states,
            "recent_checkpoints": recent_checkpoints[:10],  # Last 10 overall
            "system_health": {
                "initialized": self._initialized,
                "auto_checkpointing": self.config.enable_auto_checkpointing,
                "session_cleanup": self.config.enable_session_cleanup
            }
        }
    
    def _setup_event_handlers(self):
        """Setup integration event handlers."""
        # Session event handler for task integration
        class TaskIntegrationHandler(SessionEventHandler):
            def __init__(self, task_checkpointer: BMADTaskCheckpointer):
                self.task_checkpointer = task_checkpointer
            
            async def handle_persona_switched(self, event: SessionEvent, data: Dict[str, Any]):
                """Handle persona switches for task context updates."""
                session_id = data["session_id"]
                target_persona = data["target_persona"]
                
                # Update task contexts for new persona
                await self._update_task_context_for_persona(session_id, target_persona)
            
            async def _update_task_context_for_persona(self, session_id: str, persona_type: str):
                """Update task context for persona switch."""
                # This would be implemented to update task metadata
                # when persona switches occur
                pass
        
        # Add the handler
        task_handler = TaskIntegrationHandler(self.task_checkpointer)
        self.session_manager.add_event_handler(SessionEvent.PERSONA_SWITCHED, task_handler)
    
    async def _update_task_context_for_persona(self, session_id: str, persona_type: PersonaType):
        """Update task context when persona switches."""
        active_tasks = await self._get_session_active_tasks(session_id)
        
        for task_id in active_tasks:
            task_state = await self.task_checkpointer.get_task_state(task_id)
            if task_state:
                # Update task metadata with persona switch info
                await self.task_checkpointer.update_task_state(
                    task_id=task_id,
                    metadata={
                        "last_persona_switch": datetime.utcnow().isoformat(),
                        "current_persona": persona_type.value
                    }
                )
    
    async def _get_session_active_tasks(self, session_id: str) -> List[str]:
        """Get list of active task IDs for a session."""
        # This would query the database for active tasks in the session
        # For now, return empty list as placeholder
        return []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# Factory function for easy initialization
async def create_unified_persona_system(db_client: Any, 
                                      config: Optional[UnifiedPersonaConfig] = None) -> BMADUnifiedPersonaSystem:
    """
    Create and initialize a unified persona system.
    
    Args:
        db_client: Database client for persistence
        config: Optional configuration
        
    Returns:
        Initialized unified persona system
    """
    system = BMADUnifiedPersonaSystem(db_client, config)
    await system.initialize()
    return system
