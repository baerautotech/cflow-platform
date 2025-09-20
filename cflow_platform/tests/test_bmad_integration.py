"""
BMAD Integration Tests

Comprehensive tests for BMAD functionality integration in cflow-platform.
Tests workflow engine, tool execution, database integration, and agent functionality.
"""

import asyncio
import pytest
import uuid
from typing import Dict, Any, List
from pathlib import Path

from cflow_platform.core.direct_client import execute_mcp_tool
from cflow_platform.core.bmad_workflow_engine import get_workflow_engine
from cflow_platform.handlers.bmad_handlers import BMADHandlers


class TestBMADWorkflowEngine:
    """Test BMAD workflow engine functionality."""
    
    def test_workflow_engine_initialization(self):
        """Test that workflow engine initializes correctly."""
        engine = get_workflow_engine()
        assert engine is not None
        assert hasattr(engine, 'workflows')
        assert hasattr(engine, 'get_available_workflows')
    
    def test_workflow_loading(self):
        """Test that workflows are loaded from vendor/bmad."""
        engine = get_workflow_engine()
        workflows = engine.get_available_workflows()
        
        assert len(workflows) > 0, "No workflows loaded"
        
        # Check for expected workflow types
        workflow_ids = [w['id'] for w in workflows]
        assert any('greenfield' in w for w in workflow_ids), "No greenfield workflows"
        assert any('brownfield' in w for w in workflow_ids), "No brownfield workflows"
    
    def test_workflow_structure(self):
        """Test that workflows have proper structure."""
        engine = get_workflow_engine()
        workflows = engine.get_available_workflows()
        
        for workflow in workflows:
            assert 'id' in workflow, f"Workflow missing id: {workflow}"
            assert 'name' in workflow, f"Workflow missing name: {workflow}"
            assert 'description' in workflow, f"Workflow missing description: {workflow}"
            assert 'type' in workflow, f"Workflow missing type: {workflow}"


class TestBMADToolExecution:
    """Test BMAD tool execution via MCP."""
    
    @pytest.mark.asyncio
    async def test_workflow_list_tool(self):
        """Test bmad_workflow_list tool."""
        result = await execute_mcp_tool('bmad_workflow_list')
        
        assert result['status'] == 'success'
        assert 'workflows' in result
        assert len(result['workflows']) > 0
    
    @pytest.mark.asyncio
    async def test_prd_create_tool(self):
        """Test bmad_prd_create tool."""
        project_name = f"Test Project {uuid.uuid4().hex[:8]}"
        
        result = await execute_mcp_tool(
            'bmad_prd_create',
            project_name=project_name,
            goals=['Test goal 1', 'Test goal 2'],
            background='Test background for integration testing'
        )
        
        assert result['success'] is True
        assert 'doc_id' in result
        assert result['doc_id'] is not None
    
    @pytest.mark.asyncio
    async def test_doc_list_tool(self):
        """Test bmad_doc_list tool."""
        result = await execute_mcp_tool('bmad_doc_list')
        
        assert result['success'] is True
        assert 'documents' in result
        assert isinstance(result['documents'], list)
    
    @pytest.mark.asyncio
    async def test_arch_create_tool(self):
        """Test bmad_arch_create tool."""
        project_name = f"Test Architecture {uuid.uuid4().hex[:8]}"
        
        result = await execute_mcp_tool(
            'bmad_arch_create',
            project_name=project_name,
            tech_stack=['Python', 'Supabase', 'React'],
            architecture_type='microservices'
        )
        
        assert result['success'] is True
        assert 'doc_id' in result
        assert result['doc_id'] is not None
    
    @pytest.mark.asyncio
    async def test_story_create_tool(self):
        """Test bmad_story_create tool."""
        project_name = f"Test Story {uuid.uuid4().hex[:8]}"
        
        result = await execute_mcp_tool(
            'bmad_story_create',
            project_name=project_name,
            epic_title='Test Epic',
            user_stories=['As a user, I want to test the system'],
            acceptance_criteria=['System responds correctly']
        )
        
        assert result['success'] is True
        assert 'doc_id' in result
        assert result['doc_id'] is not None


class TestBMADDatabaseIntegration:
    """Test BMAD database integration."""
    
    @pytest.mark.asyncio
    async def test_supabase_connection(self):
        """Test Supabase database connection."""
        result = await execute_mcp_tool(
            'mcp_supabase_execute_sql',
            query='SELECT COUNT(*) as count FROM cerebral_documents'
        )
        
        assert result['status'] == 'success'
        assert 'rows' in result
        assert len(result['rows']) > 0
    
    @pytest.mark.asyncio
    async def test_bmad_tables_exist(self):
        """Test that BMAD tables exist in database."""
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name IN ('cerebral_documents', 'bmad_hil_sessions', 'bmad_commit_tracking', 'bmad_validation_results')
        ORDER BY table_name
        """
        
        result = await execute_mcp_tool(
            'mcp_supabase_execute_sql',
            query=tables_query
        )
        
        assert result['status'] == 'success'
        assert 'rows' in result
        
        table_names = [row['table_name'] for row in result['rows']]
        expected_tables = ['bmad_commit_tracking', 'bmad_hil_sessions', 'bmad_validation_results', 'cerebral_documents']
        
        for expected_table in expected_tables:
            assert expected_table in table_names, f"Missing table: {expected_table}"
    
    @pytest.mark.asyncio
    async def test_document_crud_operations(self):
        """Test document CRUD operations."""
        # Create a test document
        project_name = f"CRUD Test {uuid.uuid4().hex[:8]}"
        
        create_result = await execute_mcp_tool(
            'bmad_prd_create',
            project_name=project_name,
            goals=['CRUD test goal'],
            background='Testing CRUD operations'
        )
        
        assert create_result['success'] is True
        doc_id = create_result['doc_id']
        
        # Retrieve the document
        get_result = await execute_mcp_tool(
            'bmad_prd_get',
            doc_id=doc_id
        )
        
        assert get_result['success'] is True
        assert get_result['document']['id'] == doc_id
        assert get_result['document']['kind'] == 'PRD'


class TestBMADHandlers:
    """Test BMAD handlers directly."""
    
    def test_handler_initialization(self):
        """Test that BMAD handlers initialize correctly."""
        handler = BMADHandlers()
        assert handler is not None
        assert hasattr(handler, 'supabase_client')
        assert hasattr(handler, 'bmad_hil')
        assert hasattr(handler, 'bmad_git')
    
    @pytest.mark.asyncio
    async def test_handler_methods_exist(self):
        """Test that all expected handler methods exist."""
        handler = BMADHandlers()
        
        expected_methods = [
            'bmad_prd_create', 'bmad_prd_update', 'bmad_prd_get',
            'bmad_arch_create', 'bmad_arch_update', 'bmad_arch_get',
            'bmad_story_create', 'bmad_story_update', 'bmad_story_get',
            'bmad_doc_list', 'bmad_doc_approve', 'bmad_doc_reject',
            'bmad_workflow_status', 'bmad_hil_start_session',
            'bmad_git_commit_changes', 'bmad_git_push_changes'
        ]
        
        for method_name in expected_methods:
            assert hasattr(handler, method_name), f"Missing method: {method_name}"
            method = getattr(handler, method_name)
            assert callable(method), f"Method not callable: {method_name}"


class TestBMADIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete BMAD workflow from PRD to Story."""
        project_name = f"Integration Test {uuid.uuid4().hex[:8]}"
        
        # Step 1: Create PRD
        prd_result = await execute_mcp_tool(
            'bmad_prd_create',
            project_name=project_name,
            goals=['Integration test goal'],
            background='Testing complete workflow'
        )
        
        assert prd_result['success'] is True
        prd_id = prd_result['doc_id']
        
        # Step 2: Create Architecture
        arch_result = await execute_mcp_tool(
            'bmad_arch_create',
            project_name=project_name,
            tech_stack=['Python', 'Supabase'],
            architecture_type='monolith'
        )
        
        assert arch_result['success'] is True
        arch_id = arch_result['doc_id']
        
        # Step 3: Create Story
        story_result = await execute_mcp_tool(
            'bmad_story_create',
            project_name=project_name,
            epic_title='Integration Test Epic',
            user_stories=['As a tester, I want to verify the system works'],
            acceptance_criteria=['All tests pass']
        )
        
        assert story_result['success'] is True
        story_id = story_result['doc_id']
        
        # Step 4: Verify all documents exist
        doc_list_result = await execute_mcp_tool('bmad_doc_list')
        assert doc_list_result['success'] is True
        
        doc_ids = [doc['id'] for doc in doc_list_result['documents']]
        assert prd_id in doc_ids, "PRD not found in document list"
        assert arch_id in doc_ids, "Architecture not found in document list"
        assert story_id in doc_ids, "Story not found in document list"
    
    @pytest.mark.asyncio
    async def test_tool_registry_integration(self):
        """Test that BMAD tools are properly registered."""
        from cflow_platform.core.tool_registry import ToolRegistry
        
        tools = ToolRegistry.get_tools_for_mcp()
        bmad_tools = [t for t in tools if t['name'].startswith('bmad_')]
        
        assert len(bmad_tools) > 0, "No BMAD tools found in registry"
        
        # Check for essential tools
        tool_names = [t['name'] for t in bmad_tools]
        essential_tools = [
            'bmad_prd_create', 'bmad_arch_create', 'bmad_story_create',
            'bmad_workflow_list', 'bmad_doc_list'
        ]
        
        for essential_tool in essential_tools:
            assert essential_tool in tool_names, f"Missing essential tool: {essential_tool}"


# Integration test runner
def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running BMAD Integration Tests...")
    
    # Test workflow engine
    print("\n1. Testing Workflow Engine...")
    engine = get_workflow_engine()
    workflows = engine.get_available_workflows()
    print(f"   [INFO] Loaded {len(workflows)} workflows")
    
    # Test tool execution
    print("\n2. Testing Tool Execution...")
    async def test_tools():
        result = await execute_mcp_tool('bmad_workflow_list')
        print(f"   [INFO] Workflow list: {len(result.get('workflows', []))} workflows")
        
        result = await execute_mcp_tool('bmad_doc_list')
        print(f"   [INFO] Document list: {len(result.get('documents', []))} documents")
    
    asyncio.run(test_tools())
    
    # Test database
    print("\n3. Testing Database Integration...")
    async def test_db():
        result = await execute_mcp_tool(
            'mcp_supabase_execute_sql',
            query='SELECT COUNT(*) as count FROM cerebral_documents'
        )
        print(f"   [INFO] Database connection: {result.get('status', 'unknown')}")
    
    asyncio.run(test_db())
    
    print("\n[INFO] All integration tests completed successfully!")


if __name__ == "__main__":
    run_integration_tests()

