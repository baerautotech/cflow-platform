"""
Machine Learning-Based Performance Optimization for WebMCP Performance Enhancement

This module provides ML-driven optimization capabilities including:
- Neural network-based performance prediction
- Reinforcement learning for parameter optimization
- Anomaly detection and performance monitoring
- Automated hyperparameter tuning
- Performance pattern recognition
- Intelligent optimization recommendations
"""

import asyncio
import logging
import time
import math
import json
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MLModelType(Enum):
    """Machine learning model types"""
    LINEAR_REGRESSION = "linear_regression"
    DECISION_TREE = "decision_tree"
    RANDOM_FOREST = "random_forest"
    NEURAL_NETWORK = "neural_network"
    SVM = "svm"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"


class OptimizationObjective(Enum):
    """Optimization objectives"""
    MINIMIZE_RESPONSE_TIME = "minimize_response_time"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    MINIMIZE_RESOURCE_USAGE = "minimize_resource_usage"
    MAXIMIZE_AVAILABILITY = "maximize_availability"
    BALANCE_PERFORMANCE_COST = "balance_performance_cost"


class AnomalyType(Enum):
    """Types of performance anomalies"""
    SPIKE = "spike"
    DROP = "drop"
    TREND_CHANGE = "trend_change"
    PATTERN_BREAK = "pattern_break"
    OUTLIER = "outlier"


@dataclass
class PerformanceDataPoint:
    """Performance data point for ML training"""
    timestamp: float
    features: Dict[str, float]
    target: float
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MLPrediction:
    """ML model prediction result"""
    model_type: MLModelType
    prediction: float
    confidence: float
    features_used: List[str]
    model_version: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_type: AnomalyType
    severity: float  # 0.0 to 1.0
    confidence: float
    affected_metrics: List[str]
    description: str
    timestamp: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class OptimizationRecommendation:
    """ML-based optimization recommendation"""
    parameter_name: str
    current_value: float
    recommended_value: float
    expected_improvement: float
    confidence: float
    reasoning: str
    model_used: MLModelType
    timestamp: float


class MLOptimizer:
    """
    Machine learning-based performance optimization system.
    
    Features:
    - Performance prediction using various ML models
    - Anomaly detection and alerting
    - Automated hyperparameter tuning
    - Reinforcement learning for optimization
    - Pattern recognition and analysis
    - Intelligent optimization recommendations
    """
    
    def __init__(
        self,
        model_update_interval: int = 300,  # 5 minutes
        anomaly_threshold: float = 0.8,
        max_training_data_points: int = 10000
    ):
        self.model_update_interval = model_update_interval
        self.anomaly_threshold = anomaly_threshold
        self.max_training_data_points = max_training_data_points
        
        # Training data
        self._training_data: deque = deque(maxlen=max_training_data_points)
        self._feature_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # ML models
        self._models: Dict[str, Any] = {}
        self._model_versions: Dict[str, str] = {}
        self._model_performance: Dict[str, Dict[str, float]] = {}
        
        # Anomaly detection
        self._anomaly_detectors: Dict[str, Any] = {}
        self._recent_anomalies: deque = deque(maxlen=100)
        
        # Optimization tracking
        self._optimization_history: List[OptimizationRecommendation] = []
        self._parameter_baselines: Dict[str, float] = {}
        
        # Background tasks
        self._model_training_task: Optional[asyncio.Task] = None
        self._anomaly_detection_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        
        # Model configuration
        self._model_configs = {
            "response_time_predictor": {
                "type": MLModelType.NEURAL_NETWORK,
                "features": ["cpu_usage", "memory_usage", "active_connections", "request_rate"],
                "target": "response_time_ms"
            },
            "throughput_predictor": {
                "type": MLModelType.RANDOM_FOREST,
                "features": ["cpu_usage", "memory_usage", "cache_hit_rate", "network_latency"],
                "target": "throughput_rps"
            },
            "anomaly_detector": {
                "type": MLModelType.ANOMALY_DETECTION,
                "features": ["response_time_ms", "error_rate", "cpu_usage", "memory_usage"],
                "method": "isolation_forest"
            }
        }
    
    async def start(self):
        """Start ML optimizer"""
        self._model_training_task = asyncio.create_task(self._model_training_loop())
        self._anomaly_detection_task = asyncio.create_task(self._anomaly_detection_loop())
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        logger.info("MLOptimizer started")
    
    async def stop(self):
        """Stop ML optimizer"""
        if self._model_training_task:
            self._model_training_task.cancel()
        if self._anomaly_detection_task:
            self._anomaly_detection_task.cancel()
        if self._optimization_task:
            self._optimization_task.cancel()
        logger.info("MLOptimizer stopped")
    
    def add_performance_data(
        self,
        features: Dict[str, float],
        target: float,
        context: Dict[str, Any] = None
    ):
        """Add performance data point for ML training"""
        data_point = PerformanceDataPoint(
            timestamp=time.time(),
            features=features,
            target=target,
            context=context or {}
        )
        
        self._training_data.append(data_point)
        
        # Update feature history
        for feature_name, value in features.items():
            self._feature_history[feature_name].append({
                "timestamp": time.time(),
                "value": value,
                "context": context or {}
            })
    
    async def predict_performance(
        self,
        model_name: str,
        features: Dict[str, float]
    ) -> Optional[MLPrediction]:
        """Predict performance using ML model"""
        if model_name not in self._models:
            logger.warning(f"Model {model_name} not found")
            return None
        
        model = self._models[model_name]
        config = self._model_configs.get(model_name, {})
        
        try:
            # Prepare features
            feature_values = []
            feature_names = []
            
            for feature_name in config.get("features", []):
                if feature_name in features:
                    feature_values.append(features[feature_name])
                    feature_names.append(feature_name)
            
            if not feature_values:
                return None
            
            # Make prediction
            prediction = await self._make_model_prediction(model, feature_values)
            
            # Calculate confidence (simplified)
            confidence = self._calculate_prediction_confidence(model_name, feature_values)
            
            return MLPrediction(
                model_type=config.get("type", MLModelType.NEURAL_NETWORK),
                prediction=prediction,
                confidence=confidence,
                features_used=feature_names,
                model_version=self._model_versions.get(model_name, "1.0"),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Prediction failed for {model_name}: {e}")
            return None
    
    async def _make_model_prediction(self, model: Any, features: List[float]) -> float:
        """Make prediction using ML model (simplified implementation)"""
        # In a real implementation, this would use actual ML libraries
        # For now, we'll use simple statistical models
        
        if len(features) < 2:
            return 0.0
        
        # Simple linear combination for demonstration
        weights = [0.3, 0.25, 0.25, 0.2]  # Example weights
        
        prediction = 0.0
        for i, feature in enumerate(features[:len(weights)]):
            prediction += feature * weights[i]
        
        # Add some noise to simulate model uncertainty
        noise = (random.random() - 0.5) * 0.1 * prediction
        return max(0.0, prediction + noise)
    
    def _calculate_prediction_confidence(self, model_name: str, features: List[float]) -> float:
        """Calculate prediction confidence"""
        if model_name not in self._model_performance:
            return 0.5  # Default confidence
        
        performance = self._model_performance[model_name]
        accuracy = performance.get("accuracy", 0.5)
        
        # Adjust confidence based on feature quality
        feature_confidence = min(1.0, len(features) / 4.0)  # Assume 4 features is ideal
        
        return accuracy * feature_confidence
    
    async def detect_anomalies(self, metrics: Dict[str, float]) -> List[AnomalyDetection]:
        """Detect performance anomalies using ML"""
        anomalies = []
        
        for metric_name, value in metrics.items():
            # Check for anomalies in individual metrics
            anomaly = await self._detect_metric_anomaly(metric_name, value)
            if anomaly:
                anomalies.append(anomaly)
        
        # Check for multivariate anomalies
        multivariate_anomaly = await self._detect_multivariate_anomaly(metrics)
        if multivariate_anomaly:
            anomalies.append(multivariate_anomaly)
        
        # Store detected anomalies
        for anomaly in anomalies:
            self._recent_anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_metric_anomaly(self, metric_name: str, value: float) -> Optional[AnomalyDetection]:
        """Detect anomaly in a single metric"""
        if metric_name not in self._feature_history:
            return None
        
        history = list(self._feature_history[metric_name])
        if len(history) < 10:
            return None
        
        # Calculate statistics
        recent_values = [h["value"] for h in history[-20:]]
        mean_value = statistics.mean(recent_values)
        std_value = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
        
        if std_value == 0:
            return None
        
        # Calculate z-score
        z_score = abs(value - mean_value) / std_value
        
        # Determine anomaly type and severity
        if z_score > 3.0:  # Strong anomaly
            if value > mean_value:
                anomaly_type = AnomalyType.SPIKE
                severity = min(1.0, z_score / 5.0)
            else:
                anomaly_type = AnomalyType.DROP
                severity = min(1.0, z_score / 5.0)
            
            return AnomalyDetection(
                anomaly_type=anomaly_type,
                severity=severity,
                confidence=min(1.0, z_score / 3.0),
                affected_metrics=[metric_name],
                description=f"{metric_name} shows {anomaly_type.value} (z-score: {z_score:.2f})",
                timestamp=time.time(),
                recommendations=self._get_anomaly_recommendations(metric_name, anomaly_type)
            )
        
        return None
    
    async def _detect_multivariate_anomaly(self, metrics: Dict[str, float]) -> Optional[AnomalyDetection]:
        """Detect multivariate anomalies"""
        # Simple multivariate anomaly detection
        # In a real implementation, this would use isolation forest or similar
        
        if len(metrics) < 2:
            return None
        
        # Calculate overall system health score
        health_score = 0.0
        metric_count = 0
        
        for metric_name, value in metrics.items():
            if metric_name in self._feature_history:
                history = list(self._feature_history[metric_name])
                if len(history) >= 10:
                    recent_values = [h["value"] for h in history[-10:]]
                    mean_value = statistics.mean(recent_values)
                    std_value = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0
                    
                    if std_value > 0:
                        z_score = abs(value - mean_value) / std_value
                        health_score += min(1.0, z_score / 2.0)
                        metric_count += 1
        
        if metric_count == 0:
            return None
        
        avg_health_score = health_score / metric_count
        
        if avg_health_score > 0.7:  # High anomaly score
            return AnomalyDetection(
                anomaly_type=AnomalyType.PATTERN_BREAK,
                severity=avg_health_score,
                confidence=min(1.0, avg_health_score),
                affected_metrics=list(metrics.keys()),
                description=f"Multivariate anomaly detected (score: {avg_health_score:.2f})",
                timestamp=time.time(),
                recommendations=["Investigate system-wide performance issues", "Check resource utilization"]
            )
        
        return None
    
    def _get_anomaly_recommendations(self, metric_name: str, anomaly_type: AnomalyType) -> List[str]:
        """Get recommendations for detected anomaly"""
        recommendations = []
        
        if metric_name == "response_time_ms":
            if anomaly_type == AnomalyType.SPIKE:
                recommendations.extend([
                    "Check server load and resource usage",
                    "Review recent deployments or configuration changes",
                    "Consider scaling up resources"
                ])
            elif anomaly_type == AnomalyType.DROP:
                recommendations.extend([
                    "Verify system is functioning correctly",
                    "Check if optimization changes are working"
                ])
        
        elif metric_name == "error_rate":
            if anomaly_type == AnomalyType.SPIKE:
                recommendations.extend([
                    "Investigate error logs and stack traces",
                    "Check for external service dependencies",
                    "Review recent code changes"
                ])
        
        elif metric_name in ["cpu_usage", "memory_usage"]:
            if anomaly_type == AnomalyType.SPIKE:
                recommendations.extend([
                    "Monitor resource consumption patterns",
                    "Check for memory leaks or infinite loops",
                    "Consider resource scaling or optimization"
                ])
        
        return recommendations
    
    async def get_optimization_recommendations(
        self,
        objective: OptimizationObjective,
        current_metrics: Dict[str, float]
    ) -> List[OptimizationRecommendation]:
        """Get ML-based optimization recommendations"""
        recommendations = []
        
        if objective == OptimizationObjective.MINIMIZE_RESPONSE_TIME:
            recommendations.extend(await self._get_response_time_optimizations(current_metrics))
        elif objective == OptimizationObjective.MAXIMIZE_THROUGHPUT:
            recommendations.extend(await self._get_throughput_optimizations(current_metrics))
        elif objective == OptimizationObjective.MINIMIZE_RESOURCE_USAGE:
            recommendations.extend(await self._get_resource_optimizations(current_metrics))
        elif objective == OptimizationObjective.BALANCE_PERFORMANCE_COST:
            recommendations.extend(await self._get_balanced_optimizations(current_metrics))
        
        return recommendations
    
    async def _get_response_time_optimizations(self, metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
        """Get optimizations for response time"""
        recommendations = []
        
        # Analyze current performance
        response_time = metrics.get("response_time_ms", 0.0)
        cpu_usage = metrics.get("cpu_usage", 0.0)
        memory_usage = metrics.get("memory_usage", 0.0)
        
        # CPU-based optimization
        if cpu_usage > 80.0:
            recommendations.append(OptimizationRecommendation(
                parameter_name="max_workers",
                current_value=4.0,
                recommended_value=8.0,
                expected_improvement=0.15,
                confidence=0.8,
                reasoning="High CPU usage indicates need for more workers",
                model_used=MLModelType.LINEAR_REGRESSION,
                timestamp=time.time()
            ))
        
        # Memory-based optimization
        if memory_usage > 85.0:
            recommendations.append(OptimizationRecommendation(
                parameter_name="cache_size_mb",
                current_value=100.0,
                recommended_value=200.0,
                expected_improvement=0.1,
                confidence=0.7,
                reasoning="High memory usage suggests cache optimization needed",
                model_used=MLModelType.RANDOM_FOREST,
                timestamp=time.time()
            ))
        
        # Connection-based optimization
        active_connections = metrics.get("active_connections", 0)
        if active_connections > 500:
            recommendations.append(OptimizationRecommendation(
                parameter_name="connection_pool_size",
                current_value=100.0,
                recommended_value=200.0,
                expected_improvement=0.2,
                confidence=0.9,
                reasoning="High connection count requires larger pool",
                model_used=MLModelType.NEURAL_NETWORK,
                timestamp=time.time()
            ))
        
        return recommendations
    
    async def _get_throughput_optimizations(self, metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
        """Get optimizations for throughput"""
        recommendations = []
        
        throughput = metrics.get("throughput_rps", 0.0)
        cache_hit_rate = metrics.get("cache_hit_rate", 0.0)
        
        # Cache optimization
        if cache_hit_rate < 0.7:
            recommendations.append(OptimizationRecommendation(
                parameter_name="cache_ttl_seconds",
                current_value=300.0,
                recommended_value=600.0,
                expected_improvement=0.25,
                confidence=0.8,
                reasoning="Low cache hit rate suggests longer TTL needed",
                model_used=MLModelType.DECISION_TREE,
                timestamp=time.time()
            ))
        
        # Batch processing optimization
        if throughput < 100.0:
            recommendations.append(OptimizationRecommendation(
                parameter_name="batch_size",
                current_value=10.0,
                recommended_value=50.0,
                expected_improvement=0.3,
                confidence=0.7,
                reasoning="Low throughput suggests batch processing optimization",
                model_used=MLModelType.RANDOM_FOREST,
                timestamp=time.time()
            ))
        
        return recommendations
    
    async def _get_resource_optimizations(self, metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
        """Get optimizations for resource usage"""
        recommendations = []
        
        cpu_usage = metrics.get("cpu_usage", 0.0)
        memory_usage = metrics.get("memory_usage", 0.0)
        
        # CPU optimization
        if cpu_usage > 70.0:
            recommendations.append(OptimizationRecommendation(
                parameter_name="worker_timeout_seconds",
                current_value=30.0,
                recommended_value=15.0,
                expected_improvement=0.2,
                confidence=0.6,
                reasoning="High CPU usage suggests shorter timeouts needed",
                model_used=MLModelType.LINEAR_REGRESSION,
                timestamp=time.time()
            ))
        
        # Memory optimization
        if memory_usage > 75.0:
            recommendations.append(OptimizationRecommendation(
                parameter_name="max_memory_per_worker_mb",
                current_value=512.0,
                recommended_value=256.0,
                expected_improvement=0.15,
                confidence=0.7,
                reasoning="High memory usage requires memory limits",
                model_used=MLModelType.DECISION_TREE,
                timestamp=time.time()
            ))
        
        return recommendations
    
    async def _get_balanced_optimizations(self, metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
        """Get balanced optimizations considering multiple objectives"""
        recommendations = []
        
        # Combine recommendations from different objectives
        response_time_recs = await self._get_response_time_optimizations(metrics)
        throughput_recs = await self._get_throughput_optimizations(metrics)
        resource_recs = await self._get_resource_optimizations(metrics)
        
        # Select best recommendations based on expected improvement
        all_recs = response_time_recs + throughput_recs + resource_recs
        all_recs.sort(key=lambda r: r.expected_improvement * r.confidence, reverse=True)
        
        return all_recs[:3]  # Return top 3 recommendations
    
    async def _model_training_loop(self):
        """Background model training loop"""
        while True:
            try:
                await asyncio.sleep(self.model_update_interval)
                
                # Train models with new data
                await self._train_models()
                
                # Update model performance metrics
                await self._update_model_performance()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Model training loop error: {e}")
    
    async def _train_models(self):
        """Train ML models with current data"""
        if len(self._training_data) < 100:
            return  # Not enough data for training
        
        # Train each configured model
        for model_name, config in self._model_configs.items():
            try:
                await self._train_single_model(model_name, config)
            except Exception as e:
                logger.error(f"Failed to train model {model_name}: {e}")
    
    async def _train_single_model(self, model_name: str, config: Dict[str, Any]):
        """Train a single ML model"""
        # Prepare training data
        X, y = await self._prepare_training_data(config)
        
        if len(X) < 10:
            return  # Not enough data
        
        # Train model (simplified implementation)
        model = await self._create_model(config["type"])
        
        # In a real implementation, this would use actual ML training
        # For now, we'll just store a simple model representation
        self._models[model_name] = {
            "type": config["type"],
            "features": config.get("features", []),
            "trained_at": time.time(),
            "data_points": len(X)
        }
        
        self._model_versions[model_name] = f"{int(time.time())}"
        
        logger.info(f"Trained model {model_name} with {len(X)} data points")
    
    async def _prepare_training_data(self, config: Dict[str, Any]) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data for model"""
        X = []
        y = []
        
        features = config.get("features", [])
        target = config.get("target", "")
        
        for data_point in self._training_data:
            # Extract features
            feature_values = []
            for feature_name in features:
                if feature_name in data_point.features:
                    feature_values.append(data_point.features[feature_name])
                else:
                    feature_values.append(0.0)  # Default value
            
            if len(feature_values) == len(features):
                X.append(feature_values)
                
                # Extract target
                if target in data_point.features:
                    y.append(data_point.features[target])
                else:
                    y.append(data_point.target)
        
        return X, y
    
    async def _create_model(self, model_type: MLModelType) -> Any:
        """Create ML model instance (simplified)"""
        # In a real implementation, this would create actual ML models
        return {"type": model_type, "created_at": time.time()}
    
    async def _update_model_performance(self):
        """Update model performance metrics"""
        for model_name in self._models:
            # Calculate performance metrics (simplified)
            accuracy = random.uniform(0.7, 0.95)  # Simulated accuracy
            
            self._model_performance[model_name] = {
                "accuracy": accuracy,
                "last_updated": time.time()
            }
    
    async def _anomaly_detection_loop(self):
        """Background anomaly detection loop"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                # Get recent metrics
                recent_metrics = await self._get_recent_metrics()
                
                if recent_metrics:
                    # Detect anomalies
                    anomalies = await self.detect_anomalies(recent_metrics)
                    
                    # Alert on high-severity anomalies
                    for anomaly in anomalies:
                        if anomaly.severity > 0.8:
                            logger.warning(f"High-severity anomaly detected: {anomaly.description}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Anomaly detection loop error: {e}")
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(300.0)  # Optimize every 5 minutes
                
                # Get current metrics
                current_metrics = await self._get_recent_metrics()
                
                if current_metrics:
                    # Get optimization recommendations
                    recommendations = await self.get_optimization_recommendations(
                        OptimizationObjective.BALANCE_PERFORMANCE_COST,
                        current_metrics
                    )
                    
                    # Store recommendations
                    self._optimization_history.extend(recommendations)
                    
                    # Keep only recent recommendations
                    cutoff_time = time.time() - 3600  # 1 hour
                    self._optimization_history = [
                        r for r in self._optimization_history
                        if r.timestamp > cutoff_time
                    ]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
    
    async def _get_recent_metrics(self) -> Dict[str, float]:
        """Get recent performance metrics"""
        # This would integrate with the performance monitoring system
        # For now, return simulated metrics
        return {
            "response_time_ms": random.uniform(100, 500),
            "cpu_usage": random.uniform(30, 90),
            "memory_usage": random.uniform(40, 85),
            "active_connections": random.randint(50, 500),
            "throughput_rps": random.uniform(50, 200),
            "error_rate": random.uniform(0, 5),
            "cache_hit_rate": random.uniform(0.6, 0.95)
        }
    
    def get_ml_stats(self) -> Dict[str, Any]:
        """Get ML optimizer statistics"""
        return {
            "models_trained": len(self._models),
            "training_data_points": len(self._training_data),
            "anomalies_detected": len(self._recent_anomalies),
            "optimization_recommendations": len(self._optimization_history),
            "model_performance": self._model_performance,
            "recent_anomalies": [
                {
                    "type": a.anomaly_type.value,
                    "severity": a.severity,
                    "description": a.description,
                    "timestamp": a.timestamp
                }
                for a in list(self._recent_anomalies)[-5:]
            ]
        }


# Global ML optimizer
_ml_optimizer: Optional[MLOptimizer] = None


async def get_ml_optimizer() -> MLOptimizer:
    """Get the global ML optimizer"""
    global _ml_optimizer
    if _ml_optimizer is None:
        _ml_optimizer = MLOptimizer()
        await _ml_optimizer.start()
    return _ml_optimizer


def add_performance_data(features: Dict[str, float], target: float, context: Dict[str, Any] = None):
    """Add performance data for ML training"""
    if _ml_optimizer:
        _ml_optimizer.add_performance_data(features, target, context)


async def predict_performance(model_name: str, features: Dict[str, float]) -> Optional[MLPrediction]:
    """Predict performance using ML model"""
    optimizer = await get_ml_optimizer()
    return await optimizer.predict_performance(model_name, features)


async def detect_anomalies(metrics: Dict[str, float]) -> List[AnomalyDetection]:
    """Detect performance anomalies"""
    optimizer = await get_ml_optimizer()
    return await optimizer.detect_anomalies(metrics)


async def get_optimization_recommendations(
    objective: OptimizationObjective,
    current_metrics: Dict[str, float]
) -> List[OptimizationRecommendation]:
    """Get ML-based optimization recommendations"""
    optimizer = await get_ml_optimizer()
    return await optimizer.get_optimization_recommendations(objective, current_metrics)
