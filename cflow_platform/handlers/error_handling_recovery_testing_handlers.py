"""
Error Handling and Recovery Testing Handlers

This module provides MCP handlers for error handling and recovery testing
of the BMAD integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from cflow_platform.core.error_handling_recovery_testing_engine import (
    ErrorHandlingRecoveryTestingEngine,
    ErrorInjectionConfig,
    ErrorType,
    RecoveryStrategy,
    RecoveryTestResult
)

logger = logging.getLogger(__name__)


async def bmad_error_injection_test(
    tool_name: str,
    error_type: str,
    probability: float = 1.0,
    duration_seconds: Optional[int] = None,
    error_message: Optional[str] = None,
    error_code: Optional[int] = None,
    delay_seconds: float = 0.0,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Inject a specific error into a tool execution for testing.
    
    Args:
        tool_name: Name of the tool to test
        error_type: Type of error to inject (timeout, connection_error, etc.)
        probability: Probability of error injection (0.0 to 1.0)
        duration_seconds: Duration of error injection in seconds
        error_message: Custom error message
        error_code: Custom error code
        delay_seconds: Delay before error injection
        tool_args: Arguments to pass to the tool
        
    Returns:
        Dictionary with error injection test results
    """
    try:
        logger.info(f"Injecting {error_type} error into {tool_name}")
        
        # Validate error type
        try:
            error_type_enum = ErrorType(error_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid error type: {error_type}. Valid types: {[e.value for e in ErrorType]}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Validate probability
        if not 0.0 <= probability <= 1.0:
            return {
                "success": False,
                "error": "Probability must be between 0.0 and 1.0",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        engine = ErrorHandlingRecoveryTestingEngine()
        
        # Create error injection configuration
        error_config = ErrorInjectionConfig(
            error_type=error_type_enum,
            probability=probability,
            duration_seconds=duration_seconds,
            error_message=error_message,
            error_code=error_code,
            delay_seconds=delay_seconds
        )
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Inject the error
        result = await engine.inject_error(
            error_config=error_config,
            tool_name=tool_name,
            tool_args=tool_args
        )
        
        return {
            "success": True,
            "error_injection_result": result,
            "error_type": error_type,
            "probability": probability,
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error injection test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_recovery_strategy_test(
    tool_name: str,
    error_type: str,
    recovery_strategy: str,
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Test a specific recovery strategy against an injected error.
    
    Args:
        tool_name: Name of the tool to test
        error_type: Type of error to inject
        recovery_strategy: Recovery strategy to test (retry, fallback, circuit_breaker, etc.)
        max_attempts: Maximum number of retry attempts
        retry_delay: Delay between retry attempts
        tool_args: Arguments to pass to the tool
        
    Returns:
        Dictionary with recovery strategy test results
    """
    try:
        logger.info(f"Testing {recovery_strategy} recovery for {error_type} error in {tool_name}")
        
        # Validate error type
        try:
            error_type_enum = ErrorType(error_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid error type: {error_type}. Valid types: {[e.value for e in ErrorType]}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Validate recovery strategy
        try:
            recovery_strategy_enum = RecoveryStrategy(recovery_strategy)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid recovery strategy: {recovery_strategy}. Valid strategies: {[s.value for s in RecoveryStrategy]}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        engine = ErrorHandlingRecoveryTestingEngine()
        
        # Create error injection configuration
        error_config = ErrorInjectionConfig(
            error_type=error_type_enum,
            probability=1.0,  # Always inject for testing
            error_message=f"Test {error_type} error"
        )
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Test recovery strategy
        result = await engine.test_recovery_strategy(
            tool_name=tool_name,
            tool_args=tool_args,
            error_config=error_config,
            recovery_strategy=recovery_strategy_enum,
            max_attempts=max_attempts,
            retry_delay=retry_delay
        )
        
        return {
            "success": True,
            "test_name": result.test_name,
            "error_injected": result.error_injected.value,
            "recovery_strategy": result.recovery_strategy.value,
            "recovery_success": result.success,
            "recovery_time": result.recovery_time,
            "attempts_made": result.attempts_made,
            "fallback_used": result.fallback_used,
            "error_details": result.error_details,
            "recovery_details": result.recovery_details,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Recovery strategy test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_resilience_test_suite(
    tool_name: str,
    error_types: str,
    recovery_strategies: str,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a comprehensive resilience test suite.
    
    Args:
        tool_name: Name of the tool to test
        error_types: JSON string with list of error types to test
        recovery_strategies: JSON string with list of recovery strategies to test
        tool_args: Arguments to pass to the tool
        
    Returns:
        Dictionary with comprehensive resilience test results
    """
    try:
        logger.info(f"Running resilience test suite for {tool_name}")
        
        # Parse error types
        try:
            error_types_list = json.loads(error_types)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in error_types: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(error_types_list, list):
            return {
                "success": False,
                "error": "error_types must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Parse recovery strategies
        try:
            recovery_strategies_list = json.loads(recovery_strategies)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in recovery_strategies: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not isinstance(recovery_strategies_list, list):
            return {
                "success": False,
                "error": "recovery_strategies must be a list",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Validate error types
        error_type_enums = []
        for error_type in error_types_list:
            try:
                error_type_enums.append(ErrorType(error_type))
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid error type: {error_type}. Valid types: {[e.value for e in ErrorType]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Validate recovery strategies
        recovery_strategy_enums = []
        for recovery_strategy in recovery_strategies_list:
            try:
                recovery_strategy_enums.append(RecoveryStrategy(recovery_strategy))
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid recovery strategy: {recovery_strategy}. Valid strategies: {[s.value for s in RecoveryStrategy]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        engine = ErrorHandlingRecoveryTestingEngine()
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Run resilience test suite
        result = await engine.run_resilience_test_suite(
            tool_name=tool_name,
            tool_args=tool_args,
            error_types=error_type_enums,
            recovery_strategies=recovery_strategy_enums
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Resilience test suite failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_circuit_breaker_test(
    tool_name: str,
    failure_threshold: int = 3,
    recovery_timeout: int = 300,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Test circuit breaker functionality.
    
    Args:
        tool_name: Name of the tool to test
        failure_threshold: Number of failures before circuit opens
        recovery_timeout: Timeout in seconds before attempting recovery
        tool_args: Arguments to pass to the tool
        
    Returns:
        Dictionary with circuit breaker test results
    """
    try:
        logger.info(f"Testing circuit breaker for {tool_name}")
        
        engine = ErrorHandlingRecoveryTestingEngine()
        
        # Default tool arguments if none provided
        if tool_args is None:
            tool_args = {}
        
        # Test circuit breaker with multiple failures
        test_results = []
        
        for i in range(failure_threshold + 2):  # Test beyond threshold
            error_config = ErrorInjectionConfig(
                error_type=ErrorType.CONNECTION_ERROR,
                probability=1.0,
                error_message=f"Circuit breaker test failure {i+1}"
            )
            
            result = await engine.test_recovery_strategy(
                tool_name=tool_name,
                tool_args=tool_args,
                error_config=error_config,
                recovery_strategy=RecoveryStrategy.CIRCUIT_BREAKER
            )
            
            test_results.append(result)
        
        # Get circuit breaker status
        circuit_breaker_key = f"{tool_name}_{ErrorType.CONNECTION_ERROR.value}"
        circuit_breaker_status = engine.get_circuit_breaker_status(circuit_breaker_key)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "failure_threshold": failure_threshold,
            "recovery_timeout": recovery_timeout,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "recovery_time": r.recovery_time,
                    "error_details": r.error_details,
                    "recovery_details": r.recovery_details
                }
                for r in test_results
            ],
            "circuit_breaker_status": circuit_breaker_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Circuit breaker test failed for {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_error_recovery_history() -> Dict[str, Any]:
    """
    Get history of all error handling and recovery tests.
    
    Returns:
        Dictionary with test history
    """
    try:
        logger.info("Retrieving error recovery test history")
        
        engine = ErrorHandlingRecoveryTestingEngine()
        history = engine.get_test_history()
        
        return {
            "success": True,
            "history": history,
            "recovery_tests_count": len(history["recovery_tests"]),
            "circuit_breaker_count": len(history["circuit_breaker_states"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve error recovery test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_error_recovery_clear_history() -> Dict[str, Any]:
    """
    Clear all error handling and recovery test history.
    
    Returns:
        Dictionary with operation result
    """
    try:
        logger.info("Clearing error recovery test history")
        
        engine = ErrorHandlingRecoveryTestingEngine()
        engine.clear_test_history()
        
        return {
            "success": True,
            "message": "Error recovery test history cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear error recovery test history: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_circuit_breaker_status(
    circuit_breaker_key: str
) -> Dict[str, Any]:
    """
    Get status of a specific circuit breaker.
    
    Args:
        circuit_breaker_key: Key identifying the circuit breaker
        
    Returns:
        Dictionary with circuit breaker status
    """
    try:
        logger.info(f"Getting circuit breaker status for {circuit_breaker_key}")
        
        engine = ErrorHandlingRecoveryTestingEngine()
        status = engine.get_circuit_breaker_status(circuit_breaker_key)
        
        if status is None:
            return {
                "success": False,
                "error": f"Circuit breaker '{circuit_breaker_key}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "circuit_breaker_key": circuit_breaker_key,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status for {circuit_breaker_key}: {e}")
        return {
            "success": False,
            "error": str(e),
            "circuit_breaker_key": circuit_breaker_key,
            "timestamp": datetime.utcnow().isoformat()
        }
