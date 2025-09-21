#!/usr/bin/env python3
"""
Test script for Security and Authentication Testing functionality.

This script validates the security and authentication testing capabilities
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


async def test_security_authentication():
    """Test the security authentication functionality."""
    logger.info("Testing security authentication...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_security_authentication_test",
            endpoint="/api/test",
            auth_method="jwt"
        )
        
        logger.info(f"Security authentication result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "authentication_method" in result, "Result should contain 'authentication_method' field"
        assert "authentication_success" in result, "Result should contain 'authentication_success' field"
        
        logger.info("✅ Security authentication test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security authentication test failed: {e}")
        return False


async def test_security_authorization():
    """Test the security authorization functionality."""
    logger.info("Testing security authorization...")
    
    try:
        user_roles = json.dumps(["admin", "user"])
        required_permissions = json.dumps(["read", "write"])
        
        result = await execute_mcp_tool(
            "bmad_security_authorization_test",
            endpoint="/api/test",
            user_roles=user_roles,
            required_permissions=required_permissions
        )
        
        logger.info(f"Security authorization result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "test_type" in result, "Result should contain 'test_type' field"
        assert "authorization_success" in result, "Result should contain 'authorization_success' field"
        
        logger.info("✅ Security authorization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security authorization test failed: {e}")
        return False


async def test_security_input_validation():
    """Test the security input validation functionality."""
    logger.info("Testing security input validation...")
    
    try:
        input_fields = json.dumps(["input", "data", "query"])
        
        result = await execute_mcp_tool(
            "bmad_security_input_validation_test",
            endpoint="/api/test",
            input_fields=input_fields
        )
        
        logger.info(f"Security input validation result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "test_type" in result, "Result should contain 'test_type' field"
        assert "validation_success" in result, "Result should contain 'validation_success' field"
        
        logger.info("✅ Security input validation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security input validation test failed: {e}")
        return False


async def test_security_rate_limiting():
    """Test the security rate limiting functionality."""
    logger.info("Testing security rate limiting...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_security_rate_limiting_test",
            endpoint="/api/test",
            rate_limit=50,
            time_window=60
        )
        
        logger.info(f"Security rate limiting result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "test_type" in result, "Result should contain 'test_type' field"
        assert "rate_limiting_success" in result, "Result should contain 'rate_limiting_success' field"
        
        logger.info("✅ Security rate limiting test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security rate limiting test failed: {e}")
        return False


async def test_security_test_suite():
    """Test the security test suite functionality."""
    logger.info("Testing security test suite...")
    
    try:
        endpoints = json.dumps(["/api/test1", "/api/test2"])
        test_types = json.dumps(["authentication", "authorization"])
        
        result = await execute_mcp_tool(
            "bmad_security_test_suite",
            endpoints=endpoints,
            test_types=test_types
        )
        
        logger.info(f"Security test suite result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "total_tests" in result, "Result should contain 'total_tests' field"
        assert "successful_tests" in result, "Result should contain 'successful_tests' field"
        assert "vulnerabilities_found" in result, "Result should contain 'vulnerabilities_found' field"
        
        logger.info("✅ Security test suite passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security test suite failed: {e}")
        return False


async def test_security_vulnerability_scan():
    """Test the security vulnerability scan functionality."""
    logger.info("Testing security vulnerability scan...")
    
    try:
        scan_types = json.dumps(["authentication", "input_validation"])
        
        result = await execute_mcp_tool(
            "bmad_security_vulnerability_scan",
            endpoint="/api/test",
            scan_types=scan_types
        )
        
        logger.info(f"Security vulnerability scan result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "endpoint" in result, "Result should contain 'endpoint' field"
        assert "scan_types" in result, "Result should contain 'scan_types' field"
        assert "vulnerabilities_found" in result, "Result should contain 'vulnerabilities_found' field"
        
        logger.info("✅ Security vulnerability scan passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security vulnerability scan failed: {e}")
        return False


async def test_security_test_history():
    """Test the security test history functionality."""
    logger.info("Testing security test history...")
    
    try:
        result = await execute_mcp_tool("bmad_security_test_history")
        
        logger.info(f"Security test history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "history" in result, "Result should contain 'history' field"
        assert "security_tests_count" in result, "Result should contain 'security_tests_count' field"
        
        logger.info("✅ Security test history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security test history failed: {e}")
        return False


async def test_security_test_clear_history():
    """Test the security test clear history functionality."""
    logger.info("Testing security test clear history...")
    
    try:
        result = await execute_mcp_tool("bmad_security_test_clear_history")
        
        logger.info(f"Clear history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ Security test clear history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security test clear history failed: {e}")
        return False


async def run_all_tests():
    """Run all security and authentication testing tests."""
    logger.info("Starting Security and Authentication Testing validation...")
    
    tests = [
        ("Security Authentication Test", test_security_authentication),
        ("Security Authorization Test", test_security_authorization),
        ("Security Input Validation Test", test_security_input_validation),
        ("Security Rate Limiting Test", test_security_rate_limiting),
        ("Security Test Suite", test_security_test_suite),
        ("Security Vulnerability Scan", test_security_vulnerability_scan),
        ("Security Test History", test_security_test_history),
        ("Security Test Clear History", test_security_test_clear_history)
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
    logger.info("SECURITY AND AUTHENTICATION TESTING VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Security and Authentication Testing tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
