"""
Real-Time Optimization and Self-Tuning Mechanisms for WebMCP Performance Enhancement

This module provides real-time optimization capabilities including:
- Continuous performance monitoring and optimization
- Self-tuning parameter adjustment
- Real-time feedback loops and control systems
- Dynamic configuration management
- Performance-based auto-scaling
- Intelligent system adaptation
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


class OptimizationMode(Enum):
    """Real-time optimization modes"""
    AGGRESSIVE = "aggressive"           # Fast, potentially unstable
    BALANCED = "balanced"               # Moderate speed and stability
    CONSERVATIVE = "conservative"       # Slow, very stable
    ADAPTIVE = "adaptive"               # Dynamically adjusts


class TuningStrategy(Enum):
    """Self-tuning strategies"""
    GRADIENT_DESCENT = "gradient_descent"
    GENETIC_ALGORITHM = "genetic_algorithm"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    RANDOM_SEARCH = "random_search"


class ControlLoopType(Enum):
    """Control loop types"""
    PID = "pid"                         # Proportional-Integral-Derivative
    ADAPTIVE = "adaptive"               # Adaptive control
    MODEL_PREDICTIVE = "model_predictive"  # Model predictive control
    FUZZY = "fuzzy"                     # Fuzzy logic control


@dataclass
class OptimizationTarget:
    """Optimization target definition"""
    name: str
    current_value: float
    target_value: float
    weight: float = 1.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    tolerance: float = 0.05
    priority: int = 1


@dataclass
class TuningParameter:
    """Self-tuning parameter definition"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    step_size: float
    impact_factor: float = 1.0
    adjustment_history: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class OptimizationAction:
    """Optimization action result"""
    parameter_name: str
    old_value: float
    new_value: float
    expected_improvement: float
    confidence: float
    execution_time_ms: float
    success: bool = True
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceFeedback:
    """Performance feedback for optimization"""
    metric_name: str
    value: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)


class RealTimeOptimizer:
    """
    Real-time optimization and self-tuning system.
    
    Features:
    - Continuous performance monitoring
    - Self-tuning parameter adjustment
    - Real-time feedback loops
    - Dynamic configuration management
    - Performance-based auto-scaling
    - Intelligent system adaptation
    """
    
    def __init__(
        self,
        optimization_interval: float = 10.0,
        tuning_interval: float = 30.0,
        feedback_window: int = 100
    ):
        self.optimization_interval = optimization_interval
        self.tuning_interval = tuning_interval
        self.feedback_window = feedback_window
        
        # Optimization state
        self._optimization_mode = OptimizationMode.ADAPTIVE
        self._tuning_strategy = TuningStrategy.GRADIENT_DESCENT
        self._control_loop_type = ControlLoopType.PID
        
        # Targets and parameters
        self._optimization_targets: Dict[str, OptimizationTarget] = {}
        self._tuning_parameters: Dict[str, TuningParameter] = {}
        
        # Performance feedback
        self._performance_feedback: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=feedback_window)
        )
        self._optimization_history: deque = deque(maxlen=1000)
        
        # Control loops
        self._control_loops: Dict[str, Dict[str, float]] = {}
        
        # Background tasks
        self._optimization_task: Optional[asyncio.Task] = None
        self._tuning_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._performance_baselines: Dict[str, float] = {}
        self._performance_trends: Dict[str, List[float]] = defaultdict(list)
        
        # Optimization statistics
        self._optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "failed_optimizations": 0,
            "average_improvement": 0.0,
            "last_optimization_time": 0.0
        }
    
    async def start(self):
        """Start real-time optimizer"""
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        self._tuning_task = asyncio.create_task(self._tuning_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("RealTimeOptimizer started")
    
    async def stop(self):
        """Stop real-time optimizer"""
        if self._optimization_task:
            self._optimization_task.cancel()
        if self._tuning_task:
            self._tuning_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("RealTimeOptimizer stopped")
    
    def add_optimization_target(self, target: OptimizationTarget):
        """Add optimization target"""
        self._optimization_targets[target.name] = target
        logger.info(f"Added optimization target: {target.name}")
    
    def add_tuning_parameter(self, parameter: TuningParameter):
        """Add self-tuning parameter"""
        self._tuning_parameters[parameter.name] = parameter
        logger.info(f"Added tuning parameter: {parameter.name}")
    
    def add_performance_feedback(self, feedback: PerformanceFeedback):
        """Add performance feedback"""
        self._performance_feedback[feedback.metric_name].append(feedback)
        
        # Update performance trends
        self._performance_trends[feedback.metric_name].append(feedback.value)
        
        # Keep only recent trends
        if len(self._performance_trends[feedback.metric_name]) > 50:
            self._performance_trends[feedback.metric_name] = \
                self._performance_trends[feedback.metric_name][-50:]
    
    async def optimize_now(self) -> List[OptimizationAction]:
        """Perform immediate optimization"""
        actions = []
        
        # Analyze current performance
        performance_analysis = await self._analyze_current_performance()
        
        # Generate optimization actions
        optimization_actions = await self._generate_optimization_actions(performance_analysis)
        
        # Execute optimization actions
        for action in optimization_actions:
            try:
                executed_action = await self._execute_optimization_action(action)
                actions.append(executed_action)
                
                # Record in history
                self._optimization_history.append(executed_action)
                
            except Exception as e:
                logger.error(f"Optimization action failed: {e}")
                failed_action = OptimizationAction(
                    parameter_name=action["parameter_name"],
                    old_value=action["old_value"],
                    new_value=action["new_value"],
                    expected_improvement=action["expected_improvement"],
                    confidence=action["confidence"],
                    execution_time_ms=0.0,
                    success=False,
                    error_message=str(e)
                )
                actions.append(failed_action)
        
        # Update statistics
        self._update_optimization_stats(actions)
        
        return actions
    
    async def _analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current performance state"""
        analysis = {}
        
        # Analyze each optimization target
        for target_name, target in self._optimization_targets.items():
            current_performance = await self._get_current_performance(target_name)
            
            analysis[target_name] = {
                "current_value": current_performance,
                "target_value": target.target_value,
                "deviation": abs(current_performance - target.target_value) / target.target_value,
                "weight": target.weight,
                "priority": target.priority,
                "trend": self._calculate_performance_trend(target_name),
                "improvement_potential": self._calculate_improvement_potential(target_name, current_performance)
            }
        
        return analysis
    
    async def _get_current_performance(self, metric_name: str) -> float:
        """Get current performance value for metric"""
        if metric_name in self._performance_feedback and self._performance_feedback[metric_name]:
            # Use most recent feedback
            recent_feedback = list(self._performance_feedback[metric_name])[-1]
            return recent_feedback.value
        
        # Fallback to baseline or default
        return self._performance_baselines.get(metric_name, 0.0)
    
    def _calculate_performance_trend(self, metric_name: str) -> float:
        """Calculate performance trend"""
        if metric_name not in self._performance_trends:
            return 0.0
        
        trends = self._performance_trends[metric_name]
        if len(trends) < 2:
            return 0.0
        
        # Simple linear trend calculation
        return (trends[-1] - trends[0]) / len(trends)
    
    def _calculate_improvement_potential(self, metric_name: str, current_value: float) -> float:
        """Calculate improvement potential"""
        if metric_name not in self._optimization_targets:
            return 0.0
        
        target = self._optimization_targets[metric_name]
        deviation = abs(current_value - target.target_value) / target.target_value
        
        return min(1.0, deviation / target.tolerance)
    
    async def _generate_optimization_actions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization actions based on analysis"""
        actions = []
        
        # Sort targets by priority and improvement potential
        sorted_targets = sorted(
            analysis.items(),
            key=lambda x: (x[1]["priority"], x[1]["improvement_potential"]),
            reverse=True
        )
        
        for target_name, target_analysis in sorted_targets:
            if target_analysis["improvement_potential"] > 0.1:  # Significant improvement needed
                target_actions = await self._generate_target_optimizations(target_name, target_analysis)
                actions.extend(target_actions)
        
        return actions
    
    async def _generate_target_optimizations(self, target_name: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimizations for a specific target"""
        actions = []
        
        # Find parameters that can influence this target
        relevant_parameters = self._find_relevant_parameters(target_name)
        
        for param_name in relevant_parameters:
            if param_name not in self._tuning_parameters:
                continue
            
            parameter = self._tuning_parameters[param_name]
            
            # Calculate optimal adjustment
            adjustment = await self._calculate_parameter_adjustment(
                target_name, analysis, param_name, parameter
            )
            
            if abs(adjustment) > parameter.step_size * 0.1:  # Significant adjustment
                actions.append({
                    "parameter_name": param_name,
                    "old_value": parameter.current_value,
                    "new_value": max(
                        parameter.min_value,
                        min(parameter.max_value, parameter.current_value + adjustment)
                    ),
                    "expected_improvement": abs(adjustment) * parameter.impact_factor,
                    "confidence": self._calculate_adjustment_confidence(target_name, param_name),
                    "target": target_name
                })
        
        return actions
    
    def _find_relevant_parameters(self, target_name: str) -> List[str]:
        """Find parameters relevant to optimization target"""
        # This would be more sophisticated in a real implementation
        # For now, we'll use simple heuristics
        
        relevant_params = []
        
        if "response_time" in target_name.lower():
            relevant_params.extend(["max_workers", "connection_pool_size", "cache_size"])
        elif "throughput" in target_name.lower():
            relevant_params.extend(["batch_size", "cache_ttl", "max_connections"])
        elif "memory" in target_name.lower():
            relevant_params.extend(["cache_size", "max_memory", "gc_threshold"])
        elif "cpu" in target_name.lower():
            relevant_params.extend(["max_workers", "thread_pool_size", "timeout"])
        
        # Return only parameters that exist
        return [p for p in relevant_params if p in self._tuning_parameters]
    
    async def _calculate_parameter_adjustment(
        self,
        target_name: str,
        analysis: Dict[str, Any],
        param_name: str,
        parameter: TuningParameter
    ) -> float:
        """Calculate optimal parameter adjustment"""
        current_deviation = analysis["deviation"]
        improvement_potential = analysis["improvement_potential"]
        
        # Base adjustment based on deviation
        base_adjustment = current_deviation * parameter.step_size
        
        # Apply optimization mode multiplier
        mode_multiplier = self._get_optimization_mode_multiplier()
        
        # Apply confidence factor
        confidence = self._calculate_adjustment_confidence(target_name, param_name)
        confidence_factor = 0.5 + confidence * 0.5  # 0.5 to 1.0
        
        # Calculate final adjustment
        adjustment = base_adjustment * mode_multiplier * confidence_factor
        
        # Ensure adjustment is within parameter bounds
        max_adjustment = parameter.max_value - parameter.current_value
        min_adjustment = parameter.min_value - parameter.current_value
        
        return max(min_adjustment, min(max_adjustment, adjustment))
    
    def _get_optimization_mode_multiplier(self) -> float:
        """Get optimization mode multiplier"""
        if self._optimization_mode == OptimizationMode.AGGRESSIVE:
            return 2.0
        elif self._optimization_mode == OptimizationMode.BALANCED:
            return 1.0
        elif self._optimization_mode == OptimizationMode.CONSERVATIVE:
            return 0.5
        else:  # ADAPTIVE
            return 1.0  # Will be adjusted dynamically
    
    def _calculate_adjustment_confidence(self, target_name: str, param_name: str) -> float:
        """Calculate confidence in parameter adjustment"""
        # Base confidence on historical success
        success_count = 0
        total_count = 0
        
        for action in self._optimization_history:
            if action.parameter_name == param_name:
                total_count += 1
                if action.success and action.expected_improvement > 0:
                    success_count += 1
        
        if total_count == 0:
            return 0.5  # Default confidence
        
        success_rate = success_count / total_count
        
        # Adjust based on recent performance
        if target_name in self._performance_trends:
            trends = self._performance_trends[target_name]
            if len(trends) >= 5:
                recent_trend = statistics.mean(trends[-5:]) - statistics.mean(trends[-10:-5])
                trend_factor = 1.0 + recent_trend * 0.1  # Adjust by trend
                success_rate *= trend_factor
        
        return max(0.1, min(0.9, success_rate))
    
    async def _execute_optimization_action(self, action: Dict[str, Any]) -> OptimizationAction:
        """Execute optimization action"""
        start_time = time.time()
        
        param_name = action["parameter_name"]
        old_value = action["old_value"]
        new_value = action["new_value"]
        
        try:
            # Apply parameter change
            await self._apply_parameter_change(param_name, old_value, new_value)
            
            # Update parameter in tuning parameters
            if param_name in self._tuning_parameters:
                self._tuning_parameters[param_name].current_value = new_value
                self._tuning_parameters[param_name].adjustment_history.append({
                    "old_value": old_value,
                    "new_value": new_value,
                    "timestamp": time.time(),
                    "expected_improvement": action["expected_improvement"]
                })
            
            execution_time = (time.time() - start_time) * 1000
            
            return OptimizationAction(
                parameter_name=param_name,
                old_value=old_value,
                new_value=new_value,
                expected_improvement=action["expected_improvement"],
                confidence=action["confidence"],
                execution_time_ms=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            return OptimizationAction(
                parameter_name=param_name,
                old_value=old_value,
                new_value=new_value,
                expected_improvement=action["expected_improvement"],
                confidence=action["confidence"],
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )
    
    async def _apply_parameter_change(self, param_name: str, old_value: float, new_value: float):
        """Apply parameter change to system"""
        # This would integrate with the actual system configuration
        # For now, we'll simulate the change
        
        logger.info(f"Applying parameter change: {param_name} = {old_value} -> {new_value}")
        
        # Simulate parameter change delay
        await asyncio.sleep(0.1)
        
        # In a real implementation, this would:
        # 1. Update configuration files
        # 2. Restart services if needed
        # 3. Update runtime parameters
        # 4. Validate the change
    
    def _update_optimization_stats(self, actions: List[OptimizationAction]):
        """Update optimization statistics"""
        self._optimization_stats["total_optimizations"] += len(actions)
        
        successful = sum(1 for action in actions if action.success)
        failed = len(actions) - successful
        
        self._optimization_stats["successful_optimizations"] += successful
        self._optimization_stats["failed_optimizations"] += failed
        
        if successful > 0:
            avg_improvement = statistics.mean([
                action.expected_improvement for action in actions if action.success
            ])
            self._optimization_stats["average_improvement"] = avg_improvement
        
        self._optimization_stats["last_optimization_time"] = time.time()
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(self.optimization_interval)
                
                # Perform optimization
                actions = await self.optimize_now()
                
                if actions:
                    logger.info(f"Real-time optimization completed: {len(actions)} actions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
    
    async def _tuning_loop(self):
        """Background self-tuning loop"""
        while True:
            try:
                await asyncio.sleep(self.tuning_interval)
                
                # Perform self-tuning
                await self._perform_self_tuning()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tuning loop error: {e}")
    
    async def _perform_self_tuning(self):
        """Perform self-tuning of parameters"""
        # Analyze parameter effectiveness
        parameter_effectiveness = await self._analyze_parameter_effectiveness()
        
        # Adjust tuning strategy if needed
        await self._adjust_tuning_strategy(parameter_effectiveness)
        
        # Update parameter step sizes based on effectiveness
        await self._update_parameter_step_sizes(parameter_effectiveness)
    
    async def _analyze_parameter_effectiveness(self) -> Dict[str, float]:
        """Analyze effectiveness of tuning parameters"""
        effectiveness = {}
        
        for param_name, parameter in self._tuning_parameters.items():
            if not parameter.adjustment_history:
                effectiveness[param_name] = 0.5  # Default effectiveness
                continue
            
            # Calculate effectiveness based on recent adjustments
            recent_adjustments = list(parameter.adjustment_history)[-10:]
            
            improvements = []
            for adjustment in recent_adjustments:
                if adjustment.get("expected_improvement", 0) > 0:
                    improvements.append(adjustment["expected_improvement"])
            
            if improvements:
                effectiveness[param_name] = statistics.mean(improvements)
            else:
                effectiveness[param_name] = 0.5
        
        return effectiveness
    
    async def _adjust_tuning_strategy(self, effectiveness: Dict[str, float]):
        """Adjust tuning strategy based on effectiveness"""
        avg_effectiveness = statistics.mean(effectiveness.values()) if effectiveness else 0.5
        
        if avg_effectiveness > 0.7:
            # High effectiveness - can be more aggressive
            if self._optimization_mode == OptimizationMode.CONSERVATIVE:
                self._optimization_mode = OptimizationMode.BALANCED
                logger.info("Switched to balanced optimization mode")
        elif avg_effectiveness < 0.3:
            # Low effectiveness - be more conservative
            if self._optimization_mode == OptimizationMode.AGGRESSIVE:
                self._optimization_mode = OptimizationMode.BALANCED
                logger.info("Switched to balanced optimization mode")
    
    async def _update_parameter_step_sizes(self, effectiveness: Dict[str, float]):
        """Update parameter step sizes based on effectiveness"""
        for param_name, eff in effectiveness.items():
            if param_name in self._tuning_parameters:
                parameter = self._tuning_parameters[param_name]
                
                # Adjust step size based on effectiveness
                if eff > 0.7:
                    # High effectiveness - can use larger steps
                    parameter.step_size = min(parameter.step_size * 1.1, parameter.max_value * 0.1)
                elif eff < 0.3:
                    # Low effectiveness - use smaller steps
                    parameter.step_size = max(parameter.step_size * 0.9, parameter.max_value * 0.01)
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(5.0)  # Monitor every 5 seconds
                
                # Update performance baselines
                await self._update_performance_baselines()
                
                # Check for performance anomalies
                await self._check_performance_anomalies()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
    
    async def _update_performance_baselines(self):
        """Update performance baselines"""
        for metric_name, feedback_queue in self._performance_feedback.items():
            if feedback_queue:
                recent_values = [f.value for f in list(feedback_queue)[-10:]]
                if recent_values:
                    baseline = statistics.mean(recent_values)
                    self._performance_baselines[metric_name] = baseline
    
    async def _check_performance_anomalies(self):
        """Check for performance anomalies"""
        for metric_name, feedback_queue in self._performance_feedback.items():
            if len(feedback_queue) >= 5:
                recent_values = [f.value for f in list(feedback_queue)[-5:]]
                baseline = self._performance_baselines.get(metric_name, 0.0)
                
                if baseline > 0:
                    # Check for significant deviation
                    for value in recent_values:
                        deviation = abs(value - baseline) / baseline
                        if deviation > 0.5:  # 50% deviation
                            logger.warning(f"Performance anomaly detected in {metric_name}: {value} (baseline: {baseline})")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            "optimization_mode": self._optimization_mode.value,
            "tuning_strategy": self._tuning_strategy.value,
            "control_loop_type": self._control_loop_type.value,
            "optimization_targets": len(self._optimization_targets),
            "tuning_parameters": len(self._tuning_parameters),
            "performance_metrics_tracked": len(self._performance_feedback),
            "optimization_stats": self._optimization_stats,
            "recent_actions": [
                {
                    "parameter": action.parameter_name,
                    "old_value": action.old_value,
                    "new_value": action.new_value,
                    "success": action.success,
                    "timestamp": action.timestamp
                }
                for action in list(self._optimization_history)[-5:]
            ]
        }


# Global real-time optimizer
_real_time_optimizer: Optional[RealTimeOptimizer] = None


async def get_real_time_optimizer() -> RealTimeOptimizer:
    """Get the global real-time optimizer"""
    global _real_time_optimizer
    if _real_time_optimizer is None:
        _real_time_optimizer = RealTimeOptimizer()
        await _real_time_optimizer.start()
    return _real_time_optimizer


def add_optimization_target(target: OptimizationTarget):
    """Add optimization target"""
    if _real_time_optimizer:
        _real_time_optimizer.add_optimization_target(target)


def add_tuning_parameter(parameter: TuningParameter):
    """Add tuning parameter"""
    if _real_time_optimizer:
        _real_time_optimizer.add_tuning_parameter(parameter)


def add_performance_feedback(feedback: PerformanceFeedback):
    """Add performance feedback"""
    if _real_time_optimizer:
        _real_time_optimizer.add_performance_feedback(feedback)


async def optimize_now() -> List[OptimizationAction]:
    """Perform immediate optimization"""
    optimizer = await get_real_time_optimizer()
    return await optimizer.optimize_now()


async def get_optimization_status() -> Dict[str, Any]:
    """Get optimization status"""
    optimizer = await get_real_time_optimizer()
    return optimizer.get_optimization_status()
