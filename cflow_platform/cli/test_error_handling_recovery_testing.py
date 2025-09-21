#!/usr/bin/env python3
"""
Test script for Error Handling and Recovery Testing functionality.

This script validates the error handling and recovery testing capabilities
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


async def test_error_injection():
    """Test the error injection functionality."""
    logger.info("Testing error injection...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_error_injection_test",
            error_type="timeout",
            probability=1.0,
            delay_seconds=0.1,
            tool_name="sys_test"
        )
        
        logger.info(f"Error injection result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "error_injection_result" in result, "Result should contain 'error_injection_result' field"
        assert "error_type" in result, "Result should contain 'error_type' field"
        
        logger.info("✅ Error injection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error injection test failed: {e}")
        return False


async def test_recovery_strategy():
    """Test the recovery strategy functionality."""
    logger.info("Testing recovery strategy...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_recovery_strategy_test",
            error_type="connection_error",
            recovery_strategy="retry",
            max_attempts=2,
            retry_delay=0.5,
            tool_name="sys_test"
        )
        
        logger.info(f"Recovery strategy result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "recovery_strategy" in result, "Result should contain 'recovery_strategy' field"
        assert "recovery_success" in result, "Result should contain 'recovery_success' field"
        
        logger.info("✅ Recovery strategy test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Recovery strategy test failed: {e}")
        return False


async def test_resilience_test_suite():
    """Test the resilience test suite functionality."""
    logger.info("Testing resilience test suite...")
    
    try:
        # Create test configuration
        error_types = json.dumps(["timeout", "connection_error"])
        recovery_strategies = json.dumps(["retry", "fallback"])
        
        result = await execute_mcp_tool(
            "bmad_resilience_test_suite",
            error_types=error_types,
            recovery_strategies=recovery_strategies,
            tool_name="sys_test"
        )
        
        logger.info(f"Resilience test suite result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "total_tests" in result, "Result should contain 'total_tests' field"
        assert "successful_tests" in result, "Result should contain 'successful_tests' field"
        assert "success_rate" in result, "Result should contain 'success_rate' field"
        
        logger.info("✅ Resilience test suite passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Resilience test suite failed: {e}")
        return False


async def test_circuit_breaker():
    """Test the circuit breaker functionality."""
    logger.info("Testing circuit breaker...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_circuit_breaker_test",
            failure_threshold=2,
            recovery_timeout=60,
            tool_name="sys_test"
        )
        
        logger.info(f"Circuit breaker result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "failure_threshold" in result, "Result should contain 'failure_threshold' field"
        assert "test_results" in result, "Result should contain 'test_results' field"
        assert "circuit_breaker_status" in result, "Result should contain 'circuit_breaker_status' field"
        
        logger.info("✅ Circuit breaker test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Circuit breaker test failed: {e}")
        return False


async def test_error_recovery_history():
    """Test the error recovery history functionality."""
    logger.info("Testing error recovery history...")
    
    try:
        result = await execute_mcp_tool("bmad_error_recovery_history")
        
        logger.info(f"Error recovery history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "history" in result, "Result should contain 'history' field"
        assert "recovery_tests_count" in result, "Result should contain 'recovery_tests_count' field"
        
        logger.info("✅ Error recovery history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error recovery history failed: {e}")
        return False


async def test_error_recovery_clear_history():
    """Test the error recovery clear history functionality."""
    logger.info("Testing error recovery clear history...")
    
    try:
        result = await execute_mcp_tool("bmad_error_recovery_clear_history")
        
        logger.info(f"Clear history result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        assert "message" in result, "Result should contain 'message' field"
        
        logger.info("✅ Error recovery clear history passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error recovery clear history failed: {e}")
        return False


async def test_circuit_breaker_status():
    """Test the circuit breaker status functionality."""
    logger.info("Testing circuit breaker status...")
    
    try:
        result = await execute_mcp_tool(
            "bmad_circuit_breaker_status",
            circuit_breaker_key="test_circuit_breaker"
        )
        
        logger.info(f"Circuit breaker status result: {result}")
        
        # Validate result structure
        assert "success" in result, "Result should contain 'success' field"
        # Note: circuit_breaker_key may not be present if circuit breaker doesn't exist
        if result.get("success", False):
            assert "circuit_breaker_key" in result, "Result should contain 'circuit_breaker_key' field"
        
        logger.info("✅ Circuit breaker status passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Circuit breaker status failed: {e}")
        return False


async def run_all_tests():
    """Run all error handling and recovery testing tests."""
    logger.info("Starting Error Handling and Recovery Testing validation...")
    
    tests = [
        ("Error Injection Test", test_error_injection),
        ("Recovery Strategy Test", test_recovery_strategy),
        ("Resilience Test Suite", test_resilience_test_suite),
        ("Circuit Breaker Test", test_circuit_breaker),
        ("Error Recovery History", test_error_recovery_history),
        ("Error Recovery Clear History", test_error_recovery_clear_history),
        ("Circuit Breaker Status", test_circuit_breaker_status)
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
    logger.info("ERROR HANDLING AND RECOVERY TESTING VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        logger.info(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Error Handling and Recovery Testing tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
