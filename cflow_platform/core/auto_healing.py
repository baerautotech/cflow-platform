"""
Auto-Healing and Service Recovery System for WebMCP Performance Enhancement

This module provides automatic service recovery capabilities including:
- Service health monitoring and automatic recovery
- Resource scaling and optimization
- Automatic failover and load balancing
- Service restart and recovery strategies
- Performance-based auto-tuning
- Proactive issue detection and resolution
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import psutil

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Service recovery strategies"""
    RESTART = "restart"                 # Restart the service
    SCALE_UP = "scale_up"               # Scale up resources
    FAILOVER = "failover"               # Failover to backup
    RESET_CONNECTIONS = "reset_connections"  # Reset connections
    CLEAR_CACHE = "clear_cache"         # Clear caches
    OPTIMIZE_CONFIG = "optimize_config"  # Optimize configuration


class HealthLevel(Enum):
    """Health levels for auto-healing decisions"""
    CRITICAL = "critical"               # Immediate action required
    DEGRADED = "degraded"               # Performance issues
    WARNING = "warning"                 # Potential issues
    HEALTHY = "healthy"                 # Normal operation


@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    health_level: HealthLevel
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    last_check: float = 0.0
    consecutive_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Recovery action definition"""
    action_id: str
    service_name: str
    strategy: RecoveryStrategy
    triggered_by: str
    timestamp: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class AutoHealingRule:
    """Auto-healing rule definition"""
    rule_id: str
    service_name: str
    condition: str                     # Health condition to trigger
    strategy: RecoveryStrategy
    cooldown_seconds: float = 300.0    # Minimum time between actions
    max_actions_per_hour: int = 5      # Rate limiting
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


class AutoHealingManager:
    """
    Automatic service recovery and healing manager.
    
    Features:
    - Service health monitoring
    - Automatic recovery actions
    - Recovery strategy selection
    - Action history and tracking
    - Performance optimization
    - Proactive issue detection
    """
    
    def __init__(self, check_interval_seconds: float = 30.0):
        self.check_interval_seconds = check_interval_seconds
        
        # Service monitoring
        self._service_health: Dict[str, ServiceHealth] = {}
        self._health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Auto-healing rules
        self._healing_rules: Dict[str, AutoHealingRule] = {}
        self._rule_last_triggered: Dict[str, float] = {}
        self._rule_action_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))  # Last hour
        
        # Recovery actions
        self._recovery_actions: List[RecoveryAction] = []
        self._active_recoveries: Dict[str, asyncio.Task] = {}
        
        # Recovery strategies
        self._recovery_strategies: Dict[RecoveryStrategy, Callable] = {
            RecoveryStrategy.RESTART: self._restart_service,
            RecoveryStrategy.SCALE_UP: self._scale_up_service,
            RecoveryStrategy.FAILOVER: self._failover_service,
            RecoveryStrategy.RESET_CONNECTIONS: self._reset_connections,
            RecoveryStrategy.CLEAR_CACHE: self._clear_cache,
            RecoveryStrategy.OPTIMIZE_CONFIG: self._optimize_config
        }
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._healing_task: Optional[asyncio.Task] = None
        
        # System resources
        self._system_resources = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total
        }
    
    async def start(self):
        """Start auto-healing manager"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._healing_task = asyncio.create_task(self._healing_loop())
        logger.info("AutoHealingManager started")
    
    async def stop(self):
        """Stop auto-healing manager"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._healing_task:
            self._healing_task.cancel()
        
        # Cancel active recoveries
        for task in self._active_recoveries.values():
            task.cancel()
        
        logger.info("AutoHealingManager stopped")
    
    def register_service(self, service_name: str, health_check_func: Callable[[], Awaitable[Dict[str, Any]]]):
        """Register a service for auto-healing"""
        self._service_health[service_name] = ServiceHealth(
            service_name=service_name,
            health_level=HealthLevel.HEALTHY,
            last_check=time.time()
        )
        
        # Store health check function
        setattr(self, f"_health_check_{service_name}", health_check_func)
        logger.info(f"Registered service for auto-healing: {service_name}")
    
    def add_healing_rule(self, rule: AutoHealingRule):
        """Add an auto-healing rule"""
        self._healing_rules[rule.rule_id] = rule
        logger.info(f"Added auto-healing rule: {rule.rule_id}")
    
    def remove_healing_rule(self, rule_id: str):
        """Remove an auto-healing rule"""
        if rule_id in self._healing_rules:
            del self._healing_rules[rule_id]
            logger.info(f"Removed auto-healing rule: {rule_id}")
    
    async def _monitoring_loop(self):
        """Background service monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.check_interval_seconds)
                
                # Check all registered services
                for service_name in self._service_health:
                    await self._check_service_health(service_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Service monitoring error: {e}")
    
    async def _healing_loop(self):
        """Background auto-healing loop"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                # Evaluate healing rules
                await self._evaluate_healing_rules()
                
                # Clean up completed recoveries
                await self._cleanup_completed_recoveries()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-healing loop error: {e}")
    
    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        try:
            # Get health check function
            health_check_func = getattr(self, f"_health_check_{service_name}", None)
            if not health_check_func:
                logger.warning(f"No health check function for service: {service_name}")
                return
            
            # Execute health check
            health_data = await health_check_func()
            
            # Update service health
            health = self._service_health[service_name]
            health.cpu_usage = health_data.get("cpu_usage", 0.0)
            health.memory_usage = health_data.get("memory_usage", 0.0)
            health.response_time_ms = health_data.get("response_time_ms", 0.0)
            health.error_rate = health_data.get("error_rate", 0.0)
            health.throughput = health_data.get("throughput", 0.0)
            health.last_check = time.time()
            health.metadata = health_data
            
            # Determine health level
            health.health_level = self._determine_health_level(health)
            
            # Update consecutive failures
            if health.health_level in [HealthLevel.CRITICAL, HealthLevel.DEGRADED]:
                health.consecutive_failures += 1
            else:
                health.consecutive_failures = 0
            
            # Store in history
            self._health_history[service_name].append(health)
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            
            # Update health as critical
            health = self._service_health[service_name]
            health.health_level = HealthLevel.CRITICAL
            health.consecutive_failures += 1
            health.last_check = time.time()
            health.metadata = {"error": str(e)}
    
    def _determine_health_level(self, health: ServiceHealth) -> HealthLevel:
        """Determine health level based on metrics"""
        # Critical conditions
        if (health.cpu_usage > 95.0 or 
            health.memory_usage > 95.0 or 
            health.error_rate > 20.0 or
            health.response_time_ms > 10000.0):
            return HealthLevel.CRITICAL
        
        # Degraded conditions
        if (health.cpu_usage > 80.0 or 
            health.memory_usage > 80.0 or 
            health.error_rate > 10.0 or
            health.response_time_ms > 5000.0):
            return HealthLevel.DEGRADED
        
        # Warning conditions
        if (health.cpu_usage > 60.0 or 
            health.memory_usage > 60.0 or 
            health.error_rate > 5.0 or
            health.response_time_ms > 2000.0):
            return HealthLevel.WARNING
        
        return HealthLevel.HEALTHY
    
    async def _evaluate_healing_rules(self):
        """Evaluate all auto-healing rules"""
        current_time = time.time()
        
        for rule_id, rule in self._healing_rules.items():
            if not rule.enabled:
                continue
            
            service_name = rule.service_name
            if service_name not in self._service_health:
                continue
            
            health = self._service_health[service_name]
            
            # Check if rule condition is met
            if self._evaluate_condition(health, rule.condition):
                # Check cooldown
                if current_time - self._rule_last_triggered.get(rule_id, 0) < rule.cooldown_seconds:
                    continue
                
                # Check rate limiting
                if self._is_rate_limited(rule_id, rule.max_actions_per_hour):
                    continue
                
                # Trigger recovery action
                await self._trigger_recovery_action(rule)
                
                # Update tracking
                self._rule_last_triggered[rule_id] = current_time
                self._rule_action_counts[rule_id].append(current_time)
    
    def _evaluate_condition(self, health: ServiceHealth, condition: str) -> bool:
        """Evaluate a health condition"""
        try:
            # Simple condition evaluation
            # In a real implementation, this would be more sophisticated
            
            if condition == "critical":
                return health.health_level == HealthLevel.CRITICAL
            elif condition == "degraded":
                return health.health_level in [HealthLevel.CRITICAL, HealthLevel.DEGRADED]
            elif condition == "high_cpu":
                return health.cpu_usage > 80.0
            elif condition == "high_memory":
                return health.memory_usage > 80.0
            elif condition == "high_error_rate":
                return health.error_rate > 10.0
            elif condition == "slow_response":
                return health.response_time_ms > 5000.0
            elif condition == "consecutive_failures":
                return health.consecutive_failures >= 3
            else:
                return False
                
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    def _is_rate_limited(self, rule_id: str, max_actions_per_hour: int) -> bool:
        """Check if rule is rate limited"""
        current_time = time.time()
        hour_ago = current_time - 3600.0
        
        # Count actions in the last hour
        recent_actions = [
            timestamp for timestamp in self._rule_action_counts[rule_id]
            if timestamp > hour_ago
        ]
        
        return len(recent_actions) >= max_actions_per_hour
    
    async def _trigger_recovery_action(self, rule: AutoHealingRule):
        """Trigger a recovery action"""
        action_id = f"{rule.rule_id}_{int(time.time())}"
        
        logger.info(f"Triggering recovery action: {action_id} for {rule.service_name}")
        
        # Create recovery action
        action = RecoveryAction(
            action_id=action_id,
            service_name=rule.service_name,
            strategy=rule.strategy,
            triggered_by=rule.rule_id,
            timestamp=time.time(),
            parameters=rule.parameters
        )
        
        self._recovery_actions.append(action)
        
        # Execute recovery action
        recovery_task = asyncio.create_task(
            self._execute_recovery_action(action)
        )
        self._active_recoveries[action_id] = recovery_task
    
    async def _execute_recovery_action(self, action: RecoveryAction):
        """Execute a recovery action"""
        start_time = time.time()
        
        try:
            # Get recovery strategy function
            strategy_func = self._recovery_strategies.get(action.strategy)
            if not strategy_func:
                raise ValueError(f"Unknown recovery strategy: {action.strategy}")
            
            # Execute strategy
            await strategy_func(action)
            
            # Mark as successful
            action.success = True
            action.execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Recovery action {action.action_id} completed successfully")
            
        except Exception as e:
            # Mark as failed
            action.success = False
            action.error_message = str(e)
            action.execution_time_ms = (time.time() - start_time) * 1000
            
            logger.error(f"Recovery action {action.action_id} failed: {e}")
    
    async def _restart_service(self, action: RecoveryAction):
        """Restart service recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Restarting service: {service_name}")
        
        # In a real implementation, this would restart the actual service
        # For now, we'll simulate the restart
        await asyncio.sleep(2.0)  # Simulate restart time
        
        # Reset consecutive failures
        if service_name in self._service_health:
            self._service_health[service_name].consecutive_failures = 0
    
    async def _scale_up_service(self, action: RecoveryAction):
        """Scale up service recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Scaling up service: {service_name}")
        
        # In a real implementation, this would scale up resources
        # For now, we'll simulate the scaling
        await asyncio.sleep(1.0)  # Simulate scaling time
        
        # Update system resources (simulated)
        self._system_resources["cpu_count"] += 1
    
    async def _failover_service(self, action: RecoveryAction):
        """Failover service recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Failing over service: {service_name}")
        
        # In a real implementation, this would failover to backup
        # For now, we'll simulate the failover
        await asyncio.sleep(3.0)  # Simulate failover time
    
    async def _reset_connections(self, action: RecoveryAction):
        """Reset connections recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Resetting connections for service: {service_name}")
        
        # In a real implementation, this would reset connections
        # For now, we'll simulate the reset
        await asyncio.sleep(0.5)  # Simulate reset time
    
    async def _clear_cache(self, action: RecoveryAction):
        """Clear cache recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Clearing cache for service: {service_name}")
        
        # Clear cache using the intelligent cache system
        try:
            from .intelligent_cache import invalidate_cache
            await invalidate_cache(pattern=f"{service_name}*")
        except Exception as e:
            logger.warning(f"Cache clearing failed: {e}")
        
        await asyncio.sleep(0.2)  # Simulate cache clearing time
    
    async def _optimize_config(self, action: RecoveryAction):
        """Optimize configuration recovery strategy"""
        service_name = action.service_name
        
        logger.info(f"Optimizing configuration for service: {service_name}")
        
        # In a real implementation, this would optimize configuration
        # For now, we'll simulate the optimization
        await asyncio.sleep(1.5)  # Simulate optimization time
    
    async def _cleanup_completed_recoveries(self):
        """Clean up completed recovery actions"""
        completed_actions = []
        
        for action_id, task in list(self._active_recoveries.items()):
            if task.done():
                completed_actions.append(action_id)
        
        for action_id in completed_actions:
            del self._active_recoveries[action_id]
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health status for a service"""
        return self._service_health.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health status for all services"""
        return self._service_health.copy()
    
    def get_recovery_actions(self, limit: int = 50) -> List[RecoveryAction]:
        """Get recent recovery actions"""
        return self._recovery_actions[-limit:] if self._recovery_actions else []
    
    def get_healing_rules(self) -> Dict[str, AutoHealingRule]:
        """Get all healing rules"""
        return self._healing_rules.copy()
    
    def get_auto_healing_stats(self) -> Dict[str, Any]:
        """Get auto-healing statistics"""
        total_actions = len(self._recovery_actions)
        successful_actions = sum(1 for action in self._recovery_actions if action.success)
        
        return {
            "total_recovery_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": total_actions - successful_actions,
            "success_rate": successful_actions / max(total_actions, 1),
            "active_recoveries": len(self._active_recoveries),
            "registered_services": len(self._service_health),
            "healing_rules": len(self._healing_rules),
            "enabled_rules": sum(1 for rule in self._healing_rules.values() if rule.enabled)
        }


# Global auto-healing manager
_auto_healing_manager: Optional[AutoHealingManager] = None


async def get_auto_healing_manager() -> AutoHealingManager:
    """Get the global auto-healing manager"""
    global _auto_healing_manager
    if _auto_healing_manager is None:
        _auto_healing_manager = AutoHealingManager()
        await _auto_healing_manager.start()
    return _auto_healing_manager


async def register_service_for_auto_healing(
    service_name: str,
    health_check_func: Callable[[], Awaitable[Dict[str, Any]]]
):
    """Register a service for auto-healing"""
    manager = await get_auto_healing_manager()
    manager.register_service(service_name, health_check_func)


async def add_auto_healing_rule(rule: AutoHealingRule):
    """Add an auto-healing rule"""
    manager = await get_auto_healing_manager()
    manager.add_healing_rule(rule)


async def get_auto_healing_stats() -> Dict[str, Any]:
    """Get auto-healing statistics"""
    manager = await get_auto_healing_manager()
    return manager.get_auto_healing_stats()
