"""
Performance Monitoring and Metrics Collection for WebMCP

This module provides comprehensive performance monitoring, metrics collection,
and health checking for the WebMCP server.
"""

import asyncio
import logging
import time
import psutil
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores performance metrics with configurable retention.
    
    Features:
    - Time-series metrics storage
    - Automatic aggregation (min, max, avg, p95, p99)
    - Configurable retention periods
    - Tag-based filtering
    - Export capabilities
    """
    
    def __init__(self, retention_hours: int = 24, max_points_per_metric: int = 1000):
        self.retention_hours = retention_hours
        self.max_points_per_metric = max_points_per_metric
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self._aggregations: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._last_cleanup = time.time()
        
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        unit: str = ""
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            unit=unit
        )
        
        self._metrics[name].append(metric)
        self._update_aggregations(name)
        
        # Periodic cleanup
        if time.time() - self._last_cleanup > 3600:  # Every hour
            self._cleanup_old_metrics()
            self._last_cleanup = time.time()
    
    def _update_aggregations(self, metric_name: str):
        """Update aggregations for a metric"""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return
        
        values = [m.value for m in self._metrics[metric_name]]
        if not values:
            return
        
        # Calculate aggregations
        self._aggregations[metric_name] = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        for metric_name, metrics in self._metrics.items():
            # Remove old metrics
            while metrics and metrics[0].timestamp < cutoff_time:
                metrics.popleft()
    
    def get_metric(self, name: str, tags: Optional[Dict[str, str]] = None) -> List[PerformanceMetric]:
        """Get metrics by name and optional tags"""
        if name not in self._metrics:
            return []
        
        metrics = list(self._metrics[name])
        
        # Filter by tags if provided
        if tags:
            metrics = [
                m for m in metrics
                if all(m.tags.get(k) == v for k, v in tags.items())
            ]
        
        return metrics
    
    def get_aggregations(self, metric_name: str) -> Dict[str, float]:
        """Get aggregated statistics for a metric"""
        return self._aggregations.get(metric_name, {})
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics and aggregations"""
        return {
            "metrics": {
                name: {
                    "count": len(metrics),
                    "latest": metrics[-1].value if metrics else None,
                    "aggregations": self._aggregations[name]
                }
                for name, metrics in self._metrics.items()
            },
            "retention_hours": self.retention_hours,
            "total_metrics": len(self._metrics)
        }


class SystemMonitor:
    """
    Monitors system resources and performance.
    
    Features:
    - CPU usage monitoring
    - Memory usage tracking
    - Disk I/O monitoring
    - Network statistics
    - Process-specific metrics
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self._monitoring_task: Optional[asyncio.Task] = None
        self._interval = 10.0  # seconds
        
    async def start(self):
        """Start system monitoring"""
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("SystemMonitor started")
    
    async def stop(self):
        """Stop system monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("SystemMonitor stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self._interval)
                await self._collect_system_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record_metric("system.cpu_percent", cpu_percent, unit="percent")
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics.record_metric("system.memory_percent", memory.percent, unit="percent")
            self.metrics.record_metric("system.memory_used_mb", memory.used / 1024 / 1024, unit="MB")
            self.metrics.record_metric("system.memory_available_mb", memory.available / 1024 / 1024, unit="MB")
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self.metrics.record_metric("process.memory_rss_mb", process_memory.rss / 1024 / 1024, unit="MB")
            self.metrics.record_metric("process.memory_vms_mb", process_memory.vms / 1024 / 1024, unit="MB")
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.metrics.record_metric("system.disk_read_mb", disk_io.read_bytes / 1024 / 1024, unit="MB")
                self.metrics.record_metric("system.disk_write_mb", disk_io.write_bytes / 1024 / 1024, unit="MB")
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                self.metrics.record_metric("system.network_sent_mb", network_io.bytes_sent / 1024 / 1024, unit="MB")
                self.metrics.record_metric("system.network_recv_mb", network_io.bytes_recv / 1024 / 1024, unit="MB")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")


class HealthChecker:
    """
    Performs health checks on system components.
    
    Features:
    - Configurable health checks
    - Dependency checking
    - Automatic health status calculation
    - Health check scheduling
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self._health_checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._health_results: Dict[str, HealthCheck] = {}
        self._check_interval = 30.0  # seconds
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start health checking"""
        # Register default health checks
        self._register_default_health_checks()
        
        self._monitoring_task = asyncio.create_task(self._health_check_loop())
        logger.info("HealthChecker started")
    
    async def stop(self):
        """Stop health checking"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("HealthChecker stopped")
    
    def register_health_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Register a custom health check"""
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def _register_default_health_checks(self):
        """Register default system health checks"""
        self.register_health_check("memory", self._check_memory)
        self.register_health_check("cpu", self._check_cpu)
        self.register_health_check("disk", self._check_disk)
        self.register_health_check("connections", self._check_connections)
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                await self._run_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _run_health_checks(self):
        """Run all registered health checks"""
        for name, check_func in self._health_checks.items():
            try:
                result = check_func()
                
                # Determine status
                status = "healthy"
                if result.get("warning"):
                    status = "degraded"
                if result.get("error"):
                    status = "unhealthy"
                
                health_check = HealthCheck(
                    name=name,
                    status=status,
                    message=result.get("message", ""),
                    timestamp=time.time(),
                    details=result
                )
                
                self._health_results[name] = health_check
                
                # Record health metrics
                status_value = 1 if status == "healthy" else (0.5 if status == "degraded" else 0)
                self.metrics.record_metric(f"health.{name}", status_value, unit="status")
                
            except Exception as e:
                health_check = HealthCheck(
                    name=name,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}",
                    timestamp=time.time(),
                    details={"error": str(e)}
                )
                self._health_results[name] = health_check
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        if usage_percent > 90:
            return {"error": True, "message": f"Memory usage critical: {usage_percent:.1f}%"}
        elif usage_percent > 80:
            return {"warning": True, "message": f"Memory usage high: {usage_percent:.1f}%"}
        else:
            return {"message": f"Memory usage normal: {usage_percent:.1f}%"}
    
    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            return {"error": True, "message": f"CPU usage critical: {cpu_percent:.1f}%"}
        elif cpu_percent > 80:
            return {"warning": True, "message": f"CPU usage high: {cpu_percent:.1f}%"}
        else:
            return {"message": f"CPU usage normal: {cpu_percent:.1f}%"}
    
    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        usage_percent = (disk.used / disk.total) * 100
        
        if usage_percent > 95:
            return {"error": True, "message": f"Disk usage critical: {usage_percent:.1f}%"}
        elif usage_percent > 85:
            return {"warning": True, "message": f"Disk usage high: {usage_percent:.1f}%"}
        else:
            return {"message": f"Disk usage normal: {usage_percent:.1f}%"}
    
    def _check_connections(self) -> Dict[str, Any]:
        """Check connection pool status"""
        try:
            # This would check connection pool health
            # For now, return a placeholder
            return {"message": "Connection pools healthy"}
        except Exception as e:
            return {"error": True, "message": f"Connection check failed: {str(e)}"}
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self._health_results:
            return {"status": "unknown", "message": "No health checks performed"}
        
        # Calculate overall status
        statuses = [check.status for check in self._health_results.values()]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "timestamp": check.timestamp,
                    "details": check.details
                }
                for name, check in self._health_results.items()
            },
            "timestamp": time.time()
        }


class PerformanceMonitor:
    """
    Main performance monitoring system.
    
    Coordinates metrics collection, system monitoring, and health checking.
    """
    
    def __init__(self, retention_hours: int = 24):
        self.metrics = MetricsCollector(retention_hours)
        self.system_monitor = SystemMonitor(self.metrics)
        self.health_checker = HealthChecker(self.metrics)
        self._started = False
        
    async def start(self):
        """Start all monitoring components"""
        if self._started:
            return
        
        await self.system_monitor.start()
        await self.health_checker.start()
        self._started = True
        logger.info("PerformanceMonitor started")
    
    async def stop(self):
        """Stop all monitoring components"""
        if not self._started:
            return
        
        await self.system_monitor.stop()
        await self.health_checker.stop()
        self._started = False
        logger.info("PerformanceMonitor stopped")
    
    def record_tool_metric(
        self,
        tool_name: str,
        execution_time: float,
        success: bool,
        memory_used: int = 0
    ):
        """Record tool execution metrics"""
        self.metrics.record_metric(
            f"tool.{tool_name}.execution_time",
            execution_time,
            tags={"tool": tool_name},
            unit="seconds"
        )
        
        self.metrics.record_metric(
            f"tool.{tool_name}.success_rate",
            1.0 if success else 0.0,
            tags={"tool": tool_name},
            unit="ratio"
        )
        
        if memory_used > 0:
            self.metrics.record_metric(
                f"tool.{tool_name}.memory_used",
                memory_used / 1024 / 1024,  # Convert to MB
                tags={"tool": tool_name},
                unit="MB"
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "metrics": self.metrics.get_all_metrics(),
            "health": self.health_checker.get_overall_health(),
            "timestamp": time.time()
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            return json.dumps(self.get_performance_summary(), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global performance monitor
_performance_monitor: Optional[PerformanceMonitor] = None


async def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start()
    return _performance_monitor


async def record_tool_metric(
    tool_name: str,
    execution_time: float,
    success: bool,
    memory_used: int = 0
):
    """Record tool execution metrics"""
    monitor = await get_performance_monitor()
    monitor.record_tool_metric(tool_name, execution_time, success, memory_used)


async def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    monitor = await get_performance_monitor()
    return monitor.get_performance_summary()
