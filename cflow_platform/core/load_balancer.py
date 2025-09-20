"""
Load Balancing and Scaling for WebMCP

This module provides load balancing, auto-scaling, resource monitoring,
and performance target maintenance for the WebMCP server.
"""

import asyncio
import logging
import time
import psutil
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import aiohttp
import redis.asyncio as redis
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"


class ScalingStrategy(Enum):
    """Auto-scaling strategies"""
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    REQUEST_BASED = "request_based"
    RESPONSE_TIME_BASED = "response_time_based"
    HYBRID = "hybrid"


@dataclass
class WorkerNode:
    """Worker node information"""
    node_id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 1000
    current_connections: int = 0
    response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    status: str = "healthy"
    last_health_check: float = 0.0


@dataclass
class ScalingConfig:
    """Auto-scaling configuration"""
    min_workers: int = 2
    max_workers: int = 10
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 80.0
    target_response_time_ms: float = 500.0
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    scale_up_cooldown: float = 300.0  # 5 minutes
    scale_down_cooldown: float = 600.0  # 10 minutes


class LoadBalancer:
    """Load balancer for distributing requests across workers"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.workers: List[WorkerNode] = []
        self.current_worker_index = 0
        self.worker_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.request_history: deque = deque(maxlen=1000)
        self.response_times: deque = deque(maxlen=1000)
        
    def add_worker(self, worker: WorkerNode):
        """Add a worker node"""
        self.workers.append(worker)
        self.worker_stats[worker.node_id] = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0
        }
        logger.info(f"Worker added: {worker.node_id} ({worker.host}:{worker.port})")
    
    def remove_worker(self, node_id: str) -> bool:
        """Remove a worker node"""
        for i, worker in enumerate(self.workers):
            if worker.node_id == node_id:
                self.workers.pop(i)
                self.worker_stats.pop(node_id, None)
                logger.info(f"Worker removed: {node_id}")
                return True
        return False
    
    def select_worker(self, request: Dict[str, Any]) -> Optional[WorkerNode]:
        """Select a worker based on load balancing strategy"""
        if not self.workers:
            return None
        
        # Filter healthy workers
        healthy_workers = [w for w in self.workers if w.status == "healthy"]
        if not healthy_workers:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(healthy_workers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_workers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_workers)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(healthy_workers)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_selection(healthy_workers, request)
        else:
            return healthy_workers[0]
    
    def _round_robin_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Round-robin worker selection"""
        worker = workers[self.current_worker_index % len(workers)]
        self.current_worker_index = (self.current_worker_index + 1) % len(workers)
        return worker
    
    def _least_connections_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Least connections worker selection"""
        return min(workers, key=lambda w: w.current_connections)
    
    def _weighted_round_robin_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Weighted round-robin worker selection"""
        # Simple weighted selection based on worker weight
        total_weight = sum(w.weight for w in workers)
        if total_weight == 0:
            return workers[0]
        
        # Select worker based on weight
        import random
        random.seed(int(time.time() * 1000))
        rand = random.random() * total_weight
        
        cumulative_weight = 0
        for worker in workers:
            cumulative_weight += worker.weight
            if rand <= cumulative_weight:
                return worker
        
        return workers[-1]
    
    def _least_response_time_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Least response time worker selection"""
        return min(workers, key=lambda w: w.response_time)
    
    def _ip_hash_selection(self, workers: List[WorkerNode], request: Dict[str, Any]) -> WorkerNode:
        """IP hash worker selection"""
        client_ip = request.get("client_ip", "127.0.0.1")
        hash_value = hash(client_ip) % len(workers)
        return workers[hash_value]
    
    def update_worker_stats(self, node_id: str, response_time: float, success: bool):
        """Update worker statistics"""
        if node_id not in self.worker_stats:
            return
        
        stats = self.worker_stats[node_id]
        stats["requests"] += 1
        stats["total_response_time"] += response_time
        stats["average_response_time"] = stats["total_response_time"] / stats["requests"]
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        # Update worker response time
        for worker in self.workers:
            if worker.node_id == node_id:
                worker.response_time = stats["average_response_time"]
                break
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        total_requests = sum(stats["requests"] for stats in self.worker_stats.values())
        total_successful = sum(stats["successful_requests"] for stats in self.worker_stats.values())
        
        return {
            "strategy": self.strategy.value,
            "total_workers": len(self.workers),
            "healthy_workers": len([w for w in self.workers if w.status == "healthy"]),
            "total_requests": total_requests,
            "success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 0,
            "workers": [
                {
                    "node_id": worker.node_id,
                    "host": worker.host,
                    "port": worker.port,
                    "status": worker.status,
                    "current_connections": worker.current_connections,
                    "response_time": worker.response_time,
                    "cpu_usage": worker.cpu_usage,
                    "memory_usage": worker.memory_usage,
                    "stats": self.worker_stats.get(worker.node_id, {})
                }
                for worker in self.workers
            ]
        }


class ResourceMonitor:
    """Resource monitoring for auto-scaling"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=100)
        self.current_metrics: Dict[str, float] = {}
        self.alert_thresholds: Dict[str, float] = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "network_io_mb": 1000.0
        }
    
    async def collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io_mb = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_mb": memory_used_mb,
                "disk_percent": disk_percent,
                "network_io_mb": network_io_mb,
                "process_count": process_count,
                "timestamp": time.time()
            }
            
            self.current_metrics = metrics
            self.metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}
    
    def get_average_metrics(self, duration_minutes: int = 5) -> Dict[str, float]:
        """Get average metrics over specified duration"""
        if not self.metrics_history:
            return {}
        
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m["timestamp"] > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        averages = {}
        for key in recent_metrics[0].keys():
            if key != "timestamp":
                values = [m[key] for m in recent_metrics if key in m]
                if values:
                    averages[key] = statistics.mean(values)
        
        return averages
    
    def check_alerts(self) -> List[str]:
        """Check for resource alerts"""
        alerts = []
        
        for metric, threshold in self.alert_thresholds.items():
            if metric in self.current_metrics:
                value = self.current_metrics[metric]
                if value > threshold:
                    alerts.append(f"{metric}: {value:.2f} > {threshold}")
        
        return alerts


class AutoScaler:
    """Auto-scaling system"""
    
    def __init__(self, config: ScalingConfig):
        self.config = config
        self.resource_monitor = ResourceMonitor()
        self.scaling_history: List[Dict[str, Any]] = []
        self.last_scale_up = 0.0
        self.last_scale_down = 0.0
        self.current_workers = config.min_workers
        
        # Scaling metrics
        self.scaling_metrics = {
            "scale_ups": 0,
            "scale_downs": 0,
            "total_scaling_events": 0
        }
    
    async def evaluate_scaling(self, load_balancer: LoadBalancer, 
                              request_rate: float, response_time: float) -> Optional[str]:
        """Evaluate if scaling is needed"""
        try:
            # Collect current metrics
            metrics = await self.resource_monitor.collect_metrics()
            if not metrics:
                return None
            
            # Get average metrics over last 5 minutes
            avg_metrics = self.resource_monitor.get_average_metrics(5)
            
            # Check scale-up conditions
            scale_up_reason = self._check_scale_up_conditions(metrics, avg_metrics, 
                                                            request_rate, response_time)
            if scale_up_reason:
                return await self._scale_up(load_balancer, scale_up_reason)
            
            # Check scale-down conditions
            scale_down_reason = self._check_scale_down_conditions(metrics, avg_metrics, 
                                                                request_rate, response_time)
            if scale_down_reason:
                return await self._scale_down(load_balancer, scale_down_reason)
            
            return None
            
        except Exception as e:
            logger.error(f"Scaling evaluation error: {e}")
            return None
    
    def _check_scale_up_conditions(self, metrics: Dict[str, float], 
                                 avg_metrics: Dict[str, float], 
                                 request_rate: float, response_time: float) -> Optional[str]:
        """Check scale-up conditions"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_scale_up < self.config.scale_up_cooldown:
            return None
        
        # Check if already at max workers
        if self.current_workers >= self.config.max_workers:
            return None
        
        # CPU-based scaling
        if metrics.get("cpu_percent", 0) > self.config.target_cpu_percent * self.config.scale_up_threshold:
            return f"High CPU usage: {metrics['cpu_percent']:.2f}%"
        
        # Memory-based scaling
        if metrics.get("memory_percent", 0) > self.config.target_memory_percent * self.config.scale_up_threshold:
            return f"High memory usage: {metrics['memory_percent']:.2f}%"
        
        # Response time-based scaling
        if response_time > self.config.target_response_time_ms * self.config.scale_up_threshold:
            return f"High response time: {response_time:.2f}ms"
        
        # Request rate-based scaling
        if request_rate > 100:  # 100 requests per second threshold
            return f"High request rate: {request_rate:.2f} req/s"
        
        return None
    
    def _check_scale_down_conditions(self, metrics: Dict[str, float], 
                                   avg_metrics: Dict[str, float], 
                                   request_rate: float, response_time: float) -> Optional[str]:
        """Check scale-down conditions"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_scale_down < self.config.scale_down_cooldown:
            return None
        
        # Check if already at min workers
        if self.current_workers <= self.config.min_workers:
            return None
        
        # CPU-based scaling
        if metrics.get("cpu_percent", 0) < self.config.target_cpu_percent * self.config.scale_down_threshold:
            return f"Low CPU usage: {metrics['cpu_percent']:.2f}%"
        
        # Memory-based scaling
        if metrics.get("memory_percent", 0) < self.config.target_memory_percent * self.config.scale_down_threshold:
            return f"Low memory usage: {metrics['memory_percent']:.2f}%"
        
        # Response time-based scaling
        if response_time < self.config.target_response_time_ms * self.config.scale_down_threshold:
            return f"Low response time: {response_time:.2f}ms"
        
        # Request rate-based scaling
        if request_rate < 10:  # 10 requests per second threshold
            return f"Low request rate: {request_rate:.2f} req/s"
        
        return None
    
    async def _scale_up(self, load_balancer: LoadBalancer, reason: str) -> str:
        """Scale up workers"""
        try:
            # Add new worker
            new_worker_id = f"worker_{self.current_workers + 1}"
            new_worker = WorkerNode(
                node_id=new_worker_id,
                host="localhost",
                port=8000 + self.current_workers,
                weight=1
            )
            
            load_balancer.add_worker(new_worker)
            self.current_workers += 1
            
            # Record scaling event
            scaling_event = {
                "action": "scale_up",
                "reason": reason,
                "timestamp": time.time(),
                "workers_before": self.current_workers - 1,
                "workers_after": self.current_workers
            }
            self.scaling_history.append(scaling_event)
            self.scaling_metrics["scale_ups"] += 1
            self.scaling_metrics["total_scaling_events"] += 1
            self.last_scale_up = time.time()
            
            logger.info(f"Scaled up: {reason} -> {self.current_workers} workers")
            return f"Scaled up to {self.current_workers} workers: {reason}"
            
        except Exception as e:
            logger.error(f"Scale up error: {e}")
            return f"Scale up failed: {e}"
    
    async def _scale_down(self, load_balancer: LoadBalancer, reason: str) -> str:
        """Scale down workers"""
        try:
            # Remove least loaded worker
            if load_balancer.workers:
                least_loaded = min(load_balancer.workers, 
                                 key=lambda w: w.current_connections)
                
                load_balancer.remove_worker(least_loaded.node_id)
                self.current_workers -= 1
                
                # Record scaling event
                scaling_event = {
                    "action": "scale_down",
                    "reason": reason,
                    "timestamp": time.time(),
                    "workers_before": self.current_workers + 1,
                    "workers_after": self.current_workers
                }
                self.scaling_history.append(scaling_event)
                self.scaling_metrics["scale_downs"] += 1
                self.scaling_metrics["total_scaling_events"] += 1
                self.last_scale_down = time.time()
                
                logger.info(f"Scaled down: {reason} -> {self.current_workers} workers")
                return f"Scaled down to {self.current_workers} workers: {reason}"
            
            return "No workers to scale down"
            
        except Exception as e:
            logger.error(f"Scale down error: {e}")
            return f"Scale down failed: {e}"
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics"""
        return {
            "current_workers": self.current_workers,
            "min_workers": self.config.min_workers,
            "max_workers": self.config.max_workers,
            "scaling_metrics": self.scaling_metrics.copy(),
            "recent_scaling_events": self.scaling_history[-10:] if self.scaling_history else [],
            "last_scale_up": self.last_scale_up,
            "last_scale_down": self.last_scale_down
        }


class PerformanceTargetManager:
    """Performance target management"""
    
    def __init__(self):
        self.targets = {
            "response_time_ms": 500.0,
            "throughput_rps": 1000.0,
            "error_rate_percent": 0.1,
            "availability_percent": 99.9
        }
        
        self.current_performance: Dict[str, float] = {}
        self.performance_history: deque = deque(maxlen=1000)
        
    def update_performance(self, metrics: Dict[str, float]):
        """Update current performance metrics"""
        self.current_performance = metrics.copy()
        self.performance_history.append({
            **metrics,
            "timestamp": time.time()
        })
    
    def check_targets(self) -> Dict[str, Dict[str, Any]]:
        """Check if performance targets are met"""
        results = {}
        
        for target_name, target_value in self.targets.items():
            current_value = self.current_performance.get(target_name, 0.0)
            
            # Determine if target is met
            if target_name in ["response_time_ms"]:
                met = current_value <= target_value
            else:
                met = current_value >= target_value
            
            results[target_name] = {
                "target": target_value,
                "current": current_value,
                "met": met,
                "deviation": abs(current_value - target_value),
                "deviation_percent": abs(current_value - target_value) / target_value * 100
            }
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        target_results = self.check_targets()
        
        # Calculate overall performance score
        met_targets = sum(1 for result in target_results.values() if result["met"])
        total_targets = len(target_results)
        performance_score = (met_targets / total_targets * 100) if total_targets > 0 else 0
        
        return {
            "performance_score": performance_score,
            "targets": target_results,
            "current_metrics": self.current_performance.copy(),
            "recent_history": list(self.performance_history)[-10:] if self.performance_history else []
        }


class LoadBalancingManager:
    """Main load balancing and scaling manager"""
    
    def __init__(self, scaling_config: ScalingConfig):
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler(scaling_config)
        self.performance_manager = PerformanceTargetManager()
        
        # Start monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring tasks"""
        asyncio.create_task(self._monitoring_loop())
        logger.info("Load balancing monitoring started")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Collect metrics
                metrics = await self.auto_scaler.resource_monitor.collect_metrics()
                
                # Calculate request rate and response time
                request_rate = self._calculate_request_rate()
                response_time = self._calculate_average_response_time()
                
                # Update performance manager
                performance_metrics = {
                    "response_time_ms": response_time,
                    "throughput_rps": request_rate,
                    "error_rate_percent": self._calculate_error_rate(),
                    "availability_percent": self._calculate_availability()
                }
                self.performance_manager.update_performance(performance_metrics)
                
                # Evaluate scaling
                scaling_result = await self.auto_scaler.evaluate_scaling(
                    self.load_balancer, request_rate, response_time
                )
                
                if scaling_result:
                    logger.info(f"Auto-scaling: {scaling_result}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    def _calculate_request_rate(self) -> float:
        """Calculate current request rate"""
        # Simplified implementation
        return 50.0  # requests per second
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time"""
        # Simplified implementation
        return 250.0  # milliseconds
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        # Simplified implementation
        return 0.05  # 0.05%
    
    def _calculate_availability(self) -> float:
        """Calculate availability"""
        # Simplified implementation
        return 99.95  # 99.95%
    
    def get_load_balancing_status(self) -> Dict[str, Any]:
        """Get comprehensive load balancing status"""
        return {
            "load_balancer": self.load_balancer.get_load_balancer_stats(),
            "auto_scaler": self.auto_scaler.get_scaling_stats(),
            "performance": self.performance_manager.get_performance_summary(),
            "resource_monitor": {
                "current_metrics": self.auto_scaler.resource_monitor.current_metrics,
                "alerts": self.auto_scaler.resource_monitor.check_alerts()
            }
        }
