"""
BMAD Persona Context Management System

This module implements the context preservation mechanisms for Phase 2:
Unified Persona Activation. It provides seamless switching between BMAD
personas while maintaining context and session state.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    """Enumeration of available BMAD persona types."""
    ORCHESTRATOR = "bmad-orchestrator"
    PROJECT_MANAGER = "pm"
    ARCHITECT = "arch"
    DEVELOPER = "dev"
    SCRUM_MASTER = "sm"
    ANALYST = "analyst"
    UX_EXPERT = "ux"
    TESTER = "tester"
    MASTER = "bmad-master"


class ContextState(Enum):
    """Enumeration of context states."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CHECKPOINTED = "checkpointed"
    ARCHIVED = "archived"


@dataclass
class PersonaContext:
    """Represents the context state of a BMAD persona."""
    persona_id: str
    persona_type: PersonaType
    session_id: str
    user_id: str
    project_id: str
    state: ContextState
    created_at: datetime
    last_accessed: datetime
    context_data: Dict[str, Any]
    checkpoint_data: Optional[Dict[str, Any]] = None
    parent_context_id: Optional[str] = None
    child_contexts: List[str] = None
    
    def __post_init__(self):
        if self.child_contexts is None:
            self.child_contexts = []


@dataclass
class SessionState:
    """Represents the overall session state across all personas."""
    session_id: str
    user_id: str
    project_id: str
    active_persona_id: str
    created_at: datetime
    last_activity: datetime
    personas: Dict[str, PersonaContext]
    global_context: Dict[str, Any]
    workflow_state: Optional[Dict[str, Any]] = None


class BMADPersonaContextManager:
    """
    Manages context preservation and persona switching for BMAD.
    
    This class implements the core functionality for Phase 2: Unified Persona Activation,
    providing seamless switching between personas while maintaining context continuity.
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize the persona context manager.
        
        Args:
            storage_backend: Optional storage backend for persistence
        """
        self.storage_backend = storage_backend
        self.active_sessions: Dict[str, SessionState] = {}
        self.persona_definitions: Dict[PersonaType, Dict[str, Any]] = {}
        self._load_persona_definitions()
        
    def _load_persona_definitions(self):
        """Load persona definitions from BMAD core agents."""
        try:
            vendor_bmad_path = Path(__file__).parent.parent.parent / "vendor" / "bmad"
            agents_path = vendor_bmad_path / "bmad-core" / "agents"
            
            if not agents_path.exists():
                logger.warning(f"BMAD agents path not found: {agents_path}")
                return
                
            # Load core persona definitions
            persona_files = {
                PersonaType.ORCHESTRATOR: "bmad-orchestrator.md",
                PersonaType.PROJECT_MANAGER: "pm.md",
                PersonaType.ARCHITECT: "arch.md",
                PersonaType.DEVELOPER: "dev.md",
                PersonaType.SCRUM_MASTER: "sm.md",
                PersonaType.ANALYST: "analyst.md",
                PersonaType.MASTER: "bmad-master.md"
            }
            
            for persona_type, filename in persona_files.items():
                persona_file = agents_path / filename
                if persona_file.exists():
                    with open(persona_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract YAML configuration from markdown
                        yaml_start = content.find('```yaml')
                        if yaml_start != -1:
                            yaml_start += 7  # Skip ```yaml
                            yaml_end = content.find('```', yaml_start)
                            if yaml_end != -1:
                                yaml_content = content[yaml_start:yaml_end].strip()
                                try:
                                    persona_config = yaml.safe_load(yaml_content)
                                    self.persona_definitions[persona_type] = persona_config
                                    logger.info(f"Loaded persona definition: {persona_type.value}")
                                except yaml.YAMLError as e:
                                    logger.error(f"Failed to parse YAML for {persona_type.value}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load persona definitions: {e}")
    
    async def create_session(self, user_id: str, project_id: str, initial_persona: PersonaType = PersonaType.ORCHESTRATOR) -> str:
        """
        Create a new session with initial persona.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            initial_persona: Initial persona to activate
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create initial persona context
        persona_context = PersonaContext(
            persona_id=str(uuid.uuid4()),
            persona_type=initial_persona,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            state=ContextState.ACTIVE,
            created_at=now,
            last_accessed=now,
            context_data=self._initialize_persona_context(initial_persona)
        )
        
        # Create session state
        session_state = SessionState(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            active_persona_id=persona_context.persona_id,
            created_at=now,
            last_activity=now,
            personas={persona_context.persona_id: persona_context},
            global_context=self._initialize_global_context(user_id, project_id)
        )
        
        self.active_sessions[session_id] = session_state
        
        # Persist to storage backend if available
        if self.storage_backend:
            await self._persist_session(session_state)
        
        logger.info(f"Created session {session_id} with initial persona {initial_persona.value}")
        return session_id
    
    async def switch_persona(self, session_id: str, target_persona: PersonaType, context_preservation: bool = True) -> Dict[str, Any]:
        """
        Switch to a different persona while preserving context.
        
        Args:
            session_id: Session identifier
            target_persona: Target persona to switch to
            context_preservation: Whether to preserve context from current persona
            
        Returns:
            Switch result with new persona context
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        current_persona = session.personas[session.active_persona_id]
        
        # Check if target persona already exists in session
        existing_persona = None
        for persona in session.personas.values():
            if persona.persona_type == target_persona:
                existing_persona = persona
                break
        
        if existing_persona:
            # Resume existing persona
            await self._resume_persona(session, existing_persona, context_preservation)
            result_persona = existing_persona
        else:
            # Create new persona context
            result_persona = await self._create_new_persona(session, target_persona, context_preservation)
        
        # Update session state
        session.active_persona_id = result_persona.persona_id
        session.last_activity = datetime.utcnow()
        
        # Persist changes
        if self.storage_backend:
            await self._persist_session(session)
        
        logger.info(f"Switched to persona {target_persona.value} in session {session_id}")
        
        return {
            "session_id": session_id,
            "active_persona_id": result_persona.persona_id,
            "persona_type": result_persona.persona_type.value,
            "context_data": result_persona.context_data,
            "switch_successful": True
        }
    
    async def checkpoint_context(self, session_id: str, checkpoint_name: Optional[str] = None) -> str:
        """
        Create a checkpoint of the current context state.
        
        Args:
            session_id: Session identifier
            checkpoint_name: Optional name for the checkpoint
            
        Returns:
            Checkpoint ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        current_persona = session.personas[session.active_persona_id]
        
        checkpoint_id = checkpoint_name or str(uuid.uuid4())
        
        # Create checkpoint data
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "session_state": asdict(session),
            "active_persona_context": asdict(current_persona),
            "global_context": session.global_context
        }
        
        # Store checkpoint in current persona
        current_persona.checkpoint_data = checkpoint_data
        current_persona.state = ContextState.CHECKPOINTED
        
        # Persist checkpoint
        if self.storage_backend:
            await self._persist_checkpoint(session_id, checkpoint_data)
        
        logger.info(f"Created checkpoint {checkpoint_id} for session {session_id}")
        return checkpoint_id
    
    async def restore_context(self, session_id: str, checkpoint_id: str) -> Dict[str, Any]:
        """
        Restore context from a checkpoint.
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
            
        Returns:
            Restore result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Find checkpoint data
        checkpoint_data = None
        for persona in session.personas.values():
            if persona.checkpoint_data and persona.checkpoint_data.get("checkpoint_id") == checkpoint_id:
                checkpoint_data = persona.checkpoint_data
                break
        
        if not checkpoint_data:
            # Try to load from storage backend
            if self.storage_backend:
                checkpoint_data = await self._load_checkpoint(session_id, checkpoint_id)
        
        if not checkpoint_data:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # Restore session state
        restored_session_data = checkpoint_data["session_state"]
        restored_persona_data = checkpoint_data["active_persona_context"]
        
        # Reconstruct session state
        session.active_persona_id = restored_persona_data["persona_id"]
        session.last_activity = datetime.utcnow()
        session.global_context = checkpoint_data["global_context"]
        
        # Update persona context
        if session.active_persona_id in session.personas:
            persona = session.personas[session.active_persona_id]
            persona.context_data = restored_persona_data["context_data"]
            persona.state = ContextState.ACTIVE
            persona.last_accessed = datetime.utcnow()
        
        # Persist restored state
        if self.storage_backend:
            await self._persist_session(session)
        
        logger.info(f"Restored context from checkpoint {checkpoint_id} in session {session_id}")
        
        return {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "restore_successful": True,
            "active_persona_id": session.active_persona_id
        }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session status and context information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        active_persona = session.personas[session.active_persona_id]
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "project_id": session.project_id,
            "active_persona": {
                "id": active_persona.persona_id,
                "type": active_persona.persona_type.value,
                "state": active_persona.state.value,
                "last_accessed": active_persona.last_accessed.isoformat()
            },
            "available_personas": [
                {
                    "type": persona.persona_type.value,
                    "state": persona.state.value,
                    "last_accessed": persona.last_accessed.isoformat()
                }
                for persona in session.personas.values()
            ],
            "session_created": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "global_context_keys": list(session.global_context.keys()),
            "has_checkpoint": active_persona.checkpoint_data is not None
        }
    
    def _initialize_persona_context(self, persona_type: PersonaType) -> Dict[str, Any]:
        """Initialize context data for a persona."""
        base_context = {
            "persona_type": persona_type.value,
            "activation_time": datetime.utcnow().isoformat(),
            "conversation_history": [],
            "current_task": None,
            "workflow_state": {},
            "user_preferences": {},
            "project_context": {}
        }
        
        # Add persona-specific context based on definitions
        if persona_type in self.persona_definitions:
            persona_def = self.persona_definitions[persona_type]
            if "agent" in persona_def:
                base_context["agent_config"] = persona_def["agent"]
            if "persona" in persona_def:
                base_context["persona_config"] = persona_def["persona"]
        
        return base_context
    
    def _initialize_global_context(self, user_id: str, project_id: str) -> Dict[str, Any]:
        """Initialize global session context."""
        return {
            "user_id": user_id,
            "project_id": project_id,
            "session_start": datetime.utcnow().isoformat(),
            "project_metadata": {},
            "shared_artifacts": {},
            "workflow_history": [],
            "cross_persona_notes": []
        }
    
    async def _resume_persona(self, session: SessionState, persona: PersonaContext, context_preservation: bool):
        """Resume an existing persona context."""
        persona.state = ContextState.ACTIVE
        persona.last_accessed = datetime.utcnow()
        
        if context_preservation:
            # Merge any global context updates
            if "cross_persona_notes" in session.global_context:
                if "cross_persona_notes" not in persona.context_data:
                    persona.context_data["cross_persona_notes"] = []
                persona.context_data["cross_persona_notes"].extend(
                    session.global_context["cross_persona_notes"]
                )
                session.global_context["cross_persona_notes"] = []
    
    async def _create_new_persona(self, session: SessionState, persona_type: PersonaType, context_preservation: bool) -> PersonaContext:
        """Create a new persona context."""
        persona_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Initialize context
        context_data = self._initialize_persona_context(persona_type)
        
        # Preserve relevant context if requested
        if context_preservation and session.personas:
            # Get context from most recent persona
            latest_persona = max(session.personas.values(), key=lambda p: p.last_accessed)
            
            # Preserve shared context elements
            preserve_keys = ["project_context", "user_preferences", "shared_artifacts"]
            for key in preserve_keys:
                if key in latest_persona.context_data:
                    context_data[key] = latest_persona.context_data[key]
        
        persona = PersonaContext(
            persona_id=persona_id,
            persona_type=persona_type,
            session_id=session.session_id,
            user_id=session.user_id,
            project_id=session.project_id,
            state=ContextState.ACTIVE,
            created_at=now,
            last_accessed=now,
            context_data=context_data
        )
        
        session.personas[persona_id] = persona
        return persona
    
    async def _persist_session(self, session: SessionState):
        """Persist session state to storage backend."""
        if self.storage_backend and hasattr(self.storage_backend, 'store_session'):
            await self.storage_backend.store_session(session)
    
    async def _persist_checkpoint(self, session_id: str, checkpoint_data: Dict[str, Any]):
        """Persist checkpoint to storage backend."""
        if self.storage_backend and hasattr(self.storage_backend, 'store_checkpoint'):
            await self.storage_backend.store_checkpoint(session_id, checkpoint_data)
    
    async def _load_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint from storage backend."""
        if self.storage_backend and hasattr(self.storage_backend, 'load_checkpoint'):
            return await self.storage_backend.load_checkpoint(session_id, checkpoint_id)
        return None


class BMADPersonaContextStorage:
    """
    Storage backend for BMAD persona contexts.
    
    This class provides persistence for persona contexts using the Cerebral database.
    """
    
    def __init__(self, db_client: Any):
        """
        Initialize the storage backend.
        
        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client
    
    async def store_session(self, session: SessionState):
        """Store session state to database."""
        try:
            # Store session metadata
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "project_id": session.project_id,
                "active_persona_id": session.active_persona_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "global_context": json.dumps(session.global_context),
                "workflow_state": json.dumps(session.workflow_state) if session.workflow_state else None
            }
            
            # Store persona contexts
            for persona in session.personas.values():
                persona_data = {
                    "persona_id": persona.persona_id,
                    "session_id": session.session_id,
                    "persona_type": persona.persona_type.value,
                    "state": persona.state.value,
                    "created_at": persona.created_at.isoformat(),
                    "last_accessed": persona.last_accessed.isoformat(),
                    "context_data": json.dumps(persona.context_data),
                    "checkpoint_data": json.dumps(persona.checkpoint_data) if persona.checkpoint_data else None,
                    "parent_context_id": persona.parent_context_id,
                    "child_contexts": json.dumps(persona.child_contexts)
                }
                
                # Insert or update persona context
                await self.db_client.execute(
                    """
                    INSERT INTO bmad_persona_contexts (
                        persona_id, session_id, persona_type, state, created_at, 
                        last_accessed, context_data, checkpoint_data, parent_context_id, child_contexts
                    ) VALUES (
                        :persona_id, :session_id, :persona_type, :state, :created_at,
                        :last_accessed, :context_data, :checkpoint_data, :parent_context_id, :child_contexts
                    ) ON CONFLICT (persona_id) DO UPDATE SET
                        state = EXCLUDED.state,
                        last_accessed = EXCLUDED.last_accessed,
                        context_data = EXCLUDED.context_data,
                        checkpoint_data = EXCLUDED.checkpoint_data
                    """,
                    persona_data
                )
            
            logger.info(f"Stored session {session.session_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")
            raise
    
    async def store_checkpoint(self, session_id: str, checkpoint_data: Dict[str, Any]):
        """Store checkpoint to database."""
        try:
            checkpoint_record = {
                "checkpoint_id": checkpoint_data["checkpoint_id"],
                "session_id": session_id,
                "timestamp": checkpoint_data["timestamp"],
                "checkpoint_data": json.dumps(checkpoint_data)
            }
            
            await self.db_client.execute(
                """
                INSERT INTO bmad_checkpoints (
                    checkpoint_id, session_id, timestamp, checkpoint_data
                ) VALUES (
                    :checkpoint_id, :session_id, :timestamp, :checkpoint_data
                ) ON CONFLICT (checkpoint_id) DO UPDATE SET
                    checkpoint_data = EXCLUDED.checkpoint_data
                """,
                checkpoint_record
            )
            
            logger.info(f"Stored checkpoint {checkpoint_data['checkpoint_id']} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store checkpoint: {e}")
            raise
    
    async def load_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint from database."""
        try:
            result = await self.db_client.execute(
                """
                SELECT checkpoint_data FROM bmad_checkpoints
                WHERE checkpoint_id = :checkpoint_id AND session_id = :session_id
                """,
                {"checkpoint_id": checkpoint_id, "session_id": session_id}
            )
            
            if result:
                return json.loads(result[0]["checkpoint_data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
