"""
Memory Optimization System for WebMCP Performance Enhancement

This module provides comprehensive memory management including:
- Automatic cleanup and garbage collection
- Memory usage monitoring and alerts
- Memory-efficient data structures
- Resource pooling and reuse
- Memory leak detection
"""

import asyncio
import gc
import logging
import psutil
import threading
import time
import weakref
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import tracemalloc
import sys

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    process_memory_mb: float = 0.0
    process_memory_rss_mb: float = 0.0
    process_memory_vms_mb: float = 0.0
    memory_percent: float = 0.0
    gc_objects: int = 0
    gc_collections: int = 0
    peak_memory_mb: float = 0.0
    memory_pressure: str = "low"


@dataclass
class MemoryAlert:
    """Memory usage alert"""
    alert_type: str
    message: str
    timestamp: float
    memory_usage_mb: float
    threshold_mb: float
    severity: str  # "low", "medium", "high", "critical"


class MemoryOptimizer:
    """
    Advanced memory optimization system with monitoring and cleanup.
    
    Features:
    - Real-time memory monitoring
    - Automatic garbage collection
    - Memory pressure detection
    - Resource cleanup
    - Memory leak detection
    - Performance optimization
    """
    
    def __init__(
        self,
        memory_limit_mb: int = 512,
        cleanup_interval_seconds: float = 30.0,
        monitoring_interval_seconds: float = 5.0,
        enable_tracemalloc: bool = True,
        gc_threshold: float = 0.8
    ):
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.enable_tracemalloc = enable_tracemalloc
        self.gc_threshold = gc_threshold
        
        # Memory monitoring
        self._stats = MemoryStats()
        self._alerts: deque = deque(maxlen=100)
        self._memory_history: deque = deque(maxlen=1000)
        
        # Cleanup tracking
        self._cleanup_callbacks: List[Callable[[], None]] = []
        self._weak_refs: Set[weakref.ref] = set()
        self._resource_pools: Dict[str, List[Any]] = defaultdict(list)
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Memory pressure levels
        self._pressure_levels = {
            "low": 0.6,      # < 60% memory usage
            "medium": 0.8,   # 60-80% memory usage
            "high": 0.9,     # 80-90% memory usage
            "critical": 1.0  # > 90% memory usage
        }
        
        # Initialize tracemalloc if enabled
        if self.enable_tracemalloc:
            tracemalloc.start()
    
    async def start(self):
        """Start memory optimization and monitoring"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("MemoryOptimizer started")
    
    async def stop(self):
        """Stop memory optimization and monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Final cleanup
        await self._perform_cleanup()
        
        if self.enable_tracemalloc:
            tracemalloc.stop()
        
        logger.info("MemoryOptimizer stopped")
    
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """Register a cleanup callback"""
        with self._lock:
            self._cleanup_callbacks.append(callback)
    
    def unregister_cleanup_callback(self, callback: Callable[[], None]):
        """Unregister a cleanup callback"""
        with self._lock:
            if callback in self._cleanup_callbacks:
                self._cleanup_callbacks.remove(callback)
    
    def track_object(self, obj: Any) -> weakref.ref:
        """Track an object with weak reference"""
        with self._lock:
            ref = weakref.ref(obj, self._on_object_deleted)
            self._weak_refs.add(ref)
            return ref
    
    def _on_object_deleted(self, ref: weakref.ref):
        """Called when a tracked object is deleted"""
        with self._lock:
            self._weak_refs.discard(ref)
    
    def get_resource_from_pool(self, pool_name: str) -> Optional[Any]:
        """Get a resource from pool"""
        with self._lock:
            if self._resource_pools[pool_name]:
                return self._resource_pools[pool_name].pop()
            return None
    
    def return_resource_to_pool(self, pool_name: str, resource: Any):
        """Return a resource to pool"""
        with self._lock:
            self._resource_pools[pool_name].append(resource)
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        with self._lock:
            return MemoryStats(
                total_memory_mb=self._stats.total_memory_mb,
                available_memory_mb=self._stats.available_memory_mb,
                process_memory_mb=self._stats.process_memory_mb,
                process_memory_rss_mb=self._stats.process_memory_rss_mb,
                process_memory_vms_mb=self._stats.process_memory_vms_mb,
                memory_percent=self._stats.memory_percent,
                gc_objects=self._stats.gc_objects,
                gc_collections=self._stats.gc_collections,
                peak_memory_mb=self._stats.peak_memory_mb,
                memory_pressure=self._stats.memory_pressure
            )
    
    def get_alerts(self, limit: int = 10) -> List[MemoryAlert]:
        """Get recent memory alerts"""
        with self._lock:
            return list(self._alerts)[-limit:]
    
    def get_memory_history(self, limit: int = 100) -> List[Dict[str, float]]:
        """Get memory usage history"""
        with self._lock:
            return list(self._memory_history)[-limit:]
    
    async def _monitoring_loop(self):
        """Background task for memory monitoring"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval_seconds)
                await self._collect_memory_stats()
                await self._check_memory_pressure()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
    
    async def _cleanup_loop(self):
        """Background task for memory cleanup"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._perform_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")
    
    async def _collect_memory_stats(self):
        """Collect current memory statistics"""
        try:
            # System memory
            memory = psutil.virtual_memory()
            self._stats.total_memory_mb = memory.total / 1024 / 1024
            self._stats.available_memory_mb = memory.available / 1024 / 1024
            self._stats.memory_percent = memory.percent
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()
            self._stats.process_memory_rss_mb = process_memory.rss / 1024 / 1024
            self._stats.process_memory_vms_mb = process_memory.vms / 1024 / 1024
            self._stats.process_memory_mb = process_memory.rss / 1024 / 1024
            
            # Update peak memory
            if self._stats.process_memory_mb > self._stats.peak_memory_mb:
                self._stats.peak_memory_mb = self._stats.process_memory_mb
            
            # Garbage collection stats
            self._stats.gc_objects = len(gc.get_objects())
            self._stats.gc_collections = sum(gc.get_stats())
            
            # Store in history
            self._memory_history.append({
                "timestamp": time.time(),
                "process_memory_mb": self._stats.process_memory_mb,
                "memory_percent": self._stats.memory_percent,
                "gc_objects": self._stats.gc_objects
            })
            
        except Exception as e:
            logger.error(f"Failed to collect memory stats: {e}")
    
    async def _check_memory_pressure(self):
        """Check memory pressure and generate alerts"""
        try:
            # Determine pressure level
            memory_usage_ratio = self._stats.process_memory_mb / (self.memory_limit_bytes / 1024 / 1024)
            
            if memory_usage_ratio < self._pressure_levels["low"]:
                pressure = "low"
            elif memory_usage_ratio < self._pressure_levels["medium"]:
                pressure = "medium"
            elif memory_usage_ratio < self._pressure_levels["high"]:
                pressure = "high"
            else:
                pressure = "critical"
            
            self._stats.memory_pressure = pressure
            
            # Generate alerts for pressure changes
            if pressure in ["high", "critical"]:
                severity = "critical" if pressure == "critical" else "high"
                alert = MemoryAlert(
                    alert_type="memory_pressure",
                    message=f"Memory pressure is {pressure}: {self._stats.process_memory_mb:.1f}MB used",
                    timestamp=time.time(),
                    memory_usage_mb=self._stats.process_memory_mb,
                    threshold_mb=self.memory_limit_bytes / 1024 / 1024,
                    severity=severity
                )
                self._alerts.append(alert)
                logger.warning(f"Memory pressure alert: {alert.message}")
            
            # Check for memory limit
            if self._stats.process_memory_mb > self.memory_limit_bytes / 1024 / 1024:
                alert = MemoryAlert(
                    alert_type="memory_limit_exceeded",
                    message=f"Memory limit exceeded: {self._stats.process_memory_mb:.1f}MB > {self.memory_limit_bytes / 1024 / 1024:.1f}MB",
                    timestamp=time.time(),
                    memory_usage_mb=self._stats.process_memory_mb,
                    threshold_mb=self.memory_limit_bytes / 1024 / 1024,
                    severity="critical"
                )
                self._alerts.append(alert)
                logger.critical(f"Memory limit exceeded: {alert.message}")
                
                # Trigger immediate cleanup
                await self._perform_emergency_cleanup()
            
        except Exception as e:
            logger.error(f"Failed to check memory pressure: {e}")
    
    async def _perform_cleanup(self):
        """Perform regular memory cleanup"""
        try:
            # Run registered cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Cleanup callback failed: {e}")
            
            # Clean up weak references
            with self._lock:
                dead_refs = [ref for ref in self._weak_refs if ref() is None]
                self._weak_refs -= set(dead_refs)
            
            # Clean up resource pools
            await self._cleanup_resource_pools()
            
            # Garbage collection
            if self._stats.memory_percent > self.gc_threshold * 100:
                collected = gc.collect()
                logger.debug(f"Garbage collection freed {collected} objects")
            
            # Memory optimization
            await self._optimize_memory_usage()
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    async def _perform_emergency_cleanup(self):
        """Perform emergency memory cleanup"""
        logger.warning("Performing emergency memory cleanup")
        
        try:
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Emergency GC freed {collected} objects")
            
            # Clear resource pools
            with self._lock:
                for pool_name in list(self._resource_pools.keys()):
                    self._resource_pools[pool_name].clear()
            
            # Run all cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Emergency cleanup callback failed: {e}")
            
            # Clear memory history (keep only recent)
            with self._lock:
                if len(self._memory_history) > 100:
                    self._memory_history = deque(list(self._memory_history)[-50:], maxlen=1000)
            
            logger.info("Emergency memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")
    
    async def _cleanup_resource_pools(self):
        """Clean up resource pools"""
        with self._lock:
            for pool_name, pool in self._resource_pools.items():
                # Limit pool size
                if len(pool) > 100:
                    excess = pool[100:]
                    pool[:] = pool[:100]
                    logger.debug(f"Trimmed {pool_name} pool, removed {len(excess)} resources")
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            # If tracemalloc is enabled, get memory snapshot
            if self.enable_tracemalloc:
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:10]
                
                # Log top memory consumers
                for stat in top_stats:
                    if stat.size / 1024 / 1024 > 1:  # Only log if > 1MB
                        logger.debug(f"Memory usage: {stat.size / 1024 / 1024:.1f}MB - {stat.traceback.format()}")
            
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
    
    def force_cleanup(self):
        """Force immediate cleanup (synchronous)"""
        try:
            # Run cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Force cleanup callback failed: {e}")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Force cleanup freed {collected} objects")
            
            # Clear weak references
            with self._lock:
                dead_refs = [ref for ref in self._weak_refs if ref() is None]
                self._weak_refs -= set(dead_refs)
            
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report"""
        stats = self.get_memory_stats()
        alerts = self.get_alerts(5)
        history = self.get_memory_history(10)
        
        return {
            "current_stats": {
                "process_memory_mb": stats.process_memory_mb,
                "memory_percent": stats.memory_percent,
                "memory_pressure": stats.memory_pressure,
                "gc_objects": stats.gc_objects,
                "peak_memory_mb": stats.peak_memory_mb
            },
            "recent_alerts": [
                {
                    "type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp,
                    "memory_usage_mb": alert.memory_usage_mb
                }
                for alert in alerts
            ],
            "memory_history": history,
            "resource_pools": {
                name: len(pool) for name, pool in self._resource_pools.items()
            },
            "cleanup_callbacks": len(self._cleanup_callbacks),
            "tracked_objects": len(self._weak_refs)
        }


# Global memory optimizer
_memory_optimizer: Optional[MemoryOptimizer] = None


async def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
        await _memory_optimizer.start()
    return _memory_optimizer


async def get_memory_stats() -> MemoryStats:
    """Get current memory statistics"""
    optimizer = await get_memory_optimizer()
    return optimizer.get_memory_stats()


async def get_memory_report() -> Dict[str, Any]:
    """Get comprehensive memory report"""
    optimizer = await get_memory_optimizer()
    return optimizer.get_memory_report()


def register_memory_cleanup(callback: Callable[[], None]):
    """Register a memory cleanup callback"""
    if _memory_optimizer:
        _memory_optimizer.register_cleanup_callback(callback)


def force_memory_cleanup():
    """Force immediate memory cleanup"""
    if _memory_optimizer:
        _memory_optimizer.force_cleanup()
