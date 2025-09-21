#!/usr/bin/env python3
"""
Test script for Documentation Management functionality.

This script validates the documentation management capabilities
for BMAD integration.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.direct_client import execute_mcp_tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_documentation_generate():
    """Test the documentation generation functionality."""
    logger.info("Testing documentation generation...")
    
    try:
        result = await execute_mcp_tool("bmad_documentation_generate")
        
        logger.info(f"Documentation generation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "files_created" in result, "Result should contain 'files_created' field"
        assert "files_updated" in result, "Result should contain 'files_updated' field"
        
        # Validate files were created
        files_created = result["files_created"]
        assert len(files_created) > 0, "Should have created at least one file"
        
        # Check for expected documentation files
        expected_files = [
            "BMAD_INTEGRATION_GUIDE.md",
            "BMAD_INSTALLATION_GUIDE.md",
            "BMAD_TROUBLESHOOTING_GUIDE.md",
            "BMAD_API_REFERENCE.md",
            "BMAD_CONFIGURATION_GUIDE.md"
        ]
        
        for expected_file in expected_files:
            file_found = any(expected_file in file_path for file_path in files_created)
            assert file_found, f"Expected file {expected_file} should be created"
        
        # Check for expected runbook files
        expected_runbooks = [
            "INSTALLATION_RUNBOOK.md",
            "UNINSTALL_RUNBOOK.md",
            "TROUBLESHOOTING_RUNBOOK.md",
            "MAINTENANCE_RUNBOOK.md"
        ]
        
        for expected_runbook in expected_runbooks:
            runbook_found = any(expected_runbook in file_path for file_path in files_created)
            assert runbook_found, f"Expected runbook {expected_runbook} should be created"
        
        logger.info("✅ Documentation generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation generation test failed: {e}")
        return False


async def test_documentation_validate():
    """Test the documentation validation functionality."""
    logger.info("Testing documentation validation...")
    
    try:
        result = await execute_mcp_tool("bmad_documentation_validate")
        
        logger.info(f"Documentation validation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "errors" in result, "Result should contain 'errors' field"
        assert "warnings" in result, "Result should contain 'warnings' field"
        
        # Validate that documentation exists (should be true after generation)
        assert result["success"], "Documentation validation should succeed after generation"
        
        logger.info("✅ Documentation validation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation validation test failed: {e}")
        return False


async def test_documentation_list():
    """Test the documentation listing functionality."""
    logger.info("Testing documentation listing...")
    
    try:
        result = await execute_mcp_tool("bmad_documentation_list")
        
        logger.info(f"Documentation listing result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "documentation_files" in result, "Result should contain 'documentation_files' field"
        assert "runbook_files" in result, "Result should contain 'runbook_files' field"
        assert "total_docs" in result, "Result should contain 'total_docs' field"
        assert "total_runbooks" in result, "Result should contain 'total_runbooks' field"
        
        # Validate that files are listed
        docs_files = result["documentation_files"]
        runbooks_files = result["runbook_files"]
        
        assert len(docs_files) > 0, "Should have at least one documentation file"
        assert len(runbooks_files) > 0, "Should have at least one runbook file"
        
        # Validate file structure
        for doc_file in docs_files:
            assert "name" in doc_file, "Documentation file should contain 'name' field"
            assert "path" in doc_file, "Documentation file should contain 'path' field"
            assert "size" in doc_file, "Documentation file should contain 'size' field"
            assert "modified" in doc_file, "Documentation file should contain 'modified' field"
        
        for runbook_file in runbooks_files:
            assert "name" in runbook_file, "Runbook file should contain 'name' field"
            assert "path" in runbook_file, "Runbook file should contain 'path' field"
            assert "size" in runbook_file, "Runbook file should contain 'size' field"
            assert "modified" in runbook_file, "Runbook file should contain 'modified' field"
        
        logger.info("✅ Documentation listing test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation listing test failed: {e}")
        return False


async def test_documentation_get_content():
    """Test the documentation content retrieval functionality."""
    logger.info("Testing documentation content retrieval...")
    
    try:
        # Get content of a specific documentation file
        result = await execute_mcp_tool(
            "bmad_documentation_get_content",
            file_path="docs/BMAD_INTEGRATION_GUIDE.md"
        )
        
        logger.info(f"Documentation content retrieval result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "file_path" in result, "Result should contain 'file_path' field"
        assert "content" in result, "Result should contain 'content' field"
        assert "size" in result, "Result should contain 'size' field"
        
        # Validate content
        content = result["content"]
        assert len(content) > 0, "Content should not be empty"
        assert "# BMAD Integration Guide" in content, "Content should contain expected title"
        
        logger.info("✅ Documentation content retrieval test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation content retrieval test failed: {e}")
        return False


async def test_documentation_create_section():
    """Test the documentation section creation functionality."""
    logger.info("Testing documentation section creation...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_documentation_create_section",
            section_name="test_section",
            title="Test Section",
            content="This is a test section for validation purposes."
        )
        
        logger.info(f"Documentation section creation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "file_path" in result, "Result should contain 'file_path' field"
        
        # Validate file was created
        file_path = result["file_path"]
        assert "test_section.md" in file_path, "File path should contain test_section.md"
        
        logger.info("✅ Documentation section creation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation section creation test failed: {e}")
        return False


async def test_documentation_update():
    """Test the documentation update functionality."""
    logger.info("Testing documentation update...")
    
    try:
        # Update a specific documentation section
        new_content = """# BMAD Integration Guide (Updated)

## Overview
This guide provides comprehensive information about integrating BMAD (Breakthrough Method of Agile AI-driven Development) with the CFlow platform.

## Updated Architecture
The BMAD integration consists of several key components:
- WebMCP Server
- BMAD API Service
- Vendor BMAD Workflows
- MCP Tool Registry
- Direct Client Routing

## Updated Components

### WebMCP Server
The WebMCP server provides the central MCP instance running in the Cerebral cloud cluster.

### BMAD API Service
A dedicated Kubernetes deployment in the Cerebral cluster exposing BMAD functionality via HTTP.

### Vendor BMAD
The core BMAD-METHOD codebase vendored into vendor/bmad/.

## Updated Integration Flow
1. WebMCP receives tool calls
2. Routes to BMAD API Service
3. BMAD API Service executes vendor BMAD workflows
4. Results returned through the chain

## Updated Configuration
See BMAD_CONFIGURATION_GUIDE.md for detailed configuration information.

## Updated Troubleshooting
See BMAD_TROUBLESHOOTING_GUIDE.md for common issues and solutions.
"""
        
        result = await execute_mcp_tool(
            "bmad_documentation_update",
            section="integration",
            content=new_content
        )
        
        logger.info(f"Documentation update result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "files_updated" in result, "Result should contain 'files_updated' field"
        
        # Validate file was updated
        files_updated = result["files_updated"]
        assert len(files_updated) > 0, "Should have updated at least one file"
        
        logger.info("✅ Documentation update test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Documentation update test failed: {e}")
        return False


async def test_runbook_generate():
    """Test the runbook generation functionality."""
    logger.info("Testing runbook generation...")
    
    try:
        # Create a test runbook with steps
        test_steps = [
            {
                "step_number": 1,
                "title": "Test Step 1",
                "description": "This is the first test step",
                "commands": ["echo 'Test step 1'"],
                "expected_output": "Test step 1",
                "troubleshooting": "Check command syntax",
                "prerequisites": ["Test environment"]
            },
            {
                "step_number": 2,
                "title": "Test Step 2",
                "description": "This is the second test step",
                "commands": ["echo 'Test step 2'"],
                "expected_output": "Test step 2",
                "troubleshooting": "Check command syntax",
                "prerequisites": ["Test environment", "Step 1 completed"]
            }
        ]
        
        result = await execute_mcp_tool(
            "bmad_runbook_generate",
            runbook_type="test",
            steps=json.dumps(test_steps)
        )
        
        logger.info(f"Runbook generation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "files_created" in result, "Result should contain 'files_created' field"
        
        # Validate file was created
        files_created = result["files_created"]
        assert len(files_created) > 0, "Should have created at least one file"
        
        logger.info("✅ Runbook generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Runbook generation test failed: {e}")
        return False


async def test_documentation_update_runbook():
    """Test the runbook update functionality."""
    logger.info("Testing runbook update...")
    
    try:
        # Update a specific runbook
        new_content = """# Test Runbook (Updated)

## Step 1: Updated Test Step 1

This is the updated first test step

**Prerequisites**:
- Updated test environment

**Commands**:
```bash
echo 'Updated test step 1'
```

**Expected Output**: Updated test step 1

**Troubleshooting**: Check updated command syntax

## Step 2: Updated Test Step 2

This is the updated second test step

**Prerequisites**:
- Updated test environment
- Step 1 completed

**Commands**:
```bash
echo 'Updated test step 2'
```

**Expected Output**: Updated test step 2

**Troubleshooting**: Check updated command syntax
"""
        
        result = await execute_mcp_tool(
            "bmad_documentation_update_runbook",
            runbook_name="test",
            content=new_content
        )
        
        logger.info(f"Runbook update result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "file_path" in result, "Result should contain 'file_path' field"
        
        logger.info("✅ Runbook update test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Runbook update test failed: {e}")
        return False


async def run_all_tests():
    """Run all documentation management tests."""
    logger.info("Starting Documentation Management validation...")
    
    tests = [
        ("Documentation Generation Test", test_documentation_generate),
        ("Documentation Validation Test", test_documentation_validate),
        ("Documentation Listing Test", test_documentation_list),
        ("Documentation Content Retrieval Test", test_documentation_get_content),
        ("Documentation Section Creation Test", test_documentation_create_section),
        ("Documentation Update Test", test_documentation_update),
        ("Runbook Generation Test", test_runbook_generate),
        ("Runbook Update Test", test_documentation_update_runbook)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        start_time = time.time()
        success = await test_func()
        duration = time.time() - start_time
        
        results.append({
            "test": test_name,
            "success": success,
            "duration": duration
        })
        
        if success:
            logger.info(f"✅ {test_name} completed successfully in {duration:.2f}s")
        else:
            logger.error(f"❌ {test_name} failed after {duration:.2f}s")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("DOCUMENTATION MANAGEMENT VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Documentation Management tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
