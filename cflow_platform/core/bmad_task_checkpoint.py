"""
BMAD Task State Checkpointing System

This module implements task state checkpointing for Phase 2:
Unified Persona Activation. It provides automatic and manual
checkpointing of task states for recovery and continuity.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class CheckpointType(Enum):
    """Enumeration of checkpoint types."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    WORKFLOW = "workflow"
    ERROR_RECOVERY = "error_recovery"
    PERSONA_SWITCH = "persona_switch"


class CheckpointScope(Enum):
    """Enumeration of checkpoint scopes."""
    TASK = "task"
    WORKFLOW = "workflow"
    SESSION = "session"
    PERSONA = "persona"


@dataclass
class TaskState:
    """Represents the state of a task at a point in time."""
    task_id: str
    task_name: str
    persona_type: str
    status: str
    progress: float  # 0.0 to 1.0
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    intermediate_results: Dict[str, Any]
    error_state: Optional[Dict[str, Any]] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Checkpoint:
    """Represents a checkpoint of task state."""
    checkpoint_id: str
    session_id: str
    persona_id: str
    checkpoint_type: CheckpointType
    scope: CheckpointScope
    checkpoint_name: Optional[str]
    timestamp: datetime
    task_states: Dict[str, TaskState]
    context_snapshot: Dict[str, Any]
    dependencies: List[str]
    metadata: Dict[str, Any]
    checksum: str
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BMADTaskCheckpointer:
    """
    Manages task state checkpointing for BMAD personas.
    
    This class provides automatic and manual checkpointing of task states
    to enable recovery and continuity across persona switches and sessions.
    """
    
    def __init__(self, 
                 storage_backend: Optional[Any] = None,
                 auto_checkpoint_interval: int = 300,  # 5 minutes
                 max_checkpoints_per_task: int = 10):
        """
        Initialize the task checkpointer.
        
        Args:
            storage_backend: Storage backend for persistence
            auto_checkpoint_interval: Automatic checkpoint interval in seconds
            max_checkpoints_per_task: Maximum checkpoints to keep per task
        """
        self.storage_backend = storage_backend
        self.auto_checkpoint_interval = timedelta(seconds=auto_checkpoint_interval)
        self.max_checkpoints_per_task = max_checkpoints_per_task
        
        # Task tracking
        self.active_tasks: Dict[str, TaskState] = {}
        self.task_checkpoints: Dict[str, List[Checkpoint]] = {}
        self.checkpoint_callbacks: List[Callable] = []
        
        # Background tasks
        self._auto_checkpoint_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the automatic checkpointing task."""
        if self._auto_checkpoint_task is None or self._auto_checkpoint_task.done():
            self._auto_checkpoint_task = asyncio.create_task(self._auto_checkpoint_loop())
        
        logger.info("BMAD Task Checkpointer started")
    
    async def stop(self):
        """Stop the automatic checkpointing task."""
        if self._auto_checkpoint_task and not self._auto_checkpoint_task.done():
            self._auto_checkpoint_task.cancel()
            try:
                await self._auto_checkpoint_task
            except asyncio.CancelledError:
                pass
        
        logger.info("BMAD Task Checkpointer stopped")
    
    async def start_task(self, 
                        task_id: str,
                        task_name: str,
                        persona_type: str,
                        input_data: Dict[str, Any],
                        dependencies: Optional[List[str]] = None) -> TaskState:
        """
        Start tracking a new task.
        
        Args:
            task_id: Unique task identifier
            task_name: Human-readable task name
            persona_type: Type of persona executing the task
            input_data: Initial input data for the task
            dependencies: List of task dependencies
            
        Returns:
            Initial task state
        """
        task_state = TaskState(
            task_id=task_id,
            task_name=task_name,
            persona_type=persona_type,
            status="started",
            progress=0.0,
            input_data=input_data,
            output_data={},
            intermediate_results={},
            dependencies=dependencies or [],
            metadata={
                "start_time": datetime.utcnow().isoformat(),
                "persona_type": persona_type
            }
        )
        
        self.active_tasks[task_id] = task_state
        self.task_checkpoints[task_id] = []
        
        # Create initial checkpoint
        await self.create_checkpoint(
            task_ids=[task_id],
            checkpoint_type=CheckpointType.AUTOMATIC,
            checkpoint_name=f"task_start_{task_id}"
        )
        
        logger.info(f"Started tracking task {task_id}: {task_name}")
        return task_state
    
    async def update_task_state(self, 
                              task_id: str,
                              status: Optional[str] = None,
                              progress: Optional[float] = None,
                              output_data: Optional[Dict[str, Any]] = None,
                              intermediate_results: Optional[Dict[str, Any]] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> TaskState:
        """
        Update the state of a tracked task.
        
        Args:
            task_id: Task identifier
            status: New status
            progress: New progress (0.0 to 1.0)
            output_data: New output data
            intermediate_results: New intermediate results
            metadata: Additional metadata
            
        Returns:
            Updated task state
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not being tracked")
        
        task_state = self.active_tasks[task_id]
        
        # Update fields if provided
        if status is not None:
            task_state.status = status
        if progress is not None:
            task_state.progress = max(0.0, min(1.0, progress))
        if output_data is not None:
            task_state.output_data.update(output_data)
        if intermediate_results is not None:
            task_state.intermediate_results.update(intermediate_results)
        if metadata is not None:
            task_state.metadata.update(metadata)
        
        # Update last modified time
        task_state.metadata["last_modified"] = datetime.utcnow().isoformat()
        
        logger.debug(f"Updated task state for {task_id}: {status}, progress: {task_state.progress}")
        return task_state
    
    async def complete_task(self, 
                          task_id: str,
                          final_output: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> TaskState:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task identifier
            final_output: Final output data
            metadata: Completion metadata
            
        Returns:
            Final task state
        """
        task_state = await self.update_task_state(
            task_id=task_id,
            status="completed",
            progress=1.0,
            output_data=final_output,
            metadata=metadata or {}
        )
        
        # Add completion timestamp
        task_state.metadata["completion_time"] = datetime.utcnow().isoformat()
        
        # Create final checkpoint
        await self.create_checkpoint(
            task_ids=[task_id],
            checkpoint_type=CheckpointType.AUTOMATIC,
            checkpoint_name=f"task_complete_{task_id}"
        )
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        logger.info(f"Completed task {task_id}: {task_state.task_name}")
        return task_state
    
    async def fail_task(self, 
                       task_id: str,
                       error_info: Dict[str, Any],
                       metadata: Optional[Dict[str, Any]] = None) -> TaskState:
        """
        Mark a task as failed.
        
        Args:
            task_id: Task identifier
            error_info: Error information
            metadata: Failure metadata
            
        Returns:
            Failed task state
        """
        task_state = await self.update_task_state(
            task_id=task_id,
            status="failed",
            error_state=error_info,
            metadata=metadata or {}
        )
        
        # Add failure timestamp
        task_state.metadata["failure_time"] = datetime.utcnow().isoformat()
        
        # Create error recovery checkpoint
        await self.create_checkpoint(
            task_ids=[task_id],
            checkpoint_type=CheckpointType.ERROR_RECOVERY,
            checkpoint_name=f"task_failed_{task_id}"
        )
        
        logger.error(f"Task {task_id} failed: {task_state.task_name}")
        return task_state
    
    async def create_checkpoint(self,
                              task_ids: List[str],
                              checkpoint_type: CheckpointType = CheckpointType.MANUAL,
                              scope: CheckpointScope = CheckpointScope.TASK,
                              checkpoint_name: Optional[str] = None,
                              session_id: Optional[str] = None,
                              persona_id: Optional[str] = None,
                              context_snapshot: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a checkpoint of current task states.
        
        Args:
            task_ids: List of task IDs to checkpoint
            checkpoint_type: Type of checkpoint
            scope: Scope of checkpoint
            checkpoint_name: Optional name for checkpoint
            session_id: Session identifier
            persona_id: Persona identifier
            context_snapshot: Additional context to include
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Collect task states
        task_states = {}
        dependencies = []
        
        for task_id in task_ids:
            if task_id in self.active_tasks:
                task_state = self.active_tasks[task_id]
                task_states[task_id] = task_state
                dependencies.extend(task_state.dependencies)
        
        # Create context snapshot
        if context_snapshot is None:
            context_snapshot = {}
        
        context_snapshot.update({
            "checkpoint_timestamp": now.isoformat(),
            "checkpoint_type": checkpoint_type.value,
            "scope": scope.value,
            "active_tasks": list(self.active_tasks.keys())
        })
        
        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id or "unknown",
            persona_id=persona_id or "unknown",
            checkpoint_type=checkpoint_type,
            scope=scope,
            checkpoint_name=checkpoint_name,
            timestamp=now,
            task_states=task_states,
            context_snapshot=context_snapshot,
            dependencies=list(set(dependencies)),
            metadata={},
            checksum=self._calculate_checksum(task_states, context_snapshot)
        )
        
        # Store checkpoint for each task
        for task_id in task_ids:
            if task_id in self.task_checkpoints:
                self.task_checkpoints[task_id].append(checkpoint)
                
                # Limit checkpoints per task
                if len(self.task_checkpoints[task_id]) > self.max_checkpoints_per_task:
                    oldest_checkpoint = self.task_checkpoints[task_id].pop(0)
                    await self._cleanup_checkpoint(oldest_checkpoint)
        
        # Persist to storage backend
        if self.storage_backend:
            await self._persist_checkpoint(checkpoint)
        
        # Notify callbacks
        for callback in self.checkpoint_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(checkpoint)
                else:
                    callback(checkpoint)
            except Exception as e:
                logger.error(f"Error in checkpoint callback: {e}")
        
        logger.info(f"Created {checkpoint_type.value} checkpoint {checkpoint_id} for {len(task_ids)} tasks")
        return checkpoint_id
    
    async def restore_from_checkpoint(self, 
                                    checkpoint_id: str,
                                    task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Restore task states from a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint identifier
            task_ids: Optional list of task IDs to restore (all if None)
            
        Returns:
            Restore result
        """
        # Find checkpoint
        checkpoint = None
        for task_checkpoints in self.task_checkpoints.values():
            for cp in task_checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    checkpoint = cp
                    break
            if checkpoint:
                break
        
        if not checkpoint:
            # Try to load from storage backend
            if self.storage_backend:
                checkpoint = await self._load_checkpoint(checkpoint_id)
        
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # Determine which tasks to restore
        tasks_to_restore = task_ids or list(checkpoint.task_states.keys())
        
        restored_tasks = {}
        for task_id in tasks_to_restore:
            if task_id in checkpoint.task_states:
                task_state = checkpoint.task_states[task_id]
                
                # Restore task state
                self.active_tasks[task_id] = task_state
                
                # Initialize checkpoints list if needed
                if task_id not in self.task_checkpoints:
                    self.task_checkpoints[task_id] = []
                
                restored_tasks[task_id] = task_state
                
                logger.info(f"Restored task {task_id} from checkpoint {checkpoint_id}")
        
        return {
            "checkpoint_id": checkpoint_id,
            "restored_tasks": list(restored_tasks.keys()),
            "restore_timestamp": datetime.utcnow().isoformat(),
            "context_snapshot": checkpoint.context_snapshot
        }
    
    async def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """
        Get the current state of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Current task state or None if not found
        """
        return self.active_tasks.get(task_id)
    
    async def get_task_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """
        Get all checkpoints for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of checkpoints for the task
        """
        return self.task_checkpoints.get(task_id, [])
    
    async def get_checkpoint_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Get a checkpoint by ID.
        
        Args:
            checkpoint_id: Checkpoint identifier
            
        Returns:
            Checkpoint or None if not found
        """
        for task_checkpoints in self.task_checkpoints.values():
            for checkpoint in task_checkpoints:
                if checkpoint.checkpoint_id == checkpoint_id:
                    return checkpoint
        
        # Try to load from storage backend
        if self.storage_backend:
            return await self._load_checkpoint(checkpoint_id)
        
        return None
    
    def add_checkpoint_callback(self, callback: Callable):
        """Add a callback for checkpoint events."""
        self.checkpoint_callbacks.append(callback)
    
    def remove_checkpoint_callback(self, callback: Callable):
        """Remove a checkpoint callback."""
        if callback in self.checkpoint_callbacks:
            self.checkpoint_callbacks.remove(callback)
    
    async def _auto_checkpoint_loop(self):
        """Background task for automatic checkpointing."""
        while True:
            try:
                await asyncio.sleep(self.auto_checkpoint_interval.total_seconds())
                await self._perform_auto_checkpoint()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto checkpoint loop: {e}")
    
    async def _perform_auto_checkpoint(self):
        """Perform automatic checkpointing of active tasks."""
        if not self.active_tasks:
            return
        
        active_task_ids = list(self.active_tasks.keys())
        
        # Only checkpoint tasks that have been modified recently
        recent_tasks = []
        cutoff_time = datetime.utcnow() - timedelta(minutes=1)
        
        for task_id in active_task_ids:
            task_state = self.active_tasks[task_id]
            last_modified = task_state.metadata.get("last_modified")
            if last_modified:
                try:
                    modified_time = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    if modified_time > cutoff_time:
                        recent_tasks.append(task_id)
                except ValueError:
                    # If we can't parse the timestamp, include the task
                    recent_tasks.append(task_id)
        
        if recent_tasks:
            await self.create_checkpoint(
                task_ids=recent_tasks,
                checkpoint_type=CheckpointType.AUTOMATIC,
                checkpoint_name=f"auto_checkpoint_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )
    
    def _calculate_checksum(self, task_states: Dict[str, TaskState], context_snapshot: Dict[str, Any]) -> str:
        """Calculate checksum for checkpoint data."""
        data = {
            "task_states": {tid: asdict(ts) for tid, ts in task_states.items()},
            "context_snapshot": context_snapshot
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def _cleanup_checkpoint(self, checkpoint: Checkpoint):
        """Clean up an old checkpoint."""
        if self.storage_backend and hasattr(self.storage_backend, 'delete_checkpoint'):
            await self.storage_backend.delete_checkpoint(checkpoint.checkpoint_id)
    
    async def _persist_checkpoint(self, checkpoint: Checkpoint):
        """Persist checkpoint to storage backend."""
        if self.storage_backend and hasattr(self.storage_backend, 'store_task_checkpoint'):
            await self.storage_backend.store_task_checkpoint(checkpoint)
    
    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from storage backend."""
        if self.storage_backend and hasattr(self.storage_backend, 'load_task_checkpoint'):
            return await self.storage_backend.load_task_checkpoint(checkpoint_id)
        return None


class TaskCheckpointStorage:
    """
    Storage backend for task checkpoints.
    
    This class provides persistence for task checkpoints using the Cerebral database.
    """
    
    def __init__(self, db_client: Any):
        """
        Initialize the storage backend.
        
        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client
    
    async def store_task_checkpoint(self, checkpoint: Checkpoint):
        """Store task checkpoint to database."""
        try:
            checkpoint_data = {
                "checkpoint_id": checkpoint.checkpoint_id,
                "session_id": checkpoint.session_id,
                "persona_id": checkpoint.persona_id,
                "checkpoint_type": checkpoint.checkpoint_type.value,
                "scope": checkpoint.scope.value,
                "checkpoint_name": checkpoint.checkpoint_name,
                "timestamp": checkpoint.timestamp.isoformat(),
                "task_states": json.dumps({tid: asdict(ts) for tid, ts in checkpoint.task_states.items()}, default=str),
                "context_snapshot": json.dumps(checkpoint.context_snapshot),
                "dependencies": json.dumps(checkpoint.dependencies),
                "metadata": json.dumps(checkpoint.metadata),
                "checksum": checkpoint.checksum
            }
            
            await self.db_client.execute(
                """
                INSERT INTO bmad_task_checkpoints (
                    checkpoint_id, session_id, persona_id, checkpoint_type, scope,
                    checkpoint_name, timestamp, task_states, context_snapshot,
                    dependencies, metadata, checksum
                ) VALUES (
                    :checkpoint_id, :session_id, :persona_id, :checkpoint_type, :scope,
                    :checkpoint_name, :timestamp, :task_states, :context_snapshot,
                    :dependencies, :metadata, :checksum
                ) ON CONFLICT (checkpoint_id) DO UPDATE SET
                    task_states = EXCLUDED.task_states,
                    context_snapshot = EXCLUDED.context_snapshot,
                    metadata = EXCLUDED.metadata,
                    checksum = EXCLUDED.checksum
                """,
                checkpoint_data
            )
            
            logger.info(f"Stored task checkpoint {checkpoint.checkpoint_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to store task checkpoint: {e}")
            raise
    
    async def load_task_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load task checkpoint from database."""
        try:
            result = await self.db_client.execute(
                """
                SELECT * FROM bmad_task_checkpoints
                WHERE checkpoint_id = :checkpoint_id
                """,
                {"checkpoint_id": checkpoint_id}
            )
            
            if result:
                row = result[0]
                
                # Reconstruct task states
                task_states_data = json.loads(row["task_states"])
                task_states = {}
                for tid, ts_data in task_states_data.items():
                    task_states[tid] = TaskState(**ts_data)
                
                # Reconstruct checkpoint
                checkpoint = Checkpoint(
                    checkpoint_id=row["checkpoint_id"],
                    session_id=row["session_id"],
                    persona_id=row["persona_id"],
                    checkpoint_type=CheckpointType(row["checkpoint_type"]),
                    scope=CheckpointScope(row["scope"]),
                    checkpoint_name=row["checkpoint_name"],
                    timestamp=datetime.fromisoformat(row["timestamp"].replace('Z', '+00:00')),
                    task_states=task_states,
                    context_snapshot=json.loads(row["context_snapshot"]),
                    dependencies=json.loads(row["dependencies"]),
                    metadata=json.loads(row["metadata"]),
                    checksum=row["checksum"]
                )
                
                return checkpoint
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load task checkpoint {checkpoint_id}: {e}")
            return None
    
    async def delete_checkpoint(self, checkpoint_id: str):
        """Delete checkpoint from database."""
        try:
            await self.db_client.execute(
                """
                DELETE FROM bmad_task_checkpoints
                WHERE checkpoint_id = :checkpoint_id
                """,
                {"checkpoint_id": checkpoint_id}
            )
            
            logger.info(f"Deleted task checkpoint {checkpoint_id} from database")
            
        except Exception as e:
            logger.error(f"Failed to delete task checkpoint {checkpoint_id}: {e}")
            raise
