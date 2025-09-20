"""
Tests for BMAD Git Workflow functionality.

This module tests the git workflow integration for BMAD workflows.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from cflow_platform.core.bmad_git_workflow import BMADGitWorkflow
from cflow_platform.core.git_workflow_migration import GitWorkflowMigration


class TestBMADGitWorkflow:
    """Test cases for BMAD Git Workflow."""
    
    @pytest.fixture
    def git_workflow(self):
        """Create a BMADGitWorkflow instance for testing."""
        return BMADGitWorkflow()
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        return mock_client
    
    @pytest.mark.asyncio
    async def test_commit_bmad_changes_success(self, git_workflow, mock_supabase):
        """Test successful BMAD commit workflow."""
        # Mock the git operations
        with patch('cflow_platform.core.bmad_git_workflow.attempt_auto_commit') as mock_commit, \
             patch.object(git_workflow, 'supabase_client', mock_supabase), \
             patch.object(git_workflow, '_track_bmad_commit', return_value={"tracking_id": "test-tracking-id"}):
            
            mock_commit.return_value = {
                "status": "success",
                "commit": "abc123",
                "branch": "main"
            }
            
            result = await git_workflow.commit_bmad_changes(
                workflow_id="test-workflow",
                project_id="test-project",
                changes_summary="Test changes",
                document_ids=["doc1", "doc2"]
            )
            
            assert result["success"] is True
            assert result["commit_hash"] == "abc123"
            assert result["branch"] == "main"
            assert result["tracking_id"] == "test-tracking-id"
    
    @pytest.mark.asyncio
    async def test_commit_bmad_changes_failure(self, git_workflow):
        """Test BMAD commit workflow failure."""
        with patch('cflow_platform.core.bmad_git_workflow.attempt_auto_commit') as mock_commit:
            mock_commit.return_value = {
                "status": "error",
                "error": "Git commit failed"
            }
            
            result = await git_workflow.commit_bmad_changes(
                workflow_id="test-workflow",
                project_id="test-project",
                changes_summary="Test changes"
            )
            
            assert result["success"] is False
            assert "Git commit failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_push_bmad_changes_success(self, git_workflow, mock_supabase):
        """Test successful BMAD push workflow."""
        # Mock tracking info
        tracking_info = {
            "workflow_id": "test-workflow",
            "project_id": "test-project",
            "branch": "main"
        }
        
        with patch.object(git_workflow, 'supabase_client', mock_supabase), \
             patch.object(git_workflow, '_get_commit_tracking', return_value=tracking_info), \
             patch('cflow_platform.core.bmad_git_workflow._run_git') as mock_git, \
             patch('cflow_platform.core.bmad_git_workflow._repo_root', return_value="/test/repo"), \
             patch.object(git_workflow, '_update_push_status', return_value=True):
            
            mock_git.return_value = Mock(success=True, stdout="Push successful")
            
            result = await git_workflow.push_bmad_changes(
                tracking_id="test-tracking-id"
            )
            
            assert result["success"] is True
            assert result["tracking_id"] == "test-tracking-id"
            assert result["branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_validate_bmad_changes_comprehensive(self, git_workflow, mock_supabase):
        """Test comprehensive BMAD validation."""
        with patch.object(git_workflow, 'supabase_client', mock_supabase), \
             patch('cflow_platform.core.bmad_git_workflow._repo_root', return_value="/test/repo"), \
             patch('cflow_platform.core.bmad_git_workflow._run_git') as mock_git, \
             patch.object(git_workflow, '_validate_bmad_documents', return_value={"status": "passed"}), \
             patch.object(git_workflow, '_validate_workflow_state', return_value={"status": "passed"}), \
             patch.object(git_workflow, '_store_validation_results', return_value=True):
            
            mock_git.return_value = Mock(stdout="M  file1.py\nA  file2.py")
            
            result = await git_workflow.validate_bmad_changes(
                workflow_id="test-workflow",
                project_id="test-project",
                validation_type="comprehensive"
            )
            
            assert result["success"] is True
            assert "validation_results" in result
            validation = result["validation_results"]
            assert validation["overall_status"] == "passed"
            assert "checks" in validation
            assert validation["checks"]["git_repo"]["status"] == "passed"
            assert validation["checks"]["uncommitted_changes"]["has_changes"] is True
    
    @pytest.mark.asyncio
    async def test_get_bmad_commit_history(self, git_workflow, mock_supabase):
        """Test getting BMAD commit history."""
        mock_commits = [
            {
                "id": "commit1",
                "workflow_id": "workflow1",
                "commit_hash": "abc123",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "commit2", 
                "workflow_id": "workflow2",
                "commit_hash": "def456",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = mock_commits
        
        with patch.object(git_workflow, 'supabase_client', mock_supabase):
            result = await git_workflow.get_bmad_commit_history(
                project_id="test-project",
                limit=10
            )
            
            assert result["success"] is True
            assert len(result["commits"]) == 2
            assert result["count"] == 2
            assert result["commits"][0]["commit_hash"] == "abc123"
    
    def test_generate_bmad_commit_message(self, git_workflow):
        """Test BMAD commit message generation."""
        message = git_workflow._generate_bmad_commit_message(
            workflow_id="test-workflow",
            changes_summary="Updated PRD and Architecture",
            document_ids=["doc1", "doc2", "doc3", "doc4", "doc5"]
        )
        
        assert "bmad: test-workflow" in message
        assert "Changes: Updated PRD and Architecture" in message
        assert "Documents: doc1, doc2, doc3" in message
        assert "... and 2 more" in message


class TestGitWorkflowMigration:
    """Test cases for Git Workflow Migration."""
    
    @pytest.fixture
    def migration(self):
        """Create a GitWorkflowMigration instance for testing."""
        return GitWorkflowMigration()
    
    @pytest.mark.asyncio
    async def test_verify_tables_exist_all_exist(self, migration):
        """Test table verification when all tables exist."""
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
        
        with patch.object(migration, 'supabase_client', mock_client):
            result = await migration.verify_tables_exist()
            
            assert result["success"] is True
            assert len(result["existing_tables"]) == 3
            assert len(result["missing_tables"]) == 0
            assert result["all_tables_exist"] is True
    
    @pytest.mark.asyncio
    async def test_verify_tables_exist_some_missing(self, migration):
        """Test table verification when some tables are missing."""
        mock_client = Mock()
        
        # Mock that only one table exists
        def mock_table(table_name):
            if table_name == "bmad_commit_tracking":
                mock_table_obj = Mock()
                mock_table_obj.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
                return mock_table_obj
            else:
                raise Exception("Table does not exist")
        
        mock_client.table.side_effect = mock_table
        
        with patch.object(migration, 'supabase_client', mock_client):
            result = await migration.verify_tables_exist()
            
            assert result["success"] is True
            assert len(result["existing_tables"]) == 1
            assert len(result["missing_tables"]) == 2
            assert result["all_tables_exist"] is False
    
    @pytest.mark.asyncio
    async def test_create_git_workflow_tables_success(self, migration):
        """Test successful table creation."""
        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = Mock(data=[])
        
        with patch.object(migration, 'supabase_client', mock_client):
            result = await migration.create_git_workflow_tables()
            
            assert result["success"] is True
            assert "bmad_commit_tracking" in result["results"]
            assert "bmad_validation_results" in result["results"]
            assert "bmad_git_workflow_status" in result["results"]
    
    @pytest.mark.asyncio
    async def test_create_git_workflow_tables_no_supabase(self, migration):
        """Test table creation when Supabase is not available."""
        with patch.object(migration, 'supabase_client', None):
            result = await migration.create_git_workflow_tables()
            
            assert result["success"] is False
            assert "Supabase client not available" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])
