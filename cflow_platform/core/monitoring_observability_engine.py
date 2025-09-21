"""
Monitoring & Observability Engine for BMAD Workflows

This module provides comprehensive monitoring, alerting, and observability capabilities
for production-ready BMAD system monitoring and insights.
"""

import asyncio
import logging
import time
import uuid
import json
import psutil
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MonitoringMetricType(Enum):
    """Types of monitoring metrics"""
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE = "performance"
    RESOURCE_UTILIZATION = "resource_utilization"
    BUSINESS_METRICS = "business_metrics"
    APPLICATION_METRICS = "application_metrics"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class SystemHealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class MonitoringMetric:
    """Monitoring metric data"""
    metric_id: str
    metric_type: MonitoringMetricType
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert data"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealthCheck:
    """System health check result"""
    check_id: str
    component: str
    status: SystemHealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductionMonitoringEngine:
    """Engine for production monitoring"""
    
    def __init__(self):
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.health_checks: Dict[str, SystemHealthCheck] = {}
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
    
    async def start_monitoring(self, interval_seconds: float = 30.0):
        """Start continuous monitoring"""
        
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"Production monitoring started with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("Production monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: float):
        """Main monitoring loop"""
        
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Perform health checks
                self._perform_health_checks()
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval_seconds)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            # Network metrics
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent
            bytes_recv = network.bytes_recv
            
            # Process metrics
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            process_memory = process.memory_info().rss / (1024**2)  # MB
            
            timestamp = datetime.now()
            
            # Store metrics
            metrics = [
                MonitoringMetric("cpu_percent", MonitoringMetricType.RESOURCE_UTILIZATION, "CPU Usage", cpu_percent, "%", timestamp),
                MonitoringMetric("memory_percent", MonitoringMetricType.RESOURCE_UTILIZATION, "Memory Usage", memory_percent, "%", timestamp),
                MonitoringMetric("memory_available", MonitoringMetricType.RESOURCE_UTILIZATION, "Memory Available", memory_available, "GB", timestamp),
                MonitoringMetric("disk_percent", MonitoringMetricType.RESOURCE_UTILIZATION, "Disk Usage", disk_percent, "%", timestamp),
                MonitoringMetric("disk_free", MonitoringMetricType.RESOURCE_UTILIZATION, "Disk Free", disk_free, "GB", timestamp),
                MonitoringMetric("network_bytes_sent", MonitoringMetricType.RESOURCE_UTILIZATION, "Network Bytes Sent", bytes_sent, "bytes", timestamp),
                MonitoringMetric("network_bytes_recv", MonitoringMetricType.RESOURCE_UTILIZATION, "Network Bytes Received", bytes_recv, "bytes", timestamp),
                MonitoringMetric("process_cpu", MonitoringMetricType.APPLICATION_METRICS, "Process CPU", process_cpu, "%", timestamp),
                MonitoringMetric("process_memory", MonitoringMetricType.APPLICATION_METRICS, "Process Memory", process_memory, "MB", timestamp),
            ]
            
            for metric in metrics:
                self.metrics_history[metric.metric_id].append(metric)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _perform_health_checks(self):
        """Perform system health checks"""
        
        timestamp = datetime.now()
        
        # CPU health check
        cpu_metric = self.get_latest_metric("cpu_percent")
        if cpu_metric:
            if cpu_metric.value > 90:
                status = SystemHealthStatus.CRITICAL
                message = f"CPU usage critically high: {cpu_metric.value:.1f}%"
            elif cpu_metric.value > 80:
                status = SystemHealthStatus.WARNING
                message = f"CPU usage high: {cpu_metric.value:.1f}%"
            else:
                status = SystemHealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_metric.value:.1f}%"
            
            self.health_checks["cpu"] = SystemHealthCheck(
                check_id=f"cpu_{int(timestamp.timestamp())}",
                component="CPU",
                status=status,
                message=message,
                timestamp=timestamp,
                response_time_ms=0.1
            )
        
        # Memory health check
        memory_metric = self.get_latest_metric("memory_percent")
        if memory_metric:
            if memory_metric.value > 95:
                status = SystemHealthStatus.CRITICAL
                message = f"Memory usage critically high: {memory_metric.value:.1f}%"
            elif memory_metric.value > 85:
                status = SystemHealthStatus.WARNING
                message = f"Memory usage high: {memory_metric.value:.1f}%"
            else:
                status = SystemHealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_metric.value:.1f}%"
            
            self.health_checks["memory"] = SystemHealthCheck(
                check_id=f"memory_{int(timestamp.timestamp())}",
                component="Memory",
                status=status,
                message=message,
                timestamp=timestamp,
                response_time_ms=0.1
            )
        
        # Disk health check
        disk_metric = self.get_latest_metric("disk_percent")
        if disk_metric:
            if disk_metric.value > 95:
                status = SystemHealthStatus.CRITICAL
                message = f"Disk usage critically high: {disk_metric.value:.1f}%"
            elif disk_metric.value > 85:
                status = SystemHealthStatus.WARNING
                message = f"Disk usage high: {disk_metric.value:.1f}%"
            else:
                status = SystemHealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_metric.value:.1f}%"
            
            self.health_checks["disk"] = SystemHealthCheck(
                check_id=f"disk_{int(timestamp.timestamp())}",
                component="Disk",
                status=status,
                message=message,
                timestamp=timestamp,
                response_time_ms=0.1
            )
    
    def get_latest_metric(self, metric_id: str) -> Optional[MonitoringMetric]:
        """Get the latest metric value"""
        
        if metric_id in self.metrics_history and self.metrics_history[metric_id]:
            return self.metrics_history[metric_id][-1]
        return None
    
    def get_metric_history(self, metric_id: str, limit: int = 100) -> List[MonitoringMetric]:
        """Get metric history"""
        
        if metric_id in self.metrics_history:
            return list(self.metrics_history[metric_id])[-limit:]
        return []
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        
        total_checks = len(self.health_checks)
        healthy_checks = len([h for h in self.health_checks.values() if h.status == SystemHealthStatus.HEALTHY])
        warning_checks = len([h for h in self.health_checks.values() if h.status == SystemHealthStatus.WARNING])
        critical_checks = len([h for h in self.health_checks.values() if h.status == SystemHealthStatus.CRITICAL])
        
        overall_status = SystemHealthStatus.HEALTHY
        if critical_checks > 0:
            overall_status = SystemHealthStatus.CRITICAL
        elif warning_checks > 0:
            overall_status = SystemHealthStatus.WARNING
        
        return {
            "overall_status": overall_status.value,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "warning_checks": warning_checks,
            "critical_checks": critical_checks,
            "health_score": (healthy_checks / total_checks * 100) if total_checks > 0 else 0,
            "last_updated": datetime.now().isoformat()
        }


class AlertingSystem:
    """Alerting system for production issues"""
    
    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []
    
    def add_alert_rule(self, rule_id: str, rule_config: Dict[str, Any]):
        """Add alerting rule"""
        
        self.alert_rules[rule_id] = {
            "rule_id": rule_id,
            "metric_name": rule_config["metric_name"],
            "threshold": rule_config["threshold"],
            "severity": AlertSeverity(rule_config["severity"]),
            "comparison": rule_config.get("comparison", "greater_than"),
            "enabled": rule_config.get("enabled", True),
            "description": rule_config.get("description", ""),
            "created_at": datetime.now()
        }
        
        logger.info(f"Added alert rule: {rule_id}")
    
    def check_alerts(self, metrics: List[MonitoringMetric]):
        """Check metrics against alert rules"""
        
        for metric in metrics:
            for rule_id, rule in self.alert_rules.items():
                if not rule["enabled"] or rule["metric_name"] != metric.name:
                    continue
                
                # Check if alert condition is met
                alert_triggered = False
                if rule["comparison"] == "greater_than" and metric.value > rule["threshold"]:
                    alert_triggered = True
                elif rule["comparison"] == "less_than" and metric.value < rule["threshold"]:
                    alert_triggered = True
                elif rule["comparison"] == "equals" and metric.value == rule["threshold"]:
                    alert_triggered = True
                
                if alert_triggered:
                    # Check if alert already exists
                    existing_alert_id = f"{rule_id}_{metric.name}"
                    if existing_alert_id not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            alert_id=existing_alert_id,
                            name=f"{rule['description']} Alert",
                            description=f"{metric.name} is {metric.value} {metric.unit}, threshold: {rule['threshold']} {metric.unit}",
                            severity=rule["severity"],
                            status=AlertStatus.ACTIVE,
                            metric_name=metric.name,
                            threshold_value=rule["threshold"],
                            current_value=metric.value,
                            timestamp=datetime.now()
                        )
                        
                        self.active_alerts[existing_alert_id] = alert
                        self.alert_history.append(alert)
                        
                        # Send notifications
                        self._send_notifications(alert)
                        
                        logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            self.active_alerts[alert_id].acknowledged_by = acknowledged_by
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved")
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    def add_notification_handler(self, handler: Callable):
        """Add notification handler"""
        
        self.notification_handlers.append(handler)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        
        return self.alert_history[-limit:]


class ObservabilityDashboard:
    """Observability dashboard for system insights"""
    
    def __init__(self, monitoring_engine: ProductionMonitoringEngine, alerting_system: AlertingSystem):
        self.monitoring_engine = monitoring_engine
        self.alerting_system = alerting_system
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data"""
        
        # System health
        health_summary = self.monitoring_engine.get_system_health_summary()
        
        # Current metrics
        current_metrics = {}
        for metric_id in ["cpu_percent", "memory_percent", "disk_percent", "process_cpu", "process_memory"]:
            metric = self.monitoring_engine.get_latest_metric(metric_id)
            if metric:
                current_metrics[metric_id] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
        
        # Active alerts
        active_alerts = self.alerting_system.get_active_alerts()
        alert_summary = {
            "total_active": len(active_alerts),
            "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in active_alerts if a.severity == AlertSeverity.LOW])
        }
        
        # Performance trends (last 10 data points)
        performance_trends = {}
        for metric_id in ["cpu_percent", "memory_percent", "disk_percent"]:
            history = self.monitoring_engine.get_metric_history(metric_id, limit=10)
            performance_trends[metric_id] = [
                {"timestamp": m.timestamp.isoformat(), "value": m.value}
                for m in history
            ]
        
        return {
            "dashboard_generated_at": datetime.now().isoformat(),
            "system_health": health_summary,
            "current_metrics": current_metrics,
            "alert_summary": alert_summary,
            "performance_trends": performance_trends,
            "health_checks": {
                check_id: {
                    "component": check.component,
                    "status": check.status.value,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat(),
                    "response_time_ms": check.response_time_ms
                }
                for check_id, check in self.monitoring_engine.health_checks.items()
            }
        }


class CentralizedLogging:
    """Centralized logging system"""
    
    def __init__(self):
        self.log_entries: List[Dict[str, Any]] = []
        self.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def log(self, level: str, message: str, component: str = "system", metadata: Optional[Dict[str, Any]] = None):
        """Log an entry"""
        
        log_entry = {
            "log_id": f"log_{uuid.uuid4().hex[:8]}",
            "level": level.upper(),
            "message": message,
            "component": component,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.log_entries.append(log_entry)
        
        # Keep only last 10000 entries
        if len(self.log_entries) > 10000:
            self.log_entries = self.log_entries[-10000:]
    
    def get_logs(self, level: Optional[str] = None, component: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get log entries"""
        
        filtered_logs = self.log_entries.copy()
        
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"] == level.upper()]
        
        if component:
            filtered_logs = [log for log in filtered_logs if log["component"] == component]
        
        return filtered_logs[-limit:]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get log statistics"""
        
        total_logs = len(self.log_entries)
        if total_logs == 0:
            return {"total_logs": 0}
        
        level_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for log in self.log_entries:
            level_counts[log["level"]] += 1
            component_counts[log["component"]] += 1
        
        return {
            "total_logs": total_logs,
            "level_distribution": dict(level_counts),
            "component_distribution": dict(component_counts),
            "last_log_time": self.log_entries[-1]["timestamp"] if self.log_entries else None
        }


class MonitoringObservabilityEngine:
    """Main engine for monitoring and observability"""
    
    def __init__(self):
        self.monitoring_engine = ProductionMonitoringEngine()
        self.alerting_system = AlertingSystem()
        self.dashboard = ObservabilityDashboard(self.monitoring_engine, self.alerting_system)
        self.logging = CentralizedLogging()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        # Setup notification handler
        self.alerting_system.add_notification_handler(self._log_alert_notification)
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        
        default_rules = [
            {
                "rule_id": "cpu_high",
                "metric_name": "CPU Usage",
                "threshold": 80.0,
                "severity": "high",
                "description": "High CPU Usage"
            },
            {
                "rule_id": "memory_high",
                "metric_name": "Memory Usage",
                "threshold": 85.0,
                "severity": "high",
                "description": "High Memory Usage"
            },
            {
                "rule_id": "disk_high",
                "metric_name": "Disk Usage",
                "threshold": 90.0,
                "severity": "critical",
                "description": "High Disk Usage"
            }
        ]
        
        for rule in default_rules:
            self.alerting_system.add_alert_rule(rule["rule_id"], rule)
    
    def _log_alert_notification(self, alert: Alert):
        """Log alert notification"""
        
        self.logging.log(
            level="WARNING",
            message=f"Alert triggered: {alert.name}",
            component="alerting_system",
            metadata={
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value
            }
        )
    
    async def start_monitoring(self, interval_seconds: float = 30.0):
        """Start monitoring and observability"""
        
        await self.monitoring_engine.start_monitoring(interval_seconds)
        self.logging.log("INFO", "Monitoring and observability started", "monitoring_engine")
    
    def stop_monitoring(self):
        """Stop monitoring and observability"""
        
        self.monitoring_engine.stop_monitoring()
        self.logging.log("INFO", "Monitoring and observability stopped", "monitoring_engine")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        
        return self.monitoring_engine.get_system_health_summary()
    
    def get_performance_metrics(self, metric_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get performance metrics"""
        
        if not metric_names:
            metric_names = ["cpu_percent", "memory_percent", "disk_percent", "process_cpu", "process_memory"]
        
        metrics = {}
        for metric_name in metric_names:
            metric = self.monitoring_engine.get_latest_metric(metric_name)
            if metric:
                metrics[metric_name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
        
        return metrics
    
    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        
        resource_metrics = ["cpu_percent", "memory_percent", "memory_available", "disk_percent", "disk_free"]
        return self.get_performance_metrics(resource_metrics)
    
    def configure_alerting(self, alert_rules: List[Dict[str, Any]]):
        """Configure alerting rules"""
        
        for rule in alert_rules:
            self.alerting_system.add_alert_rule(rule["rule_id"], rule)
        
        self.logging.log("INFO", f"Configured {len(alert_rules)} alert rules", "alerting_system")
    
    def test_alerting(self) -> Dict[str, Any]:
        """Test alerting system"""
        
        # Create test alert
        test_alert = Alert(
            alert_id="test_alert",
            name="Test Alert",
            description="This is a test alert to verify alerting system functionality",
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.now()
        )
        
        self.alerting_system.active_alerts["test_alert"] = test_alert
        self.alerting_system.alert_history.append(test_alert)
        
        self.logging.log("INFO", "Alerting system test completed", "alerting_system")
        
        return {
            "test_alert_created": True,
            "alert_id": test_alert.alert_id,
            "active_alerts_count": len(self.alerting_system.active_alerts)
        }
    
    def get_observability_dashboard(self) -> Dict[str, Any]:
        """Get observability dashboard data"""
        
        return self.dashboard.generate_dashboard_data()
    
    def get_centralized_logs(self, level: Optional[str] = None, component: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get centralized logs"""
        
        logs = self.logging.get_logs(level=level, component=component, limit=limit)
        statistics = self.logging.get_log_statistics()
        
        return {
            "logs": logs,
            "statistics": statistics,
            "total_returned": len(logs)
        }
    
    def generate_monitoring_report(self, hours_back: int = 24) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        # System health
        health_summary = self.get_system_health()
        
        # Performance metrics
        performance_metrics = self.get_performance_metrics()
        
        # Active alerts
        active_alerts = self.alerting_system.get_active_alerts()
        
        # Alert history
        alert_history = self.alerting_system.get_alert_history(limit=100)
        
        # Log statistics
        log_stats = self.logging.get_log_statistics()
        
        # Dashboard data
        dashboard_data = self.get_observability_dashboard()
        
        return {
            "report_generated_at": datetime.now().isoformat(),
            "report_period_hours": hours_back,
            "system_health": health_summary,
            "performance_metrics": performance_metrics,
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            "alert_summary": {
                "total_active": len(active_alerts),
                "total_history": len(alert_history)
            },
            "log_statistics": log_stats,
            "dashboard_summary": {
                "health_score": health_summary.get("health_score", 0),
                "overall_status": health_summary.get("overall_status", "unknown")
            },
            "recommendations": self._generate_recommendations(health_summary, active_alerts)
        }
    
    def _generate_recommendations(self, health_summary: Dict[str, Any], active_alerts: List[Alert]) -> List[str]:
        """Generate monitoring recommendations"""
        
        recommendations = []
        
        if health_summary.get("health_score", 0) < 80:
            recommendations.append("System health score is below 80% - investigate critical issues")
        
        if len(active_alerts) > 5:
            recommendations.append("High number of active alerts - review alerting thresholds")
        
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append(f"{len(critical_alerts)} critical alerts require immediate attention")
        
        if health_summary.get("critical_checks", 0) > 0:
            recommendations.append("Critical health checks failing - investigate system resources")
        
        if not recommendations:
            recommendations.append("System monitoring is healthy - continue regular monitoring")
        
        return recommendations


# Global instance
_monitoring_engine: Optional[MonitoringObservabilityEngine] = None


def get_monitoring_engine() -> MonitoringObservabilityEngine:
    """Get the global monitoring and observability engine instance"""
    global _monitoring_engine
    if _monitoring_engine is None:
        _monitoring_engine = MonitoringObservabilityEngine()
    return _monitoring_engine
