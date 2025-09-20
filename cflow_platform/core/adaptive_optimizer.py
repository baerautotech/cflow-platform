"""
Adaptive Optimization System for WebMCP Performance Enhancement

This module provides sophisticated adaptive optimization capabilities including:
- Dynamic algorithm selection based on performance patterns
- Adaptive parameter tuning and optimization
- Performance prediction and optimization
- Resource allocation optimization
- Workload-aware optimization strategies
- Machine learning-based optimization decisions
"""

import asyncio
import logging
import time
import math
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Optimization strategy types"""
    PERFORMANCE_FIRST = "performance_first"     # Optimize for maximum performance
    RESOURCE_EFFICIENT = "resource_efficient"   # Optimize for resource usage
    BALANCED = "balanced"                       # Balance performance and resources
    ADAPTIVE = "adaptive"                       # Dynamically adapt based on conditions


class OptimizationTarget(Enum):
    """Optimization targets"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ERROR_RATE = "error_rate"
    COST = "cost"


@dataclass
class PerformanceMetric:
    """Performance metric with context"""
    name: str
    value: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class OptimizationDecision:
    """Optimization decision result"""
    strategy: OptimizationStrategy
    parameters: Dict[str, Any]
    confidence: float
    expected_improvement: float
    reasoning: str
    timestamp: float


@dataclass
class OptimizationResult:
    """Result of optimization action"""
    decision: OptimizationDecision
    actual_improvement: float
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    success: bool
    execution_time_ms: float


class AdaptiveOptimizer:
    """
    Advanced adaptive optimization system with machine learning capabilities.
    
    Features:
    - Dynamic algorithm selection
    - Adaptive parameter tuning
    - Performance prediction
    - Resource optimization
    - Workload-aware strategies
    - Continuous learning and improvement
    """
    
    def __init__(
        self,
        optimization_targets: List[OptimizationTarget] = None,
        learning_rate: float = 0.1,
        history_window: int = 1000
    ):
        self.optimization_targets = optimization_targets or [OptimizationTarget.RESPONSE_TIME]
        self.learning_rate = learning_rate
        self.history_window = history_window
        
        # Performance history
        self._performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_window)
        )
        self._optimization_history: List[OptimizationResult] = []
        
        # Current configuration
        self._current_strategy = OptimizationStrategy.BALANCED
        self._current_parameters: Dict[str, Any] = {}
        
        # Optimization models
        self._performance_models: Dict[str, Any] = {}
        self._optimization_models: Dict[str, Any] = {}
        
        # Background tasks
        self._optimization_task: Optional[asyncio.Task] = None
        self._learning_task: Optional[asyncio.Task] = None
        
        # Optimization rules
        self._optimization_rules: List[Callable] = []
        
        # Performance baselines
        self._performance_baselines: Dict[str, float] = {}
        
        # Adaptive parameters
        self._adaptation_speed = 0.1
        self._exploration_rate = 0.1
        self._exploitation_rate = 0.9
    
    async def start(self):
        """Start adaptive optimization"""
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        self._learning_task = asyncio.create_task(self._learning_loop())
        logger.info("AdaptiveOptimizer started")
    
    async def stop(self):
        """Stop adaptive optimization"""
        if self._optimization_task:
            self._optimization_task.cancel()
        if self._learning_task:
            self._learning_task.cancel()
        logger.info("AdaptiveOptimizer stopped")
    
    def record_performance_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self._performance_history[metric.name].append(metric)
        
        # Update performance baseline
        if metric.name not in self._performance_baselines:
            self._performance_baselines[metric.name] = metric.value
        else:
            # Exponential moving average
            self._performance_baselines[metric.name] = (
                self._adaptation_speed * metric.value +
                (1 - self._adaptation_speed) * self._performance_baselines[metric.name]
            )
    
    def add_optimization_rule(self, rule_func: Callable[[Dict[str, Any]], Optional[OptimizationDecision]]):
        """Add an optimization rule"""
        self._optimization_rules.append(rule_func)
    
    async def optimize(self, context: Dict[str, Any]) -> OptimizationDecision:
        """Perform adaptive optimization"""
        # Analyze current performance
        performance_analysis = self._analyze_performance()
        
        # Get optimization recommendations
        recommendations = await self._get_optimization_recommendations(performance_analysis, context)
        
        # Select best strategy
        best_decision = self._select_optimal_strategy(recommendations)
        
        # Apply optimization
        await self._apply_optimization(best_decision)
        
        return best_decision
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance patterns"""
        analysis = {}
        
        for metric_name, history in self._performance_history.items():
            if not history:
                continue
            
            values = [m.value for m in history]
            recent_values = values[-10:] if len(values) >= 10 else values
            
            analysis[metric_name] = {
                "current": values[-1] if values else 0.0,
                "average": statistics.mean(values),
                "trend": self._calculate_trend(values),
                "volatility": statistics.stdev(values) if len(values) > 1 else 0.0,
                "recent_average": statistics.mean(recent_values),
                "baseline": self._performance_baselines.get(metric_name, 0.0),
                "improvement_potential": self._calculate_improvement_potential(values),
                "sample_count": len(values)
            }
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_improvement_potential(self, values: List[float]) -> float:
        """Calculate potential for improvement"""
        if not values:
            return 0.0
        
        current = values[-1]
        baseline = self._performance_baselines.get("default", current)
        
        # Improvement potential is the difference from baseline
        if baseline > 0:
            return (baseline - current) / baseline
        return 0.0
    
    async def _get_optimization_recommendations(
        self,
        performance_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[OptimizationDecision]:
        """Get optimization recommendations from all sources"""
        recommendations = []
        
        # Get recommendations from rules
        for rule_func in self._optimization_rules:
            try:
                decision = rule_func(performance_analysis)
                if decision:
                    recommendations.append(decision)
            except Exception as e:
                logger.warning(f"Optimization rule failed: {e}")
        
        # Get recommendations from ML models
        ml_recommendations = await self._get_ml_recommendations(performance_analysis, context)
        recommendations.extend(ml_recommendations)
        
        # Get recommendations from heuristics
        heuristic_recommendations = self._get_heuristic_recommendations(performance_analysis)
        recommendations.extend(heuristic_recommendations)
        
        return recommendations
    
    async def _get_ml_recommendations(
        self,
        performance_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[OptimizationDecision]:
        """Get machine learning-based recommendations"""
        recommendations = []
        
        # Simple ML-based optimization (in a real implementation, this would use
        # more sophisticated ML models)
        
        # Analyze patterns and make predictions
        for metric_name, analysis in performance_analysis.items():
            if analysis["trend"] < -0.1 and analysis["volatility"] > analysis["average"] * 0.2:
                # Performance is degrading with high volatility
                decision = OptimizationDecision(
                    strategy=OptimizationStrategy.PERFORMANCE_FIRST,
                    parameters={
                        "target_metric": metric_name,
                        "aggressive_optimization": True,
                        "stability_factor": 0.8
                    },
                    confidence=0.7,
                    expected_improvement=analysis["improvement_potential"],
                    reasoning=f"ML detected degrading performance in {metric_name}",
                    timestamp=time.time()
                )
                recommendations.append(decision)
        
        return recommendations
    
    def _get_heuristic_recommendations(
        self,
        performance_analysis: Dict[str, Any]
    ) -> List[OptimizationDecision]:
        """Get heuristic-based optimization recommendations"""
        recommendations = []
        
        # High-level optimization heuristics
        for metric_name, analysis in performance_analysis.items():
            if analysis["current"] > analysis["baseline"] * 1.5:
                # Performance is significantly worse than baseline
                decision = OptimizationDecision(
                    strategy=OptimizationStrategy.BALANCED,
                    parameters={
                        "target_metric": metric_name,
                        "optimization_level": "high",
                        "focus": "immediate"
                    },
                    confidence=0.8,
                    expected_improvement=min(0.5, analysis["improvement_potential"]),
                    reasoning=f"Heuristic: {metric_name} significantly worse than baseline",
                    timestamp=time.time()
                )
                recommendations.append(decision)
            
            elif analysis["trend"] > 0.1 and analysis["volatility"] < analysis["average"] * 0.1:
                # Performance is improving with low volatility
                decision = OptimizationDecision(
                    strategy=OptimizationStrategy.RESOURCE_EFFICIENT,
                    parameters={
                        "target_metric": metric_name,
                        "optimization_level": "low",
                        "focus": "efficiency"
                    },
                    confidence=0.6,
                    expected_improvement=0.1,
                    reasoning=f"Heuristic: {metric_name} improving, focus on efficiency",
                    timestamp=time.time()
                )
                recommendations.append(decision)
        
        return recommendations
    
    def _select_optimal_strategy(self, recommendations: List[OptimizationDecision]) -> OptimizationDecision:
        """Select the optimal strategy from recommendations"""
        if not recommendations:
            # Default strategy
            return OptimizationDecision(
                strategy=OptimizationStrategy.BALANCED,
                parameters={},
                confidence=0.5,
                expected_improvement=0.0,
                reasoning="No recommendations available, using default strategy",
                timestamp=time.time()
            )
        
        # Score recommendations based on confidence and expected improvement
        scored_recommendations = []
        for rec in recommendations:
            score = (rec.confidence * 0.6 + rec.expected_improvement * 0.4)
            scored_recommendations.append((score, rec))
        
        # Select highest scoring recommendation
        scored_recommendations.sort(key=lambda x: x[0], reverse=True)
        return scored_recommendations[0][1]
    
    async def _apply_optimization(self, decision: OptimizationDecision):
        """Apply the selected optimization strategy"""
        logger.info(f"Applying optimization: {decision.strategy.value} - {decision.reasoning}")
        
        # Update current strategy and parameters
        self._current_strategy = decision.strategy
        self._current_parameters.update(decision.parameters)
        
        # Apply strategy-specific optimizations
        if decision.strategy == OptimizationStrategy.PERFORMANCE_FIRST:
            await self._apply_performance_optimization(decision.parameters)
        elif decision.strategy == OptimizationStrategy.RESOURCE_EFFICIENT:
            await self._apply_resource_optimization(decision.parameters)
        elif decision.strategy == OptimizationStrategy.BALANCED:
            await self._apply_balanced_optimization(decision.parameters)
        elif decision.strategy == OptimizationStrategy.ADAPTIVE:
            await self._apply_adaptive_optimization(decision.parameters)
    
    async def _apply_performance_optimization(self, parameters: Dict[str, Any]):
        """Apply performance-first optimization"""
        # Optimize for maximum performance
        target_metric = parameters.get("target_metric", "response_time")
        
        if target_metric == "response_time":
            # Optimize for faster response times
            self._current_parameters.update({
                "cache_aggressive": True,
                "parallel_processing": True,
                "connection_pooling": True,
                "prefetching": True
            })
        elif target_metric == "throughput":
            # Optimize for higher throughput
            self._current_parameters.update({
                "batch_processing": True,
                "async_processing": True,
                "connection_reuse": True,
                "load_balancing": True
            })
    
    async def _apply_resource_optimization(self, parameters: Dict[str, Any]):
        """Apply resource-efficient optimization"""
        # Optimize for resource usage
        self._current_parameters.update({
            "memory_optimization": True,
            "cpu_optimization": True,
            "cache_compression": True,
            "connection_pooling": False,  # Reduce resource usage
            "batch_size": 50  # Smaller batches
        })
    
    async def _apply_balanced_optimization(self, parameters: Dict[str, Any]):
        """Apply balanced optimization"""
        # Balance performance and resources
        self._current_parameters.update({
            "cache_moderate": True,
            "parallel_processing": True,
            "memory_optimization": True,
            "connection_pooling": True,
            "batch_size": 100
        })
    
    async def _apply_adaptive_optimization(self, parameters: Dict[str, Any]):
        """Apply adaptive optimization"""
        # Dynamically adapt based on current conditions
        performance_analysis = self._analyze_performance()
        
        # Determine current conditions
        avg_response_time = performance_analysis.get("response_time", {}).get("current", 0.0)
        avg_memory_usage = performance_analysis.get("memory_usage", {}).get("current", 0.0)
        
        if avg_response_time > 1000.0:  # High response time
            await self._apply_performance_optimization({"target_metric": "response_time"})
        elif avg_memory_usage > 80.0:  # High memory usage
            await self._apply_resource_optimization({"target_metric": "memory_usage"})
        else:
            await self._apply_balanced_optimization({})
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Optimize every minute
                
                # Get current context
                context = {
                    "timestamp": time.time(),
                    "system_load": self._get_system_load(),
                    "active_requests": self._get_active_request_count()
                }
                
                # Perform optimization
                decision = await self.optimize(context)
                
                logger.debug(f"Optimization completed: {decision.strategy.value}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
    
    async def _learning_loop(self):
        """Background learning loop"""
        while True:
            try:
                await asyncio.sleep(300.0)  # Learn every 5 minutes
                
                # Update ML models based on recent performance
                await self._update_performance_models()
                
                # Analyze optimization effectiveness
                await self._analyze_optimization_effectiveness()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning loop error: {e}")
    
    async def _update_performance_models(self):
        """Update performance prediction models"""
        # In a real implementation, this would update ML models
        # For now, we'll update simple statistical models
        
        for metric_name, history in self._performance_history.items():
            if len(history) < 10:
                continue
            
            values = [m.value for m in history]
            
            # Update simple moving average model
            self._performance_models[f"{metric_name}_ma"] = statistics.mean(values[-10:])
            
            # Update trend model
            if len(values) >= 5:
                recent_trend = self._calculate_trend(values[-5:])
                self._performance_models[f"{metric_name}_trend"] = recent_trend
    
    async def _analyze_optimization_effectiveness(self):
        """Analyze the effectiveness of recent optimizations"""
        if len(self._optimization_history) < 2:
            return
        
        recent_results = self._optimization_history[-10:]
        
        # Calculate average improvement
        improvements = [r.actual_improvement for r in recent_results if r.success]
        
        if improvements:
            avg_improvement = statistics.mean(improvements)
            
            # Adjust learning parameters based on effectiveness
            if avg_improvement > 0.1:  # Good improvement
                self._exploitation_rate = min(0.95, self._exploitation_rate + 0.05)
                self._exploration_rate = max(0.05, self._exploration_rate - 0.05)
            elif avg_improvement < 0.0:  # Negative improvement
                self._exploitation_rate = max(0.7, self._exploitation_rate - 0.05)
                self._exploration_rate = min(0.3, self._exploration_rate + 0.05)
    
    def _get_system_load(self) -> float:
        """Get current system load"""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            return 50.0  # Default value
    
    def _get_active_request_count(self) -> int:
        """Get current active request count"""
        # This would integrate with the request tracking system
        return 0
    
    def get_current_strategy(self) -> OptimizationStrategy:
        """Get current optimization strategy"""
        return self._current_strategy
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current optimization parameters"""
        return self._current_parameters.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        analysis = self._analyze_performance()
        
        return {
            "current_strategy": self._current_strategy.value,
            "parameters": self._current_parameters,
            "performance_metrics": analysis,
            "optimization_history_count": len(self._optimization_history),
            "learning_parameters": {
                "adaptation_speed": self._adaptation_speed,
                "exploration_rate": self._exploration_rate,
                "exploitation_rate": self._exploitation_rate
            }
        }


# Global adaptive optimizer
_adaptive_optimizer: Optional[AdaptiveOptimizer] = None


async def get_adaptive_optimizer() -> AdaptiveOptimizer:
    """Get the global adaptive optimizer"""
    global _adaptive_optimizer
    if _adaptive_optimizer is None:
        _adaptive_optimizer = AdaptiveOptimizer()
        await _adaptive_optimizer.start()
    return _adaptive_optimizer


def record_performance_metric(name: str, value: float, context: Dict[str, Any] = None):
    """Record a performance metric"""
    if _adaptive_optimizer:
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            context=context or {}
        )
        _adaptive_optimizer.record_performance_metric(metric)


async def optimize_performance(context: Dict[str, Any] = None) -> OptimizationDecision:
    """Perform adaptive optimization"""
    optimizer = await get_adaptive_optimizer()
    return await optimizer.optimize(context or {})
