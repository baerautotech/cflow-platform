"""
Predictive Scaling and Resource Management System for WebMCP Performance Enhancement

This module provides intelligent predictive scaling capabilities including:
- Predictive resource scaling based on workload patterns
- Intelligent resource allocation and optimization
- Capacity planning and forecasting
- Dynamic resource provisioning
- Cost optimization and efficiency
- Performance-based scaling decisions
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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ScalingTrigger(Enum):
    """Scaling trigger types"""
    PREDICTIVE = "predictive"           # Based on predictions
    REACTIVE = "reactive"               # Based on current metrics
    SCHEDULED = "scheduled"             # Based on schedule
    MANUAL = "manual"                   # Manual scaling


class ResourceType(Enum):
    """Resource types for scaling"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    CONNECTIONS = "connections"
    INSTANCES = "instances"


class ScalingDirection(Enum):
    """Scaling direction"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"


@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    resource_type: ResourceType
    current_usage: float
    peak_usage: float
    average_usage: float
    capacity: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkloadPattern:
    """Workload pattern analysis"""
    pattern_type: str                   # "linear", "exponential", "periodic", "spike"
    trend: float                        # Trend direction and strength
    seasonality: Optional[Dict[str, float]] = None  # Seasonal patterns
    volatility: float = 0.0             # Pattern volatility
    confidence: float = 0.0             # Pattern confidence
    next_expected_value: Optional[float] = None
    prediction_window_minutes: int = 60


@dataclass
class ScalingDecision:
    """Scaling decision result"""
    direction: ScalingDirection
    resource_type: ResourceType
    current_capacity: float
    target_capacity: float
    scaling_factor: float
    trigger: ScalingTrigger
    confidence: float
    reasoning: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingAction:
    """Scaling action to be executed"""
    decision: ScalingDecision
    execution_time: float
    estimated_duration: float
    cost_impact: float
    success: bool = False
    error_message: Optional[str] = None


class PredictiveScaler:
    """
    Intelligent predictive scaling system with advanced forecasting capabilities.
    
    Features:
    - Predictive workload analysis
    - Intelligent resource scaling
    - Cost optimization
    - Performance-based decisions
    - Capacity planning
    - Dynamic resource provisioning
    """
    
    def __init__(
        self,
        prediction_window_minutes: int = 60,
        scaling_cooldown_minutes: int = 5,
        max_scaling_factor: float = 2.0,
        min_scaling_factor: float = 0.5
    ):
        self.prediction_window_minutes = prediction_window_minutes
        self.scaling_cooldown_minutes = scaling_cooldown_minutes
        self.max_scaling_factor = max_scaling_factor
        self.min_scaling_factor = min_scaling_factor
        
        # Resource tracking
        self._resource_metrics: Dict[ResourceType, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._current_capacity: Dict[ResourceType, float] = {
            rt: 1.0 for rt in ResourceType
        }
        
        # Workload patterns
        self._workload_patterns: Dict[ResourceType, WorkloadPattern] = {}
        
        # Scaling history
        self._scaling_history: List[ScalingAction] = []
        self._last_scaling_time: Dict[ResourceType, float] = {}
        
        # Prediction models
        self._prediction_models: Dict[str, Any] = {}
        
        # Background tasks
        self._prediction_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        
        # Scaling policies
        self._scaling_policies: Dict[ResourceType, Dict[str, Any]] = {
            ResourceType.CPU: {
                "scale_up_threshold": 80.0,
                "scale_down_threshold": 30.0,
                "target_utilization": 60.0,
                "scaling_step": 0.2
            },
            ResourceType.MEMORY: {
                "scale_up_threshold": 85.0,
                "scale_down_threshold": 40.0,
                "target_utilization": 70.0,
                "scaling_step": 0.25
            },
            ResourceType.INSTANCES: {
                "scale_up_threshold": 75.0,
                "scale_down_threshold": 25.0,
                "target_utilization": 50.0,
                "scaling_step": 1.0
            }
        }
        
        # Cost optimization
        self._cost_weights: Dict[ResourceType, float] = {
            ResourceType.CPU: 1.0,
            ResourceType.MEMORY: 0.8,
            ResourceType.STORAGE: 0.5,
            ResourceType.NETWORK: 0.3,
            ResourceType.CONNECTIONS: 0.2,
            ResourceType.INSTANCES: 2.0
        }
    
    async def start(self):
        """Start predictive scaling"""
        self._prediction_task = asyncio.create_task(self._prediction_loop())
        self._scaling_task = asyncio.create_task(self._scaling_loop())
        logger.info("PredictiveScaler started")
    
    async def stop(self):
        """Stop predictive scaling"""
        if self._prediction_task:
            self._prediction_task.cancel()
        if self._scaling_task:
            self._scaling_task.cancel()
        logger.info("PredictiveScaler stopped")
    
    def record_resource_metrics(self, metrics: ResourceMetrics):
        """Record resource usage metrics"""
        self._resource_metrics[metrics.resource_type].append(metrics)
        
        # Update workload patterns
        self._update_workload_pattern(metrics.resource_type)
    
    def _update_workload_pattern(self, resource_type: ResourceType):
        """Update workload pattern analysis"""
        metrics_history = list(self._resource_metrics[resource_type])
        
        if len(metrics_history) < 10:
            return
        
        # Analyze recent usage patterns
        recent_usage = [m.current_usage for m in metrics_history[-50:]]
        
        # Calculate trend
        trend = self._calculate_trend(recent_usage)
        
        # Detect pattern type
        pattern_type = self._detect_pattern_type(recent_usage)
        
        # Calculate volatility
        volatility = self._calculate_volatility(recent_usage)
        
        # Predict next value
        next_value = self._predict_next_value(recent_usage, trend)
        
        # Calculate confidence
        confidence = self._calculate_prediction_confidence(recent_usage, trend, volatility)
        
        self._workload_patterns[resource_type] = WorkloadPattern(
            pattern_type=pattern_type,
            trend=trend,
            volatility=volatility,
            confidence=confidence,
            next_expected_value=next_value,
            prediction_window_minutes=self.prediction_window_minutes
        )
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in usage values"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _detect_pattern_type(self, values: List[float]) -> str:
        """Detect the type of workload pattern"""
        if len(values) < 10:
            return "unknown"
        
        # Calculate various pattern indicators
        trend = self._calculate_trend(values)
        volatility = self._calculate_volatility(values)
        
        # Detect spikes
        max_val = max(values)
        avg_val = statistics.mean(values)
        if max_val > avg_val * 2:
            return "spike"
        
        # Detect periodic patterns
        if self._detect_periodicity(values):
            return "periodic"
        
        # Detect exponential growth
        if trend > 0.1 and self._detect_exponential_growth(values):
            return "exponential"
        
        # Detect linear growth
        if abs(trend) > 0.01:
            return "linear"
        
        return "stable"
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility of values"""
        if len(values) < 2:
            return 0.0
        
        mean_val = statistics.mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _detect_periodicity(self, values: List[float]) -> bool:
        """Detect if values show periodic patterns"""
        if len(values) < 20:
            return False
        
        # Simple periodicity detection using autocorrelation
        n = len(values)
        mean_val = statistics.mean(values)
        
        # Calculate autocorrelation for different lags
        max_correlation = 0.0
        for lag in range(1, min(10, n // 2)):
            correlation = self._calculate_autocorrelation(values, lag, mean_val)
            max_correlation = max(max_correlation, abs(correlation))
        
        return max_correlation > 0.5  # Threshold for periodicity
    
    def _calculate_autocorrelation(self, values: List[float], lag: int, mean_val: float) -> float:
        """Calculate autocorrelation for given lag"""
        n = len(values)
        if lag >= n:
            return 0.0
        
        numerator = sum((values[i] - mean_val) * (values[i + lag] - mean_val) for i in range(n - lag))
        denominator = sum((values[i] - mean_val) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _detect_exponential_growth(self, values: List[float]) -> bool:
        """Detect exponential growth pattern"""
        if len(values) < 5:
            return False
        
        # Check if growth rate is increasing
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                growth_rate = (values[i] - values[i-1]) / values[i-1]
                growth_rates.append(growth_rate)
        
        if len(growth_rates) < 3:
            return False
        
        # Check if growth rates are increasing
        return self._calculate_trend(growth_rates) > 0.01
    
    def _predict_next_value(self, values: List[float], trend: float) -> float:
        """Predict next value based on trend"""
        if not values:
            return 0.0
        
        current_value = values[-1]
        predicted_value = current_value + trend
        
        # Apply some smoothing
        recent_avg = statistics.mean(values[-5:]) if len(values) >= 5 else current_value
        return 0.7 * predicted_value + 0.3 * recent_avg
    
    def _calculate_prediction_confidence(self, values: List[float], trend: float, volatility: float) -> float:
        """Calculate confidence in prediction"""
        if not values:
            return 0.0
        
        # Confidence based on trend consistency and volatility
        trend_consistency = 1.0 - min(1.0, volatility / statistics.mean(values))
        volatility_factor = max(0.0, 1.0 - volatility / 100.0)  # Normalize volatility
        
        return (trend_consistency + volatility_factor) / 2.0
    
    async def make_scaling_decision(self, resource_type: ResourceType) -> Optional[ScalingDecision]:
        """Make intelligent scaling decision for a resource"""
        # Check cooldown period
        if resource_type in self._last_scaling_time:
            time_since_last_scaling = time.time() - self._last_scaling_time[resource_type]
            if time_since_last_scaling < self.scaling_cooldown_minutes * 60:
                return None
        
        # Get current metrics
        current_metrics = self._get_current_metrics(resource_type)
        if not current_metrics:
            return None
        
        # Get workload pattern
        pattern = self._workload_patterns.get(resource_type)
        
        # Get scaling policy
        policy = self._scaling_policies.get(resource_type, {})
        
        # Make scaling decision
        decision = await self._evaluate_scaling_need(
            resource_type, current_metrics, pattern, policy
        )
        
        return decision
    
    def _get_current_metrics(self, resource_type: ResourceType) -> Optional[ResourceMetrics]:
        """Get current resource metrics"""
        metrics_history = self._resource_metrics.get(resource_type)
        if not metrics_history:
            return None
        
        return list(metrics_history)[-1]
    
    async def _evaluate_scaling_need(
        self,
        resource_type: ResourceType,
        current_metrics: ResourceMetrics,
        pattern: Optional[WorkloadPattern],
        policy: Dict[str, Any]
    ) -> ScalingDecision:
        """Evaluate if scaling is needed"""
        current_usage = current_metrics.current_usage
        current_capacity = self._current_capacity[resource_type]
        
        # Determine scaling direction based on current usage and predictions
        if pattern and pattern.next_expected_value:
            predicted_usage = pattern.next_expected_value
            confidence = pattern.confidence
            
            # Use prediction if confidence is high enough
            if confidence > 0.7:
                usage_for_decision = predicted_usage
                trigger = ScalingTrigger.PREDICTIVE
                reasoning = f"Predicted usage: {predicted_usage:.1f}% (confidence: {confidence:.2f})"
            else:
                usage_for_decision = current_usage
                trigger = ScalingTrigger.REACTIVE
                reasoning = f"Low prediction confidence ({confidence:.2f}), using current usage: {current_usage:.1f}%"
        else:
            usage_for_decision = current_usage
            trigger = ScalingTrigger.REACTIVE
            reasoning = f"No prediction available, using current usage: {current_usage:.1f}%"
        
        # Determine scaling direction
        scale_up_threshold = policy.get("scale_up_threshold", 80.0)
        scale_down_threshold = policy.get("scale_down_threshold", 30.0)
        target_utilization = policy.get("target_utilization", 60.0)
        
        if usage_for_decision > scale_up_threshold:
            direction = ScalingDirection.SCALE_UP
            target_capacity = current_capacity * (1.0 + policy.get("scaling_step", 0.2))
            scaling_factor = target_capacity / current_capacity
        elif usage_for_decision < scale_down_threshold and current_capacity > 1.0:
            direction = ScalingDirection.SCALE_DOWN
            target_capacity = current_capacity * (1.0 - policy.get("scaling_step", 0.2))
            target_capacity = max(1.0, target_capacity)  # Don't scale below 1
            scaling_factor = target_capacity / current_capacity
        else:
            direction = ScalingDirection.MAINTAIN
            target_capacity = current_capacity
            scaling_factor = 1.0
        
        # Calculate confidence
        confidence = pattern.confidence if pattern else 0.5
        
        return ScalingDecision(
            direction=direction,
            resource_type=resource_type,
            current_capacity=current_capacity,
            target_capacity=target_capacity,
            scaling_factor=scaling_factor,
            trigger=trigger,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=time.time()
        )
    
    async def execute_scaling_action(self, decision: ScalingDecision) -> ScalingAction:
        """Execute a scaling action"""
        start_time = time.time()
        
        try:
            # Simulate scaling execution
            await self._perform_scaling(decision)
            
            # Update current capacity
            self._current_capacity[decision.resource_type] = decision.target_capacity
            self._last_scaling_time[decision.resource_type] = time.time()
            
            # Calculate cost impact
            cost_impact = self._calculate_cost_impact(decision)
            
            execution_time = time.time() - start_time
            
            action = ScalingAction(
                decision=decision,
                execution_time=execution_time,
                estimated_duration=execution_time,
                cost_impact=cost_impact,
                success=True
            )
            
            self._scaling_history.append(action)
            
            logger.info(
                f"Scaling {decision.direction.value} {decision.resource_type.value}: "
                f"{decision.current_capacity:.2f} -> {decision.target_capacity:.2f} "
                f"(factor: {decision.scaling_factor:.2f})"
            )
            
            return action
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            action = ScalingAction(
                decision=decision,
                execution_time=execution_time,
                estimated_duration=execution_time,
                cost_impact=0.0,
                success=False,
                error_message=str(e)
            )
            
            self._scaling_history.append(action)
            
            logger.error(f"Scaling failed: {e}")
            return action
    
    async def _perform_scaling(self, decision: ScalingDecision):
        """Perform the actual scaling operation"""
        # Simulate scaling delay
        scaling_delay = abs(decision.scaling_factor - 1.0) * 2.0  # More scaling = more delay
        await asyncio.sleep(min(scaling_delay, 5.0))  # Cap at 5 seconds
        
        # In a real implementation, this would:
        # - Call cloud provider APIs
        # - Update load balancer configurations
        # - Modify resource allocations
        # - Update monitoring configurations
    
    def _calculate_cost_impact(self, decision: ScalingDecision) -> float:
        """Calculate the cost impact of a scaling decision"""
        resource_cost = self._cost_weights.get(decision.resource_type, 1.0)
        capacity_change = decision.target_capacity - decision.current_capacity
        
        return resource_cost * capacity_change
    
    async def _prediction_loop(self):
        """Background prediction loop"""
        while True:
            try:
                await asyncio.sleep(30.0)  # Update predictions every 30 seconds
                
                # Update workload patterns for all resources
                for resource_type in ResourceType:
                    if resource_type in self._resource_metrics:
                        self._update_workload_pattern(resource_type)
                
                # Update prediction models
                await self._update_prediction_models()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
    
    async def _scaling_loop(self):
        """Background scaling loop"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check scaling needs every minute
                
                # Evaluate scaling for all resources
                for resource_type in ResourceType:
                    decision = await self.make_scaling_decision(resource_type)
                    
                    if decision and decision.direction != ScalingDirection.MAINTAIN:
                        # Execute scaling if needed
                        await self.execute_scaling_action(decision)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling loop error: {e}")
    
    async def _update_prediction_models(self):
        """Update prediction models"""
        # In a real implementation, this would update ML models
        # For now, we'll update simple statistical models
        
        for resource_type, pattern in self._workload_patterns.items():
            # Store model parameters
            model_key = f"{resource_type.value}_model"
            self._prediction_models[model_key] = {
                "trend": pattern.trend,
                "volatility": pattern.volatility,
                "confidence": pattern.confidence,
                "last_updated": time.time()
            }
    
    def get_workload_patterns(self) -> Dict[ResourceType, WorkloadPattern]:
        """Get current workload patterns"""
        return self._workload_patterns.copy()
    
    def get_current_capacity(self) -> Dict[ResourceType, float]:
        """Get current resource capacity"""
        return self._current_capacity.copy()
    
    def get_scaling_history(self, limit: int = 50) -> List[ScalingAction]:
        """Get scaling history"""
        return self._scaling_history[-limit:] if self._scaling_history else []
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get scaling statistics"""
        if not self._scaling_history:
            return {"total_scaling_actions": 0}
        
        successful_actions = [a for a in self._scaling_history if a.success]
        failed_actions = [a for a in self._scaling_history if not a.success]
        
        scale_up_actions = [a for a in self._scaling_history if a.decision.direction == ScalingDirection.SCALE_UP]
        scale_down_actions = [a for a in self._scaling_history if a.decision.direction == ScalingDirection.SCALE_DOWN]
        
        total_cost_impact = sum(a.cost_impact for a in self._scaling_history)
        avg_execution_time = statistics.mean([a.execution_time for a in self._scaling_history])
        
        return {
            "total_scaling_actions": len(self._scaling_history),
            "successful_actions": len(successful_actions),
            "failed_actions": len(failed_actions),
            "scale_up_actions": len(scale_up_actions),
            "scale_down_actions": len(scale_down_actions),
            "success_rate": len(successful_actions) / len(self._scaling_history),
            "total_cost_impact": total_cost_impact,
            "average_execution_time": avg_execution_time,
            "current_capacity": self._current_capacity
        }


# Global predictive scaler
_predictive_scaler: Optional[PredictiveScaler] = None


async def get_predictive_scaler() -> PredictiveScaler:
    """Get the global predictive scaler"""
    global _predictive_scaler
    if _predictive_scaler is None:
        _predictive_scaler = PredictiveScaler()
        await _predictive_scaler.start()
    return _predictive_scaler


def record_resource_metrics(
    resource_type: ResourceType,
    current_usage: float,
    peak_usage: float,
    average_usage: float,
    capacity: float,
    metadata: Dict[str, Any] = None
):
    """Record resource usage metrics"""
    if _predictive_scaler:
        metrics = ResourceMetrics(
            resource_type=resource_type,
            current_usage=current_usage,
            peak_usage=peak_usage,
            average_usage=average_usage,
            capacity=capacity,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        _predictive_scaler.record_resource_metrics(metrics)


async def get_scaling_recommendation(resource_type: ResourceType) -> Optional[ScalingDecision]:
    """Get scaling recommendation for a resource"""
    scaler = await get_predictive_scaler()
    return await scaler.make_scaling_decision(resource_type)
