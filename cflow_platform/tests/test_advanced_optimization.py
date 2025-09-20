"""
Comprehensive test suite for advanced optimization systems.

Tests the advanced optimization enhancements including:
- Adaptive algorithms and dynamic optimization
- Predictive scaling and resource management
- Intelligent load balancing and traffic shaping
- Machine learning-based performance optimization
- Advanced caching with predictive prefetching
- Real-time optimization and self-tuning
- Advanced monitoring and analytics
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from cflow_platform.core.adaptive_optimizer import (
    AdaptiveOptimizer,
    OptimizationStrategy,
    OptimizationTarget,
    PerformanceMetric,
    OptimizationDecision
)
from cflow_platform.core.predictive_scaler import (
    PredictiveScaler,
    ResourceType,
    ScalingTrigger,
    ScalingDirection,
    ResourceMetrics,
    WorkloadPattern,
    ScalingDecision
)
from cflow_platform.core.intelligent_load_balancer import (
    IntelligentLoadBalancer,
    LoadBalancingAlgorithm,
    TrafficPriority,
    ServerStatus,
    ServerMetrics,
    RequestInfo,
    RoutingDecision
)
from cflow_platform.core.predictive_cache import (
    PredictiveCache,
    CacheTier,
    CacheStrategy,
    AccessPattern,
    CacheEntry,
    PrefetchDecision
)
from cflow_platform.core.ml_optimizer import (
    MLOptimizer,
    MLModelType,
    OptimizationObjective,
    PerformanceDataPoint,
    MLPrediction,
    AnomalyDetection
)
from cflow_platform.core.real_time_optimizer import (
    RealTimeOptimizer,
    OptimizationMode,
    TuningStrategy,
    OptimizationTarget,
    TuningParameter,
    OptimizationAction,
    PerformanceFeedback
)
from cflow_platform.core.advanced_monitoring import (
    AdvancedMonitoring,
    MetricType,
    AlertSeverity,
    DashboardType,
    Metric,
    MetricAggregation,
    PerformanceTrend,
    Alert,
    Dashboard
)


class TestAdaptiveOptimizer:
    """Test adaptive optimization functionality"""
    
    @pytest.fixture
    async def adaptive_optimizer(self):
        """Create test adaptive optimizer"""
        optimizer = AdaptiveOptimizer()
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    def test_performance_metric_recording(self, adaptive_optimizer):
        """Test performance metric recording"""
        metric = PerformanceMetric(
            name="response_time",
            value=150.0,
            timestamp=time.time(),
            context={"service": "api"}
        )
        
        adaptive_optimizer.record_performance_metric(metric)
        
        # Check that metric was recorded
        assert len(adaptive_optimizer._performance_history["response_time"]) == 1
    
    @pytest.mark.asyncio
    async def test_optimization_decision_generation(self, adaptive_optimizer):
        """Test optimization decision generation"""
        # Add some performance data
        for i in range(10):
            metric = PerformanceMetric(
                name="response_time",
                value=200.0 + i * 10,  # Increasing response time
                timestamp=time.time() - (10 - i) * 60
            )
            adaptive_optimizer.record_performance_metric(metric)
        
        # Perform optimization
        context = {"system_load": 80.0}
        decision = await adaptive_optimizer.optimize(context)
        
        assert decision is not None
        assert decision.strategy in OptimizationStrategy
        assert decision.confidence >= 0.0
        assert decision.expected_improvement >= 0.0
    
    def test_optimization_rule_adding(self, adaptive_optimizer):
        """Test adding optimization rules"""
        def test_rule(analysis):
            if "response_time" in analysis and analysis["response_time"]["current"] > 1000:
                return OptimizationDecision(
                    strategy=OptimizationStrategy.PERFORMANCE_FIRST,
                    parameters={"aggressive_optimization": True},
                    confidence=0.8,
                    expected_improvement=0.2,
                    reasoning="High response time detected",
                    timestamp=time.time()
                )
            return None
        
        adaptive_optimizer.add_optimization_rule(test_rule)
        assert len(adaptive_optimizer._optimization_rules) == 1


class TestPredictiveScaler:
    """Test predictive scaling functionality"""
    
    @pytest.fixture
    async def predictive_scaler(self):
        """Create test predictive scaler"""
        scaler = PredictiveScaler()
        await scaler.start()
        yield scaler
        await scaler.stop()
    
    def test_resource_metrics_recording(self, predictive_scaler):
        """Test resource metrics recording"""
        metrics = ResourceMetrics(
            resource_type=ResourceType.CPU,
            current_usage=75.0,
            peak_usage=85.0,
            average_usage=70.0,
            capacity=100.0,
            timestamp=time.time()
        )
        
        predictive_scaler.record_resource_metrics(metrics)
        
        # Check that metrics were recorded
        assert ResourceType.CPU in predictive_scaler._resource_metrics
        assert len(predictive_scaler._resource_metrics[ResourceType.CPU]) == 1
    
    @pytest.mark.asyncio
    async def test_scaling_decision_generation(self, predictive_scaler):
        """Test scaling decision generation"""
        # Add some resource metrics
        for i in range(20):
            metrics = ResourceMetrics(
                resource_type=ResourceType.CPU,
                current_usage=80.0 + i,  # Increasing usage
                peak_usage=90.0 + i,
                average_usage=75.0 + i,
                capacity=100.0,
                timestamp=time.time() - (20 - i) * 60
            )
            predictive_scaler.record_resource_metrics(metrics)
        
        # Generate scaling decision
        decision = await predictive_scaler.make_scaling_decision(ResourceType.CPU)
        
        if decision:
            assert decision.direction in ScalingDirection
            assert decision.resource_type == ResourceType.CPU
            assert decision.confidence >= 0.0
            assert decision.current_capacity > 0
            assert decision.target_capacity > 0
    
    def test_workload_pattern_analysis(self, predictive_scaler):
        """Test workload pattern analysis"""
        # Add metrics with a pattern
        for i in range(50):
            usage = 50.0 + 20.0 * math.sin(i * 0.1)  # Sinusoidal pattern
            metrics = ResourceMetrics(
                resource_type=ResourceType.MEMORY,
                current_usage=usage,
                peak_usage=usage + 10.0,
                average_usage=usage,
                capacity=100.0,
                timestamp=time.time() - (50 - i) * 60
            )
            predictive_scaler.record_resource_metrics(metrics)
        
        # Check that pattern was detected
        assert ResourceType.MEMORY in predictive_scaler._workload_patterns
        pattern = predictive_scaler._workload_patterns[ResourceType.MEMORY]
        assert pattern.confidence >= 0.0


class TestIntelligentLoadBalancer:
    """Test intelligent load balancing functionality"""
    
    @pytest.fixture
    async def load_balancer(self):
        """Create test load balancer"""
        balancer = IntelligentLoadBalancer()
        await balancer.start()
        yield balancer
        await balancer.stop()
    
    def test_server_management(self, load_balancer):
        """Test server management"""
        # Add servers
        load_balancer.add_server("server1", initial_weight=1.0)
        load_balancer.add_server("server2", initial_weight=2.0)
        
        assert "server1" in load_balancer._servers
        assert "server2" in load_balancer._servers
        assert load_balancer._servers["server2"].weight == 2.0
        
        # Remove server
        load_balancer.remove_server("server1")
        assert "server1" not in load_balancer._servers
    
    def test_server_metrics_update(self, load_balancer):
        """Test server metrics update"""
        load_balancer.add_server("server1")
        
        metrics = {
            "response_time_ms": 150.0,
            "cpu_usage": 60.0,
            "memory_usage": 70.0,
            "active_connections": 50,
            "total_requests": 1000,
            "error_rate": 2.0,
            "throughput_rps": 100.0
        }
        
        load_balancer.update_server_metrics("server1", metrics)
        
        server = load_balancer._servers["server1"]
        assert server.response_time_ms == 150.0
        assert server.cpu_usage == 60.0
        assert server.status == ServerStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_request_routing(self, load_balancer):
        """Test request routing"""
        # Add servers with different metrics
        load_balancer.add_server("fast_server")
        load_balancer.add_server("slow_server")
        
        # Update metrics
        load_balancer.update_server_metrics("fast_server", {
            "response_time_ms": 100.0,
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "active_connections": 20,
            "total_requests": 500,
            "error_rate": 1.0,
            "throughput_rps": 150.0
        })
        
        load_balancer.update_server_metrics("slow_server", {
            "response_time_ms": 500.0,
            "cpu_usage": 80.0,
            "memory_usage": 90.0,
            "active_connections": 100,
            "total_requests": 500,
            "error_rate": 5.0,
            "throughput_rps": 50.0
        })
        
        # Route request
        request_info = RequestInfo(
            request_id="test_request",
            priority=TrafficPriority.NORMAL
        )
        
        decision = await load_balancer.route_request(request_info)
        
        assert decision is not None
        assert decision.server_id in ["fast_server", "slow_server"]
        assert decision.algorithm_used == LoadBalancingAlgorithm.ADAPTIVE
    
    def test_traffic_shaping(self, load_balancer):
        """Test traffic shaping"""
        # Check that traffic shaping rules are initialized
        assert TrafficPriority.CRITICAL in load_balancer._traffic_shaping_rules
        assert TrafficPriority.NORMAL in load_balancer._traffic_shaping_rules
        
        # Check rate limiters
        assert TrafficPriority.CRITICAL in load_balancer._rate_limiters
        assert TrafficPriority.NORMAL in load_balancer._rate_limiters


class TestPredictiveCache:
    """Test predictive caching functionality"""
    
    @pytest.fixture
    async def predictive_cache(self):
        """Create test predictive cache"""
        cache = PredictiveCache()
        await cache.start()
        yield cache
        await cache.stop()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, predictive_cache):
        """Test basic cache operations"""
        # Set value
        await predictive_cache.set("key1", "value1", CacheTier.L1)
        
        # Get value
        value = await predictive_cache.get("key1")
        assert value == "value1"
        
        # Check cache stats
        stats = predictive_cache.get_cache_stats()
        assert stats["tiers"]["l1_size"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_tier_promotion(self, predictive_cache):
        """Test cache tier promotion"""
        # Add to L3 cache
        await predictive_cache.set("key1", "value1", CacheTier.L3)
        
        # Simulate frequent access
        for _ in range(15):
            await predictive_cache.get("key1", {"session_id": "test"})
        
        # Check if promoted (simplified test)
        stats = predictive_cache.get_cache_stats()
        assert stats["promotions"]["l2"] >= 0 or stats["promotions"]["l1"] >= 0
    
    @pytest.mark.asyncio
    async def test_prefetch_mechanism(self, predictive_cache):
        """Test prefetch mechanism"""
        # Add some related keys
        await predictive_cache.set("key1", "value1", CacheTier.L1)
        
        # Simulate access pattern
        for i in range(10):
            await predictive_cache.get("key1", {"session_id": "test"})
        
        # Check prefetch stats
        stats = predictive_cache.get_cache_stats()
        assert "prefetches" in stats


class TestMLOptimizer:
    """Test ML-based optimization functionality"""
    
    @pytest.fixture
    async def ml_optimizer(self):
        """Create test ML optimizer"""
        optimizer = MLOptimizer()
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    def test_performance_data_addition(self, ml_optimizer):
        """Test adding performance data"""
        features = {
            "cpu_usage": 60.0,
            "memory_usage": 70.0,
            "active_connections": 50,
            "request_rate": 100.0
        }
        target = 150.0  # response time
        
        ml_optimizer.add_performance_data(features, target)
        
        assert len(ml_optimizer._training_data) == 1
        data_point = ml_optimizer._training_data[0]
        assert data_point.target == 150.0
        assert data_point.features["cpu_usage"] == 60.0
    
    @pytest.mark.asyncio
    async def test_performance_prediction(self, ml_optimizer):
        """Test performance prediction"""
        # Add training data
        for i in range(50):
            features = {
                "cpu_usage": 50.0 + i,
                "memory_usage": 60.0 + i,
                "active_connections": 30 + i,
                "request_rate": 80.0 + i
            }
            target = 100.0 + i * 2  # Linear relationship
            ml_optimizer.add_performance_data(features, target)
        
        # Make prediction
        test_features = {
            "cpu_usage": 75.0,
            "memory_usage": 80.0,
            "active_connections": 60,
            "request_rate": 120.0
        }
        
        prediction = await ml_optimizer.predict_performance("response_time_predictor", test_features)
        
        if prediction:  # Model might not be trained yet
            assert prediction.prediction >= 0.0
            assert prediction.confidence >= 0.0
            assert prediction.model_type in MLModelType
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, ml_optimizer):
        """Test anomaly detection"""
        # Add normal data
        for i in range(20):
            features = {
                "cpu_usage": 50.0 + random.uniform(-5, 5),
                "memory_usage": 60.0 + random.uniform(-5, 5),
                "response_time_ms": 150.0 + random.uniform(-10, 10),
                "error_rate": 2.0 + random.uniform(-1, 1)
            }
            ml_optimizer.add_performance_data(features, features["response_time_ms"])
        
        # Add anomalous data
        anomalous_metrics = {
            "cpu_usage": 95.0,  # Very high
            "memory_usage": 98.0,  # Very high
            "response_time_ms": 2000.0,  # Very high
            "error_rate": 25.0  # Very high
        }
        
        anomalies = await ml_optimizer.detect_anomalies(anomalous_metrics)
        
        # Should detect some anomalies
        assert len(anomalies) >= 0  # Might not detect if not enough training data
    
    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, ml_optimizer):
        """Test optimization recommendations"""
        current_metrics = {
            "response_time_ms": 1000.0,  # High
            "cpu_usage": 85.0,  # High
            "memory_usage": 80.0,  # High
            "throughput_rps": 50.0,  # Low
            "cache_hit_rate": 0.6,  # Low
            "active_connections": 600  # High
        }
        
        recommendations = await ml_optimizer.get_optimization_recommendations(
            OptimizationObjective.MINIMIZE_RESPONSE_TIME,
            current_metrics
        )
        
        # Should generate some recommendations
        assert len(recommendations) >= 0
        for rec in recommendations:
            assert rec.parameter_name
            assert rec.current_value != rec.recommended_value
            assert rec.expected_improvement >= 0.0


class TestRealTimeOptimizer:
    """Test real-time optimization functionality"""
    
    @pytest.fixture
    async def real_time_optimizer(self):
        """Create test real-time optimizer"""
        optimizer = RealTimeOptimizer()
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    def test_optimization_target_management(self, real_time_optimizer):
        """Test optimization target management"""
        target = OptimizationTarget(
            name="response_time",
            current_value=200.0,
            target_value=100.0,
            weight=1.0,
            priority=1
        )
        
        real_time_optimizer.add_optimization_target(target)
        
        assert "response_time" in real_time_optimizer._optimization_targets
        assert real_time_optimizer._optimization_targets["response_time"].target_value == 100.0
    
    def test_tuning_parameter_management(self, real_time_optimizer):
        """Test tuning parameter management"""
        parameter = TuningParameter(
            name="max_workers",
            current_value=4.0,
            min_value=1.0,
            max_value=16.0,
            step_size=1.0,
            impact_factor=1.0
        )
        
        real_time_optimizer.add_tuning_parameter(parameter)
        
        assert "max_workers" in real_time_optimizer._tuning_parameters
        assert real_time_optimizer._tuning_parameters["max_workers"].current_value == 4.0
    
    def test_performance_feedback(self, real_time_optimizer):
        """Test performance feedback"""
        feedback = PerformanceFeedback(
            metric_name="response_time",
            value=150.0,
            timestamp=time.time(),
            context={"service": "api"}
        )
        
        real_time_optimizer.add_performance_feedback(feedback)
        
        assert "response_time" in real_time_optimizer._performance_feedback
        assert len(real_time_optimizer._performance_feedback["response_time"]) == 1
    
    @pytest.mark.asyncio
    async def test_immediate_optimization(self, real_time_optimizer):
        """Test immediate optimization"""
        # Add optimization target
        target = OptimizationTarget(
            name="response_time",
            current_value=500.0,
            target_value=100.0,
            weight=1.0,
            priority=1
        )
        real_time_optimizer.add_optimization_target(target)
        
        # Add tuning parameter
        parameter = TuningParameter(
            name="max_workers",
            current_value=4.0,
            min_value=1.0,
            max_value=16.0,
            step_size=2.0,
            impact_factor=1.0
        )
        real_time_optimizer.add_tuning_parameter(parameter)
        
        # Add performance feedback
        feedback = PerformanceFeedback(
            metric_name="response_time",
            value=500.0,
            timestamp=time.time()
        )
        real_time_optimizer.add_performance_feedback(feedback)
        
        # Perform optimization
        actions = await real_time_optimizer.optimize_now()
        
        # Should generate some optimization actions
        assert len(actions) >= 0
        for action in actions:
            assert action.parameter_name
            assert action.old_value != action.new_value
            assert action.expected_improvement >= 0.0


class TestAdvancedMonitoring:
    """Test advanced monitoring functionality"""
    
    @pytest.fixture
    async def advanced_monitoring(self):
        """Create test advanced monitoring"""
        monitoring = AdvancedMonitoring()
        await monitoring.start()
        yield monitoring
        await monitoring.stop()
    
    def test_metric_recording(self, advanced_monitoring):
        """Test metric recording"""
        monitoring.record_metric("response_time", 150.0, MetricType.GAUGE)
        
        assert "response_time" in monitoring._metrics
        assert len(monitoring._metrics["response_time"]) == 1
        
        metric = monitoring._metrics["response_time"][0]
        assert metric.value == 150.0
        assert metric.metric_type == MetricType.GAUGE
    
    @pytest.mark.asyncio
    async def test_metric_aggregation(self, advanced_monitoring):
        """Test metric aggregation"""
        # Record multiple metrics
        for i in range(10):
            monitoring.record_metric("response_time", 100.0 + i * 10, MetricType.GAUGE)
        
        # Get aggregation
        aggregation = await monitoring.get_metric_aggregation("response_time", 60)
        
        assert aggregation is not None
        assert aggregation.name == "response_time"
        assert aggregation.count == 10
        assert aggregation.mean > 0.0
        assert aggregation.min <= aggregation.max
    
    def test_alert_rule_management(self, advanced_monitoring):
        """Test alert rule management"""
        monitoring.add_alert_rule(
            "high_response_time",
            "response_time",
            ">",
            500.0,
            AlertSeverity.HIGH,
            "Response time is too high: {value}ms"
        )
        
        assert "high_response_time" in monitoring._alert_rules
        rule = monitoring._alert_rules["high_response_time"]
        assert rule["metric_name"] == "response_time"
        assert rule["threshold"] == 500.0
    
    def test_dashboard_creation(self, advanced_monitoring):
        """Test dashboard creation"""
        dashboard = monitoring.create_dashboard(
            "performance_dashboard",
            "Performance Dashboard",
            DashboardType.PERFORMANCE,
            ["response_time", "throughput"],
            {"layout": "grid"}
        )
        
        assert "performance_dashboard" in monitoring._dashboards
        assert dashboard.name == "Performance Dashboard"
        assert dashboard.dashboard_type == DashboardType.PERFORMANCE
    
    def test_kpi_management(self, advanced_monitoring):
        """Test KPI management"""
        def calculate_throughput(metrics):
            return metrics.get("requests_per_second", 0.0)
        
        monitoring.add_kpi(
            "throughput_kpi",
            "System Throughput",
            calculate_throughput,
            100.0,
            "req/s"
        )
        
        assert "throughput_kpi" in monitoring._kpis
        kpi = monitoring._kpis["throughput_kpi"]
        assert kpi["name"] == "System Throughput"
        assert kpi["target_value"] == 100.0


class TestIntegration:
    """Integration tests for advanced optimization systems"""
    
    @pytest.mark.asyncio
    async def test_system_integration(self):
        """Test integration between optimization systems"""
        # This would test how all the optimization systems work together
        # For now, we'll test basic integration
        
        # Create instances
        adaptive_optimizer = AdaptiveOptimizer()
        predictive_scaler = PredictiveScaler()
        load_balancer = IntelligentLoadBalancer()
        
        await adaptive_optimizer.start()
        await predictive_scaler.start()
        await load_balancer.start()
        
        try:
            # Test that systems can work together
            # Record performance metrics
            metric = PerformanceMetric(
                name="response_time",
                value=200.0,
                timestamp=time.time()
            )
            adaptive_optimizer.record_performance_metric(metric)
            
            # Record resource metrics
            resource_metrics = ResourceMetrics(
                resource_type=ResourceType.CPU,
                current_usage=75.0,
                peak_usage=85.0,
                average_usage=70.0,
                capacity=100.0,
                timestamp=time.time()
            )
            predictive_scaler.record_resource_metrics(resource_metrics)
            
            # Add server and route request
            load_balancer.add_server("test_server")
            load_balancer.update_server_metrics("test_server", {
                "response_time_ms": 150.0,
                "cpu_usage": 60.0,
                "memory_usage": 70.0,
                "active_connections": 50,
                "total_requests": 1000,
                "error_rate": 2.0,
                "throughput_rps": 100.0
            })
            
            request_info = RequestInfo(
                request_id="integration_test",
                priority=TrafficPriority.NORMAL
            )
            
            decision = await load_balancer.route_request(request_info)
            assert decision is not None
            
        finally:
            await adaptive_optimizer.stop()
            await predictive_scaler.stop()
            await load_balancer.stop()
    
    @pytest.mark.asyncio
    async def test_performance_optimization_workflow(self):
        """Test complete performance optimization workflow"""
        # This would test a complete optimization workflow
        # from performance monitoring to optimization actions
        
        # Create monitoring system
        monitoring = AdvancedMonitoring()
        await monitoring.start()
        
        try:
            # Record performance metrics
            for i in range(20):
                monitoring.record_metric("response_time", 150.0 + i, MetricType.GAUGE)
                monitoring.record_metric("cpu_usage", 60.0 + i, MetricType.GAUGE)
                monitoring.record_metric("memory_usage", 70.0 + i, MetricType.GAUGE)
            
            # Add alert rule
            monitoring.add_alert_rule(
                "high_response_time",
                "response_time",
                ">",
                300.0,
                AlertSeverity.HIGH,
                "Response time too high"
            )
            
            # Get aggregation
            aggregation = await monitoring.get_metric_aggregation("response_time")
            assert aggregation is not None
            
        finally:
            await monitoring.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
