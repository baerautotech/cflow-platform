#!/usr/bin/env python3
"""
Test script for Uninstall and Rollback functionality.

This script validates the uninstall and rollback capabilities
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


async def test_uninstall_validate():
    """Test the uninstall validation functionality."""
    logger.info("Testing uninstall validation...")
    
    try:
        result = await execute_mcp_tool("bmad_uninstall_validate")
        
        logger.info(f"Uninstall validation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "validation_results" in result, "Result should contain 'validation_results' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        
        # Validate validation results structure
        validation_results = result["validation_results"]
        assert len(validation_results) > 0, "Should have at least one validation result"
        
        for step_name, step_info in validation_results.items():
            assert "description" in step_info, f"Step {step_name} should contain 'description' field"
            assert "action" in step_info, f"Step {step_name} should contain 'action' field"
            assert "target_path" in step_info, f"Step {step_name} should contain 'target_path' field"
        
        logger.info("✅ Uninstall validation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Uninstall validation test failed: {e}")
        return False


async def test_uninstall_simulate():
    """Test the uninstall simulation functionality."""
    logger.info("Testing uninstall simulation...")
    
    try:
        result = await execute_mcp_tool("bmad_uninstall_simulate")
        
        logger.info(f"Uninstall simulation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "simulation_results" in result, "Result should contain 'simulation_results' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        assert "message" in result, "Result should contain 'message' field"
        
        # Validate simulation results structure
        simulation_results = result["simulation_results"]
        assert len(simulation_results) > 0, "Should have at least one simulation result"
        
        for step_name, step_info in simulation_results.items():
            assert "description" in step_info, f"Step {step_name} should contain 'description' field"
            assert "action" in step_info, f"Step {step_name} should contain 'action' field"
            assert "target_path" in step_info, f"Step {step_name} should contain 'target_path' field"
            assert "would_remove" in step_info, f"Step {step_name} should contain 'would_remove' field"
            assert "would_execute" in step_info, f"Step {step_name} should contain 'would_execute' field"
        
        logger.info("✅ Uninstall simulation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Uninstall simulation test failed: {e}")
        return False


async def test_rollback_create_point():
    """Test the rollback point creation functionality."""
    logger.info("Testing rollback point creation...")
    
    try:
        # Create a test rollback point
        result = await execute_mcp_tool(
            "bmad_rollback_create_point",
            name="test_rollback_point",
            description="Test rollback point for validation"
        )
        
        logger.info(f"Rollback point creation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "rollback_point" in result, "Result should contain 'rollback_point' field"
        assert "restored_files" in result, "Result should contain 'restored_files' field"
        assert "rollback_time" in result, "Result should contain 'rollback_time' field"
        
        # Validate rollback point name
        assert result["rollback_point"] == "test_rollback_point", "Rollback point name should match"
        
        logger.info("✅ Rollback point creation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback point creation test failed: {e}")
        return False


async def test_rollback_list_points():
    """Test the rollback points listing functionality."""
    logger.info("Testing rollback points listing...")
    
    try:
        result = await execute_mcp_tool("bmad_rollback_list_points")
        
        logger.info(f"Rollback points listing result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "rollback_points" in result, "Result should contain 'rollback_points' field"
        assert "total_points" in result, "Result should contain 'total_points' field"
        
        # Validate rollback points structure
        rollback_points = result["rollback_points"]
        assert isinstance(rollback_points, list), "Rollback points should be a list"
        
        # Check if our test rollback point exists
        test_point_found = any(point.get("name") == "test_rollback_point" for point in rollback_points)
        assert test_point_found, "Test rollback point should be found in the list"
        
        logger.info("✅ Rollback points listing test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback points listing test failed: {e}")
        return False


async def test_rollback_get_point_info():
    """Test the rollback point info retrieval functionality."""
    logger.info("Testing rollback point info retrieval...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_rollback_get_point_info",
            rollback_point_name="test_rollback_point"
        )
        
        logger.info(f"Rollback point info result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "rollback_point" in result, "Result should contain 'rollback_point' field"
        assert "metadata" in result, "Result should contain 'metadata' field"
        
        # Validate rollback point name
        assert result["rollback_point"] == "test_rollback_point", "Rollback point name should match"
        
        # Validate metadata structure
        metadata = result["metadata"]
        assert "name" in metadata, "Metadata should contain 'name' field"
        assert "timestamp" in metadata, "Metadata should contain 'timestamp' field"
        assert "files" in metadata, "Metadata should contain 'files' field"
        assert "directories" in metadata, "Metadata should contain 'directories' field"
        
        logger.info("✅ Rollback point info retrieval test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback point info retrieval test failed: {e}")
        return False


async def test_rollback_to_point():
    """Test the rollback to point functionality."""
    logger.info("Testing rollback to point...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_rollback_to_point",
            rollback_point_name="test_rollback_point"
        )
        
        logger.info(f"Rollback to point result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "rollback_point" in result, "Result should contain 'rollback_point' field"
        assert "restored_files" in result, "Result should contain 'restored_files' field"
        assert "rollback_time" in result, "Result should contain 'rollback_time' field"
        
        # Validate rollback point name
        assert result["rollback_point"] == "test_rollback_point", "Rollback point name should match"
        
        logger.info("✅ Rollback to point test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback to point test failed: {e}")
        return False


async def test_uninstall_step():
    """Test the uninstall step functionality."""
    logger.info("Testing uninstall step...")
    
    try:
        # Test a specific uninstall step
        result = await execute_mcp_tool(
            "bmad_uninstall_step",
            step_name="backup_current_state"
        )
        
        logger.info(f"Uninstall step result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "step_name" in result, "Result should contain 'step_name' field"
        assert "result" in result, "Result should contain 'result' field"
        
        # Validate step name
        assert result["step_name"] == "backup_current_state", "Step name should match"
        
        logger.info("✅ Uninstall step test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Uninstall step test failed: {e}")
        return False


async def test_uninstall_complete():
    """Test the complete uninstall functionality."""
    logger.info("Testing complete uninstall...")
    
    try:
        # Test complete uninstall with simulation (force=False to avoid actual uninstall)
        result = await execute_mcp_tool(
            "bmad_uninstall_complete",
            create_backup=True,
            remove_vendor_bmad=False,
            force=False
        )
        
        logger.info(f"Complete uninstall result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        assert "completed_steps" in result, "Result should contain 'completed_steps' field"
        assert "failed_steps" in result, "Result should contain 'failed_steps' field"
        assert "step_results" in result, "Result should contain 'step_results' field"
        assert "uninstall_time" in result, "Result should contain 'uninstall_time' field"
        assert "cleanup_time" in result, "Result should contain 'cleanup_time' field"
        
        logger.info("✅ Complete uninstall test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete uninstall test failed: {e}")
        return False


async def test_rollback_delete_point():
    """Test the rollback point deletion functionality."""
    logger.info("Testing rollback point deletion...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_rollback_delete_point",
            rollback_point_name="test_rollback_point"
        )
        
        logger.info(f"Rollback point deletion result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "rollback_point" in result, "Result should contain 'rollback_point' field"
        
        # Validate rollback point name
        assert result["rollback_point"] == "test_rollback_point", "Rollback point name should match"
        
        logger.info("✅ Rollback point deletion test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback point deletion test failed: {e}")
        return False


async def run_all_tests():
    """Run all uninstall and rollback tests."""
    logger.info("Starting Uninstall and Rollback validation...")
    
    tests = [
        ("Uninstall Validation Test", test_uninstall_validate),
        ("Uninstall Simulation Test", test_uninstall_simulate),
        ("Rollback Point Creation Test", test_rollback_create_point),
        ("Rollback Points Listing Test", test_rollback_list_points),
        ("Rollback Point Info Retrieval Test", test_rollback_get_point_info),
        ("Rollback to Point Test", test_rollback_to_point),
        ("Uninstall Step Test", test_uninstall_step),
        ("Complete Uninstall Test", test_uninstall_complete),
        ("Rollback Point Deletion Test", test_rollback_delete_point)
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
    logger.info("UNINSTALL AND ROLLBACK VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Uninstall and Rollback tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
