"""
Test suite for Basic BMAD Workflow Implementations (Story 1.5)

This module tests the basic workflow implementations:
- Basic PRD creation workflow
- Basic Architecture creation workflow  
- Basic Story creation workflow
- Complete basic workflow orchestration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from cflow_platform.core.basic_workflow_implementations import (
    BasicWorkflowImplementations,
    get_basic_workflows,
    create_basic_prd,
    create_basic_architecture,
    create_basic_story,
    run_complete_basic_workflow
)


@pytest.fixture
async def basic_workflows():
    """Create a BasicWorkflowImplementations instance for testing."""
    return BasicWorkflowImplementations()


@pytest.fixture
def mock_bmad_handlers():
    """Mock BMAD handlers for testing."""
    with patch('cflow_platform.core.basic_workflow_implementations.BMADHandlers') as mock:
        handler_instance = AsyncMock()
        mock.return_value = handler_instance
        
        # Mock successful responses
        handler_instance.bmad_prd_create.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "message": "PRD created successfully",
            "data": {
                "id": "test-prd-id",
                "kind": "PRD",
                "content": "# Test PRD\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        handler_instance.bmad_arch_create.return_value = {
            "success": True,
            "doc_id": "test-arch-id",
            "message": "Architecture created successfully",
            "data": {
                "id": "test-arch-id",
                "kind": "ARCHITECTURE",
                "content": "# Test Architecture\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        handler_instance.bmad_story_create.return_value = {
            "success": True,
            "doc_id": "test-story-id",
            "message": "Story created successfully",
            "data": {
                "id": "test-story-id",
                "kind": "STORY",
                "content": "# Test Story\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        handler_instance.bmad_prd_get.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "data": {
                "id": "test-prd-id",
                "kind": "PRD",
                "content": "# Test PRD",
                "status": "draft"
            }
        }
        
        handler_instance.bmad_arch_get.return_value = {
            "success": True,
            "doc_id": "test-arch-id",
            "data": {
                "id": "test-arch-id",
                "kind": "ARCHITECTURE",
                "content": "# Test Architecture",
                "status": "draft"
            }
        }
        
        handler_instance.bmad_doc_list.return_value = {
            "success": True,
            "documents": [
                {"id": "test-prd-id", "kind": "PRD", "status": "draft"},
                {"id": "test-arch-id", "kind": "ARCHITECTURE", "status": "draft"},
                {"id": "test-story-id", "kind": "STORY", "status": "draft"}
            ],
            "count": 3
        }
        
        yield handler_instance


@pytest.fixture
def mock_hil_integration():
    """Mock HIL integration for testing."""
    with patch('cflow_platform.core.basic_workflow_implementations.BMADHILIntegration') as mock:
        hil_instance = AsyncMock()
        mock.return_value = hil_instance
        
        # Mock HIL session creation
        hil_instance.trigger_hil_session.return_value = {
            "success": True,
            "session_id": "test-hil-session-id",
            "message": "HIL session started"
        }
        
        yield hil_instance


class TestBasicWorkflowImplementations:
    """Test cases for BasicWorkflowImplementations class."""
    
    @pytest.mark.asyncio
    async def test_create_basic_prd_workflow_success(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test successful PRD creation workflow."""
        result = await basic_workflows.create_basic_prd_workflow(
            project_name="Test Project",
            goals=["Goal 1", "Goal 2"],
            background="Test background"
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "doc_id" in result
        assert "hil_session_id" in result
        assert result["next_action"] == "Complete HIL session to finalize PRD"
        assert len(result["step_results"]) >= 2
        
        # Verify BMAD handler was called
        mock_bmad_handlers.bmad_prd_create.assert_called_once_with(
            project_name="Test Project",
            goals=["Goal 1", "Goal 2"],
            background="Test background"
        )
    
    @pytest.mark.asyncio
    async def test_create_basic_prd_workflow_no_hil_needed(self, basic_workflows, mock_bmad_handlers):
        """Test PRD creation when no HIL is needed."""
        # Mock document without template placeholders
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "message": "PRD created successfully",
            "data": {
                "id": "test-prd-id",
                "kind": "PRD",
                "content": "# Complete PRD\n\nAll sections filled out.",
                "status": "draft"
            }
        }
        
        result = await basic_workflows.create_basic_prd_workflow(
            project_name="Test Project"
        )
        
        assert result["workflow_status"] == "completed"
        assert result["next_action"] == "Create Architecture document"
    
    @pytest.mark.asyncio
    async def test_create_basic_architecture_workflow_success(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test successful Architecture creation workflow."""
        result = await basic_workflows.create_basic_architecture_workflow(
            project_name="Test Project",
            prd_id="test-prd-id",
            tech_stack=["Python", "React"]
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "doc_id" in result
        assert result["prd_id"] == "test-prd-id"
        assert "hil_session_id" in result
        assert result["next_action"] == "Complete HIL session to finalize Architecture"
        
        # Verify both PRD validation and Architecture creation were called
        mock_bmad_handlers.bmad_prd_get.assert_called_once_with("test-prd-id")
        mock_bmad_handlers.bmad_arch_create.assert_called_once_with(
            project_name="Test Project",
            prd_id="test-prd-id",
            tech_stack=["Python", "React"]
        )
    
    @pytest.mark.asyncio
    async def test_create_basic_architecture_workflow_prd_validation_fails(self, basic_workflows, mock_bmad_handlers):
        """Test Architecture creation when PRD validation fails."""
        mock_bmad_handlers.bmad_prd_get.return_value = {
            "success": False,
            "error": "PRD not found"
        }
        
        result = await basic_workflows.create_basic_architecture_workflow(
            project_name="Test Project",
            prd_id="invalid-prd-id"
        )
        
        assert result["workflow_status"] == "error"
        assert "PRD validation failed" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_basic_story_workflow_success(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test successful Story creation workflow."""
        result = await basic_workflows.create_basic_story_workflow(
            project_name="Test Project",
            prd_id="test-prd-id",
            arch_id="test-arch-id",
            user_stories=["Story 1", "Story 2"]
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "doc_id" in result
        assert result["prd_id"] == "test-prd-id"
        assert result["arch_id"] == "test-arch-id"
        assert "hil_session_id" in result
        assert result["next_action"] == "Complete HIL session to finalize Story"
        
        # Verify all validations and Story creation were called
        mock_bmad_handlers.bmad_prd_get.assert_called_once_with("test-prd-id")
        mock_bmad_handlers.bmad_arch_get.assert_called_once_with("test-arch-id")
        mock_bmad_handlers.bmad_story_create.assert_called_once_with(
            project_name="Test Project",
            prd_id="test-prd-id",
            arch_id="test-arch-id",
            user_stories=["Story 1", "Story 2"]
        )
    
    @pytest.mark.asyncio
    async def test_run_complete_basic_workflow_success(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test complete basic workflow execution."""
        # Mock documents without template placeholders to avoid HIL
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "message": "PRD created successfully",
            "data": {
                "id": "test-prd-id",
                "kind": "PRD",
                "content": "# Complete PRD",
                "status": "draft"
            }
        }
        
        mock_bmad_handlers.bmad_arch_create.return_value = {
            "success": True,
            "doc_id": "test-arch-id",
            "message": "Architecture created successfully",
            "data": {
                "id": "test-arch-id",
                "kind": "ARCHITECTURE",
                "content": "# Complete Architecture",
                "status": "draft"
            }
        }
        
        mock_bmad_handlers.bmad_story_create.return_value = {
            "success": True,
            "doc_id": "test-story-id",
            "message": "Story created successfully",
            "data": {
                "id": "test-story-id",
                "kind": "STORY",
                "content": "# Complete Story",
                "status": "draft"
            }
        }
        
        result = await basic_workflows.run_complete_basic_workflow(
            project_name="Test Project",
            goals=["Goal 1"],
            background="Test background",
            tech_stack=["Python"],
            user_stories=["Story 1"]
        )
        
        assert result["workflow_status"] == "completed"
        assert result["completion_percentage"] == 100.0
        assert "documents" in result
        assert result["documents"]["prd_id"] == "test-prd-id"
        assert result["documents"]["arch_id"] == "test-arch-id"
        assert result["documents"]["story_id"] == "test-story-id"
        assert result["next_action"] == "Begin implementation with Dev agent"
    
    @pytest.mark.asyncio
    async def test_run_complete_basic_workflow_prd_fails(self, basic_workflows, mock_bmad_handlers):
        """Test complete workflow when PRD creation fails."""
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": False,
            "error": "Failed to create PRD"
        }
        
        result = await basic_workflows.run_complete_basic_workflow(
            project_name="Test Project"
        )
        
        assert result["workflow_status"] == "error"
        assert "PRD workflow failed" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_workflow_status(self, basic_workflows, mock_bmad_handlers):
        """Test getting workflow status."""
        result = await basic_workflows.get_workflow_status("test-project-id")
        
        assert result["success"] is True
        assert "workflow_status" in result
        status = result["workflow_status"]
        assert status["project_id"] == "test-project-id"
        assert status["prd_exists"] is True
        assert status["architecture_exists"] is True
        assert status["story_exists"] is True
        assert status["current_step"] == "Stories Created"
        assert status["next_action"] == "Review Stories"
        assert status["completion_percentage"] == 100.0
    
    def test_determine_current_step(self, basic_workflows):
        """Test determining current workflow step."""
        # Test different document combinations
        docs_with_story = [{"kind": "STORY"}, {"kind": "PRD"}]
        assert basic_workflows._determine_current_step(docs_with_story) == "Stories Created"
        
        docs_with_arch = [{"kind": "ARCHITECTURE"}, {"kind": "PRD"}]
        assert basic_workflows._determine_current_step(docs_with_arch) == "Architecture Created"
        
        docs_with_prd = [{"kind": "PRD"}]
        assert basic_workflows._determine_current_step(docs_with_prd) == "PRD Created"
        
        docs_empty = []
        assert basic_workflows._determine_current_step(docs_empty) == "Workflow Not Started"
    
    def test_determine_next_action(self, basic_workflows):
        """Test determining next workflow action."""
        # Test different document combinations
        docs_with_story = [{"kind": "STORY"}, {"kind": "PRD"}]
        assert basic_workflows._determine_next_action(docs_with_story) == "Review Stories"
        
        docs_with_arch = [{"kind": "ARCHITECTURE"}, {"kind": "PRD"}]
        assert basic_workflows._determine_next_action(docs_with_arch) == "Create Stories"
        
        docs_with_prd = [{"kind": "PRD"}]
        assert basic_workflows._determine_next_action(docs_with_prd) == "Create Architecture"
        
        docs_empty = []
        assert basic_workflows._determine_next_action(docs_empty) == "Create PRD"
    
    def test_calculate_completion_percentage(self, basic_workflows):
        """Test calculating workflow completion percentage."""
        # Test different document combinations
        docs_all = [{"kind": "PRD"}, {"kind": "ARCHITECTURE"}, {"kind": "STORY"}]
        assert basic_workflows._calculate_completion_percentage(docs_all) == 100.0
        
        docs_prd_arch = [{"kind": "PRD"}, {"kind": "ARCHITECTURE"}]
        assert basic_workflows._calculate_completion_percentage(docs_prd_arch) == 66.66
        
        docs_prd_only = [{"kind": "PRD"}]
        assert basic_workflows._calculate_completion_percentage(docs_prd_only) == 33.33
        
        docs_empty = []
        assert basic_workflows._calculate_completion_percentage(docs_empty) == 0.0


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_create_basic_prd_function(self, mock_bmad_handlers, mock_hil_integration):
        """Test create_basic_prd convenience function."""
        result = await create_basic_prd(
            project_name="Test Project",
            goals=["Goal 1"],
            background="Test background"
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "doc_id" in result
    
    @pytest.mark.asyncio
    async def test_create_basic_architecture_function(self, mock_bmad_handlers, mock_hil_integration):
        """Test create_basic_architecture convenience function."""
        result = await create_basic_architecture(
            project_name="Test Project",
            prd_id="test-prd-id",
            tech_stack=["Python"]
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert result["prd_id"] == "test-prd-id"
    
    @pytest.mark.asyncio
    async def test_create_basic_story_function(self, mock_bmad_handlers, mock_hil_integration):
        """Test create_basic_story convenience function."""
        result = await create_basic_story(
            project_name="Test Project",
            prd_id="test-prd-id",
            arch_id="test-arch-id",
            user_stories=["Story 1"]
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert result["prd_id"] == "test-prd-id"
        assert result["arch_id"] == "test-arch-id"
    
    @pytest.mark.asyncio
    async def test_run_complete_basic_workflow_function(self, mock_bmad_handlers):
        """Test run_complete_basic_workflow convenience function."""
        # Mock documents without template placeholders
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "data": {"id": "test-prd-id", "kind": "PRD", "content": "# Complete PRD"}
        }
        mock_bmad_handlers.bmad_arch_create.return_value = {
            "success": True,
            "doc_id": "test-arch-id",
            "data": {"id": "test-arch-id", "kind": "ARCHITECTURE", "content": "# Complete Architecture"}
        }
        mock_bmad_handlers.bmad_story_create.return_value = {
            "success": True,
            "doc_id": "test-story-id",
            "data": {"id": "test-story-id", "kind": "STORY", "content": "# Complete Story"}
        }
        
        result = await run_complete_basic_workflow(
            project_name="Test Project"
        )
        
        assert result["workflow_status"] == "completed"
        assert result["completion_percentage"] == 100.0


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_workflow_creation_error(self, basic_workflows, mock_bmad_handlers):
        """Test workflow creation when BMAD handlers fail."""
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": False,
            "error": "Database connection failed"
        }
        
        result = await basic_workflows.create_basic_prd_workflow(
            project_name="Test Project"
        )
        
        assert result["workflow_status"] == "error"
        assert "Failed to create PRD" in result["message"]
    
    @pytest.mark.asyncio
    async def test_hil_integration_error(self, basic_workflows, mock_bmad_handlers):
        """Test workflow when HIL integration fails."""
        with patch('cflow_platform.core.basic_workflow_implementations.BMADHILIntegration') as mock_hil:
            hil_instance = AsyncMock()
            mock_hil.return_value = hil_instance
            hil_instance.trigger_hil_session.return_value = {
                "success": False,
                "error": "HIL service unavailable"
            }
            
            result = await basic_workflows.create_basic_prd_workflow(
                project_name="Test Project"
            )
            
            assert result["workflow_status"] == "paused_for_hil"
            # Should still return paused_for_hil even if HIL fails
            # The workflow assumes HIL will be retried later
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, basic_workflows, mock_bmad_handlers):
        """Test handling of validation errors."""
        mock_bmad_handlers.bmad_prd_get.return_value = {
            "success": False,
            "error": "Document not found"
        }
        
        result = await basic_workflows.create_basic_architecture_workflow(
            project_name="Test Project",
            prd_id="invalid-id"
        )
        
        assert result["workflow_status"] == "error"
        assert "PRD validation failed" in result["message"]
        assert len(result["step_results"]) == 1  # Only validation step failed


class TestHILIntegration:
    """Test HIL (Human-in-the-Loop) integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_prd_hil_required(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test PRD HIL requirement detection."""
        # Mock document with template placeholders
        mock_bmad_handlers.bmad_prd_create.return_value = {
            "success": True,
            "doc_id": "test-prd-id",
            "data": {
                "id": "test-prd-id",
                "kind": "PRD",
                "content": "# Test PRD\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        result = await basic_workflows.create_basic_prd_workflow(
            project_name="Test Project"
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "hil_session_id" in result
        
        # Verify HIL session was triggered
        mock_hil_integration.trigger_hil_session.assert_called_once()
        call_args = mock_hil_integration.trigger_hil_session.call_args
        assert call_args[1]["doc_id"] == "test-prd-id"
        assert call_args[1]["doc_type"] == "PRD"
    
    @pytest.mark.asyncio
    async def test_architecture_hil_required(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test Architecture HIL requirement detection."""
        # Mock document with template placeholders
        mock_bmad_handlers.bmad_arch_create.return_value = {
            "success": True,
            "doc_id": "test-arch-id",
            "data": {
                "id": "test-arch-id",
                "kind": "ARCHITECTURE",
                "content": "# Test Architecture\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        result = await basic_workflows.create_basic_architecture_workflow(
            project_name="Test Project",
            prd_id="test-prd-id"
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "hil_session_id" in result
        
        # Verify HIL session was triggered for Architecture
        mock_hil_integration.trigger_hil_session.assert_called_once()
        call_args = mock_hil_integration.trigger_hil_session.call_args
        assert call_args[1]["doc_type"] == "ARCH"
    
    @pytest.mark.asyncio
    async def test_story_hil_required(self, basic_workflows, mock_bmad_handlers, mock_hil_integration):
        """Test Story HIL requirement detection."""
        # Mock document with template placeholders
        mock_bmad_handlers.bmad_story_create.return_value = {
            "success": True,
            "doc_id": "test-story-id",
            "data": {
                "id": "test-story-id",
                "kind": "STORY",
                "content": "# Test Story\n\n*[To be filled during interactive elicitation]*",
                "status": "draft"
            }
        }
        
        result = await basic_workflows.create_basic_story_workflow(
            project_name="Test Project",
            prd_id="test-prd-id",
            arch_id="test-arch-id"
        )
        
        assert result["workflow_status"] == "paused_for_hil"
        assert "hil_session_id" in result
        
        # Verify HIL session was triggered for Story
        mock_hil_integration.trigger_hil_session.assert_called_once()
        call_args = mock_hil_integration.trigger_hil_session.call_args
        assert call_args[1]["doc_type"] == "STORY"


if __name__ == "__main__":
    pytest.main([__file__])
