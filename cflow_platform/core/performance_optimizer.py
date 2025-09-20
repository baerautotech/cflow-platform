"""
Performance Optimization System

This module provides comprehensive performance optimization for the master tool system
after legacy tool removal, including caching optimization, resource cleanup, and
performance monitoring.
"""

import asyncio
import logging
import time
import gc
import psutil
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

from .performance_cache import PerformanceCache, CacheConfig
from .async_tool_executor import AsyncToolExecutor
from .load_balancer import LoadBalancer, LoadBalancerConfig
from .master_tool_base import MasterToolManager

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of performance optimizations"""
    CACHE_OPTIMIZATION = "cache_optimization"
    MEMORY_OPTIMIZATION = "memory_optimization"
    CPU_OPTIMIZATION = "cpu_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"
    DATABASE_OPTIMIZATION = "database_optimization"
    CONCURRENCY_OPTIMIZATION = "concurrency_optimization"


@dataclass
class OptimizationResult:
    """Result of performance optimization"""
    optimization_type: OptimizationType
    success: bool
    performance_improvement: float
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    optimization_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    network_io: Dict[str, float]
    cache_hit_rate: float
    cache_size: int
    active_connections: int
    response_time_avg: float
    throughput: float


class PerformanceOptimizer:
    """Comprehensive performance optimization system"""
    
    def __init__(self, master_tool_manager: MasterToolManager):
        self.master_tool_manager = master_tool_manager
        self.optimization_history: List[OptimizationResult] = []
        self.performance_metrics_history: List[PerformanceMetrics] = []
        
        # Performance components
        self.performance_cache = PerformanceCache(CacheConfig())
        self.async_executor = AsyncToolExecutor()
        self.load_balancer = LoadBalancer(LoadBalancerConfig())
        
        # Optimization thresholds
        self.optimization_thresholds = {
            "cpu_usage": 70.0,  # Trigger optimization if CPU > 70%
            "memory_usage": 80.0,  # Trigger optimization if memory > 80%
            "cache_hit_rate": 85.0,  # Trigger optimization if cache hit rate < 85%
            "response_time": 500.0,  # Trigger optimization if response time > 500ms
            "memory_leak_threshold": 100 * 1024 * 1024  # 100MB memory increase
        }
        
        # Optimization configuration
        self.optimization_config = {
            "cache_ttl_multiplier": 1.5,  # Increase cache TTL by 50%
            "cache_size_limit": 1000,  # Maximum cache entries
            "memory_cleanup_threshold": 0.8,  # Cleanup memory when usage > 80%
            "concurrency_limit": 100,  # Maximum concurrent operations
            "batch_size": 50  # Batch processing size
        }
    
    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Cache metrics
            cache_stats = self.performance_cache.get_cache_stats()
            
            # Master tool metrics
            master_tool_stats = self.master_tool_manager.get_manager_stats()
            
            # Load balancer metrics
            load_balancer_stats = self.load_balancer.get_stats()
            
            metrics = PerformanceMetrics(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                memory_available=memory.available / (1024 * 1024),  # MB
                disk_usage=(disk.used / disk.total) * 100,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                cache_size=cache_stats.get("size", 0),
                active_connections=load_balancer_stats.get("total_requests", 0),
                response_time_avg=master_tool_stats.get("average_execution_time", 0.0),
                throughput=master_tool_stats.get("throughput", 0.0)
            )
            
            # Store metrics history
            self.performance_metrics_history.append(metrics)
            if len(self.performance_metrics_history) > 100:  # Keep last 100 metrics
                self.performance_metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            raise
    
    async def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance bottlenecks and recommend optimizations"""
        try:
            current_metrics = await self.collect_performance_metrics()
            
            bottlenecks = []
            recommendations = []
            
            # CPU bottleneck analysis
            if current_metrics.cpu_usage > self.optimization_thresholds["cpu_usage"]:
                bottlenecks.append({
                    "type": "cpu",
                    "severity": "high" if current_metrics.cpu_usage > 90 else "medium",
                    "current_value": current_metrics.cpu_usage,
                    "threshold": self.optimization_thresholds["cpu_usage"]
                })
                recommendations.append({
                    "optimization_type": OptimizationType.CPU_OPTIMIZATION,
                    "description": "Optimize CPU usage through caching and async processing",
                    "priority": "high"
                })
            
            # Memory bottleneck analysis
            if current_metrics.memory_usage > self.optimization_thresholds["memory_usage"]:
                bottlenecks.append({
                    "type": "memory",
                    "severity": "high" if current_metrics.memory_usage > 95 else "medium",
                    "current_value": current_metrics.memory_usage,
                    "threshold": self.optimization_thresholds["memory_usage"]
                })
                recommendations.append({
                    "optimization_type": OptimizationType.MEMORY_OPTIMIZATION,
                    "description": "Optimize memory usage through cleanup and caching",
                    "priority": "high"
                })
            
            # Cache performance analysis
            if current_metrics.cache_hit_rate < self.optimization_thresholds["cache_hit_rate"]:
                bottlenecks.append({
                    "type": "cache",
                    "severity": "medium",
                    "current_value": current_metrics.cache_hit_rate,
                    "threshold": self.optimization_thresholds["cache_hit_rate"]
                })
                recommendations.append({
                    "optimization_type": OptimizationType.CACHE_OPTIMIZATION,
                    "description": "Optimize cache configuration and TTL",
                    "priority": "medium"
                })
            
            # Response time analysis
            if current_metrics.response_time_avg > self.optimization_thresholds["response_time"]:
                bottlenecks.append({
                    "type": "response_time",
                    "severity": "high" if current_metrics.response_time_avg > 1000 else "medium",
                    "current_value": current_metrics.response_time_avg,
                    "threshold": self.optimization_thresholds["response_time"]
                })
                recommendations.append({
                    "optimization_type": OptimizationType.CONCURRENCY_OPTIMIZATION,
                    "description": "Optimize concurrency and async processing",
                    "priority": "high"
                })
            
            # Memory leak detection
            if len(self.performance_metrics_history) >= 5:
                recent_memory = [m.memory_usage for m in self.performance_metrics_history[-5:]]
                memory_trend = statistics.mean(recent_memory) - statistics.mean([m.memory_usage for m in self.performance_metrics_history[-10:-5]])
                
                if memory_trend > 5:  # 5% increase
                    bottlenecks.append({
                        "type": "memory_leak",
                        "severity": "medium",
                        "current_value": memory_trend,
                        "threshold": 5.0
                    })
                    recommendations.append({
                        "optimization_type": OptimizationType.MEMORY_OPTIMIZATION,
                        "description": "Address potential memory leak",
                        "priority": "medium"
                    })
            
            return {
                "analysis_timestamp": current_metrics.timestamp,
                "bottlenecks": bottlenecks,
                "recommendations": recommendations,
                "overall_health": "good" if len(bottlenecks) == 0 else "needs_attention",
                "current_metrics": {
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "cache_hit_rate": current_metrics.cache_hit_rate,
                    "response_time_avg": current_metrics.response_time_avg
                }
            }
            
        except Exception as e:
            logger.error(f"Performance bottleneck analysis failed: {e}")
            return {
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "bottlenecks": [],
                "recommendations": [],
                "overall_health": "unknown",
                "error": str(e)
            }
    
    async def optimize_cache_performance(self) -> OptimizationResult:
        """Optimize cache performance"""
        start_time = time.time()
        
        try:
            # Collect before metrics
            before_metrics = await self.collect_performance_metrics()
            
            # Optimize cache configuration
            cache_optimizations = []
            
            # Increase cache TTL for frequently accessed operations
            cache_config = self.performance_cache.config
            new_ttl = int(cache_config.default_ttl * self.optimization_config["cache_ttl_multiplier"])
            cache_config.default_ttl = new_ttl
            cache_optimizations.append(f"Increased default TTL to {new_ttl}s")
            
            # Optimize cache size
            current_cache_size = before_metrics.cache_size
            if current_cache_size > self.optimization_config["cache_size_limit"]:
                # Clean up old cache entries
                cleaned_entries = await self.performance_cache.cleanup_old_entries()
                cache_optimizations.append(f"Cleaned up {cleaned_entries} old cache entries")
            
            # Optimize cache hit rate
            if before_metrics.cache_hit_rate < self.optimization_thresholds["cache_hit_rate"]:
                # Pre-warm cache with frequently accessed operations
                pre_warmed = await self._pre_warm_cache()
                cache_optimizations.append(f"Pre-warmed cache with {pre_warmed} operations")
            
            # Collect after metrics
            await asyncio.sleep(1)  # Allow metrics to stabilize
            after_metrics = await self.collect_performance_metrics()
            
            # Calculate performance improvement
            performance_improvement = (
                (after_metrics.cache_hit_rate - before_metrics.cache_hit_rate) / 
                before_metrics.cache_hit_rate * 100
            ) if before_metrics.cache_hit_rate > 0 else 0
            
            optimization_time = time.time() - start_time
            
            result = OptimizationResult(
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                success=True,
                performance_improvement=performance_improvement,
                before_metrics={
                    "cache_hit_rate": before_metrics.cache_hit_rate,
                    "cache_size": before_metrics.cache_size,
                    "response_time": before_metrics.response_time_avg
                },
                after_metrics={
                    "cache_hit_rate": after_metrics.cache_hit_rate,
                    "cache_size": after_metrics.cache_size,
                    "response_time": after_metrics.response_time_avg
                },
                optimization_time=optimization_time,
                metadata={
                    "optimizations_applied": cache_optimizations,
                    "ttl_multiplier": self.optimization_config["cache_ttl_multiplier"]
                }
            )
            
            self.optimization_history.append(result)
            logger.info(f"Cache optimization completed: {performance_improvement:.2f}% improvement")
            return result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            logger.error(f"Cache optimization failed: {e}")
            
            return OptimizationResult(
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                success=False,
                performance_improvement=0.0,
                before_metrics={},
                after_metrics={},
                optimization_time=optimization_time,
                error=str(e)
            )
    
    async def optimize_memory_usage(self) -> OptimizationResult:
        """Optimize memory usage"""
        start_time = time.time()
        
        try:
            # Collect before metrics
            before_metrics = await self.collect_performance_metrics()
            
            memory_optimizations = []
            
            # Force garbage collection
            collected_objects = gc.collect()
            memory_optimizations.append(f"Garbage collected {collected_objects} objects")
            
            # Clean up cache if memory usage is high
            if before_metrics.memory_usage > self.optimization_config["memory_cleanup_threshold"] * 100:
                cleaned_cache = await self.performance_cache.cleanup_old_entries()
                memory_optimizations.append(f"Cleaned up {cleaned_cache} cache entries")
            
            # Optimize master tool memory usage
            master_tool_optimizations = await self._optimize_master_tool_memory()
            memory_optimizations.extend(master_tool_optimizations)
            
            # Collect after metrics
            await asyncio.sleep(1)
            after_metrics = await self.collect_performance_metrics()
            
            # Calculate memory improvement
            memory_improvement = before_metrics.memory_usage - after_metrics.memory_usage
            
            optimization_time = time.time() - start_time
            
            result = OptimizationResult(
                optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                success=True,
                performance_improvement=memory_improvement,
                before_metrics={
                    "memory_usage": before_metrics.memory_usage,
                    "memory_available": before_metrics.memory_available
                },
                after_metrics={
                    "memory_usage": after_metrics.memory_usage,
                    "memory_available": after_metrics.memory_available
                },
                optimization_time=optimization_time,
                metadata={
                    "optimizations_applied": memory_optimizations,
                    "garbage_collected": collected_objects
                }
            )
            
            self.optimization_history.append(result)
            logger.info(f"Memory optimization completed: {memory_improvement:.2f}% improvement")
            return result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            logger.error(f"Memory optimization failed: {e}")
            
            return OptimizationResult(
                optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                success=False,
                performance_improvement=0.0,
                before_metrics={},
                after_metrics={},
                optimization_time=optimization_time,
                error=str(e)
            )
    
    async def optimize_concurrency(self) -> OptimizationResult:
        """Optimize concurrency and async processing"""
        start_time = time.time()
        
        try:
            # Collect before metrics
            before_metrics = await self.collect_performance_metrics()
            
            concurrency_optimizations = []
            
            # Optimize async executor configuration
            executor_config = self.async_executor.config
            if executor_config.max_concurrent_operations < self.optimization_config["concurrency_limit"]:
                executor_config.max_concurrent_operations = self.optimization_config["concurrency_limit"]
                concurrency_optimizations.append(f"Increased max concurrent operations to {self.optimization_config['concurrency_limit']}")
            
            # Optimize batch processing
            batch_size = self.optimization_config["batch_size"]
            concurrency_optimizations.append(f"Optimized batch processing size to {batch_size}")
            
            # Optimize load balancer configuration
            load_balancer_config = self.load_balancer.config
            if load_balancer_config.max_workers < 4:
                load_balancer_config.max_workers = 4
                concurrency_optimizations.append("Increased load balancer workers to 4")
            
            # Collect after metrics
            await asyncio.sleep(1)
            after_metrics = await self.collect_performance_metrics()
            
            # Calculate performance improvement
            response_time_improvement = (
                (before_metrics.response_time_avg - after_metrics.response_time_avg) / 
                before_metrics.response_time_avg * 100
            ) if before_metrics.response_time_avg > 0 else 0
            
            optimization_time = time.time() - start_time
            
            result = OptimizationResult(
                optimization_type=OptimizationType.CONCURRENCY_OPTIMIZATION,
                success=True,
                performance_improvement=response_time_improvement,
                before_metrics={
                    "response_time_avg": before_metrics.response_time_avg,
                    "active_connections": before_metrics.active_connections,
                    "throughput": before_metrics.throughput
                },
                after_metrics={
                    "response_time_avg": after_metrics.response_time_avg,
                    "active_connections": after_metrics.active_connections,
                    "throughput": after_metrics.throughput
                },
                optimization_time=optimization_time,
                metadata={
                    "optimizations_applied": concurrency_optimizations,
                    "concurrency_limit": self.optimization_config["concurrency_limit"],
                    "batch_size": batch_size
                }
            )
            
            self.optimization_history.append(result)
            logger.info(f"Concurrency optimization completed: {response_time_improvement:.2f}% improvement")
            return result
            
        except Exception as e:
            optimization_time = time.time() - start_time
            logger.error(f"Concurrency optimization failed: {e}")
            
            return OptimizationResult(
                optimization_type=OptimizationType.CONCURRENCY_OPTIMIZATION,
                success=False,
                performance_improvement=0.0,
                before_metrics={},
                after_metrics={},
                optimization_time=optimization_time,
                error=str(e)
            )
    
    async def _pre_warm_cache(self) -> int:
        """Pre-warm cache with frequently accessed operations"""
        try:
            # Get frequently accessed master tool operations
            master_tool_stats = self.master_tool_manager.get_manager_stats()
            frequent_operations = master_tool_stats.get("frequent_operations", [])
            
            pre_warmed_count = 0
            for operation in frequent_operations[:10]:  # Pre-warm top 10 operations
                try:
                    # Execute operation to populate cache
                    await self.master_tool_manager.execute_operation(
                        operation["tool_name"],
                        operation["operation_name"],
                        operation.get("sample_arguments", {}),
                        request_id=f"pre_warm_{operation['tool_name']}_{operation['operation_name']}"
                    )
                    pre_warmed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to pre-warm operation {operation}: {e}")
            
            return pre_warmed_count
            
        except Exception as e:
            logger.error(f"Cache pre-warming failed: {e}")
            return 0
    
    async def _optimize_master_tool_memory(self) -> List[str]:
        """Optimize master tool memory usage"""
        optimizations = []
        
        try:
            # Clean up old execution history
            for tool_name, tool in self.master_tool_manager.registry.tools.items():
                if hasattr(tool, 'cleanup_execution_history'):
                    cleaned = await tool.cleanup_execution_history()
                    optimizations.append(f"Cleaned {cleaned} execution history entries for {tool_name}")
            
            # Optimize cache in master tools
            for tool_name, tool in self.master_tool_manager.registry.tools.items():
                if hasattr(tool, 'optimize_cache'):
                    await tool.optimize_cache()
                    optimizations.append(f"Optimized cache for {tool_name}")
            
        except Exception as e:
            logger.error(f"Master tool memory optimization failed: {e}")
        
        return optimizations
    
    async def run_comprehensive_optimization(self) -> Dict[str, Any]:
        """Run comprehensive performance optimization"""
        try:
            optimization_results = []
            
            # Analyze bottlenecks
            bottleneck_analysis = await self.analyze_performance_bottlenecks()
            
            # Run optimizations based on recommendations
            for recommendation in bottleneck_analysis["recommendations"]:
                optimization_type = recommendation["optimization_type"]
                
                if optimization_type == OptimizationType.CACHE_OPTIMIZATION:
                    result = await self.optimize_cache_performance()
                elif optimization_type == OptimizationType.MEMORY_OPTIMIZATION:
                    result = await self.optimize_memory_usage()
                elif optimization_type == OptimizationType.CONCURRENCY_OPTIMIZATION:
                    result = await self.optimize_concurrency()
                else:
                    continue
                
                optimization_results.append(result)
            
            # Calculate overall improvement
            total_improvement = sum(r.performance_improvement for r in optimization_results if r.success)
            successful_optimizations = sum(1 for r in optimization_results if r.success)
            
            return {
                "optimization_success": successful_optimizations > 0,
                "total_optimizations": len(optimization_results),
                "successful_optimizations": successful_optimizations,
                "total_performance_improvement": total_improvement,
                "optimization_results": [
                    {
                        "type": r.optimization_type.value,
                        "success": r.success,
                        "improvement": r.performance_improvement,
                        "optimization_time": r.optimization_time,
                        "error": r.error
                    }
                    for r in optimization_results
                ],
                "bottleneck_analysis": bottleneck_analysis,
                "optimized_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Comprehensive optimization failed: {e}")
            return {
                "optimization_success": False,
                "error": str(e),
                "optimized_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_optimization_history(self) -> Dict[str, Any]:
        """Get optimization history and statistics"""
        if not self.optimization_history:
            return {
                "total_optimizations": 0,
                "successful_optimizations": 0,
                "average_improvement": 0.0,
                "optimization_types": {}
            }
        
        successful_optimizations = [r for r in self.optimization_history if r.success]
        total_improvement = sum(r.performance_improvement for r in successful_optimizations)
        
        optimization_types = {}
        for result in self.optimization_history:
            opt_type = result.optimization_type.value
            if opt_type not in optimization_types:
                optimization_types[opt_type] = {
                    "count": 0,
                    "successful": 0,
                    "total_improvement": 0.0
                }
            
            optimization_types[opt_type]["count"] += 1
            if result.success:
                optimization_types[opt_type]["successful"] += 1
                optimization_types[opt_type]["total_improvement"] += result.performance_improvement
        
        return {
            "total_optimizations": len(self.optimization_history),
            "successful_optimizations": len(successful_optimizations),
            "average_improvement": total_improvement / len(successful_optimizations) if successful_optimizations else 0.0,
            "optimization_types": optimization_types,
            "latest_optimization": self.optimization_history[-1].optimization_type.value if self.optimization_history else None
        }
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends over time"""
        if len(self.performance_metrics_history) < 2:
            return {
                "trends_available": False,
                "message": "Insufficient data for trend analysis"
            }
        
        recent_metrics = self.performance_metrics_history[-10:]  # Last 10 measurements
        
        cpu_trend = statistics.mean([m.cpu_usage for m in recent_metrics[-5:]]) - statistics.mean([m.cpu_usage for m in recent_metrics[:5]])
        memory_trend = statistics.mean([m.memory_usage for m in recent_metrics[-5:]]) - statistics.mean([m.memory_usage for m in recent_metrics[:5]])
        response_time_trend = statistics.mean([m.response_time_avg for m in recent_metrics[-5:]]) - statistics.mean([m.response_time_avg for m in recent_metrics[:5]])
        cache_hit_trend = statistics.mean([m.cache_hit_rate for m in recent_metrics[-5:]]) - statistics.mean([m.cache_hit_rate for m in recent_metrics[:5]])
        
        return {
            "trends_available": True,
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "response_time_trend": response_time_trend,
            "cache_hit_trend": cache_hit_trend,
            "overall_trend": "improving" if (cpu_trend < 0 and memory_trend < 0 and response_time_trend < 0) else "stable",
            "analysis_period": f"{len(recent_metrics)} measurements",
            "latest_metrics": {
                "cpu_usage": recent_metrics[-1].cpu_usage,
                "memory_usage": recent_metrics[-1].memory_usage,
                "response_time_avg": recent_metrics[-1].response_time_avg,
                "cache_hit_rate": recent_metrics[-1].cache_hit_rate
            }
        }
