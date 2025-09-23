#!/usr/bin/env python3
"""
BMAD Phase 2 Simple Integration Tests

This test suite validates the Phase 2 enhancements with simplified tests
that work with the actual implementation.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPhase2ModuleImports:
    """Test that Phase 2 modules can be imported."""
    
    def test_persona_context_import(self):
        """Test persona context module import."""
        try:
            from cflow_platform.core.bmad_persona_context import PersonaContext, BMADPersonaContextManager
            assert PersonaContext is not None
            assert BMADPersonaContextManager is not None
        except ImportError as e:
            pytest.fail(f"Failed to import persona context: {e}")
    
    def test_session_manager_import(self):
        """Test session manager module import."""
        try:
            from cflow_platform.core.bmad_session_manager import BMADSessionManager
            assert BMADSessionManager is not None
        except ImportError as e:
            pytest.fail(f"Failed to import session manager: {e}")
    
    def test_task_checkpoint_import(self):
        """Test task checkpoint module import."""
        try:
            from cflow_platform.core.bmad_task_checkpoint import BMADTaskCheckpointer
            assert BMADTaskCheckpointer is not None
        except ImportError as e:
            pytest.fail(f"Failed to import task checkpoint: {e}")
    
    def test_unified_system_import(self):
        """Test unified persona system import."""
        try:
            from cflow_platform.core.bmad_unified_persona_system import BMADUnifiedPersonaSystem
            assert BMADUnifiedPersonaSystem is not None
        except ImportError as e:
            pytest.fail(f"Failed to import unified persona system: {e}")
    
    def test_context_serialization_import(self):
        """Test context serialization import."""
        try:
            from cflow_platform.core.bmad_context_serialization import ContextSerializer
            assert ContextSerializer is not None
        except ImportError as e:
            pytest.fail(f"Failed to import context serializer: {e}")


class TestPhase2ClassInstantiation:
    """Test that Phase 2 classes can be instantiated."""
    
    def test_persona_context_instantiation(self):
        """Test PersonaContext instantiation."""
        from cflow_platform.core.bmad_persona_context import PersonaContext, PersonaType
        
        # Create persona context
        context = PersonaContext(
            persona_id="test-persona",
            persona_type=PersonaType.PROJECT_MANAGER,
            session_id="test-session",
            user_id="test-user"
        )
        
        assert context.persona_id == "test-persona"
        assert context.persona_type == PersonaType.PROJECT_MANAGER
        assert context.session_id == "test-session"
        assert context.user_id == "test-user"
    
    def test_persona_context_manager_instantiation(self):
        """Test BMADPersonaContextManager instantiation."""
        from cflow_platform.core.bmad_persona_context import BMADPersonaContextManager
        
        # Create manager
        manager = BMADPersonaContextManager()
        assert manager is not None
    
    def test_session_manager_instantiation(self):
        """Test BMADSessionManager instantiation."""
        from cflow_platform.core.bmad_session_manager import BMADSessionManager
        
        # Create mock DB client
        mock_db_client = MagicMock()
        
        # Create session manager
        session_manager = BMADSessionManager(mock_db_client)
        assert session_manager is not None
    
    def test_task_checkpointer_instantiation(self):
        """Test BMADTaskCheckpointer instantiation."""
        from cflow_platform.core.bmad_task_checkpoint import BMADTaskCheckpointer
        
        # Create mock DB client
        mock_db_client = MagicMock()
        
        # Create task checkpointer
        checkpointer = BMADTaskCheckpointer(mock_db_client)
        assert checkpointer is not None
    
    def test_unified_system_instantiation(self):
        """Test BMADUnifiedPersonaSystem instantiation."""
        from cflow_platform.core.bmad_unified_persona_system import BMADUnifiedPersonaSystem
        
        # Create mock DB client
        mock_db_client = MagicMock()
        
        # Create unified system
        unified_system = BMADUnifiedPersonaSystem(mock_db_client)
        assert unified_system is not None
    
    def test_context_serializer_instantiation(self):
        """Test ContextSerializer instantiation."""
        from cflow_platform.core.bmad_context_serialization import ContextSerializer
        
        # Create serializer
        serializer = ContextSerializer()
        assert serializer is not None


class TestPhase2BasicFunctionality:
    """Test basic Phase 2 functionality."""
    
    def test_persona_context_state_management(self):
        """Test persona context state management."""
        from cflow_platform.core.bmad_persona_context import PersonaContext, PersonaType
        
        # Create context
        context = PersonaContext(
            persona_id="test-persona",
            persona_type=PersonaType.PROJECT_MANAGER,
            session_id="test-session",
            user_id="test-user"
        )
        
        # Test state management
        context.update_state("project", "e-commerce")
        context.update_state("status", "planning")
        
        assert context.get_state("project") == "e-commerce"
        assert context.get_state("status") == "planning"
        assert context.get_state("nonexistent", "default") == "default"
    
    def test_context_serialization_basic(self):
        """Test basic context serialization."""
        from cflow_platform.core.bmad_context_serialization import ContextSerializer, SerializationFormat
        
        serializer = ContextSerializer()
        
        # Test data
        test_data = {
            "persona_id": "test-persona",
            "state": {"project": "test", "status": "active"},
            "metadata": {"priority": "high"}
        }
        
        # Test JSON serialization
        serialized = serializer.serialize(test_data, SerializationFormat.JSON)
        assert isinstance(serialized, bytes)
        
        # Test deserialization
        deserialized = serializer.deserialize(serialized, SerializationFormat.JSON)
        assert deserialized == test_data


class TestPhase2DeploymentVerification:
    """Test Phase 2 deployment verification."""
    
    def test_phase2_files_exist(self):
        """Test that Phase 2 files exist."""
        phase2_files = [
            "cflow_platform/core/bmad_persona_context.py",
            "cflow_platform/core/bmad_session_manager.py",
            "cflow_platform/core/bmad_task_checkpoint.py",
            "cflow_platform/core/bmad_unified_persona_system.py",
            "cflow_platform/core/bmad_context_serialization.py"
        ]
        
        for file_path in phase2_files:
            assert os.path.exists(file_path), f"Phase 2 file {file_path} does not exist"
    
    def test_phase2_database_schemas_exist(self):
        """Test that Phase 2 database schemas exist."""
        schema_files = [
            "docs/agentic-plan/sql/005_bmad_persona_context_schema.sql",
            "docs/agentic-plan/sql/006_bmad_task_checkpoints_schema.sql"
        ]
        
        for file_path in schema_files:
            assert os.path.exists(file_path), f"Phase 2 schema file {file_path} does not exist"
    
    def test_phase2_api_endpoints_exist(self):
        """Test that Phase 2 API endpoints exist."""
        endpoint_file = "bmad_api_service/persona_endpoints.py"
        assert os.path.exists(endpoint_file), f"Phase 2 API endpoints file {endpoint_file} does not exist"


class TestPhase2Integration:
    """Test Phase 2 integration capabilities."""
    
    def test_persona_context_manager_integration(self):
        """Test persona context manager integration."""
        from cflow_platform.core.bmad_persona_context import BMADPersonaContextManager, PersonaContext, PersonaType
        
        # Create manager
        manager = BMADPersonaContextManager()
        
        # Create contexts
        context1 = PersonaContext(
            persona_id="pm",
            persona_type=PersonaType.PROJECT_MANAGER,
            session_id="session1",
            user_id="user1"
        )
        
        context2 = PersonaContext(
            persona_id="dev",
            persona_type=PersonaType.DEVELOPER,
            session_id="session1",
            user_id="user1"
        )
        
        # Test context management
        manager.activate_context("pm", context1)
        manager.activate_context("dev", context2)
        
        # Verify contexts
        assert manager.get_active_context("pm") == context1
        assert manager.get_active_context("dev") == context2
    
    def test_unified_system_integration(self):
        """Test unified persona system integration."""
        from cflow_platform.core.bmad_unified_persona_system import BMADUnifiedPersonaSystem
        from unittest.mock import MagicMock
        
        # Create mock DB client
        mock_db_client = MagicMock()
        
        # Create unified system
        unified_system = BMADUnifiedPersonaSystem(mock_db_client)
        
        # Verify system components
        assert unified_system.persona_context_manager is not None
        assert unified_system.session_manager is not None
        assert unified_system.task_checkpoint_manager is not None
        assert unified_system.context_serializer is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
