"""
Advanced Monitoring and Analytics System for WebMCP Performance Enhancement

This module provides comprehensive monitoring capabilities including:
- Real-time performance analytics and dashboards
- Advanced metrics collection and aggregation
- Performance trend analysis and forecasting
- Custom metrics and KPI tracking
- Alerting and notification systems
- Performance reporting and insights
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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types for monitoring"""
    COUNTER = "counter"                 # Incremental counter
    GAUGE = "gauge"                     # Current value
    HISTOGRAM = "histogram"             # Distribution of values
    TIMER = "timer"                     # Duration measurements
    RATE = "rate"                       # Rate of change
    PERCENTILE = "percentile"           # Percentile values


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DashboardType(Enum):
    """Dashboard types"""
    PERFORMANCE = "performance"
    SYSTEM_HEALTH = "system_health"
    BUSINESS_METRICS = "business_metrics"
    CUSTOM = "custom"


@dataclass
class Metric:
    """Metric definition"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricAggregation:
    """Metric aggregation result"""
    name: str
    metric_type: MetricType
    count: int
    sum: float
    min: float
    max: float
    mean: float
    median: float
    std_dev: float
    percentiles: Dict[int, float] = field(default_factory=dict)
    time_window_seconds: int = 60


@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    trend_direction: str                # "increasing", "decreasing", "stable"
    trend_strength: float               # 0.0 to 1.0
    change_rate: float                  # Rate of change per unit time
    confidence: float                   # Confidence in trend
    forecast: List[float] = field(default_factory=list)  # Future predictions
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    metric_name: str
    condition: str
    threshold: float
    current_value: float
    severity: AlertSeverity
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Dashboard definition"""
    dashboard_id: str
    name: str
    dashboard_type: DashboardType
    metrics: List[str]
    layout: Dict[str, Any]
    refresh_interval: int = 30
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedMonitoring:
    """
    Advanced monitoring and analytics system.
    
    Features:
    - Real-time metrics collection and aggregation
    - Performance trend analysis and forecasting
    - Custom dashboards and visualizations
    - Advanced alerting and notification
    - Performance reporting and insights
    - KPI tracking and analysis
    """
    
    def __init__(
        self,
        metrics_retention_hours: int = 24,
        aggregation_interval: int = 60,
        trend_analysis_window: int = 100
    ):
        self.metrics_retention_hours = metrics_retention_hours
        self.aggregation_interval = aggregation_interval
        self.trend_analysis_window = trend_analysis_window
        
        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=metrics_retention_hours * 3600)
        )
        self._aggregated_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=metrics_retention_hours * 60)  # One per minute
        )
        
        # Performance trends
        self._performance_trends: Dict[str, PerformanceTrend] = {}
        
        # Alerts
        self._alert_rules: Dict[str, Dict[str, Any]] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=1000)
        
        # Dashboards
        self._dashboards: Dict[str, Dashboard] = {}
        self._dashboard_data: Dict[str, Dict[str, Any]] = {}
        
        # KPIs
        self._kpis: Dict[str, Dict[str, Any]] = {}
        self._kpi_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Background tasks
        self._metrics_task: Optional[asyncio.Task] = None
        self._aggregation_task: Optional[asyncio.Task] = None
        self._trend_analysis_task: Optional[asyncio.Task] = None
        self._alerting_task: Optional[asyncio.Task] = None
        self._dashboard_task: Optional[asyncio.Task] = None
        
        # Notification channels
        self._notification_channels: List[Callable[[Alert], Awaitable[None]]] = []
        
        # Custom metrics
        self._custom_metrics: Dict[str, Callable[[], Awaitable[float]]] = {}
    
    async def start(self):
        """Start advanced monitoring"""
        self._metrics_task = asyncio.create_task(self._metrics_processing_loop())
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        self._trend_analysis_task = asyncio.create_task(self._trend_analysis_loop())
        self._alerting_task = asyncio.create_task(self._alerting_loop())
        self._dashboard_task = asyncio.create_task(self._dashboard_loop())
        logger.info("AdvancedMonitoring started")
    
    async def stop(self):
        """Stop advanced monitoring"""
        if self._metrics_task:
            self._metrics_task.cancel()
        if self._aggregation_task:
            self._aggregation_task.cancel()
        if self._trend_analysis_task:
            self._trend_analysis_task.cancel()
        if self._alerting_task:
            self._alerting_task.cancel()
        if self._dashboard_task:
            self._dashboard_task.cancel()
        logger.info("AdvancedMonitoring stopped")
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Dict[str, str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=time.time(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self._metrics[name].append(metric)
    
    async def get_metric_aggregation(
        self,
        name: str,
        time_window_seconds: int = 60
    ) -> Optional[MetricAggregation]:
        """Get metric aggregation for time window"""
        if name not in self._metrics:
            return None
        
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds
        
        # Filter metrics within time window
        recent_metrics = [
            m for m in self._metrics[name]
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        values = [m.value for m in recent_metrics]
        
        # Calculate statistics
        aggregation = MetricAggregation(
            name=name,
            metric_type=recent_metrics[0].metric_type,
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            time_window_seconds=time_window_seconds
        )
        
        # Calculate percentiles
        sorted_values = sorted(values)
        percentiles = [50, 90, 95, 99]
        for p in percentiles:
            index = int((p / 100.0) * len(sorted_values))
            index = min(index, len(sorted_values) - 1)
            aggregation.percentiles[p] = sorted_values[index]
        
        return aggregation
    
    async def get_performance_trend(self, metric_name: str) -> Optional[PerformanceTrend]:
        """Get performance trend analysis for metric"""
        return self._performance_trends.get(metric_name)
    
    def add_alert_rule(
        self,
        rule_id: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        message: str
    ):
        """Add alert rule"""
        self._alert_rules[rule_id] = {
            "metric_name": metric_name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "message": message
        }
        logger.info(f"Added alert rule: {rule_id}")
    
    def add_notification_channel(self, channel: Callable[[Alert], Awaitable[None]]):
        """Add notification channel"""
        self._notification_channels.append(channel)
        logger.info("Added notification channel")
    
    def create_dashboard(
        self,
        dashboard_id: str,
        name: str,
        dashboard_type: DashboardType,
        metrics: List[str],
        layout: Dict[str, Any]
    ) -> Dashboard:
        """Create a new dashboard"""
        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            name=name,
            dashboard_type=dashboard_type,
            metrics=metrics,
            layout=layout
        )
        
        self._dashboards[dashboard_id] = dashboard
        logger.info(f"Created dashboard: {dashboard_id}")
        
        return dashboard
    
    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data"""
        if dashboard_id not in self._dashboards:
            return {}
        
        dashboard = self._dashboards[dashboard_id]
        data = {}
        
        # Collect data for each metric
        for metric_name in dashboard.metrics:
            aggregation = await self.get_metric_aggregation(metric_name)
            if aggregation:
                data[metric_name] = {
                    "current_value": aggregation.mean,
                    "min": aggregation.min,
                    "max": aggregation.max,
                    "count": aggregation.count,
                    "percentiles": aggregation.percentiles,
                    "trend": self._performance_trends.get(metric_name)
                }
        
        return data
    
    def add_kpi(
        self,
        kpi_id: str,
        name: str,
        calculation_func: Callable[[Dict[str, float]], float],
        target_value: float,
        unit: str = ""
    ):
        """Add KPI tracking"""
        self._kpis[kpi_id] = {
            "name": name,
            "calculation_func": calculation_func,
            "target_value": target_value,
            "unit": unit
        }
        logger.info(f"Added KPI: {kpi_id}")
    
    async def calculate_kpi(self, kpi_id: str) -> Optional[float]:
        """Calculate KPI value"""
        if kpi_id not in self._kpis:
            return None
        
        kpi_config = self._kpis[kpi_id]
        
        # Collect current metric values
        metric_values = {}
        for metric_name in self._metrics:
            if self._metrics[metric_name]:
                latest_metric = list(self._metrics[metric_name])[-1]
                metric_values[metric_name] = latest_metric.value
        
        # Calculate KPI
        try:
            kpi_value = kpi_config["calculation_func"](metric_values)
            
            # Store in history
            self._kpi_history[kpi_id].append({
                "value": kpi_value,
                "timestamp": time.time(),
                "target": kpi_config["target_value"]
            })
            
            return kpi_value
            
        except Exception as e:
            logger.error(f"KPI calculation failed for {kpi_id}: {e}")
            return None
    
    def register_custom_metric(self, name: str, calculation_func: Callable[[], Awaitable[float]]):
        """Register custom metric calculation function"""
        self._custom_metrics[name] = calculation_func
        logger.info(f"Registered custom metric: {name}")
    
    async def _metrics_processing_loop(self):
        """Background metrics processing loop"""
        while True:
            try:
                await asyncio.sleep(10.0)  # Process every 10 seconds
                
                # Calculate custom metrics
                await self._calculate_custom_metrics()
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics processing loop error: {e}")
    
    async def _calculate_custom_metrics(self):
        """Calculate custom metrics"""
        for metric_name, calculation_func in self._custom_metrics.items():
            try:
                value = await calculation_func()
                self.record_metric(metric_name, value, MetricType.GAUGE)
            except Exception as e:
                logger.error(f"Custom metric calculation failed for {metric_name}: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics"""
        current_time = time.time()
        cutoff_time = current_time - (self.metrics_retention_hours * 3600)
        
        for metric_name in list(self._metrics.keys()):
            # Remove old metrics
            while self._metrics[metric_name] and self._metrics[metric_name][0].timestamp < cutoff_time:
                self._metrics[metric_name].popleft()
            
            # Remove empty metric collections
            if not self._metrics[metric_name]:
                del self._metrics[metric_name]
    
    async def _aggregation_loop(self):
        """Background aggregation loop"""
        while True:
            try:
                await asyncio.sleep(self.aggregation_interval)
                
                # Aggregate metrics
                await self._aggregate_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Aggregation loop error: {e}")
    
    async def _aggregate_metrics(self):
        """Aggregate metrics for all metric types"""
        for metric_name in self._metrics:
            aggregation = await self.get_metric_aggregation(metric_name, self.aggregation_interval)
            if aggregation:
                self._aggregated_metrics[metric_name].append(aggregation)
    
    async def _trend_analysis_loop(self):
        """Background trend analysis loop"""
        while True:
            try:
                await asyncio.sleep(300.0)  # Analyze trends every 5 minutes
                
                # Analyze trends for all metrics
                await self._analyze_trends()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trend analysis loop error: {e}")
    
    async def _analyze_trends(self):
        """Analyze performance trends"""
        for metric_name in self._metrics:
            trend = await self._calculate_trend(metric_name)
            if trend:
                self._performance_trends[metric_name] = trend
    
    async def _calculate_trend(self, metric_name: str) -> Optional[PerformanceTrend]:
        """Calculate trend for a metric"""
        if metric_name not in self._metrics or len(self._metrics[metric_name]) < 10:
            return None
        
        # Get recent values
        recent_metrics = list(self._metrics[metric_name])[-self.trend_analysis_window:]
        values = [m.value for m in recent_metrics]
        timestamps = [m.timestamp for m in recent_metrics]
        
        if len(values) < 5:
            return None
        
        # Calculate trend using linear regression
        n = len(values)
        x = [(t - timestamps[0]) / 3600.0 for t in timestamps]  # Hours since first measurement
        
        # Linear regression
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:
            trend_direction = "stable"
            trend_strength = 0.0
        elif slope > 0:
            trend_direction = "increasing"
            trend_strength = min(1.0, abs(slope) / 10.0)  # Normalize
        else:
            trend_direction = "decreasing"
            trend_strength = min(1.0, abs(slope) / 10.0)
        
        # Calculate confidence based on data quality
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        mean_value = statistics.mean(values)
        
        if mean_value > 0:
            coefficient_of_variation = std_dev / mean_value
            confidence = max(0.1, 1.0 - coefficient_of_variation)
        else:
            confidence = 0.5
        
        # Generate forecast (simple linear extrapolation)
        forecast = []
        last_timestamp = timestamps[-1]
        last_value = values[-1]
        
        for i in range(1, 6):  # Forecast next 5 time periods
            forecast_time = last_timestamp + (i * 3600)  # 1 hour intervals
            forecast_value = last_value + (slope * i)
            forecast.append(forecast_value)
        
        return PerformanceTrend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            change_rate=slope,
            confidence=confidence,
            forecast=forecast
        )
    
    async def _alerting_loop(self):
        """Background alerting loop"""
        while True:
            try:
                await asyncio.sleep(30.0)  # Check alerts every 30 seconds
                
                # Check alert rules
                await self._check_alert_rules()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alerting loop error: {e}")
    
    async def _check_alert_rules(self):
        """Check alert rules and trigger alerts"""
        current_time = time.time()
        
        for rule_id, rule in self._alert_rules.items():
            metric_name = rule["metric_name"]
            
            if metric_name not in self._metrics or not self._metrics[metric_name]:
                continue
            
            # Get current metric value
            latest_metric = list(self._metrics[metric_name])[-1]
            current_value = latest_metric.value
            
            # Check alert condition
            should_alert = False
            if rule["condition"] == ">":
                should_alert = current_value > rule["threshold"]
            elif rule["condition"] == "<":
                should_alert = current_value < rule["threshold"]
            elif rule["condition"] == ">=":
                should_alert = current_value >= rule["threshold"]
            elif rule["condition"] == "<=":
                should_alert = current_value <= rule["threshold"]
            elif rule["condition"] == "==":
                should_alert = abs(current_value - rule["threshold"]) < 0.01
            
            if should_alert:
                # Create alert if not already active
                if rule_id not in self._active_alerts:
                    alert = Alert(
                        alert_id=f"{rule_id}_{int(current_time)}",
                        metric_name=metric_name,
                        condition=rule["condition"],
                        threshold=rule["threshold"],
                        current_value=current_value,
                        severity=rule["severity"],
                        message=rule["message"].format(
                            metric=metric_name,
                            value=current_value,
                            threshold=rule["threshold"]
                        ),
                        timestamp=current_time
                    )
                    
                    self._active_alerts[rule_id] = alert
                    self._alert_history.append(alert)
                    
                    # Send notifications
                    await self._send_alert_notifications(alert)
                    
                    logger.warning(f"Alert triggered: {rule_id} - {alert.message}")
            
            else:
                # Resolve alert if it was active
                if rule_id in self._active_alerts:
                    alert = self._active_alerts[rule_id]
                    alert.resolved = True
                    alert.resolved_at = current_time
                    
                    # Send resolution notification
                    await self._send_alert_notifications(alert)
                    
                    del self._active_alerts[rule_id]
                    logger.info(f"Alert resolved: {rule_id}")
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications to all channels"""
        for channel in self._notification_channels:
            try:
                await channel(alert)
            except Exception as e:
                logger.error(f"Notification channel failed: {e}")
    
    async def _dashboard_loop(self):
        """Background dashboard update loop"""
        while True:
            try:
                await asyncio.sleep(30.0)  # Update dashboards every 30 seconds
                
                # Update dashboard data
                for dashboard_id in self._dashboards:
                    self._dashboard_data[dashboard_id] = await self.get_dashboard_data(dashboard_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dashboard loop error: {e}")
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring system summary"""
        return {
            "metrics_tracked": len(self._metrics),
            "active_alerts": len(self._active_alerts),
            "dashboards": len(self._dashboards),
            "kpis": len(self._kpis),
            "custom_metrics": len(self._custom_metrics),
            "notification_channels": len(self._notification_channels),
            "recent_alerts": [
                {
                    "metric": alert.metric_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "resolved": alert.resolved
                }
                for alert in list(self._alert_history)[-5:]
            ]
        }


# Global advanced monitoring
_advanced_monitoring: Optional[AdvancedMonitoring] = None


async def get_advanced_monitoring() -> AdvancedMonitoring:
    """Get the global advanced monitoring system"""
    global _advanced_monitoring
    if _advanced_monitoring is None:
        _advanced_monitoring = AdvancedMonitoring()
        await _advanced_monitoring.start()
    return _advanced_monitoring


def record_metric(name: str, value: float, metric_type: MetricType = MetricType.GAUGE, **kwargs):
    """Record a metric"""
    if _advanced_monitoring:
        _advanced_monitoring.record_metric(name, value, metric_type, **kwargs)


async def get_metric_aggregation(name: str, time_window_seconds: int = 60) -> Optional[MetricAggregation]:
    """Get metric aggregation"""
    monitoring = await get_advanced_monitoring()
    return await monitoring.get_metric_aggregation(name, time_window_seconds)


async def get_performance_trend(metric_name: str) -> Optional[PerformanceTrend]:
    """Get performance trend"""
    monitoring = await get_advanced_monitoring()
    return await monitoring.get_performance_trend(metric_name)


def add_alert_rule(rule_id: str, metric_name: str, condition: str, threshold: float, severity: AlertSeverity, message: str):
    """Add alert rule"""
    if _advanced_monitoring:
        _advanced_monitoring.add_alert_rule(rule_id, metric_name, condition, threshold, severity, message)


async def get_monitoring_summary() -> Dict[str, Any]:
    """Get monitoring summary"""
    monitoring = await get_advanced_monitoring()
    return monitoring.get_monitoring_summary()
