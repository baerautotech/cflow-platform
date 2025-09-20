"""
Comprehensive test suite for caching and performance optimization systems.

Tests the performance enhancements including:
- Intelligent caching with TTL and compression
- Batch processing with dependency resolution
- Memory optimization and cleanup
- Performance analysis and reporting
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from cflow_platform.core.intelligent_cache import (
    IntelligentCache,
    CacheStrategy,
    CacheEntry,
    CacheStats,
    get_cache,
    cache_tool_result,
    get_cached_result
)
from cflow_platform.core.batch_processor import (
    BatchProcessor,
    BatchToolRequest,
    BatchExecutionMode,
    BatchFailureMode,
    BatchExecutionResult,
    get_batch_processor,
    execute_tool_batch
)
from cflow_platform.core.memory_optimizer import (
    MemoryOptimizer,
    MemoryStats,
    MemoryAlert,
    get_memory_optimizer,
    get_memory_stats
)
from cflow_platform.core.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetric,
    PerformanceTrend,
    PerformanceBottleneck,
    PerformanceReport,
    get_performance_analyzer,
    record_performance_metric
)


class TestIntelligentCache:
    """Test intelligent caching system"""
    
    @pytest.fixture
    async def cache(self):
        """Create test cache"""
        cache = IntelligentCache(max_size_mb=10, max_entries=100, enable_compression=True)
        await cache.start()
        yield cache
        await cache.stop()
    
    @pytest.mark.asyncio
    async def test_cache_basic_operations(self, cache):
        """Test basic cache operations"""
        # Test set and get
        result = {"status": "success", "data": "test_data"}
        await cache.set("test_tool", {"param": "value"}, result)
        
        cached = await cache.get("test_tool", {"param": "value"})
        assert cached == result
        
        # Test miss
        cached = await cache.get("test_tool", {"param": "different"})
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_strategies(self, cache):
        """Test different cache strategies"""
        # Test no cache strategy
        await cache.set("no_cache_tool", {}, {"data": "test"}, tags=["no_cache"])
        cached = await cache.get("no_cache_tool", {})
        assert cached is None  # Should not be cached
        
        # Test persistent strategy
        await cache.set("persistent_tool", {}, {"data": "persistent"})
        cached = await cache.get("persistent_tool", {})
        assert cached == {"data": "persistent"}
    
    @pytest.mark.asyncio
    async def test_cache_compression(self, cache):
        """Test cache compression"""
        # Create large data
        large_data = {"data": "x" * 10000}  # 10KB of data
        
        await cache.set("large_tool", {}, large_data)
        cached = await cache.get("large_tool", {})
        
        assert cached == large_data
        
        # Check that compression was used
        stats = cache.get_stats()
        assert stats.compression_ratio > 0
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache):
        """Test cache TTL expiration"""
        # Set with short TTL
        await cache.set("ttl_tool", {}, {"data": "test"}, ttl_seconds=0.1)
        
        # Should be available immediately
        cached = await cache.get("ttl_tool", {})
        assert cached == {"data": "test"}
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should be expired
        cached = await cache.get("ttl_tool", {})
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation"""
        # Set multiple entries with tags
        await cache.set("tool1", {"id": "1"}, {"data": "test1"}, tags=["group1"])
        await cache.set("tool2", {"id": "2"}, {"data": "test2"}, tags=["group1"])
        await cache.set("tool3", {"id": "3"}, {"data": "test3"}, tags=["group2"])
        
        # Verify entries exist
        assert await cache.get("tool1", {"id": "1"}) == {"data": "test1"}
        assert await cache.get("tool2", {"id": "2"}) == {"data": "test2"}
        assert await cache.get("tool3", {"id": "3"}) == {"data": "test3"}
        
        # Invalidate by tag
        await cache.invalidate(tags=["group1"])
        
        # Group1 entries should be gone
        assert await cache.get("tool1", {"id": "1"}) is None
        assert await cache.get("tool2", {"id": "2"}) is None
        
        # Group2 entry should remain
        assert await cache.get("tool3", {"id": "3"}) == {"data": "test3"}
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache):
        """Test cache eviction"""
        # Fill cache beyond limit
        for i in range(150):  # More than max_entries (100)
            await cache.set(f"tool_{i}", {}, {"data": f"test_{i}"})
        
        # Check that cache was evicted
        stats = cache.get_stats()
        assert stats.total_entries <= 100
        
        # Check that eviction occurred
        assert stats.eviction_count > 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics"""
        # Perform operations
        await cache.set("tool1", {}, {"data": "test1"})
        await cache.get("tool1", {})  # Hit
        await cache.get("tool2", {})  # Miss
        
        stats = cache.get_stats()
        
        assert stats.hit_count == 1
        assert stats.miss_count == 1
        assert stats.hit_rate == 0.5
        assert stats.total_entries == 1


class TestBatchProcessor:
    """Test batch processing system"""
    
    @pytest.fixture
    async def batch_processor(self):
        """Create test batch processor"""
        processor = BatchProcessor(max_concurrent=5, enable_caching=True)
        return processor
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, batch_processor):
        """Test parallel batch execution"""
        requests = [
            BatchToolRequest("test_tool", {"id": i}, request_id=f"req_{i}")
            for i in range(5)
        ]
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            mock_execute.return_value = Mock(
                result={"status": "success", "data": "test"},
                success=True,
                execution_time=0.1,
                error=None
            )
            
            result = await batch_processor.execute_batch(
                requests,
                execution_mode=BatchExecutionMode.PARALLEL
            )
            
            assert result.success_count == 5
            assert result.failure_count == 0
            assert len(result.results) == 5
            assert mock_execute.call_count == 5
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, batch_processor):
        """Test sequential batch execution"""
        requests = [
            BatchToolRequest("test_tool", {"id": i}, request_id=f"req_{i}")
            for i in range(3)
        ]
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            mock_execute.return_value = Mock(
                result={"status": "success", "data": "test"},
                success=True,
                execution_time=0.1,
                error=None
            )
            
            result = await batch_processor.execute_batch(
                requests,
                execution_mode=BatchExecutionMode.SEQUENTIAL
            )
            
            assert result.success_count == 3
            assert result.failure_count == 0
            assert len(result.results) == 3
    
    @pytest.mark.asyncio
    async def test_dependency_ordered_execution(self, batch_processor):
        """Test dependency-ordered batch execution"""
        requests = [
            BatchToolRequest("tool_a", {}, request_id="a"),
            BatchToolRequest("tool_b", {}, request_id="b", dependencies=["a"]),
            BatchToolRequest("tool_c", {}, request_id="c", dependencies=["b"]),
        ]
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            mock_execute.return_value = Mock(
                result={"status": "success", "data": "test"},
                success=True,
                execution_time=0.1,
                error=None
            )
            
            result = await batch_processor.execute_batch(
                requests,
                execution_mode=BatchExecutionMode.DEPENDENCY_ORDERED
            )
            
            assert result.success_count == 3
            assert result.failure_count == 0
            
            # Check execution order (a should execute first, then b, then c)
            call_args = [call[0][0] for call in mock_execute.call_args_list]
            assert "tool_a" in call_args[0]
            assert "tool_b" in call_args[1]
            assert "tool_c" in call_args[2]
    
    @pytest.mark.asyncio
    async def test_fail_fast_mode(self, batch_processor):
        """Test fail-fast mode"""
        requests = [
            BatchToolRequest("tool1", {}, request_id="1"),
            BatchToolRequest("tool2", {}, request_id="2"),
            BatchToolRequest("tool3", {}, request_id="3"),
        ]
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            def side_effect(*args, **kwargs):
                if "tool2" in str(args):
                    return Mock(
                        result={"status": "error", "message": "test error"},
                        success=False,
                        execution_time=0.1,
                        error="test error"
                    )
                return Mock(
                    result={"status": "success", "data": "test"},
                    success=True,
                    execution_time=0.1,
                    error=None
                )
            
            mock_execute.side_effect = side_effect
            
            result = await batch_processor.execute_batch(
                requests,
                execution_mode=BatchExecutionMode.SEQUENTIAL,
                failure_mode=BatchFailureMode.FAIL_FAST
            )
            
            # Should stop after tool2 fails
            assert result.success_count == 1
            assert result.failure_count == 1
            assert len(result.results) == 2  # Only tool1 and tool2
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, batch_processor):
        """Test retry mechanism"""
        request = BatchToolRequest(
            "failing_tool",
            {},
            request_id="retry_test",
            max_retries=2
        )
        
        call_count = 0
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count < 3:  # Fail first 2 times
                    raise Exception("Simulated failure")
                
                return Mock(
                    result={"status": "success", "data": "test"},
                    success=True,
                    execution_time=0.1,
                    error=None
                )
            
            mock_execute.side_effect = side_effect
            
            result = await batch_processor.execute_batch([request])
            
            assert result.success_count == 1
            assert result.failure_count == 0
            assert call_count == 3  # Should have retried twice


class TestMemoryOptimizer:
    """Test memory optimization system"""
    
    @pytest.fixture
    async def memory_optimizer(self):
        """Create test memory optimizer"""
        optimizer = MemoryOptimizer(
            memory_limit_mb=100,
            cleanup_interval_seconds=1.0,
            monitoring_interval_seconds=0.5
        )
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, memory_optimizer):
        """Test memory monitoring"""
        # Wait for monitoring to collect data
        await asyncio.sleep(1.0)
        
        stats = memory_optimizer.get_memory_stats()
        
        assert stats.process_memory_mb > 0
        assert stats.total_memory_mb > 0
        assert stats.memory_percent >= 0
        assert stats.gc_objects > 0
    
    @pytest.mark.asyncio
    async def test_memory_alerts(self, memory_optimizer):
        """Test memory alert generation"""
        # Simulate high memory usage
        with patch.object(memory_optimizer, '_stats') as mock_stats:
            mock_stats.process_memory_mb = 450  # High usage
            mock_stats.memory_percent = 85
            
            await memory_optimizer._check_memory_pressure()
            
            alerts = memory_optimizer.get_alerts()
            assert len(alerts) > 0
            assert any(alert.alert_type == "memory_pressure" for alert in alerts)
    
    @pytest.mark.asyncio
    async def test_cleanup_callbacks(self, memory_optimizer):
        """Test cleanup callback registration"""
        callback_called = False
        
        def cleanup_callback():
            nonlocal callback_called
            callback_called = True
        
        memory_optimizer.register_cleanup_callback(cleanup_callback)
        
        # Trigger cleanup
        await memory_optimizer._perform_cleanup()
        
        assert callback_called
    
    @pytest.mark.asyncio
    async def test_resource_pools(self, memory_optimizer):
        """Test resource pool management"""
        # Add resources to pool
        for i in range(5):
            memory_optimizer.return_resource_to_pool("test_pool", f"resource_{i}")
        
        # Get resources from pool
        resource = memory_optimizer.get_resource_from_pool("test_pool")
        assert resource is not None
        
        # Pool should have fewer resources now
        assert len(memory_optimizer._resource_pools["test_pool"]) == 4
    
    @pytest.mark.asyncio
    async def test_emergency_cleanup(self, memory_optimizer):
        """Test emergency cleanup"""
        # Simulate memory limit exceeded
        with patch.object(memory_optimizer, '_stats') as mock_stats:
            mock_stats.process_memory_mb = 600  # Exceeds limit
            mock_stats.memory_percent = 95
            
            await memory_optimizer._check_memory_pressure()
            
            # Should trigger emergency cleanup
            # (We can't easily test the cleanup itself, but we can verify alerts)
            alerts = memory_optimizer.get_alerts()
            assert any(alert.alert_type == "memory_limit_exceeded" for alert in alerts)


class TestPerformanceAnalyzer:
    """Test performance analysis system"""
    
    @pytest.fixture
    async def performance_analyzer(self):
        """Create test performance analyzer"""
        analyzer = PerformanceAnalyzer(
            analysis_interval_seconds=1.0,
            trend_window_minutes=1,
            report_interval_minutes=1
        )
        await analyzer.start()
        yield analyzer
        await analyzer.stop()
    
    @pytest.mark.asyncio
    async def test_metric_recording(self, performance_analyzer):
        """Test performance metric recording"""
        # Record some metrics
        performance_analyzer.record_metric("test_metric", 100.0, {"tag": "test"}, "ms", "test_category")
        performance_analyzer.record_metric("test_metric", 150.0, {"tag": "test"}, "ms", "test_category")
        performance_analyzer.record_metric("test_metric", 120.0, {"tag": "test"}, "ms", "test_category")
        
        # Get metric history
        history = performance_analyzer.get_metric_history("test_metric")
        assert len(history) == 3
        
        # Get metric stats
        stats = performance_analyzer.get_metric_stats("test_metric")
        assert stats["count"] == 3
        assert stats["mean"] == 123.33  # Approximate
        assert stats["latest"] == 120.0
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, performance_analyzer):
        """Test trend analysis"""
        # Record metrics with clear trend
        base_time = time.time()
        for i in range(20):
            performance_analyzer.record_metric(
                "trend_metric",
                100.0 + i * 5,  # Increasing trend
                timestamp=base_time + i * 60  # 1 minute intervals
            )
        
        # Analyze trends
        trends = performance_analyzer.analyze_trends()
        
        assert "trend_metric" in trends
        trend = trends["trend_metric"]
        assert trend.trend_direction == "degrading"  # Increasing values = degrading performance
        assert trend.confidence > 0.5  # Should be confident about the trend
    
    @pytest.mark.asyncio
    async def test_bottleneck_identification(self, performance_analyzer):
        """Test bottleneck identification"""
        # Record metrics that exceed thresholds
        for i in range(10):
            performance_analyzer.record_metric(
                "execution_time_ms",
                600.0,  # Exceeds warning threshold (500ms)
                category="performance"
            )
        
        # Identify bottlenecks
        bottlenecks = performance_analyzer.identify_bottlenecks()
        
        assert len(bottlenecks) > 0
        execution_bottlenecks = [b for b in bottlenecks if "execution_time" in b.description]
        assert len(execution_bottlenecks) > 0
        
        bottleneck = execution_bottlenecks[0]
        assert bottleneck.severity in ["high", "critical"]
        assert len(bottleneck.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_performance_report(self, performance_analyzer):
        """Test performance report generation"""
        # Record various metrics
        for i in range(20):
            performance_analyzer.record_metric("metric1", 100.0 + i, category="category1")
            performance_analyzer.record_metric("metric2", 200.0 - i, category="category2")
        
        # Generate report
        report = performance_analyzer.generate_performance_report()
        
        assert report.report_id is not None
        assert report.health_score >= 0.0 and report.health_score <= 1.0
        assert len(report.trends) > 0
        assert "total_metrics_collected" in report.summary
        assert len(report.recommendations) > 0


class TestIntegration:
    """Integration tests for caching and performance systems"""
    
    @pytest.mark.asyncio
    async def test_cache_batch_integration(self):
        """Test integration between cache and batch processor"""
        # Create batch requests
        requests = [
            BatchToolRequest("cached_tool", {"id": 1}, request_id="req1"),
            BatchToolRequest("cached_tool", {"id": 1}, request_id="req2"),  # Duplicate
        ]
        
        with patch('cflow_platform.core.batch_processor.execute_tool_async') as mock_execute:
            mock_execute.return_value = Mock(
                result={"status": "success", "data": "cached"},
                success=True,
                execution_time=0.1,
                error=None
            )
            
            # Execute batch
            processor = BatchProcessor(enable_caching=True, enable_deduplication=True)
            result = await processor.execute_batch(requests)
            
            # Should deduplicate and cache
            assert result.success_count == 2
            assert mock_execute.call_count == 1  # Only called once due to deduplication
    
    @pytest.mark.asyncio
    async def test_memory_performance_integration(self):
        """Test integration between memory optimizer and performance analyzer"""
        # Record memory metrics
        for i in range(10):
            record_performance_metric(
                "memory_usage_mb",
                400.0 + i * 10,  # Increasing memory usage
                {"process": "test"},
                "MB",
                "memory"
            )
        
        # Get performance report
        analyzer = await get_performance_analyzer()
        report = analyzer.generate_performance_report()
        
        # Should detect memory trend
        memory_trends = [t for t in report.trends if "memory" in t.metric_name]
        assert len(memory_trends) > 0
        
        # Should have memory recommendations
        memory_recommendations = [r for r in report.recommendations if "memory" in r.lower()]
        assert len(memory_recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance_optimization(self):
        """Test end-to-end performance optimization"""
        # Simulate tool execution with caching and performance monitoring
        from cflow_platform.core.async_tool_executor import execute_tool_async, ToolPriority
        
        with patch('cflow_platform.core.async_tool_executor.execute_mcp_tool') as mock_execute:
            mock_execute.return_value = {"status": "success", "data": "test_result"}
            
            # Execute tool with caching enabled
            result1 = await execute_tool_async(
                tool_name="test_tool",
                kwargs={"param": "value"},
                priority=ToolPriority.HIGH
            )
            
            # Execute same tool again (should hit cache)
            result2 = await execute_tool_async(
                tool_name="test_tool",
                kwargs={"param": "value"},
                priority=ToolPriority.HIGH
            )
            
            # Both should succeed
            assert result1.success
            assert result2.success
            
            # Second execution should be faster (cached)
            assert result2.execution_time < result1.execution_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
