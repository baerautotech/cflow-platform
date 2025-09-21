#!/usr/bin/env python3
"""
Test script for Installation Flow Testing functionality.

This script validates the installation flow testing capabilities
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


async def test_installation_prerequisites():
    """Test the installation prerequisites functionality."""
    logger.info("Testing installation prerequisites...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_test_prerequisites")
        
        logger.info(f"Installation prerequisites result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "prerequisites" in result, "Result should contain 'prerequisites' field"
        
        logger.info("✅ Installation prerequisites test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation prerequisites test failed: {e}")
        return False


async def test_installation_flow_steps():
    """Test the installation flow steps functionality."""
    logger.info("Testing installation flow steps...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_get_flow_steps")
        
        logger.info(f"Installation flow steps result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "steps" in result, "Result should contain 'steps' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        
        # Validate steps structure
        steps = result["steps"]
        assert len(steps) > 0, "Should have at least one installation step"
        
        for step in steps:
            assert "name" in step, "Step should contain 'name' field"
            assert "description" in step, "Step should contain 'description' field"
            assert "command" in step, "Step should contain 'command' field"
        
        logger.info("✅ Installation flow steps test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation flow steps test failed: {e}")
        return False


async def test_installation_environment_validation():
    """Test the installation environment validation functionality."""
    logger.info("Testing installation environment validation...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_validate_environment")
        
        logger.info(f"Installation environment validation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "step" in result, "Result should contain 'step' field"
        assert "result" in result, "Result should contain 'result' field"
        
        logger.info("✅ Installation environment validation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation environment validation test failed: {e}")
        return False


async def test_installation_components_validation():
    """Test the installation components validation functionality."""
    logger.info("Testing installation components validation...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_validate_components")
        
        logger.info(f"Installation components validation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "checks" in result, "Result should contain 'checks' field"
        
        logger.info("✅ Installation components validation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation components validation test failed: {e}")
        return False


async def test_installation_step_test():
    """Test the installation step testing functionality."""
    logger.info("Testing installation step testing...")
    
    try:
        # Test a specific installation step
        result = await execute_mcp_tool(
            "bmad_installation_step_test",
            step_name="environment_validation"
        )
        
        logger.info(f"Installation step test result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "step_name" in result, "Result should contain 'step_name' field"
        assert "result" in result, "Result should contain 'result' field"
        
        logger.info("✅ Installation step test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation step test failed: {e}")
        return False


async def test_installation_rollback():
    """Test the installation rollback functionality."""
    logger.info("Testing installation rollback...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_rollback_test")
        
        logger.info(f"Installation rollback result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        assert "completed_steps" in result, "Result should contain 'completed_steps' field"
        
        logger.info("✅ Installation rollback test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation rollback test failed: {e}")
        return False


async def test_installation_flow_test():
    """Test the complete installation flow testing functionality."""
    logger.info("Testing complete installation flow...")
    
    try:
        # Test with skip_optional_steps to avoid long-running tests
        result = await execute_mcp_tool(
            "bmad_installation_flow_test",
            test_environment=False,
            skip_optional_steps=True
        )
        
        logger.info(f"Installation flow test result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "total_steps" in result, "Result should contain 'total_steps' field"
        assert "completed_steps" in result, "Result should contain 'completed_steps' field"
        assert "failed_steps" in result, "Result should contain 'failed_steps' field"
        assert "step_results" in result, "Result should contain 'step_results' field"
        assert "installation_time" in result, "Result should contain 'installation_time' field"
        assert "validation_time" in result, "Result should contain 'validation_time' field"
        
        logger.info("✅ Installation flow test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation flow test failed: {e}")
        return False


async def test_installation_report_generation():
    """Test the installation report generation functionality."""
    logger.info("Testing installation report generation...")
    
    try:
        result = await execute_mcp_tool("bmad_installation_generate_report")
        
        logger.info(f"Installation report generation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "report" in result, "Result should contain 'report' field"
        
        # Validate report structure
        report = result["report"]
        assert "installation_flow" in report, "Report should contain 'installation_flow' field"
        assert "prerequisites" in report, "Report should contain 'prerequisites' field"
        assert "validation_checks" in report, "Report should contain 'validation_checks' field"
        
        logger.info("✅ Installation report generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation report generation test failed: {e}")
        return False


async def run_all_tests():
    """Run all installation flow testing tests."""
    logger.info("Starting Installation Flow Testing validation...")
    
    tests = [
        ("Installation Prerequisites Test", test_installation_prerequisites),
        ("Installation Flow Steps Test", test_installation_flow_steps),
        ("Installation Environment Validation Test", test_installation_environment_validation),
        ("Installation Components Validation Test", test_installation_components_validation),
        ("Installation Step Test", test_installation_step_test),
        ("Installation Rollback Test", test_installation_rollback),
        ("Installation Flow Test", test_installation_flow_test),
        ("Installation Report Generation Test", test_installation_report_generation)
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
    logger.info("INSTALLATION FLOW TESTING VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Installation Flow Testing tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
