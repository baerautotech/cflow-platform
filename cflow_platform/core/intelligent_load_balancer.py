"""
Intelligent Load Balancing and Traffic Shaping System for WebMCP Performance Enhancement

This module provides sophisticated load balancing capabilities including:
- Intelligent request routing based on server health and performance
- Traffic shaping and rate limiting with QoS support
- Dynamic load balancing algorithms
- Predictive load distribution
- Advanced traffic management and prioritization
- Real-time performance-based routing decisions
"""

import asyncio
import logging
import time
import random
import math
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"


class TrafficPriority(Enum):
    """Traffic priority levels"""
    CRITICAL = "critical"               # Highest priority
    HIGH = "high"                       # High priority
    NORMAL = "normal"                   # Normal priority
    LOW = "low"                         # Low priority


class ServerStatus(Enum):
    """Server status types"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class ServerMetrics:
    """Server performance metrics"""
    server_id: str
    response_time_ms: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    total_requests: int
    error_rate: float
    throughput_rps: float
    status: ServerStatus
    last_health_check: float
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestInfo:
    """Request information for routing decisions"""
    request_id: str
    priority: TrafficPriority
    expected_duration_ms: Optional[float] = None
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    client_info: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RoutingDecision:
    """Load balancing routing decision"""
    server_id: str
    algorithm_used: LoadBalancingAlgorithm
    confidence: float
    reasoning: str
    estimated_wait_time_ms: float
    server_metrics: ServerMetrics
    timestamp: float


@dataclass
class TrafficShapingRule:
    """Traffic shaping rule definition"""
    rule_id: str
    priority: TrafficPriority
    max_requests_per_second: float
    max_concurrent_requests: int
    burst_capacity: int
    enabled: bool = True


class IntelligentLoadBalancer:
    """
    Advanced intelligent load balancer with traffic shaping capabilities.
    
    Features:
    - Multiple load balancing algorithms
    - Intelligent server selection
    - Traffic shaping and rate limiting
    - Predictive load distribution
    - QoS support with priority handling
    - Real-time performance monitoring
    """
    
    def __init__(
        self,
        default_algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ADAPTIVE,
        health_check_interval: float = 30.0,
        metrics_window: int = 100
    ):
        self.default_algorithm = default_algorithm
        self.health_check_interval = health_check_interval
        self.metrics_window = metrics_window
        
        # Server management
        self._servers: Dict[str, ServerMetrics] = {}
        self._server_metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=metrics_window)
        )
        
        # Load balancing state
        self._current_algorithm = default_algorithm
        self._round_robin_index: Dict[str, int] = defaultdict(int)
        self._connection_counts: Dict[str, int] = defaultdict(int)
        
        # Traffic shaping
        self._traffic_shaping_rules: Dict[TrafficPriority, TrafficShapingRule] = {}
        self._request_queues: Dict[TrafficPriority, asyncio.Queue] = {}
        self._rate_limiters: Dict[TrafficPriority, Dict[str, Any]] = {}
        
        # Performance tracking
        self._routing_decisions: deque = deque(maxlen=1000)
        self._performance_history: deque = deque(maxlen=metrics_window)
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._traffic_shaping_task: Optional[asyncio.Task] = None
        self._algorithm_adaptation_task: Optional[asyncio.Task] = None
        
        # Initialize traffic shaping
        self._initialize_traffic_shaping()
    
    def _initialize_traffic_shaping(self):
        """Initialize traffic shaping rules and queues"""
        # Default traffic shaping rules
        default_rules = {
            TrafficPriority.CRITICAL: TrafficShapingRule(
                rule_id="critical",
                priority=TrafficPriority.CRITICAL,
                max_requests_per_second=1000.0,
                max_concurrent_requests=500,
                burst_capacity=100
            ),
            TrafficPriority.HIGH: TrafficShapingRule(
                rule_id="high",
                priority=TrafficPriority.HIGH,
                max_requests_per_second=500.0,
                max_concurrent_requests=250,
                burst_capacity=50
            ),
            TrafficPriority.NORMAL: TrafficShapingRule(
                rule_id="normal",
                priority=TrafficPriority.NORMAL,
                max_requests_per_second=200.0,
                max_concurrent_requests=100,
                burst_capacity=20
            ),
            TrafficPriority.LOW: TrafficShapingRule(
                rule_id="low",
                priority=TrafficPriority.LOW,
                max_requests_per_second=50.0,
                max_concurrent_requests=25,
                burst_capacity=5
            )
        }
        
        for priority, rule in default_rules.items():
            self._traffic_shaping_rules[priority] = rule
            self._request_queues[priority] = asyncio.Queue()
            self._rate_limiters[priority] = {
                "last_reset": time.time(),
                "request_count": 0,
                "burst_tokens": rule.burst_capacity
            }
    
    async def start(self):
        """Start intelligent load balancer"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._traffic_shaping_task = asyncio.create_task(self._traffic_shaping_loop())
        self._algorithm_adaptation_task = asyncio.create_task(self._algorithm_adaptation_loop())
        logger.info("IntelligentLoadBalancer started")
    
    async def stop(self):
        """Stop intelligent load balancer"""
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._traffic_shaping_task:
            self._traffic_shaping_task.cancel()
        if self._algorithm_adaptation_task:
            self._algorithm_adaptation_task.cancel()
        logger.info("IntelligentLoadBalancer stopped")
    
    def add_server(self, server_id: str, initial_weight: float = 1.0):
        """Add a server to the load balancer"""
        self._servers[server_id] = ServerMetrics(
            server_id=server_id,
            response_time_ms=0.0,
            cpu_usage=0.0,
            memory_usage=0.0,
            active_connections=0,
            total_requests=0,
            error_rate=0.0,
            throughput_rps=0.0,
            status=ServerStatus.HEALTHY,
            last_health_check=time.time(),
            weight=initial_weight
        )
        logger.info(f"Added server: {server_id}")
    
    def remove_server(self, server_id: str):
        """Remove a server from the load balancer"""
        if server_id in self._servers:
            del self._servers[server_id]
            logger.info(f"Removed server: {server_id}")
    
    def update_server_metrics(self, server_id: str, metrics: Dict[str, Any]):
        """Update server performance metrics"""
        if server_id not in self._servers:
            return
        
        server = self._servers[server_id]
        
        # Update metrics
        server.response_time_ms = metrics.get("response_time_ms", server.response_time_ms)
        server.cpu_usage = metrics.get("cpu_usage", server.cpu_usage)
        server.memory_usage = metrics.get("memory_usage", server.memory_usage)
        server.active_connections = metrics.get("active_connections", server.active_connections)
        server.total_requests = metrics.get("total_requests", server.total_requests)
        server.error_rate = metrics.get("error_rate", server.error_rate)
        server.throughput_rps = metrics.get("throughput_rps", server.throughput_rps)
        server.last_health_check = time.time()
        
        # Update status based on metrics
        server.status = self._determine_server_status(server)
        
        # Store in history
        self._server_metrics_history[server_id].append(server)
        
        # Update connection counts
        self._connection_counts[server_id] = server.active_connections
    
    def _determine_server_status(self, server: ServerMetrics) -> ServerStatus:
        """Determine server status based on metrics"""
        # Critical conditions
        if (server.error_rate > 20.0 or 
            server.cpu_usage > 95.0 or 
            server.memory_usage > 95.0 or
            server.response_time_ms > 10000.0):
            return ServerStatus.UNHEALTHY
        
        # Overloaded conditions
        if (server.cpu_usage > 80.0 or 
            server.memory_usage > 80.0 or 
            server.response_time_ms > 5000.0 or
            server.active_connections > 1000):
            return ServerStatus.OVERLOADED
        
        # Degraded conditions
        if (server.cpu_usage > 60.0 or 
            server.memory_usage > 60.0 or 
            server.response_time_ms > 2000.0 or
            server.error_rate > 5.0):
            return ServerStatus.DEGRADED
        
        return ServerStatus.HEALTHY
    
    async def route_request(self, request_info: RequestInfo) -> RoutingDecision:
        """Route a request to the best available server"""
        # Apply traffic shaping
        if not await self._apply_traffic_shaping(request_info):
            # Request rejected by traffic shaping
            return RoutingDecision(
                server_id="",
                algorithm_used=self._current_algorithm,
                confidence=0.0,
                reasoning="Request rejected by traffic shaping",
                estimated_wait_time_ms=float('inf'),
                server_metrics=None,
                timestamp=time.time()
            )
        
        # Select server using load balancing algorithm
        server_id = await self._select_server(request_info)
        
        if not server_id:
            return RoutingDecision(
                server_id="",
                algorithm_used=self._current_algorithm,
                confidence=0.0,
                reasoning="No healthy servers available",
                estimated_wait_time_ms=float('inf'),
                server_metrics=None,
                timestamp=time.time()
            )
        
        server_metrics = self._servers[server_id]
        
        # Create routing decision
        decision = RoutingDecision(
            server_id=server_id,
            algorithm_used=self._current_algorithm,
            confidence=self._calculate_routing_confidence(server_metrics),
            reasoning=self._generate_routing_reasoning(server_metrics),
            estimated_wait_time_ms=self._estimate_wait_time(server_metrics),
            server_metrics=server_metrics,
            timestamp=time.time()
        )
        
        # Record routing decision
        self._routing_decisions.append(decision)
        
        # Update connection count
        self._connection_counts[server_id] += 1
        
        return decision
    
    async def _apply_traffic_shaping(self, request_info: RequestInfo) -> bool:
        """Apply traffic shaping rules to request"""
        priority = request_info.priority
        rule = self._traffic_shaping_rules.get(priority)
        
        if not rule or not rule.enabled:
            return True  # No traffic shaping applied
        
        rate_limiter = self._rate_limiters[priority]
        current_time = time.time()
        
        # Reset counters if needed
        if current_time - rate_limiter["last_reset"] >= 1.0:
            rate_limiter["request_count"] = 0
            rate_limiter["last_reset"] = current_time
        
        # Check rate limit
        if rate_limiter["request_count"] >= rule.max_requests_per_second:
            # Check burst capacity
            if rate_limiter["burst_tokens"] <= 0:
                return False  # Request rejected
            rate_limiter["burst_tokens"] -= 1
        
        rate_limiter["request_count"] += 1
        
        # Replenish burst tokens
        if current_time - rate_limiter["last_reset"] >= 1.0:
            rate_limiter["burst_tokens"] = min(
                rule.burst_capacity,
                rate_limiter["burst_tokens"] + 1
            )
        
        return True
    
    async def _select_server(self, request_info: RequestInfo) -> Optional[str]:
        """Select server using current load balancing algorithm"""
        available_servers = self._get_available_servers()
        
        if not available_servers:
            return None
        
        if self._current_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_selection(available_servers)
        elif self._current_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_selection(available_servers)
        elif self._current_algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(available_servers)
        elif self._current_algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(available_servers)
        elif self._current_algorithm == LoadBalancingAlgorithm.WEIGHTED_LEAST_CONNECTIONS:
            return self._weighted_least_connections_selection(available_servers)
        elif self._current_algorithm == LoadBalancingAlgorithm.ADAPTIVE:
            return await self._adaptive_selection(available_servers, request_info)
        elif self._current_algorithm == LoadBalancingAlgorithm.PREDICTIVE:
            return await self._predictive_selection(available_servers, request_info)
        else:
            return random.choice(available_servers)
    
    def _get_available_servers(self) -> List[str]:
        """Get list of available servers"""
        available = []
        for server_id, server in self._servers.items():
            if server.status in [ServerStatus.HEALTHY, ServerStatus.DEGRADED]:
                available.append(server_id)
        return available
    
    def _round_robin_selection(self, available_servers: List[str]) -> str:
        """Round robin server selection"""
        if not available_servers:
            return None
        
        index = self._round_robin_index["default"] % len(available_servers)
        selected_server = available_servers[index]
        self._round_robin_index["default"] += 1
        return selected_server
    
    def _least_connections_selection(self, available_servers: List[str]) -> str:
        """Least connections server selection"""
        if not available_servers:
            return None
        
        min_connections = float('inf')
        selected_server = None
        
        for server_id in available_servers:
            connections = self._connection_counts.get(server_id, 0)
            if connections < min_connections:
                min_connections = connections
                selected_server = server_id
        
        return selected_server
    
    def _least_response_time_selection(self, available_servers: List[str]) -> str:
        """Least response time server selection"""
        if not available_servers:
            return None
        
        min_response_time = float('inf')
        selected_server = None
        
        for server_id in available_servers:
            server = self._servers[server_id]
            if server.response_time_ms < min_response_time:
                min_response_time = server.response_time_ms
                selected_server = server_id
        
        return selected_server
    
    def _weighted_round_robin_selection(self, available_servers: List[str]) -> str:
        """Weighted round robin server selection"""
        if not available_servers:
            return None
        
        # Calculate total weight
        total_weight = sum(self._servers[server_id].weight for server_id in available_servers)
        
        if total_weight == 0:
            return self._round_robin_selection(available_servers)
        
        # Select based on weights
        random_value = random.random() * total_weight
        current_weight = 0.0
        
        for server_id in available_servers:
            current_weight += self._servers[server_id].weight
            if random_value <= current_weight:
                return server_id
        
        return available_servers[-1]  # Fallback
    
    def _weighted_least_connections_selection(self, available_servers: List[str]) -> str:
        """Weighted least connections server selection"""
        if not available_servers:
            return None
        
        min_weighted_connections = float('inf')
        selected_server = None
        
        for server_id in available_servers:
            connections = self._connection_counts.get(server_id, 0)
            weight = self._servers[server_id].weight
            weighted_connections = connections / max(weight, 0.1)
            
            if weighted_connections < min_weighted_connections:
                min_weighted_connections = weighted_connections
                selected_server = server_id
        
        return selected_server
    
    async def _adaptive_selection(self, available_servers: List[str], request_info: RequestInfo) -> str:
        """Adaptive server selection based on current conditions"""
        if not available_servers:
            return None
        
        # Score servers based on multiple factors
        server_scores = {}
        
        for server_id in available_servers:
            server = self._servers[server_id]
            
            # Calculate composite score
            score = 0.0
            
            # Response time score (lower is better)
            response_score = max(0, 1.0 - (server.response_time_ms / 5000.0))
            score += response_score * 0.3
            
            # CPU usage score (lower is better)
            cpu_score = max(0, 1.0 - (server.cpu_usage / 100.0))
            score += cpu_score * 0.25
            
            # Memory usage score (lower is better)
            memory_score = max(0, 1.0 - (server.memory_usage / 100.0))
            score += memory_score * 0.2
            
            # Connection count score (lower is better)
            connection_score = max(0, 1.0 - (server.active_connections / 1000.0))
            score += connection_score * 0.15
            
            # Error rate score (lower is better)
            error_score = max(0, 1.0 - (server.error_rate / 100.0))
            score += error_score * 0.1
            
            server_scores[server_id] = score
        
        # Select server with highest score
        return max(server_scores.items(), key=lambda x: x[1])[0]
    
    async def _predictive_selection(self, available_servers: List[str], request_info: RequestInfo) -> str:
        """Predictive server selection based on expected performance"""
        if not available_servers:
            return None
        
        # Predict future performance for each server
        predictions = {}
        
        for server_id in available_servers:
            server = self._servers[server_id]
            
            # Simple prediction based on current trends
            predicted_response_time = self._predict_response_time(server_id)
            predicted_cpu_usage = self._predict_cpu_usage(server_id)
            predicted_memory_usage = self._predict_memory_usage(server_id)
            
            # Calculate predicted score
            score = 0.0
            
            response_score = max(0, 1.0 - (predicted_response_time / 5000.0))
            score += response_score * 0.4
            
            cpu_score = max(0, 1.0 - (predicted_cpu_usage / 100.0))
            score += cpu_score * 0.3
            
            memory_score = max(0, 1.0 - (predicted_memory_usage / 100.0))
            score += memory_score * 0.3
            
            predictions[server_id] = score
        
        # Select server with best predicted performance
        return max(predictions.items(), key=lambda x: x[1])[0]
    
    def _predict_response_time(self, server_id: str) -> float:
        """Predict future response time for server"""
        history = list(self._server_metrics_history[server_id])
        if len(history) < 2:
            return self._servers[server_id].response_time_ms
        
        # Simple linear prediction
        recent_times = [s.response_time_ms for s in history[-5:]]
        trend = statistics.mean(recent_times[-2:]) - statistics.mean(recent_times[:2])
        
        current_time = self._servers[server_id].response_time_ms
        return max(0, current_time + trend)
    
    def _predict_cpu_usage(self, server_id: str) -> float:
        """Predict future CPU usage for server"""
        history = list(self._server_metrics_history[server_id])
        if len(history) < 2:
            return self._servers[server_id].cpu_usage
        
        recent_usage = [s.cpu_usage for s in history[-5:]]
        trend = statistics.mean(recent_usage[-2:]) - statistics.mean(recent_usage[:2])
        
        current_usage = self._servers[server_id].cpu_usage
        return max(0, min(100, current_usage + trend))
    
    def _predict_memory_usage(self, server_id: str) -> float:
        """Predict future memory usage for server"""
        history = list(self._server_metrics_history[server_id])
        if len(history) < 2:
            return self._servers[server_id].memory_usage
        
        recent_usage = [s.memory_usage for s in history[-5:]]
        trend = statistics.mean(recent_usage[-2:]) - statistics.mean(recent_usage[:2])
        
        current_usage = self._servers[server_id].memory_usage
        return max(0, min(100, current_usage + trend))
    
    def _calculate_routing_confidence(self, server_metrics: ServerMetrics) -> float:
        """Calculate confidence in routing decision"""
        # Base confidence on server health and performance
        health_score = 1.0 if server_metrics.status == ServerStatus.HEALTHY else 0.5
        
        performance_score = 1.0
        if server_metrics.response_time_ms > 1000:
            performance_score -= 0.2
        if server_metrics.cpu_usage > 80:
            performance_score -= 0.2
        if server_metrics.memory_usage > 80:
            performance_score -= 0.2
        if server_metrics.error_rate > 5:
            performance_score -= 0.2
        
        return max(0.0, min(1.0, health_score * performance_score))
    
    def _generate_routing_reasoning(self, server_metrics: ServerMetrics) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasons = []
        
        if server_metrics.status == ServerStatus.HEALTHY:
            reasons.append("server is healthy")
        elif server_metrics.status == ServerStatus.DEGRADED:
            reasons.append("server is degraded but functional")
        
        if server_metrics.response_time_ms < 500:
            reasons.append("low response time")
        elif server_metrics.response_time_ms < 1000:
            reasons.append("moderate response time")
        
        if server_metrics.cpu_usage < 50:
            reasons.append("low CPU usage")
        elif server_metrics.cpu_usage < 80:
            reasons.append("moderate CPU usage")
        
        if server_metrics.active_connections < 100:
            reasons.append("low connection count")
        
        return f"Selected because: {', '.join(reasons)}" if reasons else "Selected by algorithm"
    
    def _estimate_wait_time(self, server_metrics: ServerMetrics) -> float:
        """Estimate wait time for request"""
        # Simple estimation based on current load
        base_time = server_metrics.response_time_ms
        
        # Adjust based on CPU usage
        if server_metrics.cpu_usage > 80:
            base_time *= 2.0
        elif server_metrics.cpu_usage > 60:
            base_time *= 1.5
        
        # Adjust based on connection count
        if server_metrics.active_connections > 500:
            base_time *= 1.5
        elif server_metrics.active_connections > 200:
            base_time *= 1.2
        
        return base_time
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Update server status based on metrics
                for server_id, server in self._servers.items():
                    # Check if server is responding
                    if time.time() - server.last_health_check > self.health_check_interval * 2:
                        server.status = ServerStatus.UNHEALTHY
                    else:
                        server.status = self._determine_server_status(server)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _traffic_shaping_loop(self):
        """Background traffic shaping loop"""
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                # Process request queues for each priority
                for priority in TrafficPriority:
                    await self._process_request_queue(priority)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Traffic shaping loop error: {e}")
    
    async def _process_request_queue(self, priority: TrafficPriority):
        """Process requests in priority queue"""
        queue = self._request_queues.get(priority)
        if not queue:
            return
        
        # Process up to burst capacity requests
        rule = self._traffic_shaping_rules.get(priority)
        if not rule:
            return
        
        for _ in range(min(rule.burst_capacity, queue.qsize())):
            try:
                request_info = await asyncio.wait_for(queue.get(), timeout=0.1)
                # Route the request
                await self.route_request(request_info)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    async def _algorithm_adaptation_loop(self):
        """Background algorithm adaptation loop"""
        while True:
            try:
                await asyncio.sleep(300.0)  # Adapt every 5 minutes
                
                # Analyze recent performance
                performance = self._analyze_performance()
                
                # Adapt algorithm based on performance
                new_algorithm = self._select_optimal_algorithm(performance)
                
                if new_algorithm != self._current_algorithm:
                    logger.info(f"Adapting load balancing algorithm: {self._current_algorithm.value} -> {new_algorithm.value}")
                    self._current_algorithm = new_algorithm
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Algorithm adaptation loop error: {e}")
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze recent load balancing performance"""
        if not self._routing_decisions:
            return {}
        
        recent_decisions = list(self._routing_decisions)[-100:]  # Last 100 decisions
        
        # Calculate average confidence
        avg_confidence = statistics.mean([d.confidence for d in recent_decisions])
        
        # Calculate average wait time
        avg_wait_time = statistics.mean([d.estimated_wait_time_ms for d in recent_decisions])
        
        # Analyze server distribution
        server_distribution = defaultdict(int)
        for decision in recent_decisions:
            server_distribution[decision.server_id] += 1
        
        return {
            "average_confidence": avg_confidence,
            "average_wait_time": avg_wait_time,
            "server_distribution": dict(server_distribution),
            "total_decisions": len(recent_decisions)
        }
    
    def _select_optimal_algorithm(self, performance: Dict[str, Any]) -> LoadBalancingAlgorithm:
        """Select optimal load balancing algorithm based on performance"""
        if not performance:
            return self._current_algorithm
        
        avg_confidence = performance.get("average_confidence", 0.5)
        avg_wait_time = performance.get("average_wait_time", 1000.0)
        
        # If performance is poor, try different algorithms
        if avg_confidence < 0.6 or avg_wait_time > 2000.0:
            if self._current_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return LoadBalancingAlgorithm.LEAST_CONNECTIONS
            elif self._current_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return LoadBalancingAlgorithm.ADAPTIVE
            elif self._current_algorithm == LoadBalancingAlgorithm.ADAPTIVE:
                return LoadBalancingAlgorithm.PREDICTIVE
            else:
                return LoadBalancingAlgorithm.ROUND_ROBIN
        
        return self._current_algorithm
    
    def get_server_status(self) -> Dict[str, ServerMetrics]:
        """Get current server status"""
        return self._servers.copy()
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        total_servers = len(self._servers)
        healthy_servers = sum(1 for s in self._servers.values() if s.status == ServerStatus.HEALTHY)
        
        return {
            "total_servers": total_servers,
            "healthy_servers": healthy_servers,
            "current_algorithm": self._current_algorithm.value,
            "total_routing_decisions": len(self._routing_decisions),
            "traffic_shaping_rules": len(self._traffic_shaping_rules),
            "connection_counts": dict(self._connection_counts)
        }


# Global intelligent load balancer
_intelligent_load_balancer: Optional[IntelligentLoadBalancer] = None


async def get_intelligent_load_balancer() -> IntelligentLoadBalancer:
    """Get the global intelligent load balancer"""
    global _intelligent_load_balancer
    if _intelligent_load_balancer is None:
        _intelligent_load_balancer = IntelligentLoadBalancer()
        await _intelligent_load_balancer.start()
    return _intelligent_load_balancer


async def route_request(
    request_id: str,
    priority: TrafficPriority = TrafficPriority.NORMAL,
    expected_duration_ms: Optional[float] = None,
    resource_requirements: Dict[str, float] = None,
    client_info: Dict[str, Any] = None
) -> RoutingDecision:
    """Route a request using intelligent load balancing"""
    balancer = await get_intelligent_load_balancer()
    
    request_info = RequestInfo(
        request_id=request_id,
        priority=priority,
        expected_duration_ms=expected_duration_ms,
        resource_requirements=resource_requirements or {},
        client_info=client_info or {}
    )
    
    return await balancer.route_request(request_info)
