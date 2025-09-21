"""
Performance and Load Testing Engine for BMAD Integration

This module provides comprehensive performance and load testing capabilities
for the BMAD integration, including stress testing, load testing, and
performance benchmarking.
"""

import asyncio
import time
import statistics
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single test execution."""
    tool_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoadTestResult:
    """Results from a load test execution."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    total_duration: float
    memory_peak: float
    cpu_peak: float
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StressTestResult:
    """Results from a stress test execution."""
    test_name: str
    max_concurrent_users: int
    breaking_point: Optional[int]
    performance_degradation_point: Optional[int]
    error_rate_threshold_reached: bool
    memory_exhaustion_point: Optional[int]
    cpu_saturation_point: Optional[int]
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PerformanceLoadTestingEngine:
    """
    Engine for performance and load testing of BMAD integration.
    
    This class provides comprehensive testing capabilities including:
    - Load testing with configurable concurrent users
    - Stress testing to find breaking points
    - Performance benchmarking
    - Resource monitoring
    - Performance regression detection
    """
    
    def __init__(self):
        """Initialize the performance load testing engine."""
        self._test_results: List[LoadTestResult] = []
        self._stress_results: List[StressTestResult] = []
        self._baseline_metrics: Dict[str, float] = {}
        self._monitoring_active = False
        self._system_monitor = SystemResourceMonitor()
        
    async def run_load_test(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10
    ) -> LoadTestResult:
        """
        Run a load test for a specific tool.
        
        Args:
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration in seconds
            ramp_up_seconds: Ramp-up time in seconds
            
        Returns:
            LoadTestResult with test metrics
        """
        logger.info(f"Starting load test for {tool_name} with {concurrent_users} concurrent users")
        
        # Start system monitoring
        await self._system_monitor.start_monitoring()
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Create semaphore for concurrent user control
        semaphore = asyncio.Semaphore(concurrent_users)
        
        # Track metrics
        metrics: List[PerformanceMetrics] = []
        errors: List[str] = []
        
        async def execute_tool_request():
            """Execute a single tool request."""
            async with semaphore:
                request_start = time.time()
                try:
                    # Import here to avoid circular imports
                    from cflow_platform.core.direct_client import execute_mcp_tool
                    
                    result = await execute_mcp_tool(tool_name, **tool_args)
                    
                    request_end = time.time()
                    execution_time = request_end - request_start
                    
                    # Get system metrics
                    memory_usage = psutil.virtual_memory().percent
                    cpu_usage = psutil.cpu_percent()
                    
                    metrics.append(PerformanceMetrics(
                        tool_name=tool_name,
                        execution_time=execution_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        success=True
                    ))
                    
                except Exception as e:
                    request_end = time.time()
                    execution_time = request_end - request_start
                    
                    memory_usage = psutil.virtual_memory().percent
                    cpu_usage = psutil.cpu_percent()
                    
                    error_msg = str(e)
                    errors.append(error_msg)
                    
                    metrics.append(PerformanceMetrics(
                        tool_name=tool_name,
                        execution_time=execution_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        success=False,
                        error_message=error_msg
                    ))
        
        # Create tasks for the load test
        tasks = []
        
        # Ramp-up phase
        ramp_up_tasks = concurrent_users
        ramp_up_delay = ramp_up_seconds / concurrent_users if concurrent_users > 0 else 0
        
        for i in range(concurrent_users):
            if ramp_up_delay > 0:
                await asyncio.sleep(ramp_up_delay)
            tasks.append(asyncio.create_task(execute_tool_request()))
        
        # Continue creating tasks during the test duration
        while time.time() < end_time:
            # Wait for some tasks to complete before creating new ones
            if len(tasks) >= concurrent_users * 2:
                # Wait for some tasks to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)
            
            # Create new task
            tasks.append(asyncio.create_task(execute_tool_request()))
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)
        
        # Wait for all remaining tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop system monitoring
        await self._system_monitor.stop_monitoring()
        
        # Calculate results
        total_duration = time.time() - start_time
        successful_requests = sum(1 for m in metrics if m.success)
        failed_requests = len(metrics) - successful_requests
        
        if metrics:
            response_times = [m.execution_time for m in metrics]
            average_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
            
            requests_per_second = len(metrics) / total_duration
            
            # Get peak resource usage
            memory_peak = max(m.memory_usage for m in metrics) if metrics else 0
            cpu_peak = max(m.cpu_usage for m in metrics) if metrics else 0
        else:
            average_response_time = 0
            min_response_time = 0
            max_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
            requests_per_second = 0
            memory_peak = 0
            cpu_peak = 0
        
        result = LoadTestResult(
            test_name=f"load_test_{tool_name}",
            total_requests=len(metrics),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            total_duration=total_duration,
            memory_peak=memory_peak,
            cpu_peak=cpu_peak,
            errors=errors
        )
        
        self._test_results.append(result)
        logger.info(f"Load test completed: {successful_requests}/{len(metrics)} successful requests")
        
        return result
    
    async def run_stress_test(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        max_concurrent_users: int = 100,
        increment: int = 10,
        duration_per_level: int = 30
    ) -> StressTestResult:
        """
        Run a stress test to find the breaking point.
        
        Args:
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            max_concurrent_users: Maximum number of concurrent users to test
            increment: Increment for concurrent users
            duration_per_level: Duration for each stress level
            
        Returns:
            StressTestResult with stress test findings
        """
        logger.info(f"Starting stress test for {tool_name} up to {max_concurrent_users} concurrent users")
        
        breaking_point = None
        performance_degradation_point = None
        error_rate_threshold_reached = False
        memory_exhaustion_point = None
        cpu_saturation_point = None
        recommendations = []
        
        baseline_response_time = None
        
        for concurrent_users in range(increment, max_concurrent_users + 1, increment):
            logger.info(f"Testing with {concurrent_users} concurrent users")
            
            # Run load test for this level
            result = await self.run_load_test(
                tool_name=tool_name,
                tool_args=tool_args,
                concurrent_users=concurrent_users,
                duration_seconds=duration_per_level,
                ramp_up_seconds=5
            )
            
            # Check for breaking point (error rate > 50%)
            error_rate = result.failed_requests / result.total_requests if result.total_requests > 0 else 0
            if error_rate > 0.5 and breaking_point is None:
                breaking_point = concurrent_users
                error_rate_threshold_reached = True
            
            # Check for performance degradation (> 2x baseline response time)
            if baseline_response_time is None:
                baseline_response_time = result.average_response_time
            elif result.average_response_time > baseline_response_time * 2 and performance_degradation_point is None:
                performance_degradation_point = concurrent_users
            
            # Check for memory exhaustion (> 90% memory usage)
            if result.memory_peak > 90 and memory_exhaustion_point is None:
                memory_exhaustion_point = concurrent_users
            
            # Check for CPU saturation (> 95% CPU usage)
            if result.cpu_peak > 95 and cpu_saturation_point is None:
                cpu_saturation_point = concurrent_users
            
            # Stop if we've hit breaking point
            if breaking_point:
                break
        
        # Generate recommendations
        if breaking_point:
            recommendations.append(f"System breaks at {breaking_point} concurrent users")
            recommendations.append(f"Recommended max concurrent users: {breaking_point - increment}")
        
        if performance_degradation_point:
            recommendations.append(f"Performance degrades at {performance_degradation_point} concurrent users")
        
        if memory_exhaustion_point:
            recommendations.append(f"Memory exhaustion at {memory_exhaustion_point} concurrent users")
            recommendations.append("Consider increasing available memory or optimizing memory usage")
        
        if cpu_saturation_point:
            recommendations.append(f"CPU saturation at {cpu_saturation_point} concurrent users")
            recommendations.append("Consider scaling horizontally or optimizing CPU usage")
        
        if not recommendations:
            recommendations.append("System handled stress test well")
            recommendations.append(f"Tested up to {max_concurrent_users} concurrent users without issues")
        
        stress_result = StressTestResult(
            test_name=f"stress_test_{tool_name}",
            max_concurrent_users=max_concurrent_users,
            breaking_point=breaking_point,
            performance_degradation_point=performance_degradation_point,
            error_rate_threshold_reached=error_rate_threshold_reached,
            memory_exhaustion_point=memory_exhaustion_point,
            cpu_saturation_point=cpu_saturation_point,
            recommendations=recommendations
        )
        
        self._stress_results.append(stress_result)
        logger.info(f"Stress test completed. Breaking point: {breaking_point}")
        
        return stress_result
    
    async def run_performance_benchmark(
        self,
        tools_to_test: List[Tuple[str, Dict[str, Any]]],
        iterations: int = 10
    ) -> Dict[str, Dict[str, float]]:
        """
        Run performance benchmarks for multiple tools.
        
        Args:
            tools_to_test: List of (tool_name, tool_args) tuples
            iterations: Number of iterations per tool
            
        Returns:
            Dictionary with benchmark results for each tool
        """
        logger.info(f"Starting performance benchmark for {len(tools_to_test)} tools")
        
        benchmark_results = {}
        
        for tool_name, tool_args in tools_to_test:
            logger.info(f"Benchmarking {tool_name}")
            
            execution_times = []
            memory_usages = []
            cpu_usages = []
            success_count = 0
            
            for i in range(iterations):
                start_time = time.time()
                start_memory = psutil.virtual_memory().percent
                start_cpu = psutil.cpu_percent()
                
                try:
                    from cflow_platform.core.direct_client import execute_mcp_tool
                    result = await execute_mcp_tool(tool_name, **tool_args)
                    
                    end_time = time.time()
                    end_memory = psutil.virtual_memory().percent
                    end_cpu = psutil.cpu_percent()
                    
                    execution_times.append(end_time - start_time)
                    memory_usages.append(end_memory - start_memory)
                    cpu_usages.append(end_cpu - start_cpu)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Benchmark iteration {i+1} failed for {tool_name}: {e}")
                    continue
                
                # Small delay between iterations
                await asyncio.sleep(0.1)
            
            if execution_times:
                benchmark_results[tool_name] = {
                    "average_execution_time": statistics.mean(execution_times),
                    "min_execution_time": min(execution_times),
                    "max_execution_time": max(execution_times),
                    "std_deviation": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                    "average_memory_usage": statistics.mean(memory_usages),
                    "average_cpu_usage": statistics.mean(cpu_usages),
                    "success_rate": success_count / iterations,
                    "iterations": iterations
                }
            else:
                benchmark_results[tool_name] = {
                    "error": "No successful iterations",
                    "success_rate": 0,
                    "iterations": iterations
                }
        
        logger.info("Performance benchmark completed")
        return benchmark_results
    
    async def detect_performance_regression(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        baseline_metrics: Dict[str, float],
        threshold_percentage: float = 20.0
    ) -> Dict[str, Any]:
        """
        Detect performance regression by comparing current metrics to baseline.
        
        Args:
            tool_name: Name of the tool to test
            tool_args: Arguments to pass to the tool
            baseline_metrics: Baseline performance metrics
            threshold_percentage: Threshold for regression detection
            
        Returns:
            Dictionary with regression analysis results
        """
        logger.info(f"Detecting performance regression for {tool_name}")
        
        # Run current benchmark
        current_results = await self.run_performance_benchmark([(tool_name, tool_args)], iterations=5)
        
        if tool_name not in current_results or "error" in current_results[tool_name]:
            return {
                "regression_detected": False,
                "error": "Could not run current benchmark",
                "current_metrics": None,
                "baseline_metrics": baseline_metrics
            }
        
        current_metrics = current_results[tool_name]
        
        # Compare metrics
        regression_detected = False
        regression_details = {}
        
        for metric_name in ["average_execution_time", "average_memory_usage", "average_cpu_usage"]:
            if metric_name in baseline_metrics and metric_name in current_metrics:
                baseline_value = baseline_metrics[metric_name]
                current_value = current_metrics[metric_name]
                
                if baseline_value > 0:
                    percentage_change = ((current_value - baseline_value) / baseline_value) * 100
                    
                    if percentage_change > threshold_percentage:
                        regression_detected = True
                        regression_details[metric_name] = {
                            "baseline": baseline_value,
                            "current": current_value,
                            "percentage_change": percentage_change,
                            "regression": True
                        }
                    else:
                        regression_details[metric_name] = {
                            "baseline": baseline_value,
                            "current": current_value,
                            "percentage_change": percentage_change,
                            "regression": False
                        }
        
        return {
            "regression_detected": regression_detected,
            "regression_details": regression_details,
            "current_metrics": current_metrics,
            "baseline_metrics": baseline_metrics,
            "threshold_percentage": threshold_percentage
        }
    
    def get_test_history(self) -> Dict[str, List[Any]]:
        """Get history of all test results."""
        return {
            "load_tests": self._test_results,
            "stress_tests": self._stress_results
        }
    
    def clear_test_history(self):
        """Clear all test history."""
        self._test_results.clear()
        self._stress_results.clear()
        logger.info("Test history cleared")


class SystemResourceMonitor:
    """Monitor system resources during testing."""
    
    def __init__(self):
        self._monitoring = False
        self._metrics_history: List[Dict[str, float]] = []
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start monitoring system resources."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._metrics_history.clear()
        
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring system resources."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System resource monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # Collect system metrics
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent()
                disk = psutil.disk_usage('/')
                
                metrics = {
                    "timestamp": time.time(),
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "cpu_percent": cpu,
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
                
                self._metrics_history.append(metrics)
                
                # Keep only last 1000 metrics to prevent memory issues
                if len(self._metrics_history) > 1000:
                    self._metrics_history = self._metrics_history[-1000:]
                
                await asyncio.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)
    
    def get_peak_metrics(self) -> Dict[str, float]:
        """Get peak metrics from monitoring history."""
        if not self._metrics_history:
            return {}
        
        return {
            "peak_memory_percent": max(m["memory_percent"] for m in self._metrics_history),
            "peak_cpu_percent": max(m["cpu_percent"] for m in self._metrics_history),
            "min_disk_free_gb": min(m["disk_free_gb"] for m in self._metrics_history),
            "monitoring_duration": self._metrics_history[-1]["timestamp"] - self._metrics_history[0]["timestamp"] if len(self._metrics_history) > 1 else 0
        }
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics from monitoring history."""
        if not self._metrics_history:
            return {}
        
        return {
            "avg_memory_percent": statistics.mean(m["memory_percent"] for m in self._metrics_history),
            "avg_cpu_percent": statistics.mean(m["cpu_percent"] for m in self._metrics_history),
            "avg_disk_free_gb": statistics.mean(m["disk_free_gb"] for m in self._metrics_history)
        }
