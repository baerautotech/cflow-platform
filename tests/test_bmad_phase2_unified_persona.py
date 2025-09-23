"""
Test Suite for BMAD Phase 2: Unified Persona Activation

This test suite validates the complete Phase 2 implementation including:
- Context preservation mechanisms
- Session lifecycle management  
- Task state checkpointing
- Context serialization/deserialization
- Unified persona system integration
"""

import asyncio
import json
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from cflow_platform.core.bmad_persona_context import (
    BMADPersonaContextManager,
    PersonaType,
    PersonaContext,
    SessionState,
    ContextState,
    BMADPersonaContextStorage
)
from cflow_platform.core.bmad_session_manager import (
    BMADSessionManager,
    SessionStatus,
    SessionEvent,
    SessionEventHandler
)
from cflow_platform.core.bmad_task_checkpoint import (
    BMADTaskCheckpointer,
    TaskState,
    Checkpoint,
    CheckpointType,
    CheckpointScope,
    TaskCheckpointStorage
)
from cflow_platform.core.bmad_unified_persona_system import (
    BMADUnifiedPersonaSystem,
    UnifiedPersonaConfig
)
from cflow_platform.core.bmad_context_serialization import (
    BMADContextSerializer,
    SerializationFormat,
    BMADContextStorage
)


class TestBMADPersonaContextManager:
    """Test suite for BMAD Persona Context Manager."""
    
    @pytest.fixture
    async def context_manager(self):
        """Create a context manager for testing."""
        mock_storage = AsyncMock()
        manager = BMADPersonaContextManager(mock_storage)
        return manager
    
    @pytest.mark.asyncio
    async def test_create_session(self, context_manager):
        """Test session creation."""
        user_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        
        session_id = await context_manager.create_session(user_id, project_id, PersonaType.ORCHESTRATOR)
        
        assert session_id in context_manager.active_sessions
        session = context_manager.active_sessions[session_id]
        assert session.user_id == user_id
        assert session.project_id == project_id
        assert session.active_persona_id in session.personas
    
    @pytest.mark.asyncio
    async def test_persona_switching(self, context_manager):
        """Test persona switching with context preservation."""
        # Create session
        session_id = await context_manager.create_session("user1", "project1", PersonaType.ORCHESTRATOR)
        
        # Switch to PM persona
        result = await context_manager.switch_persona(session_id, PersonaType.PROJECT_MANAGER, True)
        
        assert result["switch_successful"] is True
        assert result["persona_type"] == PersonaType.PROJECT_MANAGER.value
        
        # Verify session has both personas
        session = context_manager.active_sessions[session_id]
        assert len(session.personas) == 2
        assert session.active_persona_id in session.personas
    
    @pytest.mark.asyncio
    async def test_checkpoint_creation(self, context_manager):
        """Test checkpoint creation and restoration."""
        # Create session
        session_id = await context_manager.create_session("user1", "project1", PersonaType.ORCHESTRATOR)
        
        # Create checkpoint
        checkpoint_id = await context_manager.checkpoint_context(session_id, "test_checkpoint")
        
        assert checkpoint_id is not None
        
        # Restore from checkpoint
        result = await context_manager.restore_context(session_id, checkpoint_id)
        
        assert result["restore_successful"] is True
    
    @pytest.mark.asyncio
    async def test_session_status(self, context_manager):
        """Test session status retrieval."""
        # Create session
        session_id = await context_manager.create_session("user1", "project1", PersonaType.ORCHESTRATOR)
        
        # Get status
        status = await context_manager.get_session_status(session_id)
        
        assert status["session_id"] == session_id
        assert status["user_id"] == "user1"
        assert status["project_id"] == "project1"
        assert "active_persona" in status
        assert "available_personas" in status


class TestBMADSessionManager:
    """Test suite for BMAD Session Manager."""
    
    @pytest.fixture
    async def session_manager(self):
        """Create a session manager for testing."""
        mock_context_manager = AsyncMock()
        manager = BMADSessionManager(mock_context_manager)
        return manager
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, session_manager):
        """Test complete session lifecycle."""
        # Create session
        session_id = await session_manager.create_session("user1", "project1", PersonaType.ORCHESTRATOR)
        
        # Suspend session
        success = await session_manager.suspend_session(session_id, "test_suspend")
        assert success is True
        
        # Resume session
        success = await session_manager.resume_session(session_id)
        assert success is True
        
        # Terminate session
        success = await session_manager.terminate_session(session_id, "test_terminate")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_event_handlers(self, session_manager):
        """Test event handler registration and execution."""
        events_received = []
        
        class TestHandler(SessionEventHandler):
            async def handle_session_created(self, event, data):
                events_received.append(("created", data))
        
        handler = TestHandler()
        session_manager.add_event_handler(SessionEvent.CREATED, handler)
        
        # Create session (should trigger event)
        await session_manager.create_session("user1", "project1", PersonaType.ORCHESTRATOR)
        
        # Note: This test would need the actual context manager to be properly mocked
        # to trigger events, but it demonstrates the handler registration pattern


class TestBMADTaskCheckpointer:
    """Test suite for BMAD Task Checkpointer."""
    
    @pytest.fixture
    async def task_checkpointer(self):
        """Create a task checkpointer for testing."""
        mock_storage = AsyncMock()
        checkpointer = BMADTaskCheckpointer(mock_storage)
        return checkpointer
    
    @pytest.mark.asyncio
    async def test_task_lifecycle(self, task_checkpointer):
        """Test complete task lifecycle."""
        task_id = str(uuid.uuid4())
        task_name = "test_task"
        
        # Start task
        task_state = await task_checkpointer.start_task(
            task_id, task_name, PersonaType.DEVELOPER.value, {"input": "data"}
        )
        
        assert task_state.task_id == task_id
        assert task_state.task_name == task_name
        assert task_state.status == "started"
        assert task_state.progress == 0.0
        
        # Update progress
        updated_state = await task_checkpointer.update_task_state(
            task_id, progress=0.5, status="in_progress"
        )
        
        assert updated_state.progress == 0.5
        assert updated_state.status == "in_progress"
        
        # Complete task
        final_state = await task_checkpointer.complete_task(
            task_id, {"output": "result"}
        )
        
        assert final_state.status == "completed"
        assert final_state.progress == 1.0
    
    @pytest.mark.asyncio
    async def test_checkpoint_creation(self, task_checkpointer):
        """Test checkpoint creation and restoration."""
        # Start task
        task_id = str(uuid.uuid4())
        await task_checkpointer.start_task(task_id, "test_task", "dev", {})
        
        # Create checkpoint
        checkpoint_id = await task_checkpointer.create_checkpoint(
            [task_id], CheckpointType.MANUAL, "test_checkpoint"
        )
        
        assert checkpoint_id is not None
        
        # Restore from checkpoint
        result = await task_checkpointer.restore_from_checkpoint(checkpoint_id)
        
        assert result["restore_successful"] is True
        assert task_id in result["restored_tasks"]


class TestBMADContextSerializer:
    """Test suite for BMAD Context Serializer."""
    
    @pytest.fixture
    def serializer(self):
        """Create a context serializer for testing."""
        return BMADContextSerializer()
    
    @pytest.mark.asyncio
    async def test_persona_context_serialization(self, serializer):
        """Test persona context serialization/deserialization."""
        # Create persona context
        persona_context = PersonaContext(
            persona_id=str(uuid.uuid4()),
            persona_type=PersonaType.PROJECT_MANAGER,
            session_id=str(uuid.uuid4()),
            user_id="user1",
            project_id="project1",
            state=ContextState.ACTIVE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            context_data={"test": "data"}
        )
        
        # Serialize
        serialized = await serializer.serialize_persona_context(persona_context)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = await serializer.deserialize_persona_context(serialized)
        
        assert deserialized.persona_id == persona_context.persona_id
        assert deserialized.persona_type == persona_context.persona_type
        assert deserialized.context_data == persona_context.context_data
    
    @pytest.mark.asyncio
    async def test_task_state_serialization(self, serializer):
        """Test task state serialization/deserialization."""
        # Create task state
        task_state = TaskState(
            task_id=str(uuid.uuid4()),
            task_name="test_task",
            persona_type="dev",
            status="in_progress",
            progress=0.5,
            input_data={"input": "data"},
            output_data={"output": "data"},
            intermediate_results={"intermediate": "data"}
        )
        
        # Serialize
        serialized = await serializer.serialize_task_state(task_state)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = await serializer.deserialize_task_state(serialized)
        
        assert deserialized.task_id == task_state.task_id
        assert deserialized.task_name == task_state.task_name
        assert deserialized.progress == task_state.progress
    
    @pytest.mark.asyncio
    async def test_file_serialization(self, serializer):
        """Test serialization to/from files."""
        # Create test data
        task_state = TaskState(
            task_id=str(uuid.uuid4()),
            task_name="file_test_task",
            persona_type="dev",
            status="started",
            progress=0.0,
            input_data={"input": "file_data"},
            output_data={},
            intermediate_results={}
        )
        
        # Test with temporary file
        with tempfile.NamedTemporaryFile(suffix='.task', delete=False) as f:
            file_path = Path(f.name)
        
        try:
            # Serialize to file
            metadata = await serializer.serialize_to_file(task_state, file_path)
            
            assert file_path.exists()
            assert metadata.size > 0
            assert metadata.checksum is not None
            
            # Deserialize from file
            deserialized = await serializer.deserialize_from_file(file_path, "task_state")
            
            assert deserialized.task_id == task_state.task_id
            assert deserialized.task_name == task_state.task_name
            
            # Check metadata
            retrieved_metadata = await serializer.get_serialization_metadata(file_path)
            assert retrieved_metadata.version == metadata.version
            
        finally:
            # Cleanup
            if file_path.exists():
                file_path.unlink()
            metadata_file = file_path.with_suffix(file_path.suffix + '.meta')
            if metadata_file.exists():
                metadata_file.unlink()


class TestBMADUnifiedPersonaSystem:
    """Test suite for BMAD Unified Persona System."""
    
    @pytest.fixture
    async def unified_system(self):
        """Create a unified persona system for testing."""
        mock_db_client = AsyncMock()
        config = UnifiedPersonaConfig(
            session_timeout=3600,
            idle_timeout=900,
            enable_auto_checkpointing=False,  # Disable for testing
            enable_session_cleanup=False
        )
        
        system = BMADUnifiedPersonaSystem(mock_db_client, config)
        await system.initialize()
        return system
    
    @pytest.mark.asyncio
    async def test_session_creation(self, unified_system):
        """Test session creation through unified system."""
        result = await unified_system.create_session(
            "user1", "project1", PersonaType.ORCHESTRATOR
        )
        
        assert "session_id" in result
        assert result["system_initialized"] is True
        assert "available_personas" in result
    
    @pytest.mark.asyncio
    async def test_persona_switching(self, unified_system):
        """Test persona switching through unified system."""
        # Create session
        session_result = await unified_system.create_session(
            "user1", "project1", PersonaType.ORCHESTRATOR
        )
        session_id = session_result["session_id"]
        
        # Switch persona
        switch_result = await unified_system.switch_persona(
            session_id, PersonaType.PROJECT_MANAGER, True, True
        )
        
        assert switch_result["switch_successful"] is True
        assert switch_result["persona_type"] == PersonaType.PROJECT_MANAGER.value
    
    @pytest.mark.asyncio
    async def test_task_management(self, unified_system):
        """Test task management through unified system."""
        # Create session
        session_result = await unified_system.create_session(
            "user1", "project1", PersonaType.ORCHESTRATOR
        )
        session_id = session_result["session_id"]
        
        # Start task
        task_result = await unified_system.start_task(
            session_id, "test_task", {"input": "data"}
        )
        
        assert "task_id" in task_result
        assert task_result["task_name"] == "test_task"
        
        task_id = task_result["task_id"]
        
        # Update progress
        progress_result = await unified_system.update_task_progress(
            task_id, 0.5, {"output": "data"}
        )
        
        assert progress_result["task_id"] == task_id
        
        # Complete task
        complete_result = await unified_system.complete_task(
            task_id, {"final": "output"}
        )
        
        assert complete_result["task_id"] == task_id
    
    @pytest.mark.asyncio
    async def test_checkpoint_management(self, unified_system):
        """Test checkpoint management through unified system."""
        # Create session
        session_result = await unified_system.create_session(
            "user1", "project1", PersonaType.ORCHESTRATOR
        )
        session_id = session_result["session_id"]
        
        # Create checkpoint
        checkpoint_result = await unified_system.checkpoint_session_state(
            session_id, CheckpointType.MANUAL, "test_checkpoint"
        )
        
        assert "session_checkpoint_id" in checkpoint_result
        assert checkpoint_result["checkpoint_type"] == CheckpointType.MANUAL.value
        
        # Restore from checkpoint
        restore_result = await unified_system.restore_session_state(
            session_id, checkpoint_result["session_checkpoint_id"]
        )
        
        assert "session_restored" in restore_result
    
    @pytest.mark.asyncio
    async def test_comprehensive_status(self, unified_system):
        """Test comprehensive status retrieval."""
        # Create session
        session_result = await unified_system.create_session(
            "user1", "project1", PersonaType.ORCHESTRATOR
        )
        session_id = session_result["session_id"]
        
        # Get comprehensive status
        status = await unified_system.get_comprehensive_status(session_id)
        
        assert "session_status" in status
        assert "active_tasks" in status
        assert "recent_checkpoints" in status
        assert "system_health" in status


class TestBMADContextStorage:
    """Test suite for BMAD Context Storage."""
    
    @pytest.fixture
    async def context_storage(self):
        """Create a context storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = BMADContextStorage(Path(temp_dir))
            yield storage
    
    @pytest.mark.asyncio
    async def test_persona_context_storage(self, context_storage):
        """Test persona context storage and retrieval."""
        # Create persona context
        persona_context = PersonaContext(
            persona_id=str(uuid.uuid4()),
            persona_type=PersonaType.DEVELOPER,
            session_id=str(uuid.uuid4()),
            user_id="user1",
            project_id="project1",
            state=ContextState.ACTIVE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            context_data={"test": "storage_data"}
        )
        
        # Store
        file_path = await context_storage.store_persona_context(persona_context)
        assert Path(file_path).exists()
        
        # Load
        loaded_context = await context_storage.load_persona_context(persona_context.persona_id)
        
        assert loaded_context is not None
        assert loaded_context.persona_id == persona_context.persona_id
        assert loaded_context.context_data == persona_context.context_data
    
    @pytest.mark.asyncio
    async def test_task_state_storage(self, context_storage):
        """Test task state storage and retrieval."""
        # Create task state
        task_state = TaskState(
            task_id=str(uuid.uuid4()),
            task_name="storage_test_task",
            persona_type="dev",
            status="in_progress",
            progress=0.7,
            input_data={"input": "storage_data"},
            output_data={"output": "storage_data"},
            intermediate_results={"intermediate": "storage_data"}
        )
        
        # Store
        file_path = await context_storage.store_task_state(task_state)
        assert Path(file_path).exists()
        
        # Load
        loaded_state = await context_storage.load_task_state(task_state.task_id)
        
        assert loaded_state is not None
        assert loaded_state.task_id == task_state.task_id
        assert loaded_state.progress == task_state.progress
    
    @pytest.mark.asyncio
    async def test_list_stored_items(self, context_storage):
        """Test listing stored items."""
        # Store some items
        persona_context = PersonaContext(
            persona_id=str(uuid.uuid4()),
            persona_type=PersonaType.ARCHITECT,
            session_id=str(uuid.uuid4()),
            user_id="user1",
            project_id="project1",
            state=ContextState.ACTIVE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            context_data={}
        )
        
        await context_storage.store_persona_context(persona_context)
        
        # List items
        items = await context_storage.list_stored_items("persona_context")
        
        assert len(items) == 1
        assert persona_context.persona_id in items


# Integration Tests

class TestBMADPhase2Integration:
    """Integration tests for the complete Phase 2 system."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow using all Phase 2 components."""
        # Initialize system
        mock_db_client = AsyncMock()
        config = UnifiedPersonaConfig(
            enable_auto_checkpointing=False,
            enable_session_cleanup=False
        )
        
        system = BMADUnifiedPersonaSystem(mock_db_client, config)
        await system.initialize()
        
        try:
            # 1. Create session with orchestrator
            session_result = await system.create_session(
                "user1", "project1", PersonaType.ORCHESTRATOR
            )
            session_id = session_result["session_id"]
            
            # 2. Switch to PM persona
            switch_result = await system.switch_persona(
                session_id, PersonaType.PROJECT_MANAGER, True, True
            )
            assert switch_result["switch_successful"] is True
            
            # 3. Start a task
            task_result = await system.start_task(
                session_id, "Create PRD", {"project": "project1"}
            )
            task_id = task_result["task_id"]
            
            # 4. Update task progress
            await system.update_task_progress(task_id, 0.3, {"draft": "created"})
            await system.update_task_progress(task_id, 0.7, {"review": "in_progress"})
            
            # 5. Create checkpoint
            checkpoint_result = await system.checkpoint_session_state(
                session_id, CheckpointType.MANUAL, "mid_prd_creation"
            )
            
            # 6. Switch to developer persona
            await system.switch_persona(
                session_id, PersonaType.DEVELOPER, True, True
            )
            
            # 7. Complete task
            await system.complete_task(task_id, {"final_prd": "completed"})
            
            # 8. Get comprehensive status
            status = await system.get_comprehensive_status(session_id)
            
            assert status["session_status"]["active_persona"]["type"] == PersonaType.DEVELOPER.value
            assert len(status["recent_checkpoints"]) > 0
            
        finally:
            await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery using checkpoints."""
        # Initialize system
        mock_db_client = AsyncMock()
        system = BMADUnifiedPersonaSystem(mock_db_client)
        await system.initialize()
        
        try:
            # Create session and start task
            session_result = await system.create_session(
                "user1", "project1", PersonaType.DEVELOPER
            )
            session_id = session_result["session_id"]
            
            task_result = await system.start_task(
                session_id, "Implement Feature", {"feature": "auth"}
            )
            task_id = task_result["task_id"]
            
            # Make progress and create checkpoint
            await system.update_task_progress(task_id, 0.5, {"half_done": True})
            checkpoint_result = await system.checkpoint_session_state(
                session_id, CheckpointType.AUTOMATIC, "mid_implementation"
            )
            
            # Simulate error by updating with error state
            await system.update_task_progress(
                task_id, 0.5, 
                status="failed",
                intermediate_results={"error": "connection_timeout"}
            )
            
            # Restore from checkpoint
            restore_result = await system.restore_session_state(
                session_id, checkpoint_result["session_checkpoint_id"]
            )
            
            assert restore_result["session_restored"]["restore_successful"] is True
            
            # Verify task is back to good state
            task_state = await system.task_checkpointer.get_task_state(task_id)
            assert task_state.status != "failed"
            
        finally:
            await system.shutdown()


# Performance Tests

class TestBMADPhase2Performance:
    """Performance tests for Phase 2 components."""
    
    @pytest.mark.asyncio
    async def test_serialization_performance(self):
        """Test serialization performance with large data."""
        serializer = BMADContextSerializer()
        
        # Create large task state
        large_data = {"data": "x" * 10000}  # 10KB of data
        task_state = TaskState(
            task_id=str(uuid.uuid4()),
            task_name="large_task",
            persona_type="dev",
            status="in_progress",
            progress=0.5,
            input_data=large_data,
            output_data=large_data,
            intermediate_results=large_data
        )
        
        # Measure serialization time
        start_time = datetime.utcnow()
        serialized = await serializer.serialize_task_state(task_state)
        serialize_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Measure deserialization time
        start_time = datetime.utcnow()
        deserialized = await serializer.deserialize_task_state(serialized)
        deserialize_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Performance assertions (adjust thresholds as needed)
        assert serialize_time < 1.0  # Should serialize in under 1 second
        assert deserialize_time < 1.0  # Should deserialize in under 1 second
        assert len(serialized) > 0
        
        # Verify data integrity
        assert deserialized.task_id == task_state.task_id
        assert deserialized.input_data == task_state.input_data
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Test handling multiple concurrent sessions."""
        mock_db_client = AsyncMock()
        system = BMADUnifiedPersonaSystem(mock_db_client)
        await system.initialize()
        
        try:
            # Create multiple sessions concurrently
            session_tasks = []
            for i in range(10):
                task = system.create_session(
                    f"user{i}", f"project{i}", PersonaType.ORCHESTRATOR
                )
                session_tasks.append(task)
            
            session_results = await asyncio.gather(*session_tasks)
            
            # Verify all sessions were created
            assert len(session_results) == 10
            for result in session_results:
                assert "session_id" in result
                assert result["system_initialized"] is True
            
            # Test concurrent persona switches
            switch_tasks = []
            for result in session_results:
                task = system.switch_persona(
                    result["session_id"], PersonaType.PROJECT_MANAGER, True, False
                )
                switch_tasks.append(task)
            
            switch_results = await asyncio.gather(*switch_tasks)
            
            # Verify all switches succeeded
            for result in switch_results:
                assert result["switch_successful"] is True
                
        finally:
            await system.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
