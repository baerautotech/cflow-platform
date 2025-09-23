"""
BMAD Session Lifecycle Management System

This module implements session lifecycle management for Phase 2:
Unified Persona Activation. It handles session creation, maintenance,
cleanup, and resource management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

from .bmad_persona_context import BMADPersonaContextManager, PersonaType, SessionState

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Enumeration of session statuses."""
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionEvent(Enum):
    """Enumeration of session events."""
    CREATED = "created"
    ACTIVATED = "activated"
    PERSONA_SWITCHED = "persona_switched"
    CHECKPOINTED = "checkpointed"
    RESTORED = "restored"
    IDLE = "idle"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class SessionMetrics:
    """Session performance and usage metrics."""
    session_id: str
    total_duration: timedelta
    persona_switches: int
    checkpoints_created: int
    context_restores: int
    idle_time: timedelta
    last_activity: datetime
    resource_usage: Dict[str, Any]


class BMADSessionManager:
    """
    Manages the lifecycle of BMAD sessions.
    
    This class handles session creation, maintenance, cleanup, and resource
    management for the BMAD persona context system.
    """
    
    def __init__(self, 
                 context_manager: BMADPersonaContextManager,
                 session_timeout: int = 3600,  # 1 hour
                 idle_timeout: int = 900,      # 15 minutes
                 max_sessions_per_user: int = 10,
                 cleanup_interval: int = 300):  # 5 minutes
        """
        Initialize the session manager.
        
        Args:
            context_manager: Persona context manager instance
            session_timeout: Maximum session duration in seconds
            idle_timeout: Maximum idle time before suspension in seconds
            max_sessions_per_user: Maximum concurrent sessions per user
            cleanup_interval: Cleanup interval in seconds
        """
        self.context_manager = context_manager
        self.session_timeout = timedelta(seconds=session_timeout)
        self.idle_timeout = timedelta(seconds=idle_timeout)
        self.max_sessions_per_user = max_sessions_per_user
        self.cleanup_interval = cleanup_interval
        
        # Session tracking
        self.active_sessions: Dict[str, SessionState] = {}
        self.session_metrics: Dict[str, SessionMetrics] = {}
        self.event_handlers: Dict[SessionEvent, List[Callable]] = {
            event: [] for event in SessionEvent
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the session manager background tasks."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        if self._metrics_task is None or self._metrics_task.done():
            self._metrics_task = asyncio.create_task(self._metrics_loop())
        
        logger.info("BMAD Session Manager started")
    
    async def stop(self):
        """Stop the session manager background tasks."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_task and not self._metrics_task.done():
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        
        logger.info("BMAD Session Manager stopped")
    
    async def create_session(self, 
                           user_id: str, 
                           project_id: str, 
                           initial_persona: PersonaType = PersonaType.ORCHESTRATOR) -> str:
        """
        Create a new session with lifecycle management.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            initial_persona: Initial persona to activate
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If user has reached maximum session limit
        """
        # Check session limits
        user_sessions = await self._get_user_sessions(user_id)
        if len(user_sessions) >= self.max_sessions_per_user:
            # Terminate oldest session
            oldest_session = min(user_sessions.values(), key=lambda s: s.created_at)
            await self.terminate_session(oldest_session.session_id, "session_limit_reached")
        
        # Create new session
        session_id = await self.context_manager.create_session(user_id, project_id, initial_persona)
        session = self.context_manager.active_sessions[session_id]
        
        # Initialize metrics
        self.session_metrics[session_id] = SessionMetrics(
            session_id=session_id,
            total_duration=timedelta(0),
            persona_switches=0,
            checkpoints_created=0,
            context_restores=0,
            idle_time=timedelta(0),
            last_activity=datetime.utcnow(),
            resource_usage={}
        )
        
        # Emit event
        await self._emit_event(SessionEvent.CREATED, {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "initial_persona": initial_persona.value
        })
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def switch_persona(self, 
                           session_id: str, 
                           target_persona: PersonaType, 
                           context_preservation: bool = True) -> Dict[str, Any]:
        """
        Switch persona with session lifecycle tracking.
        
        Args:
            session_id: Session identifier
            target_persona: Target persona to switch to
            context_preservation: Whether to preserve context
            
        Returns:
            Switch result
        """
        # Perform persona switch
        result = await self.context_manager.switch_persona(
            session_id, target_persona, context_preservation
        )
        
        # Update metrics
        if session_id in self.session_metrics:
            self.session_metrics[session_id].persona_switches += 1
            self.session_metrics[session_id].last_activity = datetime.utcnow()
        
        # Emit event
        await self._emit_event(SessionEvent.PERSONA_SWITCHED, {
            "session_id": session_id,
            "target_persona": target_persona.value,
            "context_preserved": context_preservation
        })
        
        return result
    
    async def checkpoint_session(self, 
                               session_id: str, 
                               checkpoint_name: Optional[str] = None) -> str:
        """
        Create a checkpoint with session tracking.
        
        Args:
            session_id: Session identifier
            checkpoint_name: Optional checkpoint name
            
        Returns:
            Checkpoint ID
        """
        # Create checkpoint
        checkpoint_id = await self.context_manager.checkpoint_context(session_id, checkpoint_name)
        
        # Update metrics
        if session_id in self.session_metrics:
            self.session_metrics[session_id].checkpoints_created += 1
        
        # Emit event
        await self._emit_event(SessionEvent.CHECKPOINTED, {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint_name
        })
        
        return checkpoint_id
    
    async def restore_session(self, 
                            session_id: str, 
                            checkpoint_id: str) -> Dict[str, Any]:
        """
        Restore session from checkpoint.
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
            
        Returns:
            Restore result
        """
        # Restore context
        result = await self.context_manager.restore_context(session_id, checkpoint_id)
        
        # Update metrics
        if session_id in self.session_metrics:
            self.session_metrics[session_id].context_restores += 1
            self.session_metrics[session_id].last_activity = datetime.utcnow()
        
        # Emit event
        await self._emit_event(SessionEvent.RESTORED, {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id
        })
        
        return result
    
    async def suspend_session(self, session_id: str, reason: str = "user_requested") -> bool:
        """
        Suspend a session.
        
        Args:
            session_id: Session identifier
            reason: Reason for suspension
            
        Returns:
            True if suspended successfully
        """
        if session_id not in self.context_manager.active_sessions:
            return False
        
        session = self.context_manager.active_sessions[session_id]
        
        # Suspend all personas in session
        for persona in session.personas.values():
            if persona.state.value == "active":
                persona.state.value = "suspended"
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        
        # Emit event
        await self._emit_event(SessionEvent.SUSPENDED, {
            "session_id": session_id,
            "reason": reason
        })
        
        logger.info(f"Suspended session {session_id}: {reason}")
        return True
    
    async def resume_session(self, session_id: str) -> bool:
        """
        Resume a suspended session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if resumed successfully
        """
        if session_id not in self.context_manager.active_sessions:
            return False
        
        session = self.context_manager.active_sessions[session_id]
        
        # Resume active persona
        if session.active_persona_id in session.personas:
            persona = session.personas[session.active_persona_id]
            persona.state.value = "active"
            persona.last_accessed = datetime.utcnow()
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        
        # Update metrics
        if session_id in self.session_metrics:
            self.session_metrics[session_id].last_activity = datetime.utcnow()
        
        # Emit event
        await self._emit_event(SessionEvent.ACTIVATED, {
            "session_id": session_id
        })
        
        logger.info(f"Resumed session {session_id}")
        return True
    
    async def terminate_session(self, session_id: str, reason: str = "user_requested") -> bool:
        """
        Terminate a session permanently.
        
        Args:
            session_id: Session identifier
            reason: Reason for termination
            
        Returns:
            True if terminated successfully
        """
        if session_id not in self.context_manager.active_sessions:
            return False
        
        session = self.context_manager.active_sessions[session_id]
        
        # Archive all personas
        for persona in session.personas.values():
            persona.state.value = "archived"
        
        # Remove from active sessions
        del self.context_manager.active_sessions[session_id]
        
        # Clean up metrics
        if session_id in self.session_metrics:
            del self.session_metrics[session_id]
        
        # Emit event
        await self._emit_event(SessionEvent.TERMINATED, {
            "session_id": session_id,
            "reason": reason
        })
        
        logger.info(f"Terminated session {session_id}: {reason}")
        return True
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive session status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        # Get basic status from context manager
        status = await self.context_manager.get_session_status(session_id)
        
        # Add lifecycle information
        if session_id in self.session_metrics:
            metrics = self.session_metrics[session_id]
            status["metrics"] = {
                "total_duration": str(metrics.total_duration),
                "persona_switches": metrics.persona_switches,
                "checkpoints_created": metrics.checkpoints_created,
                "context_restores": metrics.context_restores,
                "idle_time": str(metrics.idle_time),
                "last_activity": metrics.last_activity.isoformat(),
                "resource_usage": metrics.resource_usage
            }
        
        # Add lifecycle status
        status["lifecycle_status"] = await self._get_session_lifecycle_status(session_id)
        
        return status
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session information
        """
        user_sessions = await self._get_user_sessions(user_id)
        return [
            await self.get_session_status(session_id)
            for session_id in user_sessions.keys()
        ]
    
    def add_event_handler(self, event: SessionEvent, handler: Callable):
        """Add an event handler for session events."""
        self.event_handlers[event].append(handler)
    
    def remove_event_handler(self, event: SessionEvent, handler: Callable):
        """Remove an event handler."""
        if handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)
    
    async def _cleanup_loop(self):
        """Background task for session cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _metrics_loop(self):
        """Background task for metrics collection."""
        while True:
            try:
                await asyncio.sleep(60)  # Update metrics every minute
                await self._update_session_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired and idle sessions."""
        now = datetime.utcnow()
        expired_sessions = []
        idle_sessions = []
        
        for session_id, session in self.context_manager.active_sessions.items():
            # Check for expired sessions
            if now - session.created_at > self.session_timeout:
                expired_sessions.append(session_id)
            # Check for idle sessions
            elif now - session.last_activity > self.idle_timeout:
                idle_sessions.append(session_id)
        
        # Suspend idle sessions
        for session_id in idle_sessions:
            await self.suspend_session(session_id, "idle_timeout")
            await self._emit_event(SessionEvent.IDLE, {"session_id": session_id})
        
        # Terminate expired sessions
        for session_id in expired_sessions:
            await self.terminate_session(session_id, "session_timeout")
            await self._emit_event(SessionEvent.EXPIRED, {"session_id": session_id})
        
        if expired_sessions or idle_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired and {len(idle_sessions)} idle sessions")
    
    async def _update_session_metrics(self):
        """Update session metrics."""
        now = datetime.utcnow()
        
        for session_id, metrics in self.session_metrics.items():
            if session_id in self.context_manager.active_sessions:
                session = self.context_manager.active_sessions[session_id]
                
                # Update duration
                metrics.total_duration = now - session.created_at
                
                # Update idle time
                if session.last_activity < now - timedelta(minutes=1):
                    metrics.idle_time += timedelta(minutes=1)
                
                # Update resource usage (placeholder for future implementation)
                metrics.resource_usage = {
                    "memory_usage": 0,  # Placeholder
                    "cpu_usage": 0,     # Placeholder
                    "api_calls": 0      # Placeholder
                }
    
    async def _get_user_sessions(self, user_id: str) -> Dict[str, SessionState]:
        """Get all sessions for a user."""
        return {
            session_id: session
            for session_id, session in self.context_manager.active_sessions.items()
            if session.user_id == user_id
        }
    
    async def _get_session_lifecycle_status(self, session_id: str) -> str:
        """Get the lifecycle status of a session."""
        if session_id not in self.context_manager.active_sessions:
            return SessionStatus.TERMINATED.value
        
        session = self.context_manager.active_sessions[session_id]
        now = datetime.utcnow()
        
        # Check if expired
        if now - session.created_at > self.session_timeout:
            return SessionStatus.EXPIRED.value
        
        # Check if idle
        if now - session.last_activity > self.idle_timeout:
            return SessionStatus.IDLE.value
        
        # Check if suspended
        active_persona = session.personas.get(session.active_persona_id)
        if active_persona and active_persona.state.value == "suspended":
            return SessionStatus.SUSPENDED.value
        
        return SessionStatus.ACTIVE.value
    
    async def _emit_event(self, event: SessionEvent, data: Dict[str, Any]):
        """Emit a session event to registered handlers."""
        for handler in self.event_handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, data)
                else:
                    handler(event, data)
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")


class SessionEventHandler:
    """
    Base class for session event handlers.
    
    This class provides a foundation for implementing custom session
    event handlers for monitoring, logging, and other purposes.
    """
    
    async def handle_session_created(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session creation events."""
        pass
    
    async def handle_session_activated(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session activation events."""
        pass
    
    async def handle_persona_switched(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle persona switch events."""
        pass
    
    async def handle_session_checkpointed(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session checkpoint events."""
        pass
    
    async def handle_session_restored(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session restore events."""
        pass
    
    async def handle_session_idle(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session idle events."""
        pass
    
    async def handle_session_suspended(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session suspension events."""
        pass
    
    async def handle_session_expired(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session expiration events."""
        pass
    
    async def handle_session_terminated(self, event: SessionEvent, data: Dict[str, Any]):
        """Handle session termination events."""
        pass
    
    async def __call__(self, event: SessionEvent, data: Dict[str, Any]):
        """Route events to appropriate handlers."""
        handler_map = {
            SessionEvent.CREATED: self.handle_session_created,
            SessionEvent.ACTIVATED: self.handle_session_activated,
            SessionEvent.PERSONA_SWITCHED: self.handle_persona_switched,
            SessionEvent.CHECKPOINTED: self.handle_session_checkpointed,
            SessionEvent.RESTORED: self.handle_session_restored,
            SessionEvent.IDLE: self.handle_session_idle,
            SessionEvent.SUSPENDED: self.handle_session_suspended,
            SessionEvent.EXPIRED: self.handle_session_expired,
            SessionEvent.TERMINATED: self.handle_session_terminated,
        }
        
        handler = handler_map.get(event)
        if handler:
            await handler(event, data)
