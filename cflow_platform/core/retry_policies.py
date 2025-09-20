"""
Retry Policies and Exponential Backoff System for WebMCP Performance Enhancement

This module provides sophisticated retry mechanisms including:
- Exponential backoff with jitter
- Circuit breaker integration
- Retry policies for different failure types
- Adaptive retry strategies
- Retry metrics and monitoring
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import math

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    FIXED = "fixed"                     # Fixed delay between retries
    EXPONENTIAL = "exponential"         # Exponential backoff
    LINEAR = "linear"                   # Linear backoff
    ADAPTIVE = "adaptive"               # Adaptive based on failure patterns


class JitterType(Enum):
    """Jitter types for backoff calculation"""
    NONE = "none"                       # No jitter
    UNIFORM = "uniform"                 # Uniform random jitter
    GAUSSIAN = "gaussian"              # Gaussian random jitter
    FULL = "full"                      # Full jitter


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter_type: JitterType = JitterType.UNIFORM
    jitter_factor: float = 0.1          # 10% jitter by default
    backoff_multiplier: float = 2.0
    should_retry: Optional[Callable[[Exception], bool]] = None
    retry_on_exceptions: List[type] = None
    
    def __post_init__(self):
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [Exception]


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    delay_seconds: float
    exception: Exception
    timestamp: float
    success: bool = False


@dataclass
class RetryStats:
    """Retry statistics"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_retry_time: float = 0.0
    average_delay: float = 0.0
    max_delay_used: float = 0.0
    retry_rate: float = 0.0


class RetryManager:
    """
    Advanced retry manager with multiple strategies and monitoring.
    
    Features:
    - Multiple retry strategies (fixed, exponential, linear, adaptive)
    - Jitter to prevent thundering herd
    - Circuit breaker integration
    - Retry metrics and monitoring
    - Custom retry conditions
    """
    
    def __init__(self):
        self._retry_stats: Dict[str, RetryStats] = {}
        self._retry_history: Dict[str, List[RetryAttempt]] = {}
        self._adaptive_delays: Dict[str, float] = {}
    
    def _calculate_delay(
        self,
        attempt: int,
        policy: RetryPolicy,
        service_name: str
    ) -> float:
        """Calculate delay for retry attempt"""
        if policy.strategy == RetryStrategy.FIXED:
            delay = policy.base_delay_seconds
        elif policy.strategy == RetryStrategy.LINEAR:
            delay = policy.base_delay_seconds * attempt
        elif policy.strategy == RetryStrategy.EXPONENTIAL:
            delay = policy.base_delay_seconds * (policy.backoff_multiplier ** (attempt - 1))
        elif policy.strategy == RetryStrategy.ADAPTIVE:
            delay = self._calculate_adaptive_delay(attempt, policy, service_name)
        else:
            delay = policy.base_delay_seconds
        
        # Apply jitter
        delay = self._apply_jitter(delay, policy)
        
        # Ensure delay is within bounds
        delay = max(0.0, min(delay, policy.max_delay_seconds))
        
        return delay
    
    def _calculate_adaptive_delay(
        self,
        attempt: int,
        policy: RetryPolicy,
        service_name: str
    ) -> float:
        """Calculate adaptive delay based on historical performance"""
        # Start with base delay
        base_delay = policy.base_delay_seconds * (policy.backoff_multiplier ** (attempt - 1))
        
        # Adjust based on historical success rate
        if service_name in self._retry_stats:
            stats = self._retry_stats[service_name]
            if stats.total_attempts > 0:
                success_rate = stats.successful_attempts / stats.total_attempts
                
                # If success rate is high, reduce delay
                # If success rate is low, increase delay
                if success_rate > 0.8:
                    base_delay *= 0.8
                elif success_rate < 0.3:
                    base_delay *= 1.5
        
        # Use exponential backoff as base
        return base_delay
    
    def _apply_jitter(self, delay: float, policy: RetryPolicy) -> float:
        """Apply jitter to delay"""
        if policy.jitter_type == JitterType.NONE:
            return delay
        
        jitter_range = delay * policy.jitter_factor
        
        if policy.jitter_type == JitterType.UNIFORM:
            jitter = random.uniform(-jitter_range, jitter_range)
        elif policy.jitter_type == JitterType.GAUSSIAN:
            jitter = random.gauss(0, jitter_range / 3)  # 3-sigma rule
        elif policy.jitter_type == JitterType.FULL:
            jitter = random.uniform(0, delay)
            return jitter
        else:
            jitter = 0.0
        
        return max(0.0, delay + jitter)
    
    def _should_retry(
        self,
        exception: Exception,
        attempt: int,
        policy: RetryPolicy
    ) -> bool:
        """Determine if retry should be attempted"""
        # Check max attempts
        if attempt >= policy.max_attempts:
            return False
        
        # Check exception type
        if not any(isinstance(exception, exc_type) for exc_type in policy.retry_on_exceptions):
            return False
        
        # Check custom retry condition
        if policy.should_retry and not policy.should_retry(exception):
            return False
        
        return True
    
    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        service_name: str = "default",
        policy: Optional[RetryPolicy] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            service_name: Name of the service (for tracking)
            policy: Retry policy to use
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        if policy is None:
            policy = RetryPolicy()
        
        last_exception = None
        total_retry_time = 0.0
        max_delay_used = 0.0
        
        for attempt in range(1, policy.max_attempts + 1):
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record successful attempt
                if attempt > 1:  # Only count retries, not first attempt
                    self._record_retry_attempt(
                        service_name, attempt - 1, 0.0, None, time.time(), True
                    )
                
                # Update stats
                self._update_retry_stats(service_name, True, total_retry_time, max_delay_used)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if we should retry
                if not self._should_retry(e, attempt, policy):
                    break
                
                # Calculate delay for next attempt
                if attempt < policy.max_attempts:
                    delay = self._calculate_delay(attempt, policy, service_name)
                    max_delay_used = max(max_delay_used, delay)
                    
                    # Record retry attempt
                    self._record_retry_attempt(
                        service_name, attempt, delay, e, time.time(), False
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                    total_retry_time += delay
                    
                    logger.warning(
                        f"Retry {attempt}/{policy.max_attempts} for {service_name}: {str(e)} "
                        f"(delay: {delay:.2f}s)"
                    )
        
        # All retries failed
        self._update_retry_stats(service_name, False, total_retry_time, max_delay_used)
        
        if last_exception:
            logger.error(
                f"All retry attempts failed for {service_name} after {policy.max_attempts} attempts"
            )
            raise last_exception
        
        raise Exception("Retry failed with no exception recorded")
    
    def _record_retry_attempt(
        self,
        service_name: str,
        attempt: int,
        delay: float,
        exception: Optional[Exception],
        timestamp: float,
        success: bool
    ):
        """Record a retry attempt"""
        if service_name not in self._retry_history:
            self._retry_history[service_name] = []
        
        retry_attempt = RetryAttempt(
            attempt_number=attempt,
            delay_seconds=delay,
            exception=exception,
            timestamp=timestamp,
            success=success
        )
        
        self._retry_history[service_name].append(retry_attempt)
        
        # Keep only recent history
        if len(self._retry_history[service_name]) > 100:
            self._retry_history[service_name] = self._retry_history[service_name][-100:]
    
    def _update_retry_stats(
        self,
        service_name: str,
        success: bool,
        total_retry_time: float,
        max_delay_used: float
    ):
        """Update retry statistics"""
        if service_name not in self._retry_stats:
            self._retry_stats[service_name] = RetryStats()
        
        stats = self._retry_stats[service_name]
        stats.total_attempts += 1
        
        if success:
            stats.successful_attempts += 1
        else:
            stats.failed_attempts += 1
        
        stats.total_retry_time += total_retry_time
        stats.max_delay_used = max(stats.max_delay_used, max_delay_used)
        
        if stats.total_attempts > 0:
            stats.average_delay = stats.total_retry_time / stats.total_attempts
            stats.retry_rate = (stats.total_attempts - stats.successful_attempts) / stats.total_attempts
    
    def get_retry_stats(self, service_name: str) -> Optional[RetryStats]:
        """Get retry statistics for a service"""
        return self._retry_stats.get(service_name)
    
    def get_retry_history(self, service_name: str, limit: int = 20) -> List[RetryAttempt]:
        """Get retry history for a service"""
        history = self._retry_history.get(service_name, [])
        return history[-limit:] if history else []
    
    def get_all_stats(self) -> Dict[str, RetryStats]:
        """Get retry statistics for all services"""
        return self._retry_stats.copy()
    
    def reset_stats(self, service_name: Optional[str] = None):
        """Reset retry statistics"""
        if service_name:
            self._retry_stats.pop(service_name, None)
            self._retry_history.pop(service_name, None)
        else:
            self._retry_stats.clear()
            self._retry_history.clear()


# Decorator for easy retry usage
def with_retry(
    service_name: str = "default",
    policy: Optional[RetryPolicy] = None,
    **policy_kwargs
):
    """
    Decorator to add retry logic to async functions.
    
    Usage:
        @with_retry(service_name="api_service", max_attempts=3)
        async def call_api():
            # function implementation
            pass
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create policy from kwargs if not provided
            retry_policy = policy
            if retry_policy is None and policy_kwargs:
                retry_policy = RetryPolicy(**policy_kwargs)
            
            retry_manager = RetryManager()
            return await retry_manager.execute_with_retry(
                func, *args, service_name=service_name, policy=retry_policy, **kwargs
            )
        return wrapper
    return decorator


# Global retry manager
_retry_manager: Optional[RetryManager] = None


def get_retry_manager() -> RetryManager:
    """Get the global retry manager"""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = RetryManager()
    return _retry_manager


async def execute_with_retry(
    func: Callable[..., Awaitable[Any]],
    *args,
    service_name: str = "default",
    policy: Optional[RetryPolicy] = None,
    **kwargs
) -> Any:
    """Execute function with retry logic using global retry manager"""
    manager = get_retry_manager()
    return await manager.execute_with_retry(
        func, *args, service_name=service_name, policy=policy, **kwargs
    )


# Predefined retry policies for common scenarios
class RetryPolicies:
    """Predefined retry policies for common scenarios"""
    
    # Fast retry for transient failures
    FAST = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=0.1,
        max_delay_seconds=1.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter_type=JitterType.UNIFORM,
        backoff_multiplier=2.0
    )
    
    # Standard retry for API calls
    STANDARD = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=30.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter_type=JitterType.UNIFORM,
        backoff_multiplier=2.0
    )
    
    # Aggressive retry for critical operations
    AGGRESSIVE = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=0.5,
        max_delay_seconds=60.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter_type=JitterType.UNIFORM,
        backoff_multiplier=1.5
    )
    
    # Conservative retry for expensive operations
    CONSERVATIVE = RetryPolicy(
        max_attempts=2,
        base_delay_seconds=5.0,
        max_delay_seconds=120.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter_type=JitterType.GAUSSIAN,
        backoff_multiplier=3.0
    )
    
    # Adaptive retry that learns from patterns
    ADAPTIVE = RetryPolicy(
        max_attempts=4,
        base_delay_seconds=1.0,
        max_delay_seconds=60.0,
        strategy=RetryStrategy.ADAPTIVE,
        jitter_type=JitterType.UNIFORM,
        backoff_multiplier=2.0
    )


# Integration with circuit breakers
class RetryWithCircuitBreaker:
    """
    Retry manager integrated with circuit breakers.
    
    This provides retry logic that respects circuit breaker states
    and can trigger circuit breaker state changes based on retry patterns.
    """
    
    def __init__(self, retry_manager: RetryManager, circuit_breaker_manager=None):
        self.retry_manager = retry_manager
        self.circuit_breaker_manager = circuit_breaker_manager
    
    async def execute_with_retry_and_circuit_breaker(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        service_name: str = "default",
        policy: Optional[RetryPolicy] = None,
        **kwargs
    ) -> Any:
        """Execute with both retry and circuit breaker protection"""
        # Check circuit breaker first
        if self.circuit_breaker_manager:
            circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker(service_name)
            if circuit_breaker:
                try:
                    return await circuit_breaker.call(
                        lambda: self.retry_manager.execute_with_retry(
                            func, *args, service_name=service_name, policy=policy, **kwargs
                        )
                    )
                except Exception as e:
                    # Circuit breaker or retry failed
                    raise e
            else:
                # No circuit breaker, just use retry
                return await self.retry_manager.execute_with_retry(
                    func, *args, service_name=service_name, policy=policy, **kwargs
                )
        else:
            # No circuit breaker manager, just use retry
            return await self.retry_manager.execute_with_retry(
                func, *args, service_name=service_name, policy=policy, **kwargs
            )


# Utility functions for common retry scenarios
async def retry_on_timeout(
    func: Callable[..., Awaitable[Any]],
    *args,
    timeout_seconds: float = 30.0,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """Retry function on timeout with exponential backoff"""
    policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay_seconds=1.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retry_on_exceptions=[asyncio.TimeoutError]
    )
    
    return await execute_with_retry(func, *args, policy=policy, **kwargs)


async def retry_on_connection_error(
    func: Callable[..., Awaitable[Any]],
    *args,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """Retry function on connection errors"""
    import aiohttp
    
    policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay_seconds=2.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retry_on_exceptions=[
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            ConnectionError,
            OSError
        ]
    )
    
    return await execute_with_retry(func, *args, policy=policy, **kwargs)


async def retry_on_http_error(
    func: Callable[..., Awaitable[Any]],
    *args,
    retryable_status_codes: List[int] = None,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """Retry function on HTTP errors"""
    import aiohttp
    
    if retryable_status_codes is None:
        retryable_status_codes = [429, 500, 502, 503, 504]
    
    def should_retry_http(exception: Exception) -> bool:
        if isinstance(exception, aiohttp.ClientResponseError):
            return exception.status in retryable_status_codes
        return True
    
    policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay_seconds=1.0,
        strategy=RetryStrategy.EXPONENTIAL,
        retry_on_exceptions=[aiohttp.ClientResponseError],
        should_retry=should_retry_http
    )
    
    return await execute_with_retry(func, *args, policy=policy, **kwargs)
