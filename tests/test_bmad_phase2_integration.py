#!/usr/bin/env python3
"""
BMAD Phase 2 Integration Tests

This test suite validates the Phase 2 enhancements:
- Advanced persona context management
- Session lifecycle management  
- Task state checkpointing
- Context serialization system
- Unified persona system integration

Test Categories:
1. Persona Context Management
2. Session Lifecycle Operations
3. Task Checkpointing
4. Context Serialization
5. Unified Persona System
6. API Endpoint Integration
"""

import os
import sys
import asyncio
import json
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cflow_platform.core.bmad_persona_context import PersonaContext, BMADPersonaContextManager
from cflow_platform.core.bmad_session_manager import BMADSessionManager
from cflow_platform.core.bmad_task_checkpoint import BMADTaskCheckpoint
from cflow_platform.core.bmad_context_serialization import ContextSerializer, SerializationFormat
from cflow_platform.core.bmad_unified_persona_system import BMADUnifiedPersonaSystem


class TestPersonaContextManagement:
    """Test suite for persona context management functionality."""
    
    @pytest.mark.asyncio
    async def test_persona_context_creation_and_state_management(self):
        """Test basic persona context creation and state management."""
        # Create persona context
        context = PersonaContext("test-persona", {"project": "test-project"})
        
        # Verify initial state
        assert context.persona_id == "test-persona"
        assert context.get_state("project") == "test-project"
        assert isinstance(context.context_id, str)
        assert isinstance(context.created_at, datetime)
        
        # Test state updates
        context.update_state("feature", "authentication")
        assert context.get_state("feature") == "authentication"
        
        context.update_state("priority", "high")
        assert context.get_state("priority") == "high"
        
        # Test state retrieval with default
        assert context.get_state("nonexistent", "default") == "default"
    
    @pytest.mark.asyncio
    async def test_persona_context_history_management(self):
        """Test conversational history management."""
        context = PersonaContext("test-persona")
        
        # Add history entries
        context.add_to_history({"user": "Create a login system"})
        context.add_to_history({"agent": "I'll help you create a login system"})
        context.add_to_history({"user": "What are the requirements?"})
        
        # Verify history
        history = context.get_history()
        assert len(history) == 3
        assert history[0]["user"] == "Create a login system"
        assert history[1]["agent"] == "I'll help you create a login system"
        assert history[2]["user"] == "What are the requirements?"
        
        # Test history with limit
        recent_history = context.get_history(2)
        assert len(recent_history) == 2
        assert recent_history[0]["agent"] == "I'll help you create a login system"
    
    @pytest.mark.asyncio
    async def test_persona_context_active_tool_workflow(self):
        """Test active tool and workflow management."""
        context = PersonaContext("test-persona")
        
        # Test active tool
        context.set_active_tool("bmad_prd_create")
        assert context.active_tool == "bmad_prd_create"
        
        context.clear_active_tool()
        assert context.active_tool is None
        
        # Test active workflow
        context.set_active_workflow("greenfield-prd.yaml")
        assert context.active_workflow == "greenfield-prd.yaml"
        
        context.clear_active_workflow()
        assert context.active_workflow is None
    
    @pytest.mark.asyncio
    async def test_persona_context_serialization(self):
        """Test context serialization and deserialization."""
        # Create context with complex state
        context = PersonaContext("test-persona", {
            "project": "e-commerce",
            "features": ["auth", "payment", "inventory"],
            "metadata": {"priority": "high", "deadline": "2024-12-31"}
        })
        
        # Add history
        context.add_to_history({"user": "Start project"})
        context.add_to_history({"agent": "Initializing"})
        
        # Set active tool and workflow
        context.set_active_tool("bmad_arch_create")
        context.set_active_workflow("brownfield-service.yaml")
        
        # Serialize
        serialized = context.to_dict()
        
        # Deserialize
        deserialized = PersonaContext.from_dict(serialized)
        
        # Verify all data preserved
        assert deserialized.persona_id == context.persona_id
        assert deserialized.context_id == context.context_id
        assert deserialized.get_state("project") == context.get_state("project")
        assert deserialized.get_state("features") == context.get_state("features")
        assert len(deserialized.get_history()) == len(context.get_history())
        assert deserialized.active_tool == context.active_tool
        assert deserialized.active_workflow == context.active_workflow


class TestPersonaContextManager:
    """Test suite for persona context manager functionality."""
    
    @pytest.mark.asyncio
    async def test_context_manager_activation_and_retrieval(self):
        """Test context activation and retrieval."""
        manager = BMADPersonaContextManager()
        
        # Create contexts
        context1 = PersonaContext("persona1", {"project": "project1"})
        context2 = PersonaContext("persona2", {"project": "project2"})
        
        # Activate contexts
        manager.activate_context("persona1", context1)
        manager.activate_context("persona2", context2)
        
        # Retrieve contexts
        retrieved1 = manager.get_active_context("persona1")
        retrieved2 = manager.get_active_context("persona2")
        
        assert retrieved1 == context1
        assert retrieved2 == context2
        assert retrieved1.get_state("project") == "project1"
        assert retrieved2.get_state("project") == "project2"
    
    @pytest.mark.asyncio
    async def test_context_manager_stack_operations(self):
        """Test context stack push/pop operations."""
        manager = BMADPersonaContextManager()
        
        # Create contexts
        context1 = PersonaContext("persona1")
        context2 = PersonaContext("persona2")
        context3 = PersonaContext("persona3")
        
        # Push contexts onto stack
        manager.push_context(context1)
        assert manager.get_current_persona_context() == context1
        
        manager.push_context(context2)
        assert manager.get_current_persona_context() == context2
        assert context2.parent_context_id == context1.context_id
        
        manager.push_context(context3)
        assert manager.get_current_persona_context() == context3
        assert context3.parent_context_id == context2.context_id
        
        # Pop contexts from stack
        popped3 = manager.pop_context()
        assert popped3 == context3
        assert manager.get_current_persona_context() == context2
        
        popped2 = manager.pop_context()
        assert popped2 == context2
        assert manager.get_current_persona_context() == context1
        
        popped1 = manager.pop_context()
        assert popped1 == context1
        assert manager.get_current_persona_context() is None
    
    @pytest.mark.asyncio
    async def test_context_manager_persona_switching(self):
        """Test persona switching functionality."""
        manager = BMADPersonaContextManager()
        
        # Create initial context
        pm_context = PersonaContext("pm", {"project": "e-commerce"})
        manager.activate_context("pm", pm_context)
        manager.push_context(pm_context)
        
        # Switch to dev persona (should create new context)
        dev_context = manager.switch_persona("dev")
        assert dev_context.persona_id == "dev"
        assert manager.get_current_persona_context() == dev_context
        assert manager.get_active_context("dev") == dev_context
        assert manager.get_active_context("pm") == pm_context  # PM context preserved
        
        # Switch back to PM (should activate existing context)
        switched_back = manager.switch_persona("pm")
        assert switched_back == pm_context
        assert manager.get_current_persona_context() == pm_context


class TestSessionLifecycleManagement:
    """Test suite for session lifecycle management."""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager with mock DB client."""
        return BMADSessionManager(MockDBSessionClient())
    
    @pytest.mark.asyncio
    async def test_session_creation_and_retrieval(self, session_manager):
        """Test session creation and retrieval."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        initial_persona_id = "bmad-orchestrator"
        
        # Create session
        result = await session_manager.create_session(tenant_id, user_id, initial_persona_id)
        
        assert result is not None
        assert "session" in result
        assert "initial_context" in result
        
        session_id = result['session']['session_id']
        assert session_id is not None
        
        # Retrieve session
        retrieved_session = await session_manager.get_session(session_id, tenant_id)
        assert retrieved_session is not None
        assert retrieved_session['status'] == 'active'
        assert retrieved_session['current_persona_context_id'] is not None
    
    @pytest.mark.asyncio
    async def test_session_lifecycle_operations(self, session_manager):
        """Test session suspend, resume, and terminate operations."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Create session
        result = await session_manager.create_session(tenant_id, user_id, "pm")
        session_id = result['session']['session_id']
        
        # Suspend session
        success = await session_manager.suspend_session(session_id, tenant_id)
        assert success is True
        
        session = await session_manager.get_session(session_id, tenant_id)
        assert session['status'] == 'suspended'
        
        # Resume session
        success = await session_manager.resume_session(session_id, tenant_id)
        assert success is True
        
        session = await session_manager.get_session(session_id, tenant_id)
        assert session['status'] == 'active'
        
        # Terminate session
        success = await session_manager.terminate_session(session_id, tenant_id)
        assert success is True
        
        session = await session_manager.get_session(session_id, tenant_id)
        assert session['status'] == 'terminated'
        assert session['end_time'] is not None
    
    @pytest.mark.asyncio
    async def test_session_cleanup_expired_sessions(self, session_manager):
        """Test automatic cleanup of expired sessions."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Create sessions
        result1 = await session_manager.create_session(tenant_id, user_id, "pm")
        session_id1 = result1['session']['session_id']
        
        result2 = await session_manager.create_session(tenant_id, user_id, "dev")
        session_id2 = result2['session']['session_id']
        
        # Manually expire first session by setting last_active to past
        mock_client = session_manager.db_client
        past_time = datetime.utcnow() - timedelta(minutes=session_manager.session_timeout_minutes + 1)
        mock_client.sessions[str(session_id1)]['last_active'] = past_time.isoformat()
        
        # Run cleanup
        cleaned_count = await session_manager.cleanup_expired_sessions()
        assert cleaned_count == 1
        
        # Verify first session expired, second still active
        session1 = await session_manager.get_session(session_id1, tenant_id)
        assert session1['status'] == 'expired'
        
        session2 = await session_manager.get_session(session_id2, tenant_id)
        assert session2['status'] == 'active'


class TestTaskCheckpointing:
    """Test suite for task checkpointing functionality."""
    
    @pytest.fixture
    def checkpoint_manager(self):
        """Create checkpoint manager with mock DB client."""
        return BMADTaskCheckpoint(MockDBCheckpointClient())
    
    @pytest.mark.asyncio
    async def test_checkpoint_creation_and_retrieval(self, checkpoint_manager):
        """Test checkpoint creation and retrieval."""
        tenant_id = uuid.uuid4()
        task_id = uuid.uuid4()
        workflow_id = uuid.uuid4()
        
        # Create checkpoint
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            tenant_id, task_id, workflow_id, "step1", {"data": "step1_complete"}
        )
        
        assert checkpoint_id is not None
        
        # Retrieve checkpoint
        checkpoint = await checkpoint_manager.get_checkpoint(checkpoint_id, tenant_id)
        assert checkpoint is not None
        assert checkpoint['task_id'] == str(task_id)
        assert checkpoint['step_id'] == "step1"
        assert checkpoint['status'] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_checkpoint_versioning(self, checkpoint_manager):
        """Test checkpoint versioning for same step."""
        tenant_id = uuid.uuid4()
        task_id = uuid.uuid4()
        workflow_id = uuid.uuid4()
        
        # Create multiple checkpoints for same step with different versions
        checkpoint_id1 = await checkpoint_manager.create_checkpoint(
            tenant_id, task_id, workflow_id, "step1", {"data": "version1"}, version=1
        )
        
        checkpoint_id2 = await checkpoint_manager.create_checkpoint(
            tenant_id, task_id, workflow_id, "step1", {"data": "version2"}, version=2
        )
        
        assert checkpoint_id1 != checkpoint_id2
        
        # Get latest checkpoint
        latest = await checkpoint_manager.get_latest_checkpoint_for_task(task_id, tenant_id)
        assert latest is not None
        assert latest['version'] == 2
        assert latest['state']['data'] == "version2"
    
    @pytest.mark.asyncio
    async def test_checkpoint_status_updates(self, checkpoint_manager):
        """Test checkpoint status updates."""
        tenant_id = uuid.uuid4()
        task_id = uuid.uuid4()
        workflow_id = uuid.uuid4()
        
        # Create checkpoint
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            tenant_id, task_id, workflow_id, "step1", {"data": "processing"}
        )
        
        # Update status
        success = await checkpoint_manager.update_checkpoint_status(
            checkpoint_id, tenant_id, "completed"
        )
        assert success is True
        
        # Verify status update
        checkpoint = await checkpoint_manager.get_checkpoint(checkpoint_id, tenant_id)
        assert checkpoint['status'] == "completed"


class TestContextSerialization:
    """Test suite for context serialization functionality."""
    
    @pytest.fixture
    def serializer(self):
        """Create context serializer."""
        return ContextSerializer()
    
    def test_json_serialization(self, serializer):
        """Test JSON serialization format."""
        test_data = {
            "persona_id": "test-persona",
            "state": {"project": "test", "features": ["auth", "payment"]},
            "history": [{"user": "hello"}, {"agent": "hi"}],
            "metadata": {"priority": "high"}
        }
        
        # Serialize
        serialized = serializer.serialize(test_data, SerializationFormat.JSON)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = serializer.deserialize(serialized, SerializationFormat.JSON)
        assert deserialized == test_data
    
    def test_pickle_serialization(self, serializer):
        """Test Pickle serialization format."""
        test_data = {
            "persona_id": "test-persona",
            "state": {"project": "test", "features": ["auth", "payment"]},
            "history": [{"user": "hello"}, {"agent": "hi"}],
            "metadata": {"priority": "high"}
        }
        
        # Serialize
        serialized = serializer.serialize(test_data, SerializationFormat.PICKLE)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = serializer.deserialize(serialized, SerializationFormat.PICKLE)
        assert deserialized == test_data
    
    def test_compression_and_checksum(self, serializer):
        """Test compression and checksum features."""
        test_data = {
            "persona_id": "test-persona",
            "state": {"project": "test", "features": ["auth", "payment"]},
            "history": [{"user": "hello"}, {"agent": "hi"}],
            "metadata": {"priority": "high"}
        }
        
        # Serialize with compression and checksum
        serialized = serializer.serialize(
            test_data, 
            SerializationFormat.JSON, 
            compress=True, 
            add_checksum=True
        )
        assert isinstance(serialized, bytes)
        
        # Deserialize with compression and checksum
        deserialized = serializer.deserialize(
            serialized, 
            SerializationFormat.JSON, 
            is_compressed=True, 
            has_checksum=True
        )
        assert deserialized == test_data


class TestUnifiedPersonaSystem:
    """Test suite for unified persona system integration."""
    
    @pytest.fixture
    def unified_system(self):
        """Create unified persona system with mock DB client."""
        return BMADUnifiedPersonaSystem(MockDBSessionClient())
    
    @pytest.mark.asyncio
    async def test_session_initialization(self, unified_system):
        """Test user session initialization."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Initialize session
        result = await unified_system.initialize_user_session(
            tenant_id, user_id, "bmad-orchestrator"
        )
        
        assert "session_id" in result
        assert "current_context" in result
        assert result["current_context"]["persona_id"] == "bmad-orchestrator"
    
    @pytest.mark.asyncio
    async def test_persona_switching(self, unified_system):
        """Test persona switching with context preservation."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Initialize session
        init_result = await unified_system.initialize_user_session(
            tenant_id, user_id, "pm"
        )
        session_id = init_result["session_id"]
        
        # Switch to dev persona
        switch_result = await unified_system.switch_persona(
            session_id, tenant_id, user_id, "dev"
        )
        
        assert switch_result["session_id"] == session_id
        assert switch_result["current_context"]["persona_id"] == "dev"
    
    @pytest.mark.asyncio
    async def test_context_state_updates(self, unified_system):
        """Test context state updates."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Initialize session
        init_result = await unified_system.initialize_user_session(
            tenant_id, user_id, "pm"
        )
        session_id = init_result["session_id"]
        
        # Update context state
        success = await unified_system.update_persona_context_state(
            session_id, tenant_id, "project_status", "in_progress"
        )
        assert success is True
        
        # Add to history
        success = await unified_system.add_to_persona_history(
            session_id, tenant_id, {"user": "Updated project status"}
        )
        assert success is True
    
    @pytest.mark.asyncio
    async def test_task_checkpoint_integration(self, unified_system):
        """Test task checkpoint integration."""
        tenant_id = uuid.uuid4()
        task_id = uuid.uuid4()
        workflow_id = uuid.uuid4()
        
        # Create checkpoint
        checkpoint_id = await unified_system.create_task_checkpoint(
            tenant_id, task_id, workflow_id, "step1", {"data": "processing"}
        )
        
        assert checkpoint_id is not None
        
        # Retrieve latest checkpoint
        latest = await unified_system.get_latest_task_checkpoint(task_id, tenant_id)
        assert latest is not None
        assert latest["step_id"] == "step1"


class TestAPIEndpointIntegration:
    """Test suite for API endpoint integration."""
    
    def test_persona_endpoints_import(self):
        """Test that persona endpoints can be imported."""
        try:
            from bmad_api_service.persona_endpoints import router
            assert router is not None
            assert router.prefix == "/bmad/persona"
        except ImportError as e:
            pytest.fail(f"Failed to import persona endpoints: {e}")
    
    def test_endpoint_routes_defined(self):
        """Test that all required routes are defined."""
        from bmad_api_service.persona_endpoints import router
        
        # Get all routes
        routes = [route.path for route in router.routes]
        
        # Verify required routes exist
        required_routes = [
            "/bmad/persona/session/initialize",
            "/bmad/persona/session/{session_id}/switch-persona",
            "/bmad/persona/session/{session_id}/current-context",
            "/bmad/persona/context/{context_id}/state",
            "/bmad/persona/context/{context_id}/history",
            "/bmad/persona/task/checkpoint",
            "/bmad/persona/task/{task_id}/latest-checkpoint",
            "/bmad/persona/session/cleanup-expired"
        ]
        
        for route in required_routes:
            assert any(route in r for r in routes), f"Route {route} not found in {routes}"


class TestPhase2Deployment:
    """Test suite for Phase 2 deployment verification."""
    
    def test_phase2_modules_available(self):
        """Test that all Phase 2 modules are available."""
        modules = [
            "cflow_platform.core.bmad_persona_context",
            "cflow_platform.core.bmad_session_manager", 
            "cflow_platform.core.bmad_task_checkpoint",
            "cflow_platform.core.bmad_unified_persona_system",
            "cflow_platform.core.bmad_context_serialization"
        ]
        
        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"Phase 2 module {module} not available: {e}")
    
    def test_phase2_classes_instantiable(self):
        """Test that Phase 2 classes can be instantiated."""
        from cflow_platform.core.bmad_persona_context import PersonaContext, BMADPersonaContextManager
        from cflow_platform.core.bmad_session_manager import BMADSessionManager
        from cflow_platform.core.bmad_task_checkpoint import BMADTaskCheckpoint
        from cflow_platform.core.bmad_unified_persona_system import BMADUnifiedPersonaSystem
        from cflow_platform.core.bmad_context_serialization import ContextSerializer
        
        # Test instantiation
        context = PersonaContext("test")
        manager = BMADPersonaContextManager()
        session_mgr = BMADSessionManager(MockDBSessionClient())
        checkpoint_mgr = BMADTaskCheckpoint(MockDBCheckpointClient())
        unified_system = BMADUnifiedPersonaSystem(MockDBSessionClient())
        serializer = ContextSerializer()
        
        # Verify objects created
        assert context is not None
        assert manager is not None
        assert session_mgr is not None
        assert checkpoint_mgr is not None
        assert unified_system is not None
        assert serializer is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
