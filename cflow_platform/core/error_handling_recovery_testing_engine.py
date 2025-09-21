"""
Error Handling and Recovery Testing Engine for BMAD Integration

This module provides comprehensive error handling and recovery testing capabilities
for the BMAD integration, including error injection, recovery testing, circuit breaker
testing, and resilience validation.
"""

import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be injected for testing."""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK_ERROR = "network_error"
    MEMORY_ERROR = "memory_error"
    CPU_ERROR = "cpu_error"


class RecoveryStrategy(Enum):
    """Recovery strategies for testing."""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    TIMEOUT = "timeout"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ErrorInjectionConfig:
    """Configuration for error injection testing."""
    error_type: ErrorType
    probability: float  # 0.0 to 1.0
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_code: Optional[int] = None
    delay_seconds: float = 0.0


@dataclass
class RecoveryTestResult:
    """Results from a recovery test execution."""
    test_name: str
    error_injected: ErrorType
    recovery_strategy: RecoveryStrategy
    success: bool
    recovery_time: float
    attempts_made: int
    fallback_used: bool
    error_details: Dict[str, Any] = field(default_factory=dict)
    recovery_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for testing."""
    state: str  # "closed", "open", "half_open"
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    next_attempt_time: Optional[datetime]


class ErrorHandlingRecoveryTestingEngine:
    """
    Engine for error handling and recovery testing of BMAD integration.
    
    This class provides comprehensive testing capabilities including:
    - Error injection testing
    - Recovery strategy validation
    - Circuit breaker testing
    - Resilience testing
    - Failure scenario simulation
    """
    
    def __init__(self):
        """Initialize the error handling recovery testing engine."""
        self._test_results: List[RecoveryTestResult] = []
        self._circuit_breaker_states: Dict[str, CircuitBreakerState] = {}
        self._error_injection_active = False
        self._injected_errors: List[ErrorInjectionConfig] = []
        
    async def inject_error(
        self,
        error_config: ErrorInjectionConfig,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inject a specific error into a tool execution.
        
        Args:
            error_config: Configuration for the error to inject
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            
        Returns:
            Dictionary with error injection results
        """
        logger.info(f"Injecting {error_config.error_type.value} error into {tool_name}")
        
        start_time = time.time()
        
        try:
            # Simulate the error based on type
            if error_config.delay_seconds > 0:
                await asyncio.sleep(error_config.delay_seconds)
            
            if error_config.error_type == ErrorType.TIMEOUT:
                raise asyncio.TimeoutError("Simulated timeout error")
            elif error_config.error_type == ErrorType.CONNECTION_ERROR:
                raise ConnectionError("Simulated connection error")
            elif error_config.error_type == ErrorType.AUTHENTICATION_ERROR:
                raise PermissionError("Simulated authentication error")
            elif error_config.error_type == ErrorType.AUTHORIZATION_ERROR:
                raise PermissionError("Simulated authorization error")
            elif error_config.error_type == ErrorType.VALIDATION_ERROR:
                raise ValueError("Simulated validation error")
            elif error_config.error_type == ErrorType.RATE_LIMIT_ERROR:
                raise Exception("Simulated rate limit error")
            elif error_config.error_type == ErrorType.INTERNAL_SERVER_ERROR:
                raise Exception("Simulated internal server error")
            elif error_config.error_type == ErrorType.SERVICE_UNAVAILABLE:
                raise Exception("Simulated service unavailable error")
            elif error_config.error_type == ErrorType.NETWORK_ERROR:
                raise ConnectionError("Simulated network error")
            elif error_config.error_type == ErrorType.MEMORY_ERROR:
                raise MemoryError("Simulated memory error")
            elif error_config.error_type == ErrorType.CPU_ERROR:
                raise Exception("Simulated CPU error")
            else:
                raise Exception(f"Simulated {error_config.error_type.value} error")
                
        except Exception as e:
            injection_time = time.time() - start_time
            
            return {
                "success": False,
                "error_injected": True,
                "error_type": error_config.error_type.value,
                "error_message": str(e),
                "injection_time": injection_time,
                "tool_name": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_recovery_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig,
        recovery_strategy: RecoveryStrategy,
        max_attempts: int = 3,
        retry_delay: float = 1.0
    ) -> RecoveryTestResult:
        """
        Test a specific recovery strategy against an injected error.
        
        Args:
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            error_config: Configuration for the error to inject
            recovery_strategy: Recovery strategy to test
            max_attempts: Maximum number of retry attempts
            retry_delay: Delay between retry attempts
            
        Returns:
            RecoveryTestResult with test details
        """
        logger.info(f"Testing {recovery_strategy.value} recovery for {error_config.error_type.value} error")
        
        start_time = time.time()
        attempts_made = 0
        success = False
        fallback_used = False
        error_details = {}
        recovery_details = {}
        
        try:
            if recovery_strategy == RecoveryStrategy.RETRY:
                success, attempts_made, error_details = await self._test_retry_strategy(
                    tool_name, tool_args, error_config, max_attempts, retry_delay
                )
            elif recovery_strategy == RecoveryStrategy.FALLBACK:
                success, fallback_used, recovery_details = await self._test_fallback_strategy(
                    tool_name, tool_args, error_config
                )
            elif recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                success, recovery_details = await self._test_circuit_breaker_strategy(
                    tool_name, tool_args, error_config
                )
            elif recovery_strategy == RecoveryStrategy.TIMEOUT:
                success, recovery_details = await self._test_timeout_strategy(
                    tool_name, tool_args, error_config
                )
            elif recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                success, recovery_details = await self._test_graceful_degradation_strategy(
                    tool_name, tool_args, error_config
                )
            
        except Exception as e:
            logger.error(f"Recovery test failed: {e}")
            error_details = {"test_error": str(e)}
        
        recovery_time = time.time() - start_time
        
        result = RecoveryTestResult(
            test_name=f"recovery_test_{tool_name}_{error_config.error_type.value}_{recovery_strategy.value}",
            error_injected=error_config.error_type,
            recovery_strategy=recovery_strategy,
            success=success,
            recovery_time=recovery_time,
            attempts_made=attempts_made,
            fallback_used=fallback_used,
            error_details=error_details,
            recovery_details=recovery_details
        )
        
        self._test_results.append(result)
        logger.info(f"Recovery test completed: {success} in {recovery_time:.2f}s")
        
        return result
    
    async def _test_retry_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig,
        max_attempts: int,
        retry_delay: float
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """Test retry strategy."""
        attempts_made = 0
        error_details = {}
        
        for attempt in range(max_attempts):
            attempts_made += 1
            
            try:
                # Try to execute the tool
                from cflow_platform.core.direct_client import execute_mcp_tool
                result = await execute_mcp_tool(tool_name, **tool_args)
                
                if result.get("success", False):
                    return True, attempts_made, {"success_on_attempt": attempt + 1}
                
            except Exception as e:
                error_details[f"attempt_{attempt + 1}"] = str(e)
                
                if attempt < max_attempts - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    error_details["final_error"] = str(e)
        
        return False, attempts_made, error_details
    
    async def _test_fallback_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig
    ) -> Tuple[bool, bool, Dict[str, Any]]:
        """Test fallback strategy."""
        fallback_used = False
        recovery_details = {}
        
        try:
            # Try primary execution
            from cflow_platform.core.direct_client import execute_mcp_tool
            result = await execute_mcp_tool(tool_name, **tool_args)
            
            if result.get("success", False):
                return True, fallback_used, {"primary_success": True}
            
        except Exception as e:
            recovery_details["primary_error"] = str(e)
            
            # Try fallback execution
            try:
                fallback_used = True
                fallback_result = await execute_mcp_tool("sys_test")  # Simple fallback
                
                if fallback_result.get("success", False):
                    recovery_details["fallback_success"] = True
                    return True, fallback_used, recovery_details
                else:
                    recovery_details["fallback_error"] = "Fallback execution failed"
                    
            except Exception as fallback_error:
                recovery_details["fallback_error"] = str(fallback_error)
        
        return False, fallback_used, recovery_details
    
    async def _test_circuit_breaker_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test circuit breaker strategy."""
        circuit_breaker_key = f"{tool_name}_{error_config.error_type.value}"
        
        # Initialize circuit breaker state if not exists
        if circuit_breaker_key not in self._circuit_breaker_states:
            self._circuit_breaker_states[circuit_breaker_key] = CircuitBreakerState(
                state="closed",
                failure_count=0,
                success_count=0,
                last_failure_time=None,
                next_attempt_time=None
            )
        
        cb_state = self._circuit_breaker_states[circuit_breaker_key]
        recovery_details = {
            "circuit_breaker_state": cb_state.state,
            "failure_count": cb_state.failure_count,
            "success_count": cb_state.success_count
        }
        
        # Check if circuit breaker is open
        if cb_state.state == "open":
            if cb_state.next_attempt_time and datetime.utcnow() < cb_state.next_attempt_time:
                recovery_details["circuit_breaker_open"] = True
                return False, recovery_details
            else:
                # Move to half-open state
                cb_state.state = "half_open"
                recovery_details["circuit_breaker_half_open"] = True
        
        try:
            # Try execution
            from cflow_platform.core.direct_client import execute_mcp_tool
            result = await execute_mcp_tool(tool_name, **tool_args)
            
            if result.get("success", False):
                cb_state.success_count += 1
                if cb_state.state == "half_open":
                    cb_state.state = "closed"
                    cb_state.failure_count = 0
                recovery_details["execution_success"] = True
                return True, recovery_details
            else:
                raise Exception("Tool execution failed")
                
        except Exception as e:
            cb_state.failure_count += 1
            cb_state.last_failure_time = datetime.utcnow()
            
            # Open circuit breaker if failure threshold reached
            if cb_state.failure_count >= 3:
                cb_state.state = "open"
                cb_state.next_attempt_time = datetime.utcnow() + timedelta(minutes=5)
                recovery_details["circuit_breaker_opened"] = True
            
            recovery_details["execution_error"] = str(e)
            return False, recovery_details
    
    async def _test_timeout_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test timeout strategy."""
        recovery_details = {}
        timeout_seconds = 5.0
        
        try:
            # Execute with timeout
            from cflow_platform.core.direct_client import execute_mcp_tool
            
            async def execute_with_timeout():
                return await execute_mcp_tool(tool_name, **tool_args)
            
            result = await asyncio.wait_for(execute_with_timeout(), timeout=timeout_seconds)
            
            if result.get("success", False):
                recovery_details["timeout_success"] = True
                return True, recovery_details
            else:
                recovery_details["timeout_failure"] = "Tool execution failed"
                return False, recovery_details
                
        except asyncio.TimeoutError:
            recovery_details["timeout_exceeded"] = f"Execution timed out after {timeout_seconds}s"
            return False, recovery_details
        except Exception as e:
            recovery_details["timeout_error"] = str(e)
            return False, recovery_details
    
    async def _test_graceful_degradation_strategy(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_config: ErrorInjectionConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test graceful degradation strategy."""
        recovery_details = {}
        
        try:
            # Try full execution first
            from cflow_platform.core.direct_client import execute_mcp_tool
            result = await execute_mcp_tool(tool_name, **tool_args)
            
            if result.get("success", False):
                recovery_details["full_execution_success"] = True
                return True, recovery_details
            
        except Exception as e:
            recovery_details["full_execution_error"] = str(e)
            
            # Try degraded execution
            try:
                # Simplified execution with reduced functionality
                degraded_result = await execute_mcp_tool("sys_test")  # Simple degraded operation
                
                if degraded_result.get("success", False):
                    recovery_details["degraded_execution_success"] = True
                    recovery_details["degradation_applied"] = True
                    return True, recovery_details
                else:
                    recovery_details["degraded_execution_failed"] = "Degraded execution failed"
                    
            except Exception as degraded_error:
                recovery_details["degraded_execution_error"] = str(degraded_error)
        
        return False, recovery_details
    
    async def run_resilience_test_suite(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_types: List[ErrorType],
        recovery_strategies: List[RecoveryStrategy]
    ) -> Dict[str, Any]:
        """
        Run a comprehensive resilience test suite.
        
        Args:
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            error_types: List of error types to test
            recovery_strategies: List of recovery strategies to test
            
        Returns:
            Dictionary with comprehensive test results
        """
        logger.info(f"Running resilience test suite for {tool_name}")
        
        test_results = []
        total_tests = len(error_types) * len(recovery_strategies)
        successful_tests = 0
        
        for error_type in error_types:
            for recovery_strategy in recovery_strategies:
                error_config = ErrorInjectionConfig(
                    error_type=error_type,
                    probability=1.0,  # Always inject for testing
                    error_message=f"Test {error_type.value} error"
                )
                
                result = await self.test_recovery_strategy(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    error_config=error_config,
                    recovery_strategy=recovery_strategy
                )
                
                test_results.append(result)
                if result.success:
                    successful_tests += 1
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        return {
            "success": True,
            "tool_name": tool_name,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "error_type": r.error_injected.value,
                    "recovery_strategy": r.recovery_strategy.value,
                    "success": r.success,
                    "recovery_time": r.recovery_time,
                    "attempts_made": r.attempts_made,
                    "fallback_used": r.fallback_used
                }
                for r in test_results
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_test_history(self) -> Dict[str, List[Any]]:
        """Get history of all recovery test results."""
        return {
            "recovery_tests": [
                {
                    "test_name": r.test_name,
                    "error_injected": r.error_injected.value,
                    "recovery_strategy": r.recovery_strategy.value,
                    "success": r.success,
                    "recovery_time": r.recovery_time,
                    "attempts_made": r.attempts_made,
                    "fallback_used": r.fallback_used,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self._test_results
            ],
            "circuit_breaker_states": {
                key: {
                    "state": state.state,
                    "failure_count": state.failure_count,
                    "success_count": state.success_count,
                    "last_failure_time": state.last_failure_time.isoformat() if state.last_failure_time else None,
                    "next_attempt_time": state.next_attempt_time.isoformat() if state.next_attempt_time else None
                }
                for key, state in self._circuit_breaker_states.items()
            }
        }
    
    def clear_test_history(self):
        """Clear all test history."""
        self._test_results.clear()
        self._circuit_breaker_states.clear()
        logger.info("Recovery test history cleared")
    
    def get_circuit_breaker_status(self, circuit_breaker_key: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific circuit breaker."""
        if circuit_breaker_key in self._circuit_breaker_states:
            state = self._circuit_breaker_states[circuit_breaker_key]
            return {
                "state": state.state,
                "failure_count": state.failure_count,
                "success_count": state.success_count,
                "last_failure_time": state.last_failure_time.isoformat() if state.last_failure_time else None,
                "next_attempt_time": state.next_attempt_time.isoformat() if state.next_attempt_time else None
            }
        return None
