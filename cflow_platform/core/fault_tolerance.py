"""
Fault Tolerance and Monitoring for WebMCP

This module provides circuit breaker patterns, graceful degradation,
health monitoring, metrics collection, and alerting for the WebMCP server.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import aiohttp
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count = 0
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_open_count": 0,
            "circuit_half_open_count": 0
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.stats["total_requests"] += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.stats["circuit_half_open_count"] += 1
                logger.info(f"Circuit breaker {self.config.name} transitioning to HALF_OPEN")
            else:
                self.stats["failed_requests"] += 1
                raise Exception(f"Circuit breaker {self.config.name} is OPEN")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.success_count += 1
        self.stats["successful_requests"] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker {self.config.name} transitioning to CLOSED")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.stats["failed_requests"] += 1
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.stats["circuit_open_count"] += 1
            logger.warning(f"Circuit breaker {self.config.name} transitioning to OPEN")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            **self.stats,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_rate": (self.stats["failed_requests"] / 
                           max(1, self.stats["total_requests"]) * 100)
        }


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.overall_health = "healthy"
        self.last_check_time = 0.0
        self.check_interval = 30.0  # 30 seconds
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
        self.health_status[name] = {
            "status": "unknown",
            "last_check": 0.0,
            "error": None,
            "response_time": 0.0
        }
        logger.info(f"Registered health check: {name}")
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                check_start = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                check_time = time.time() - check_start
                
                self.health_status[name] = {
                    "status": "healthy",
                    "last_check": time.time(),
                    "error": None,
                    "response_time": check_time,
                    "result": result
                }
                
                results[name] = {
                    "status": "healthy",
                    "response_time": check_time,
                    "result": result
                }
                
            except Exception as e:
                check_time = time.time() - check_start
                
                self.health_status[name] = {
                    "status": "unhealthy",
                    "last_check": time.time(),
                    "error": str(e),
                    "response_time": check_time
                }
                
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time": check_time
                }
                
                logger.error(f"Health check {name} failed: {e}")
        
        # Determine overall health
        unhealthy_checks = [name for name, status in results.items() 
                           if status["status"] == "unhealthy"]
        
        if unhealthy_checks:
            self.overall_health = "unhealthy"
        else:
            self.overall_health = "healthy"
        
        self.last_check_time = time.time()
        
        return {
            "overall_health": self.overall_health,
            "last_check": self.last_check_time,
            "check_duration": time.time() - start_time,
            "checks": results
        }
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        while True:
            try:
                await self.run_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "overall_health": self.overall_health,
            "last_check": self.last_check_time,
            "checks": self.health_status.copy()
        }


class MetricsCollector:
    """Comprehensive metrics collection system"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "performance": {
                "response_times": [],
                "throughput": 0,
                "error_rate": 0.0,
                "active_connections": 0
            },
            "system": {
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "disk_usage": 0.0,
                "network_io": 0.0
            },
            "business": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0
            }
        }
        self.start_time = time.time()
    
    def record_response_time(self, response_time: float):
        """Record response time metric"""
        self.metrics["performance"]["response_times"].append(response_time)
        
        # Keep only last 1000 measurements
        if len(self.metrics["performance"]["response_times"]) > 1000:
            self.metrics["performance"]["response_times"] = \
                self.metrics["performance"]["response_times"][-1000:]
    
    def record_request(self, success: bool):
        """Record request metric"""
        self.metrics["business"]["total_requests"] += 1
        if success:
            self.metrics["business"]["successful_requests"] += 1
        else:
            self.metrics["business"]["failed_requests"] += 1
        
        # Update error rate
        total = self.metrics["business"]["total_requests"]
        failed = self.metrics["business"]["failed_requests"]
        self.metrics["performance"]["error_rate"] = (failed / total * 100) if total > 0 else 0
    
    def record_cache_hit(self, hit: bool):
        """Record cache hit/miss metric"""
        if hit:
            self.metrics["business"]["cache_hits"] += 1
        else:
            self.metrics["business"]["cache_misses"] += 1
    
    def record_system_metrics(self, memory_mb: float, cpu_percent: float, 
                             disk_percent: float, network_mb: float):
        """Record system metrics"""
        self.metrics["system"]["memory_usage"] = memory_mb
        self.metrics["system"]["cpu_usage"] = cpu_percent
        self.metrics["system"]["disk_usage"] = disk_percent
        self.metrics["system"]["network_io"] = network_mb
    
    def record_active_connections(self, connections: int):
        """Record active connections"""
        self.metrics["performance"]["active_connections"] = connections
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        response_times = self.metrics["performance"]["response_times"]
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "performance": {
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
                "throughput_rps": self.metrics["performance"]["throughput"],
                "error_rate_percent": self.metrics["performance"]["error_rate"],
                "active_connections": self.metrics["performance"]["active_connections"]
            },
            "system": self.metrics["system"].copy(),
            "business": {
                **self.metrics["business"],
                "cache_hit_rate": (
                    self.metrics["business"]["cache_hits"] / 
                    max(1, self.metrics["business"]["cache_hits"] + self.metrics["business"]["cache_misses"]) * 100
                )
            }
        }


class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_channels: List[Callable] = []
    
    def add_alert_rule(self, name: str, condition: Callable, severity: str = "warning"):
        """Add an alert rule"""
        self.alert_rules[name] = {
            "condition": condition,
            "severity": severity,
            "enabled": True,
            "last_triggered": 0.0
        }
        logger.info(f"Added alert rule: {name}")
    
    def add_alert_channel(self, channel: Callable):
        """Add an alert channel (e.g., email, Slack, webhook)"""
        self.alert_channels.append(channel)
        logger.info("Added alert channel")
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check all alert rules"""
        for name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue
            
            try:
                if rule["condition"](metrics):
                    await self._trigger_alert(name, rule, metrics)
            except Exception as e:
                logger.error(f"Alert rule {name} error: {e}")
    
    async def _trigger_alert(self, name: str, rule: Dict[str, Any], metrics: Dict[str, Any]):
        """Trigger an alert"""
        alert = {
            "name": name,
            "severity": rule["severity"],
            "timestamp": time.time(),
            "metrics": metrics,
            "message": f"Alert {name} triggered"
        }
        
        self.alerts.append(alert)
        rule["last_triggered"] = time.time()
        
        # Send to all channels
        for channel in self.alert_channels:
            try:
                await channel(alert)
            except Exception as e:
                logger.error(f"Alert channel error: {e}")
        
        logger.warning(f"Alert triggered: {name} - {rule['severity']}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        return [alert for alert in self.alerts if alert["timestamp"] > time.time() - 3600]  # Last hour


class GracefulDegradation:
    """Graceful degradation system"""
    
    def __init__(self):
        self.fallback_handlers: Dict[str, Callable] = {}
        self.degradation_levels: Dict[str, str] = {}
        self.current_level = "full"
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Register a fallback handler for a service"""
        self.fallback_handlers[service_name] = fallback_func
        logger.info(f"Registered fallback for service: {service_name}")
    
    async def execute_with_fallback(self, service_name: str, primary_func: Callable, 
                                   *args, **kwargs) -> Any:
        """Execute function with fallback"""
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function failed for {service_name}: {e}")
            
            # Try fallback
            if service_name in self.fallback_handlers:
                fallback_func = self.fallback_handlers[service_name]
                try:
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {service_name}: {fallback_error}")
                    raise fallback_error
            else:
                raise e
    
    def set_degradation_level(self, level: str):
        """Set system degradation level"""
        self.current_level = level
        logger.info(f"System degradation level set to: {level}")
    
    def get_degradation_level(self) -> str:
        """Get current degradation level"""
        return self.current_level


class FaultToleranceManager:
    """Main fault tolerance manager"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_monitor = HealthMonitor()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.graceful_degradation = GracefulDegradation()
        
        # Default health checks
        self._register_default_health_checks()
        self._register_default_alert_rules()
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        async def redis_health_check():
            try:
                # Check Redis connection
                redis_client = redis.Redis(host='localhost', port=6379, db=0)
                await redis_client.ping()
                return {"status": "healthy", "response_time": "< 1ms"}
            except Exception as e:
                raise Exception(f"Redis health check failed: {e}")
        
        async def http_health_check():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8000/health', timeout=5) as response:
                        if response.status == 200:
                            return {"status": "healthy", "status_code": response.status}
                        else:
                            raise Exception(f"HTTP health check failed: {response.status}")
            except Exception as e:
                raise Exception(f"HTTP health check failed: {e}")
        
        self.health_monitor.register_health_check("redis", redis_health_check)
        self.health_monitor.register_health_check("http", http_health_check)
    
    def _register_default_alert_rules(self):
        """Register default alert rules"""
        def high_error_rate(metrics):
            return metrics.get("performance", {}).get("error_rate", 0) > 5.0
        
        def high_response_time(metrics):
            avg_time = metrics.get("performance", {}).get("average_response_time", 0)
            return avg_time > 1.0  # 1 second
        
        def high_memory_usage(metrics):
            memory = metrics.get("system", {}).get("memory_usage", 0)
            return memory > 400  # 400MB
        
        self.alert_manager.add_alert_rule("high_error_rate", high_error_rate, "critical")
        self.alert_manager.add_alert_rule("high_response_time", high_response_time, "warning")
        self.alert_manager.add_alert_rule("high_memory_usage", high_memory_usage, "warning")
    
    def create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create a circuit breaker"""
        circuit_breaker = CircuitBreaker(config)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
    
    async def start_monitoring(self):
        """Start all monitoring systems"""
        # Start health monitoring
        asyncio.create_task(self.health_monitor.start_monitoring())
        
        # Start alert checking
        asyncio.create_task(self._alert_checking_loop())
        
        logger.info("Fault tolerance monitoring started")
    
    async def _alert_checking_loop(self):
        """Alert checking loop"""
        while True:
            try:
                metrics = self.metrics_collector.get_metrics_summary()
                await self.alert_manager.check_alerts(metrics)
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Alert checking error: {e}")
                await asyncio.sleep(5)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "health": self.health_monitor.get_health_status(),
            "metrics": self.metrics_collector.get_metrics_summary(),
            "circuit_breakers": {
                name: cb.get_stats() 
                for name, cb in self.circuit_breakers.items()
            },
            "alerts": self.alert_manager.get_active_alerts(),
            "degradation_level": self.graceful_degradation.get_degradation_level()
        }