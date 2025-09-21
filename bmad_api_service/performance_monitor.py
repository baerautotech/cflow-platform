"""
Performance Monitor for BMAD API Service

This module provides performance monitoring and metrics
collection for the BMAD API service.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitor for BMAD API service.
    
    This class collects and tracks performance metrics
    for the BMAD API service.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self._execution_times = defaultdict(list)
        self._tool_stats = defaultdict(lambda: {
            "executions": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0
        })
        
        self._recent_executions = deque(maxlen=1000)  # Keep last 1000 executions
        self._start_time = time.time()
        
        self._system_stats = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "memory_available": 0.0,
            "disk_usage": 0.0,
            "network_io": {"bytes_sent": 0, "bytes_recv": 0}
        }
    
    async def record_execution_time(self, tool_name: str, execution_time: float, success: bool = True) -> None:
        """
        Record execution time for a tool.
        
        Args:
            tool_name: Name of the tool
            execution_time: Execution time in seconds
            success: Whether the execution was successful
        """
        try:
            # Record execution time
            self._execution_times[tool_name].append(execution_time)
            
            # Update tool stats
            stats = self._tool_stats[tool_name]
            stats["executions"] += 1
            stats["total_time"] += execution_time
            stats["min_time"] = min(stats["min_time"], execution_time)
            stats["max_time"] = max(stats["max_time"], execution_time)
            
            if not success:
                stats["errors"] += 1
            
            # Record recent execution
            execution_record = {
                "tool_name": tool_name,
                "execution_time": execution_time,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            self._recent_executions.append(execution_record)
            
            logger.debug(f"Recorded execution time for {tool_name}: {execution_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to record execution time: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        try:
            uptime = time.time() - self._start_time
            
            # Calculate overall stats
            total_executions = sum(stats["executions"] for stats in self._tool_stats.values())
            total_time = sum(stats["total_time"] for stats in self._tool_stats.values())
            total_errors = sum(stats["errors"] for stats in self._tool_stats.values())
            
            # Calculate averages
            avg_execution_time = total_time / total_executions if total_executions > 0 else 0.0
            success_rate = (total_executions - total_errors) / total_executions if total_executions > 0 else 0.0
            
            # Get system stats
            system_stats = await self._get_system_stats()
            
            return {
                "uptime": uptime,
                "total_executions": total_executions,
                "total_time": total_time,
                "total_errors": total_errors,
                "average_execution_time": avg_execution_time,
                "success_rate": success_rate,
                "tool_stats": dict(self._tool_stats),
                "system_stats": system_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.
        
        Returns:
            Dictionary with detailed metrics
        """
        try:
            # Get basic stats
            stats = await self.get_stats()
            
            # Add recent execution trends
            recent_executions = list(self._recent_executions)
            recent_trends = self._calculate_recent_trends(recent_executions)
            
            # Add tool performance rankings
            tool_rankings = self._calculate_tool_rankings()
            
            return {
                **stats,
                "recent_trends": recent_trends,
                "tool_rankings": tool_rankings,
                "detailed_metrics": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_recent_trends(self, recent_executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate recent performance trends.
        
        Args:
            recent_executions: List of recent executions
            
        Returns:
            Dictionary with trend information
        """
        if not recent_executions:
            return {
                "trend_period": "1 hour",
                "executions_count": 0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "trend_direction": "stable"
            }
        
        # Filter to last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_executions_1h = [
            exec for exec in recent_executions
            if datetime.fromisoformat(exec["timestamp"]) > one_hour_ago
        ]
        
        if not recent_executions_1h:
            return {
                "trend_period": "1 hour",
                "executions_count": 0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "trend_direction": "stable"
            }
        
        # Calculate metrics
        executions_count = len(recent_executions_1h)
        avg_execution_time = sum(exec["execution_time"] for exec in recent_executions_1h) / executions_count
        success_count = sum(1 for exec in recent_executions_1h if exec["success"])
        success_rate = success_count / executions_count
        
        # Determine trend direction (simplified)
        trend_direction = "stable"
        if avg_execution_time > 1.0:
            trend_direction = "slower"
        elif avg_execution_time < 0.5:
            trend_direction = "faster"
        
        return {
            "trend_period": "1 hour",
            "executions_count": executions_count,
            "average_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "trend_direction": trend_direction
        }
    
    def _calculate_tool_rankings(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate tool performance rankings.
        
        Returns:
            Dictionary with tool rankings
        """
        # Sort tools by execution time
        tools_by_time = sorted(
            self._tool_stats.items(),
            key=lambda x: x[1]["total_time"] / x[1]["executions"] if x[1]["executions"] > 0 else 0,
            reverse=True
        )
        
        # Sort tools by execution count
        tools_by_count = sorted(
            self._tool_stats.items(),
            key=lambda x: x[1]["executions"],
            reverse=True
        )
        
        # Sort tools by error rate
        tools_by_errors = sorted(
            self._tool_stats.items(),
            key=lambda x: x[1]["errors"] / x[1]["executions"] if x[1]["executions"] > 0 else 0,
            reverse=True
        )
        
        return {
            "by_execution_time": [
                {
                    "tool_name": tool_name,
                    "average_time": stats["total_time"] / stats["executions"] if stats["executions"] > 0 else 0,
                    "executions": stats["executions"]
                }
                for tool_name, stats in tools_by_time[:10]
            ],
            "by_execution_count": [
                {
                    "tool_name": tool_name,
                    "executions": stats["executions"],
                    "average_time": stats["total_time"] / stats["executions"] if stats["executions"] > 0 else 0
                }
                for tool_name, stats in tools_by_count[:10]
            ],
            "by_error_rate": [
                {
                    "tool_name": tool_name,
                    "error_rate": stats["errors"] / stats["executions"] if stats["executions"] > 0 else 0,
                    "errors": stats["errors"],
                    "executions": stats["executions"]
                }
                for tool_name, stats in tools_by_errors[:10]
            ]
        }
    
    async def _get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "memory_available": memory_available,
                "disk_usage": disk_usage,
                "network_io": network_io
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "memory_available": 0.0,
                "disk_usage": 0.0,
                "network_io": {"bytes_sent": 0, "bytes_recv": 0}
            }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self._execution_times.clear()
        self._tool_stats.clear()
        self._recent_executions.clear()
        self._start_time = time.time()
        
        logger.info("Performance statistics reset")
    
    def get_tool_performance(self, tool_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool performance metrics
        """
        if tool_name not in self._tool_stats:
            return {
                "tool_name": tool_name,
                "executions": 0,
                "average_time": 0.0,
                "min_time": 0.0,
                "max_time": 0.0,
                "errors": 0,
                "success_rate": 0.0
            }
        
        stats = self._tool_stats[tool_name]
        executions = stats["executions"]
        
        return {
            "tool_name": tool_name,
            "executions": executions,
            "average_time": stats["total_time"] / executions if executions > 0 else 0.0,
            "min_time": stats["min_time"] if stats["min_time"] != float('inf') else 0.0,
            "max_time": stats["max_time"],
            "errors": stats["errors"],
            "success_rate": (executions - stats["errors"]) / executions if executions > 0 else 0.0
        }
