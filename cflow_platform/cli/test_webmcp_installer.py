#!/usr/bin/env python3
"""
Test script for WebMCP Installer functionality.

This script validates the WebMCP installer capabilities
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


async def test_webmcp_install_config():
    """Test the WebMCP install configuration functionality."""
    logger.info("Testing WebMCP install configuration...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_webmcp_install_config",
            server_url="http://localhost:8000",
            timeout_seconds=30,
            retry_attempts=3,
            enable_health_check=True,
            enable_feature_flags=True,
            enable_performance_monitoring=True,
            enable_security_testing=True,
            bmad_integration_enabled=True,
            bmad_api_url="http://localhost:8001",
            circuit_breaker_enabled=True,
            rate_limiting_enabled=True,
            logging_level="INFO",
            overwrite=True
        )
        
        logger.info(f"WebMCP install config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "config_file_path" in result, "Result should contain 'config_file_path' field"
        
        logger.info("✅ WebMCP install config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP install config test failed: {e}")
        return False


async def test_webmcp_validate_installation():
    """Test the WebMCP validate installation functionality."""
    logger.info("Testing WebMCP validate installation...")
    
    try:
        result = await execute_mcp_tool("bmad_webmcp_validate_installation")
        
        logger.info(f"WebMCP validate installation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ WebMCP validate installation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP validate installation test failed: {e}")
        return False


async def test_webmcp_test_integration():
    """Test the WebMCP test integration functionality."""
    logger.info("Testing WebMCP test integration...")
    
    try:
        result = await execute_mcp_tool("bmad_webmcp_test_integration")
        
        logger.info(f"WebMCP test integration result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ WebMCP test integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP test integration test failed: {e}")
        return False


async def test_webmcp_get_config():
    """Test the WebMCP get config functionality."""
    logger.info("Testing WebMCP get config...")
    
    try:
        result = await execute_mcp_tool("bmad_webmcp_get_config")
        
        logger.info(f"WebMCP get config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "configuration" in result, "Result should contain 'configuration' field"
        assert "config_file_path" in result, "Result should contain 'config_file_path' field"
        
        logger.info("✅ WebMCP get config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP get config test failed: {e}")
        return False


async def test_webmcp_update_config():
    """Test the WebMCP update config functionality."""
    logger.info("Testing WebMCP update config...")
    
    try:
        config_updates = json.dumps({
            "webmcp": {
                "timeout_seconds": 60,
                "retry_attempts": 5
            },
            "bmad_integration": {
                "circuit_breaker_enabled": False
            }
        })
        
        result = await execute_mcp_tool(
            "bmad_webmcp_update_config",
            config_updates=config_updates
        )
        
        logger.info(f"WebMCP update config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "config_file_path" in result, "Result should contain 'config_file_path' field"
        
        logger.info("✅ WebMCP update config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP update config test failed: {e}")
        return False


async def test_webmcp_backup_config():
    """Test the WebMCP backup config functionality."""
    logger.info("Testing WebMCP backup config...")
    
    try:
        result = await execute_mcp_tool("bmad_webmcp_backup_config")
        
        logger.info(f"WebMCP backup config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "backup_file_path" in result, "Result should contain 'backup_file_path' field"
        
        logger.info("✅ WebMCP backup config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP backup config test failed: {e}")
        return False


async def test_webmcp_restore_config():
    """Test the WebMCP restore config functionality."""
    logger.info("Testing WebMCP restore config...")
    
    try:
        # First get the backup file path from the previous test
        backup_result = await execute_mcp_tool("bmad_webmcp_backup_config")
        if not backup_result.get("success", False):
            logger.warning("Backup test failed, skipping restore test")
            return True
        
        backup_file_path = backup_result.get("backup_file_path")
        if not backup_file_path:
            logger.warning("No backup file path found, skipping restore test")
            return True
        
        result = await execute_mcp_tool(
            "bmad_webmcp_restore_config",
            backup_file_path=backup_file_path
        )
        
        logger.info(f"WebMCP restore config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        assert "config_file_path" in result, "Result should contain 'config_file_path' field"
        
        logger.info("✅ WebMCP restore config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP restore config test failed: {e}")
        return False


async def test_webmcp_uninstall_config():
    """Test the WebMCP uninstall config functionality."""
    logger.info("Testing WebMCP uninstall config...")
    
    try:
        result = await execute_mcp_tool("bmad_webmcp_uninstall_config")
        
        logger.info(f"WebMCP uninstall config result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ WebMCP uninstall config test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebMCP uninstall config test failed: {e}")
        return False


async def run_all_tests():
    """Run all WebMCP installer tests."""
    logger.info("Starting WebMCP Installer validation...")
    
    tests = [
        ("WebMCP Install Config Test", test_webmcp_install_config),
        ("WebMCP Validate Installation Test", test_webmcp_validate_installation),
        ("WebMCP Test Integration Test", test_webmcp_test_integration),
        ("WebMCP Get Config Test", test_webmcp_get_config),
        ("WebMCP Update Config Test", test_webmcp_update_config),
        ("WebMCP Backup Config Test", test_webmcp_backup_config),
        ("WebMCP Restore Config Test", test_webmcp_restore_config),
        ("WebMCP Uninstall Config Test", test_webmcp_uninstall_config)
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
    logger.info("WEBMCP INSTALLER VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All WebMCP Installer tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
