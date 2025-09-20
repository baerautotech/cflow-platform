"""
Comprehensive test suite for async tool execution infrastructure.

Tests the performance enhancements including:
- Async tool execution with priority queuing
- Connection pooling
- Response streaming
- Performance monitoring
- Memory management
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from cflow_platform.core.async_tool_executor import (
    AsyncToolExecutor,
    ToolPriority,
    ToolExecutionRequest,
    ToolExecutionResult,
    execute_tool_async,
    get_executor
)
from cflow_platform.core.connection_pool import (
    ConnectionPoolManager,
    HTTPConnectionPool,
    RedisConnectionPool,
    SupabaseConnectionPool,
    PoolConfig
)
from cflow_platform.core.response_streaming import (
    StreamResponse,
    StreamManager,
    StreamEventType,
    create_stream,
    stream_tool_execution
)
from cflow_platform.core.performance_monitor import (
    PerformanceMonitor,
    MetricsCollector,
    SystemMonitor,
    HealthChecker
)


class TestAsyncToolExecutor:
    """Test async tool executor functionality"""
    
    @pytest.fixture
    async def executor(self):
        """Create test executor"""
        executor = AsyncToolExecutor(max_concurrent=5, enable_monitoring=False)
        await executor.start()
        yield executor
        await executor.stop()
    
    @pytest.mark.asyncio
    async def test_tool_execution_success(self, executor):
        """Test successful tool execution"""
        # Mock the direct client
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            mock_execute.return_value = {"status": "success", "result": "test_result"}
            
            result = await executor.execute_tool(
                tool_name="test_tool",
                kwargs={"param": "value"},
                priority=ToolPriority.NORMAL
            )
            
            assert result.success is True
            assert result.result["status"] == "success"
            assert result.result["result"] == "test_result"
            assert result.execution_time > 0
            assert result.memory_used >= 0
    
    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self, executor):
        """Test tool execution timeout"""
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            # Simulate timeout
            async def slow_execution(*args, **kwargs):
                await asyncio.sleep(5)  # Longer than timeout
                return {"status": "success"}
            
            mock_execute.side_effect = slow_execution
            
            result = await executor.execute_tool(
                tool_name="slow_tool",
                kwargs={},
                timeout_seconds=0.1  # Very short timeout
            )
            
            assert result.success is False
            assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_priority_queuing(self, executor):
        """Test priority-based tool execution"""
        execution_order = []
        
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            async def track_execution(tool_name, **kwargs):
                execution_order.append(tool_name)
                return {"status": "success", "tool": tool_name}
            
            mock_execute.side_effect = track_execution
            
            # Submit tools with different priorities
            tasks = [
                executor.execute_tool("low_priority", {}, ToolPriority.LOW),
                executor.execute_tool("high_priority", {}, ToolPriority.HIGH),
                executor.execute_tool("critical_priority", {}, ToolPriority.CRITICAL),
                executor.execute_tool("normal_priority", {}, ToolPriority.NORMAL),
            ]
            
            # Execute all tasks
            await asyncio.gather(*tasks)
            
            # Critical should execute first, then high, normal, low
            assert execution_order[0] == "critical_priority"
            assert execution_order[1] == "high_priority"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, executor):
        """Test circuit breaker functionality"""
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            # Simulate failures
            mock_execute.side_effect = Exception("Service unavailable")
            
            # Execute multiple times to trigger circuit breaker
            for _ in range(6):  # More than failure threshold
                result = await executor.execute_tool("failing_tool", {})
                assert result.success is False
            
            # Circuit should now be open
            result = await executor.execute_tool("failing_tool", {})
            assert "circuit breaker open" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, executor):
        """Test memory usage monitoring"""
        # Set very low memory limit
        executor.memory_limit_bytes = 1024  # 1KB
        
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = await executor.execute_tool("memory_intensive_tool", {})
            
            # Should fail due to memory limit
            assert result.success is False
            assert "memory limit exceeded" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, executor):
        """Test performance metrics collection"""
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            # Execute multiple tools
            await executor.execute_tool("test_tool_1", {})
            await executor.execute_tool("test_tool_2", {})
            
            metrics = executor.get_metrics()
            
            assert metrics["total_executions"] == 2
            assert metrics["successful_executions"] == 2
            assert metrics["failed_executions"] == 0
            assert metrics["average_execution_time"] > 0
            assert "test_tool_1" in metrics["tool_execution_counts"]
            assert "test_tool_2" in metrics["tool_execution_counts"]


class TestConnectionPool:
    """Test connection pooling functionality"""
    
    @pytest.fixture
    async def pool_manager(self):
        """Create test pool manager"""
        config = PoolConfig(max_connections=5, min_connections=2)
        manager = ConnectionPoolManager(config)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_http_pool_creation(self, pool_manager):
        """Test HTTP connection pool creation"""
        pool = pool_manager.get_http_pool("test")
        
        # Should create new pool
        assert isinstance(pool, HTTPConnectionPool)
        
        # Get client
        client = await pool.get_client()
        assert isinstance(client, AsyncMock) or hasattr(client, 'get')
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_redis_pool_creation(self, pool_manager):
        """Test Redis connection pool creation"""
        pool = pool_manager.get_redis_pool("test", "redis://localhost:6379")
        
        # Should create new pool
        assert isinstance(pool, RedisConnectionPool)
        
        # Test connection (mocked)
        with patch('redis.asyncio.Redis.ping', new_callable=AsyncMock) as mock_ping:
            mock_ping.return_value = True
            client = await pool.get_client()
            assert client is not None
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_supabase_pool_creation(self, pool_manager):
        """Test Supabase connection pool creation"""
        pool = pool_manager.get_supabase_pool(
            "test",
            "https://test.supabase.co",
            "test_key"
        )
        
        # Should create new pool
        assert isinstance(pool, SupabaseConnectionPool)
        
        client = await pool.get_client()
        assert client is not None
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_pool_reuse(self, pool_manager):
        """Test connection pool reuse"""
        pool1 = pool_manager.get_http_pool("shared")
        pool2 = pool_manager.get_http_pool("shared")
        
        # Should return same instance
        assert pool1 is pool2
    
    @pytest.mark.asyncio
    async def test_pool_metrics(self, pool_manager):
        """Test connection pool metrics"""
        pool = pool_manager.get_http_pool("metrics_test")
        
        # Get client to generate metrics
        await pool.get_client()
        
        metrics = pool_manager.get_metrics()
        
        assert "active_pools" in metrics
        assert "metrics_test" in metrics["pool_names"]
        assert metrics["active_pools"] >= 1


class TestResponseStreaming:
    """Test response streaming functionality"""
    
    @pytest.fixture
    async def stream_manager(self):
        """Create test stream manager"""
        manager = StreamManager(max_streams=10, cleanup_interval=1.0)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stream_creation(self, stream_manager):
        """Test stream creation and basic functionality"""
        stream = await stream_manager.create_stream("test_stream")
        
        assert stream.stream_id == "test_stream"
        assert not stream._is_complete
        assert not stream._is_error
        
        # Subscribe to events
        queue = stream.subscribe()
        assert len(stream._subscribers) == 1
        
        # Emit test event
        await stream.emit_event(StreamEventType.DATA, {"test": "data"})
        
        # Check event was received
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["event_type"] == "data"
        assert event["data"]["test"] == "data"
        
        stream.unsubscribe(queue)
        await stream.stop()
    
    @pytest.mark.asyncio
    async def test_progress_emission(self, stream_manager):
        """Test progress emission"""
        stream = await stream_manager.create_stream("progress_test")
        queue = stream.subscribe()
        
        # Emit progress updates
        await stream.emit_progress(25.0, "25% complete")
        await stream.emit_progress(50.0, "50% complete")
        await stream.emit_progress(100.0, "Complete")
        
        # Check progress events
        events = []
        for _ in range(3):
            event = await asyncio.wait_for(queue.get(), timeout=1.0)
            if event["event_type"] == "progress":
                events.append(event)
        
        assert len(events) == 3
        assert events[0]["progress"] == 25.0
        assert events[1]["progress"] == 50.0
        assert events[2]["progress"] == 100.0
        
        stream.unsubscribe(queue)
        await stream.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, stream_manager):
        """Test error emission and handling"""
        stream = await stream_manager.create_stream("error_test")
        queue = stream.subscribe()
        
        # Emit error
        await stream.emit_error("Test error", {"details": "error details"})
        
        # Check error event
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["event_type"] == "error"
        assert event["error"] == "Test error"
        assert event["data"]["details"] == "error details"
        assert stream._is_error
        
        stream.unsubscribe(queue)
        await stream.stop()
    
    @pytest.mark.asyncio
    async def test_heartbeat(self, stream_manager):
        """Test heartbeat functionality"""
        stream = await stream_manager.create_stream("heartbeat_test", heartbeat_interval=0.1)
        queue = stream.subscribe()
        
        # Wait for heartbeat
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["event_type"] == "heartbeat"
        assert event["data"]["stream_id"] == "heartbeat_test"
        
        stream.unsubscribe(queue)
        await stream.stop()
    
    @pytest.mark.asyncio
    async def test_stream_timeout(self, stream_manager):
        """Test stream timeout"""
        stream = await stream_manager.create_stream("timeout_test", timeout_seconds=0.1)
        queue = stream.subscribe()
        
        # Wait for timeout event
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["event_type"] == "error"
        assert "timeout" in event["error"]
        
        stream.unsubscribe(queue)
        await stream.stop()
    
    @pytest.mark.asyncio
    async def test_stream_cleanup(self, stream_manager):
        """Test automatic stream cleanup"""
        # Create completed stream
        stream = await stream_manager.create_stream("cleanup_test")
        await stream.stop()  # Mark as complete
        
        # Wait for cleanup
        await asyncio.sleep(1.5)  # Longer than cleanup interval
        
        # Stream should be cleaned up
        assert stream_manager.get_stream("cleanup_test") is None


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create test performance monitor"""
        monitor = PerformanceMonitor(retention_hours=1)
        await monitor.start()
        yield monitor
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, performance_monitor):
        """Test metrics collection"""
        # Record some metrics
        performance_monitor.record_tool_metric("test_tool", 1.5, True, 1024)
        performance_monitor.record_tool_metric("test_tool", 2.0, False, 2048)
        
        # Check metrics
        metrics = performance_monitor.metrics.get_all_metrics()
        
        assert "metrics" in metrics
        assert "tool.test_tool.execution_time" in metrics["metrics"]
        assert "tool.test_tool.success_rate" in metrics["metrics"]
        assert "tool.test_tool.memory_used" in metrics["metrics"]
    
    @pytest.mark.asyncio
    async def test_health_checks(self, performance_monitor):
        """Test health checking"""
        # Wait for health checks to run
        await asyncio.sleep(1)
        
        health = performance_monitor.health_checker.get_overall_health()
        
        assert "status" in health
        assert "checks" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Should have default health checks
        assert "memory" in health["checks"]
        assert "cpu" in health["checks"]
        assert "disk" in health["checks"]
    
    @pytest.mark.asyncio
    async def test_performance_summary(self, performance_monitor):
        """Test performance summary generation"""
        summary = performance_monitor.get_performance_summary()
        
        assert "metrics" in summary
        assert "health" in summary
        assert "timestamp" in summary
        
        # Should have system metrics
        assert "system.cpu_percent" in summary["metrics"]["metrics"]
        assert "system.memory_percent" in summary["metrics"]["metrics"]
    
    @pytest.mark.asyncio
    async def test_custom_health_check(self, performance_monitor):
        """Test custom health check registration"""
        def custom_check():
            return {"message": "Custom check passed", "custom": True}
        
        performance_monitor.health_checker.register_health_check("custom", custom_check)
        
        # Wait for health check to run
        await asyncio.sleep(1)
        
        health = performance_monitor.health_checker.get_overall_health()
        assert "custom" in health["checks"]
        assert health["checks"]["custom"]["message"] == "Custom check passed"


class TestIntegration:
    """Integration tests for the complete async infrastructure"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_execution(self):
        """Test end-to-end tool execution with all components"""
        # This would test the complete flow:
        # 1. Tool execution with async executor
        # 2. Connection pooling for external services
        # 3. Performance monitoring
        # 4. Response streaming for long operations
        
        # For now, test basic integration
        executor = AsyncToolExecutor(max_concurrent=2, enable_monitoring=False)
        await executor.start()
        
        try:
            with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
                mock_execute.return_value = {"status": "success", "result": "integration_test"}
                
                result = await execute_tool_async(
                    tool_name="integration_test",
                    kwargs={"test": True},
                    priority=ToolPriority.HIGH
                )
                
                assert result.success is True
                assert result.result["status"] == "success"
                
        finally:
            await executor.stop()
    
    @pytest.mark.asyncio
    async def test_streaming_tool_execution(self):
        """Test streaming tool execution"""
        with patch('cflow_platform.core.response_streaming.execute_tool_async') as mock_execute:
            mock_execute.return_value = Mock(
                result={"status": "success", "data": "streamed_result"},
                execution_time=0.5,
                success=True
            )
            
            stream = await stream_tool_execution(
                tool_name="streaming_test",
                kwargs={"stream": True},
                timeout_seconds=10.0
            )
            
            # Subscribe to stream
            queue = stream.subscribe()
            
            # Wait for completion
            await asyncio.wait_for(queue.get(), timeout=2.0)
            
            # Stream should complete
            assert stream._is_complete or stream._is_error
            
            stream.unsubscribe(queue)
            await stream.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
