"""
Comprehensive test suite for fault tolerance and monitoring systems.

Tests the fault tolerance enhancements including:
- Circuit breaker patterns and state management
- Graceful degradation with fallback strategies
- Health monitoring and status reporting
- Alerting system with configurable thresholds
- Retry policies with exponential backoff
- Distributed tracing and observability
- Auto-healing and service recovery
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from cflow_platform.core.fault_tolerance import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    FailureType,
    GracefulDegradationManager,
    HealthMonitor,
    AlertManager,
    FaultToleranceManager,
    CircuitBreakerOpenException
)
from cflow_platform.core.retry_policies import (
    RetryManager,
    RetryPolicy,
    RetryStrategy,
    JitterType,
    RetryPolicies,
    with_retry,
    execute_with_retry
)
from cflow_platform.core.distributed_tracing import (
    Tracer,
    Span,
    SpanStatus,
    SpanKind,
    Trace,
    TraceCollector,
    TraceSpan,
    trace_function
)
from cflow_platform.core.auto_healing import (
    AutoHealingManager,
    AutoHealingRule,
    RecoveryStrategy,
    HealthLevel,
    RecoveryAction,
    ServiceHealth
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create test circuit breaker"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,
            half_open_max_calls=2
        )
        return CircuitBreaker("test_service", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state"""
        # Mock successful function
        async def successful_func():
            return "success"
        
        result = await circuit_breaker.call(successful_func)
        assert result == "success"
        
        state = circuit_breaker.get_state()
        assert state["state"] == CircuitState.CLOSED.value
        assert state["total_successes"] == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self, circuit_breaker):
        """Test circuit breaker opening after failure threshold"""
        # Mock failing function
        async def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Circuit should be open
        state = circuit_breaker.get_state()
        assert state["state"] == CircuitState.OPEN.value
        assert state["failure_count"] == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state(self, circuit_breaker):
        """Test circuit breaker in open state"""
        # Open the circuit
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Should fail fast in open state
        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self, circuit_breaker):
        """Test circuit breaker in half-open state"""
        # Open the circuit
        async def failing_func():
            raise Exception("Test failure")
        
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Mock successful function for half-open testing
        async def successful_func():
            return "recovered"
        
        # Should allow calls in half-open state
        result = await circuit_breaker.call(successful_func)
        assert result == "recovered"
        
        # Should close circuit after success
        state = circuit_breaker.get_state()
        assert state["state"] == CircuitState.CLOSED.value
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_classification(self, circuit_breaker):
        """Test failure type classification"""
        # Test timeout classification
        async def timeout_func():
            raise asyncio.TimeoutError("Timeout")
        
        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(timeout_func)
        
        failures = circuit_breaker.get_failure_history()
        assert len(failures) == 1
        assert failures[0].failure_type == FailureType.TIMEOUT


class TestGracefulDegradation:
    """Test graceful degradation functionality"""
    
    @pytest.fixture
    def degradation_manager(self):
        """Create test degradation manager"""
        return GracefulDegradationManager()
    
    @pytest.mark.asyncio
    async def test_primary_function_success(self, degradation_manager):
        """Test when primary function succeeds"""
        async def primary_func():
            return "primary_result"
        
        async def fallback_func():
            return "fallback_result"
        
        degradation_manager.register_fallback("test_service", fallback_func)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service", primary_func
        )
        
        assert result == "primary_result"
    
    @pytest.mark.asyncio
    async def test_fallback_execution(self, degradation_manager):
        """Test fallback execution when primary fails"""
        async def failing_func():
            raise Exception("Primary failed")
        
        async def fallback_func():
            return "fallback_result"
        
        degradation_manager.register_fallback("test_service", fallback_func)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service", failing_func
        )
        
        assert result == "fallback_result"
        
        stats = degradation_manager.get_fallback_stats("test_service")
        assert stats["fallback_count"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_fallbacks(self, degradation_manager):
        """Test multiple fallback strategies"""
        async def failing_func():
            raise Exception("Primary failed")
        
        async def fallback1():
            raise Exception("Fallback 1 failed")
        
        async def fallback2():
            return "fallback2_result"
        
        degradation_manager.register_fallback("test_service", fallback1, priority=1)
        degradation_manager.register_fallback("test_service", fallback2, priority=2)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service", failing_func
        )
        
        assert result == "fallback2_result"  # Higher priority should be tried first


class TestHealthMonitor:
    """Test health monitoring functionality"""
    
    @pytest.fixture
    async def health_monitor(self):
        """Create test health monitor"""
        monitor = HealthMonitor(check_interval_seconds=0.1)
        await monitor.start()
        yield monitor
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_health_check_registration(self, health_monitor):
        """Test health check registration"""
        async def health_check_func():
            return {"status": "healthy", "cpu_usage": 50.0}
        
        health_monitor.register_health_check("test_service", health_check_func)
        
        # Check that service is registered
        health_status = await health_monitor.check_service_health("test_service")
        assert health_status.service_name == "test_service"
        assert health_status.status in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_health_status_determination(self, health_monitor):
        """Test health status determination"""
        async def healthy_check():
            return {"cpu_usage": 30.0, "memory_usage": 40.0, "error_rate": 1.0}
        
        async def degraded_check():
            return {"cpu_usage": 85.0, "memory_usage": 75.0, "error_rate": 8.0}
        
        async def unhealthy_check():
            return {"cpu_usage": 98.0, "memory_usage": 96.0, "error_rate": 25.0}
        
        health_monitor.register_health_check("healthy_service", healthy_check)
        health_monitor.register_health_check("degraded_service", degraded_check)
        health_monitor.register_health_check("unhealthy_service", unhealthy_check)
        
        # Check health statuses
        healthy_status = await health_monitor.check_service_health("healthy_service")
        degraded_status = await health_monitor.check_service_health("degraded_service")
        unhealthy_status = await health_monitor.check_service_health("unhealthy_service")
        
        assert healthy_status.status == "healthy"
        assert degraded_status.status == "degraded"
        assert unhealthy_status.status == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_overall_health(self, health_monitor):
        """Test overall system health"""
        async def healthy_check():
            return {"cpu_usage": 50.0, "memory_usage": 60.0, "error_rate": 2.0}
        
        health_monitor.register_health_check("service1", healthy_check)
        health_monitor.register_health_check("service2", healthy_check)
        
        overall_health = await health_monitor.get_overall_health()
        
        assert "overall_status" in overall_health
        assert "services" in overall_health
        assert "total_services" in overall_health
        assert overall_health["total_services"] == 2


class TestAlertManager:
    """Test alert management functionality"""
    
    @pytest.fixture
    def alert_manager(self):
        """Create test alert manager"""
        return AlertManager()
    
    @pytest.mark.asyncio
    async def test_alert_rule_creation(self, alert_manager):
        """Test alert rule creation"""
        alert_manager.add_alert_rule(
            "high_cpu_alert",
            "test_service",
            "cpu_usage",
            80.0,
            ">",
            "high"
        )
        
        # Verify rule was added
        assert len(alert_manager._alert_rules) == 1
        assert "high_cpu_alert" in alert_manager._alert_rules
    
    @pytest.mark.asyncio
    async def test_alert_triggering(self, alert_manager):
        """Test alert triggering"""
        # Add alert rule
        alert_manager.add_alert_rule(
            "high_cpu_alert",
            "test_service",
            "cpu_usage",
            80.0,
            ">",
            "high"
        )
        
        # Mock notification channel
        notification_called = False
        
        async def notification_channel(alert):
            nonlocal notification_called
            notification_called = True
            assert alert.alert_type == "cpu_usage"
            assert alert.severity == "high"
        
        alert_manager.add_notification_channel(notification_channel)
        
        # Trigger alert
        metrics = {
            "test_service": {
                "cpu_usage": 85.0
            }
        }
        
        await alert_manager.evaluate_alerts(metrics)
        
        # Check that notification was called
        assert notification_called
        assert len(alert_manager.get_active_alerts()) == 1
    
    @pytest.mark.asyncio
    async def test_alert_cooldown(self, alert_manager):
        """Test alert cooldown mechanism"""
        # Add alert rule with short cooldown
        alert_manager.add_alert_rule(
            "test_alert",
            "test_service",
            "cpu_usage",
            80.0,
            ">",
            "high",
            cooldown_seconds=1.0
        )
        
        notification_count = 0
        
        async def notification_channel(alert):
            nonlocal notification_count
            notification_count += 1
        
        alert_manager.add_notification_channel(notification_channel)
        
        # Trigger alert twice quickly
        metrics = {"test_service": {"cpu_usage": 85.0}}
        
        await alert_manager.evaluate_alerts(metrics)
        await alert_manager.evaluate_alerts(metrics)
        
        # Should only trigger once due to cooldown
        assert notification_count == 1
        
        # Wait for cooldown and trigger again
        await asyncio.sleep(1.1)
        await alert_manager.evaluate_alerts(metrics)
        
        # Should trigger again after cooldown
        assert notification_count == 2


class TestRetryPolicies:
    """Test retry policy functionality"""
    
    @pytest.fixture
    def retry_manager(self):
        """Create test retry manager"""
        return RetryManager()
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, retry_manager):
        """Test successful execution without retries"""
        async def successful_func():
            return "success"
        
        policy = RetryPolicy(max_attempts=3)
        result = await retry_manager.execute_with_retry(
            successful_func, service_name="test_service", policy=policy
        )
        
        assert result == "success"
        
        stats = retry_manager.get_retry_stats("test_service")
        assert stats.total_attempts == 1
        assert stats.successful_attempts == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_manager):
        """Test retry on failure"""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        policy = RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0.1,
            strategy=RetryStrategy.FIXED
        )
        
        result = await retry_manager.execute_with_retry(
            failing_func, service_name="test_service", policy=policy
        )
        
        assert result == "success"
        assert call_count == 3
        
        stats = retry_manager.get_retry_stats("test_service")
        assert stats.total_attempts == 1  # Only successful attempt is counted
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, retry_manager):
        """Test exponential backoff strategy"""
        start_time = time.time()
        
        async def always_failing_func():
            raise Exception("Always fails")
        
        policy = RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0.1,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_multiplier=2.0
        )
        
        with pytest.raises(Exception):
            await retry_manager.execute_with_retry(
                always_failing_func, service_name="test_service", policy=policy
            )
        
        # Check that exponential backoff was used
        # Should take at least 0.1 + 0.2 = 0.3 seconds
        elapsed_time = time.time() - start_time
        assert elapsed_time >= 0.3
    
    @pytest.mark.asyncio
    async def test_retry_with_jitter(self, retry_manager):
        """Test retry with jitter"""
        delays = []
        
        async def capture_delay_func():
            delays.append(time.time())
            raise Exception("Always fails")
        
        policy = RetryPolicy(
            max_attempts=2,
            base_delay_seconds=0.1,
            strategy=RetryStrategy.FIXED,
            jitter_type=JitterType.UNIFORM,
            jitter_factor=0.5
        )
        
        with pytest.raises(Exception):
            await retry_manager.execute_with_retry(
                capture_delay_func, service_name="test_service", policy=policy
            )
        
        # Should have some jitter in delays
        if len(delays) >= 2:
            time_diff = delays[1] - delays[0]
            # Should be close to base delay but with some variation
            assert 0.05 <= time_diff <= 0.15
    
    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry decorator"""
        call_count = 0
        
        @with_retry(service_name="decorated_service", max_attempts=3, base_delay_seconds=0.1)
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = await decorated_func()
        assert result == "success"
        assert call_count == 2


class TestDistributedTracing:
    """Test distributed tracing functionality"""
    
    @pytest.fixture
    def tracer(self):
        """Create test tracer"""
        return Tracer("test_service")
    
    def test_span_creation(self, tracer):
        """Test span creation and management"""
        span = tracer.start_span("test_operation")
        
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.name == "test_operation"
        assert span.start_time > 0
        
        # Check that span is active
        assert span.span_id in tracer._active_spans
    
    def test_span_completion(self, tracer):
        """Test span completion"""
        span = tracer.start_span("test_operation")
        span_id = span.span_id
        
        # End the span
        tracer.end_span(span_id, status=SpanStatus.OK)
        
        # Check that span is no longer active
        assert span_id not in tracer._active_spans
        
        # Check that span is in completed spans
        completed_spans = list(tracer._completed_spans)
        assert len(completed_spans) == 1
        assert completed_spans[0].span_id == span_id
        assert completed_spans[0].status == SpanStatus.OK
    
    def test_span_attributes_and_events(self, tracer):
        """Test adding attributes and events to spans"""
        span = tracer.start_span("test_operation")
        
        # Add attributes
        tracer.add_span_attribute(span.span_id, "test_attr", "test_value")
        tracer.add_span_event(span.span_id, "test_event", {"key": "value"})
        
        # Check attributes and events
        assert span.attributes["test_attr"] == "test_value"
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"
    
    def test_trace_context_manager(self):
        """Test trace span context manager"""
        tracer = Tracer("test_service")
        
        with TraceSpan("context_operation") as span:
            assert span is not None
            assert span.name == "context_operation"
        
        # Span should be completed
        assert span.span_id not in tracer._active_spans
    
    @pytest.mark.asyncio
    async def test_trace_decorator(self):
        """Test trace function decorator"""
        tracer = Tracer("test_service")
        
        @trace_function("decorated_operation")
        async def decorated_func():
            return "result"
        
        result = await decorated_func()
        assert result == "result"
        
        # Check that span was created and completed
        completed_spans = list(tracer._completed_spans)
        assert len(completed_spans) == 1
        assert completed_spans[0].name == "decorated_operation"


class TestAutoHealing:
    """Test auto-healing functionality"""
    
    @pytest.fixture
    async def auto_healing_manager(self):
        """Create test auto-healing manager"""
        manager = AutoHealingManager(check_interval_seconds=0.1)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_service_registration(self, auto_healing_manager):
        """Test service registration"""
        async def health_check():
            return {"cpu_usage": 50.0, "memory_usage": 60.0}
        
        auto_healing_manager.register_service("test_service", health_check)
        
        # Check that service is registered
        health = auto_healing_manager.get_service_health("test_service")
        assert health is not None
        assert health.service_name == "test_service"
    
    @pytest.mark.asyncio
    async def test_health_level_determination(self, auto_healing_manager):
        """Test health level determination"""
        # Test critical health
        health = ServiceHealth(
            service_name="test_service",
            health_level=HealthLevel.HEALTHY,
            cpu_usage=98.0,
            memory_usage=96.0,
            error_rate=25.0
        )
        
        level = auto_healing_manager._determine_health_level(health)
        assert level == HealthLevel.CRITICAL
        
        # Test healthy health
        health.cpu_usage = 30.0
        health.memory_usage = 40.0
        health.error_rate = 1.0
        
        level = auto_healing_manager._determine_health_level(health)
        assert level == HealthLevel.HEALTHY
    
    @pytest.mark.asyncio
    async def test_auto_healing_rule(self, auto_healing_manager):
        """Test auto-healing rule execution"""
        # Register service with failing health check
        async def failing_health_check():
            return {"cpu_usage": 95.0, "memory_usage": 90.0, "error_rate": 15.0}
        
        auto_healing_manager.register_service("test_service", failing_health_check)
        
        # Add healing rule
        rule = AutoHealingRule(
            rule_id="critical_rule",
            service_name="test_service",
            condition="critical",
            strategy=RecoveryStrategy.RESTART,
            cooldown_seconds=1.0
        )
        auto_healing_manager.add_healing_rule(rule)
        
        # Wait for monitoring and healing
        await asyncio.sleep(1.0)
        
        # Check that recovery action was triggered
        actions = auto_healing_manager.get_recovery_actions()
        assert len(actions) > 0
        
        # Check that action is for the correct service and strategy
        action = actions[-1]
        assert action.service_name == "test_service"
        assert action.strategy == RecoveryStrategy.RESTART
    
    def test_recovery_strategies(self, auto_healing_manager):
        """Test recovery strategy functions"""
        action = RecoveryAction(
            action_id="test_action",
            service_name="test_service",
            strategy=RecoveryStrategy.CLEAR_CACHE,
            triggered_by="test_rule",
            timestamp=time.time()
        )
        
        # Test that recovery strategies are callable
        for strategy in RecoveryStrategy:
            strategy_func = auto_healing_manager._recovery_strategies.get(strategy)
            assert strategy_func is not None
            assert callable(strategy_func)


class TestIntegration:
    """Integration tests for fault tolerance systems"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Test circuit breaker integration with retry policies"""
        # Create circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.5
        )
        circuit_breaker = CircuitBreaker("test_service", config)
        
        # Create retry manager
        retry_manager = RetryManager()
        
        call_count = 0
        
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        # Execute with both circuit breaker and retry
        result = await circuit_breaker.call(
            lambda: retry_manager.execute_with_retry(
                flaky_function,
                service_name="test_service",
                policy=RetryPolicy(max_attempts=2, base_delay_seconds=0.1)
            )
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_health_monitoring_with_alerts(self):
        """Test health monitoring integration with alerts"""
        # Create health monitor
        health_monitor = HealthMonitor(check_interval_seconds=0.1)
        await health_monitor.start()
        
        # Create alert manager
        alert_manager = AlertManager()
        
        # Add alert rule
        alert_manager.add_alert_rule(
            "high_cpu_alert",
            "test_service",
            "cpu_usage",
            80.0,
            ">",
            "high"
        )
        
        # Register health check that triggers alert
        async def high_cpu_health_check():
            return {"cpu_usage": 85.0, "memory_usage": 60.0, "error_rate": 2.0}
        
        health_monitor.register_health_check("test_service", high_cpu_health_check)
        
        # Wait for monitoring
        await asyncio.sleep(0.5)
        
        # Check that alert was triggered
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) > 0
        
        await health_monitor.stop()
    
    @pytest.mark.asyncio
    async def test_tracing_with_fault_tolerance(self):
        """Test distributed tracing integration with fault tolerance"""
        tracer = Tracer("test_service")
        
        # Create a function that fails and gets retried
        call_count = 0
        
        async def traced_function():
            nonlocal call_count
            call_count += 1
            
            with TraceSpan("operation_step") as span:
                if call_count < 2:
                    span.attributes["error"] = "temporary_failure"
                    raise Exception("Temporary failure")
                
                span.attributes["success"] = True
                return "success"
        
        # Execute with retry
        retry_manager = RetryManager()
        result = await retry_manager.execute_with_retry(
            traced_function,
            service_name="test_service",
            policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.1)
        )
        
        assert result == "success"
        assert call_count == 2
        
        # Check that spans were created
        completed_spans = list(tracer._completed_spans)
        assert len(completed_spans) >= 2  # At least one failed and one successful


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
