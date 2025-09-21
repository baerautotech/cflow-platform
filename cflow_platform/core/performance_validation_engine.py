"""
Performance Validation Engine for BMAD Workflows

This module provides comprehensive performance testing capabilities including
load testing, stress testing, scalability testing, and SLO validation.
"""

import asyncio
import logging
import time
import uuid
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class PerformanceTestType(Enum):
    """Types of performance tests"""
    LOAD = "load"
    STRESS = "stress"
    SCALABILITY = "scalability"
    SPIKE = "spike"
    VOLUME = "volume"
    ENDURANCE = "endurance"


class PerformanceTestStatus(Enum):
    """Performance test status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SLOStatus(Enum):
    """SLO validation status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    test_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLOThreshold:
    """Service Level Objective threshold"""
    metric_name: str
    threshold_value: float
    operator: str  # "lt", "lte", "gt", "gte", "eq"
    severity: str  # "critical", "warning", "info"
    description: str


@dataclass
class PerformanceTestResult:
    """Result of performance test execution"""
    test_id: str
    test_type: PerformanceTestType
    status: PerformanceTestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    metrics: List[PerformanceMetric] = field(default_factory=list)
    slo_results: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    git_workflow_result: Optional[Dict[str, Any]] = None


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    target_users: int
    ramp_up_duration: int  # seconds
    test_duration: int  # seconds
    ramp_down_duration: int  # seconds
    concurrent_requests: int
    request_timeout: float  # seconds
    think_time: float  # seconds between requests


@dataclass
class StressTestConfig:
    """Configuration for stress testing"""
    start_users: int
    max_users: int
    increment_users: int
    increment_interval: int  # seconds
    test_duration: int  # seconds
    failure_threshold: float  # percentage of failed requests
    resource_threshold: float  # CPU/Memory usage threshold


@dataclass
class ScalabilityTestConfig:
    """Configuration for scalability testing"""
    min_users: int
    max_users: int
    user_increment: int
    test_duration_per_level: int  # seconds
    performance_degradation_threshold: float  # percentage
    resource_scaling_threshold: float  # percentage


class PerformanceMetricsCollector:
    """Collects system and application performance metrics"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.collection_active = False
        self.collection_thread: Optional[threading.Thread] = None
    
    async def start_collection(self, test_id: str, interval: float = 1.0) -> None:
        """Start collecting performance metrics"""
        
        if self.collection_active:
            await self.stop_collection()
        
        self.collection_active = True
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            args=(test_id, interval),
            daemon=True
        )
        self.collection_thread.start()
        
        logger.info(f"Started performance metrics collection for test {test_id}")
    
    async def stop_collection(self) -> List[PerformanceMetric]:
        """Stop collecting performance metrics and return collected data"""
        
        self.collection_active = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5.0)
        
        collected_metrics = self.metrics.copy()
        self.metrics.clear()
        
        logger.info(f"Stopped performance metrics collection, collected {len(collected_metrics)} metrics")
        return collected_metrics
    
    def _collect_metrics_loop(self, test_id: str, interval: float) -> None:
        """Main metrics collection loop"""
        
        while self.collection_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Collect application metrics (simplified)
                active_threads = threading.active_count()
                
                # Store metrics
                timestamp = datetime.now()
                
                self.metrics.extend([
                    PerformanceMetric(
                        metric_name="cpu_usage",
                        value=cpu_percent,
                        unit="percent",
                        timestamp=timestamp,
                        test_id=test_id
                    ),
                    PerformanceMetric(
                        metric_name="memory_usage",
                        value=memory.percent,
                        unit="percent",
                        timestamp=timestamp,
                        test_id=test_id
                    ),
                    PerformanceMetric(
                        metric_name="memory_available",
                        value=memory.available / (1024**3),  # GB
                        unit="GB",
                        timestamp=timestamp,
                        test_id=test_id
                    ),
                    PerformanceMetric(
                        metric_name="disk_usage",
                        value=disk.percent,
                        unit="percent",
                        timestamp=timestamp,
                        test_id=test_id
                    ),
                    PerformanceMetric(
                        metric_name="active_threads",
                        value=active_threads,
                        unit="count",
                        timestamp=timestamp,
                        test_id=test_id
                    )
                ])
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(interval)
    
    def get_metric_summary(self, test_id: str) -> Dict[str, Any]:
        """Get summary statistics for collected metrics"""
        
        test_metrics = [m for m in self.metrics if m.test_id == test_id]
        
        if not test_metrics:
            return {}
        
        # Group metrics by name
        metric_groups = {}
        for metric in test_metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for metric_name, values in metric_groups.items():
            if values:
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]


class SLOValidator:
    """Validates performance against Service Level Objectives"""
    
    def __init__(self):
        self.slo_thresholds = self._get_default_slo_thresholds()
    
    def _get_default_slo_thresholds(self) -> List[SLOThreshold]:
        """Get default SLO thresholds"""
        
        return [
            SLOThreshold(
                metric_name="response_time",
                threshold_value=500.0,
                operator="lte",
                severity="critical",
                description="Response time must be under 500ms"
            ),
            SLOThreshold(
                metric_name="response_time",
                threshold_value=1000.0,
                operator="lte",
                severity="warning",
                description="Response time should be under 1000ms"
            ),
            SLOThreshold(
                metric_name="cpu_usage",
                threshold_value=80.0,
                operator="lte",
                severity="critical",
                description="CPU usage must be under 80%"
            ),
            SLOThreshold(
                metric_name="memory_usage",
                threshold_value=85.0,
                operator="lte",
                severity="critical",
                description="Memory usage must be under 85%"
            ),
            SLOThreshold(
                metric_name="error_rate",
                threshold_value=1.0,
                operator="lte",
                severity="critical",
                description="Error rate must be under 1%"
            ),
            SLOThreshold(
                metric_name="throughput",
                threshold_value=100.0,
                operator="gte",
                severity="warning",
                description="Throughput should be at least 100 requests/second"
            )
        ]
    
    def validate_slos(self, metrics: List[PerformanceMetric]) -> List[Dict[str, Any]]:
        """Validate metrics against SLO thresholds"""
        
        slo_results = []
        
        # Group metrics by name
        metric_groups = {}
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)
        
        # Validate each SLO threshold
        for threshold in self.slo_thresholds:
            if threshold.metric_name not in metric_groups:
                continue
            
            values = metric_groups[threshold.metric_name]
            if not values:
                continue
            
            # Calculate representative value (average for most metrics, max for some)
            if threshold.metric_name in ["response_time", "cpu_usage", "memory_usage"]:
                value = max(values)  # Use max for critical metrics
            else:
                value = statistics.mean(values)  # Use average for others
            
            # Check threshold
            passed = self._check_threshold(value, threshold.threshold_value, threshold.operator)
            
            slo_results.append({
                "metric_name": threshold.metric_name,
                "threshold_value": threshold.threshold_value,
                "actual_value": value,
                "operator": threshold.operator,
                "severity": threshold.severity,
                "description": threshold.description,
                "passed": passed,
                "status": SLOStatus.PASSED if passed else SLOStatus.FAILED
            })
        
        return slo_results
    
    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value meets threshold criteria"""
        
        if operator == "lt":
            return value < threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "gt":
            return value > threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "eq":
            return abs(value - threshold) < 0.001
        else:
            return False


class LoadTestEngine:
    """Engine for load testing"""
    
    def __init__(self):
        self.metrics_collector = PerformanceMetricsCollector()
        self.slo_validator = SLOValidator()
    
    async def run_load_test(
        self,
        config: LoadTestConfig,
        test_function: Callable[[], Any]
    ) -> PerformanceTestResult:
        """Run load test with specified configuration"""
        
        test_id = f"load_test_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting load test {test_id} with {config.target_users} users")
            
            # Start metrics collection
            await self.metrics_collector.start_collection(test_id)
            
            # Run load test
            test_results = await self._execute_load_test(config, test_function)
            
            # Stop metrics collection
            metrics = await self.metrics_collector.stop_collection()
            
            # Validate SLOs
            slo_results = self.slo_validator.validate_slos(metrics)
            
            # Calculate summary
            summary = self._calculate_load_test_summary(test_results, metrics)
            
            end_time = datetime.now()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.LOAD,
                status=PerformanceTestStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                metrics=metrics,
                slo_results=slo_results,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Load test {test_id} failed: {e}")
            await self.metrics_collector.stop_collection()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.LOAD,
                status=PerformanceTestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _execute_load_test(
        self,
        config: LoadTestConfig,
        test_function: Callable[[], Any]
    ) -> List[Dict[str, Any]]:
        """Execute the actual load test"""
        
        results = []
        
        # Simulate ramp-up phase
        logger.info(f"Ramping up to {config.target_users} users over {config.ramp_up_duration} seconds")
        await self._ramp_up_users(config.target_users, config.ramp_up_duration)
        
        # Execute load test
        logger.info(f"Running load test for {config.test_duration} seconds")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=config.concurrent_requests) as executor:
            futures = []
            
            while time.time() - start_time < config.test_duration:
                # Submit requests
                for _ in range(config.concurrent_requests):
                    future = executor.submit(self._execute_single_request, test_function)
                    futures.append(future)
                
                # Wait for think time
                await asyncio.sleep(config.think_time)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=config.request_timeout)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "response_time": config.request_timeout
                    })
        
        # Simulate ramp-down phase
        logger.info(f"Ramping down over {config.ramp_down_duration} seconds")
        await self._ramp_down_users(config.target_users, config.ramp_down_duration)
        
        return results
    
    async def _ramp_up_users(self, target_users: int, duration: int) -> None:
        """Simulate user ramp-up"""
        
        ramp_interval = duration / target_users if target_users > 0 else 0
        for i in range(target_users):
            await asyncio.sleep(ramp_interval)
    
    async def _ramp_down_users(self, target_users: int, duration: int) -> None:
        """Simulate user ramp-down"""
        
        ramp_interval = duration / target_users if target_users > 0 else 0
        for i in range(target_users):
            await asyncio.sleep(ramp_interval)
    
    def _execute_single_request(self, test_function: Callable[[], Any]) -> Dict[str, Any]:
        """Execute a single test request"""
        
        start_time = time.time()
        
        try:
            result = test_function()
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": True,
                "response_time": response_time,
                "result": result
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    def _calculate_load_test_summary(
        self,
        test_results: List[Dict[str, Any]],
        metrics: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Calculate load test summary statistics"""
        
        if not test_results:
            return {}
        
        successful_requests = [r for r in test_results if r.get("success", False)]
        failed_requests = [r for r in test_results if not r.get("success", False)]
        
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        summary = {
            "total_requests": len(test_results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": (len(successful_requests) / len(test_results)) * 100 if test_results else 0,
            "error_rate": (len(failed_requests) / len(test_results)) * 100 if test_results else 0
        }
        
        if response_times:
            summary.update({
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99)
            })
        
        # Add system metrics summary
        metrics_summary = self.metrics_collector.get_metric_summary(test_results[0].get("test_id", ""))
        summary["system_metrics"] = metrics_summary
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]


class StressTestEngine:
    """Engine for stress testing"""
    
    def __init__(self):
        self.metrics_collector = PerformanceMetricsCollector()
        self.slo_validator = SLOValidator()
    
    async def run_stress_test(
        self,
        config: StressTestConfig,
        test_function: Callable[[], Any]
    ) -> PerformanceTestResult:
        """Run stress test with specified configuration"""
        
        test_id = f"stress_test_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting stress test {test_id} from {config.start_users} to {config.max_users} users")
            
            # Start metrics collection
            await self.metrics_collector.start_collection(test_id)
            
            # Run stress test
            test_results = await self._execute_stress_test(config, test_function)
            
            # Stop metrics collection
            metrics = await self.metrics_collector.stop_collection()
            
            # Validate SLOs
            slo_results = self.slo_validator.validate_slos(metrics)
            
            # Calculate summary
            summary = self._calculate_stress_test_summary(test_results, metrics)
            
            end_time = datetime.now()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.STRESS,
                status=PerformanceTestStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                metrics=metrics,
                slo_results=slo_results,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Stress test {test_id} failed: {e}")
            await self.metrics_collector.stop_collection()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.STRESS,
                status=PerformanceTestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _execute_stress_test(
        self,
        config: StressTestConfig,
        test_function: Callable[[], Any]
    ) -> List[Dict[str, Any]]:
        """Execute the actual stress test"""
        
        results = []
        current_users = config.start_users
        
        while current_users <= config.max_users:
            logger.info(f"Testing with {current_users} users")
            
            # Run test at current user level
            level_results = await self._run_test_level(current_users, config, test_function)
            results.extend(level_results)
            
            # Check if we've hit failure threshold
            failure_rate = self._calculate_failure_rate(level_results)
            if failure_rate > config.failure_threshold:
                logger.warning(f"Failure rate {failure_rate:.2f}% exceeds threshold {config.failure_threshold:.2f}%")
                break
            
            # Increment users
            current_users += config.increment_users
            await asyncio.sleep(config.increment_interval)
        
        return results
    
    async def _run_test_level(
        self,
        user_count: int,
        config: StressTestConfig,
        test_function: Callable[[], Any]
    ) -> List[Dict[str, Any]]:
        """Run test at specific user level"""
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=user_count) as executor:
            futures = []
            
            while time.time() - start_time < config.test_duration:
                # Submit requests
                for _ in range(user_count):
                    future = executor.submit(self._execute_single_request, test_function)
                    futures.append(future)
                
                await asyncio.sleep(0.1)  # Small delay between batches
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5.0)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "response_time": 5000.0
                    })
        
        return results
    
    def _execute_single_request(self, test_function: Callable[[], Any]) -> Dict[str, Any]:
        """Execute a single test request"""
        
        start_time = time.time()
        
        try:
            result = test_function()
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": True,
                "response_time": response_time,
                "result": result
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    def _calculate_failure_rate(self, results: List[Dict[str, Any]]) -> float:
        """Calculate failure rate percentage"""
        
        if not results:
            return 0.0
        
        failed_count = len([r for r in results if not r.get("success", False)])
        return (failed_count / len(results)) * 100
    
    def _calculate_stress_test_summary(
        self,
        test_results: List[Dict[str, Any]],
        metrics: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Calculate stress test summary statistics"""
        
        if not test_results:
            return {}
        
        successful_requests = [r for r in test_results if r.get("success", False)]
        failed_requests = [r for r in test_results if not r.get("success", False)]
        
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        summary = {
            "total_requests": len(test_results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": (len(successful_requests) / len(test_results)) * 100 if test_results else 0,
            "error_rate": (len(failed_requests) / len(test_results)) * 100 if test_results else 0,
            "max_users_tested": max([r.get("user_count", 0) for r in test_results], default=0)
        }
        
        if response_times:
            summary.update({
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99)
            })
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]


class ScalabilityTestEngine:
    """Engine for scalability testing"""
    
    def __init__(self):
        self.metrics_collector = PerformanceMetricsCollector()
        self.slo_validator = SLOValidator()
    
    async def run_scalability_test(
        self,
        config: ScalabilityTestConfig,
        test_function: Callable[[], Any]
    ) -> PerformanceTestResult:
        """Run scalability test with specified configuration"""
        
        test_id = f"scalability_test_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting scalability test {test_id} from {config.min_users} to {config.max_users} users")
            
            # Start metrics collection
            await self.metrics_collector.start_collection(test_id)
            
            # Run scalability test
            test_results = await self._execute_scalability_test(config, test_function)
            
            # Stop metrics collection
            metrics = await self.metrics_collector.stop_collection()
            
            # Validate SLOs
            slo_results = self.slo_validator.validate_slos(metrics)
            
            # Calculate summary
            summary = self._calculate_scalability_test_summary(test_results, metrics)
            
            end_time = datetime.now()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.SCALABILITY,
                status=PerformanceTestStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                metrics=metrics,
                slo_results=slo_results,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Scalability test {test_id} failed: {e}")
            await self.metrics_collector.stop_collection()
            
            return PerformanceTestResult(
                test_id=test_id,
                test_type=PerformanceTestType.SCALABILITY,
                status=PerformanceTestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _execute_scalability_test(
        self,
        config: ScalabilityTestConfig,
        test_function: Callable[[], Any]
    ) -> List[Dict[str, Any]]:
        """Execute the actual scalability test"""
        
        results = []
        user_levels = list(range(config.min_users, config.max_users + 1, config.user_increment))
        
        baseline_performance = None
        
        for user_count in user_levels:
            logger.info(f"Testing scalability with {user_count} users")
            
            # Run test at current user level
            level_results = await self._run_test_level(user_count, config, test_function)
            
            # Calculate performance metrics for this level
            level_performance = self._calculate_level_performance(level_results)
            level_performance["user_count"] = user_count
            
            results.append(level_performance)
            
            # Check for performance degradation
            if baseline_performance is None:
                baseline_performance = level_performance
            else:
                degradation = self._calculate_performance_degradation(baseline_performance, level_performance)
                if degradation > config.performance_degradation_threshold:
                    logger.warning(f"Performance degradation {degradation:.2f}% exceeds threshold {config.performance_degradation_threshold:.2f}%")
                    break
            
            await asyncio.sleep(1.0)  # Brief pause between levels
        
        return results
    
    async def _run_test_level(
        self,
        user_count: int,
        config: ScalabilityTestConfig,
        test_function: Callable[[], Any]
    ) -> List[Dict[str, Any]]:
        """Run test at specific user level"""
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=user_count) as executor:
            futures = []
            
            while time.time() - start_time < config.test_duration_per_level:
                # Submit requests
                for _ in range(user_count):
                    future = executor.submit(self._execute_single_request, test_function)
                    futures.append(future)
                
                await asyncio.sleep(0.1)  # Small delay between batches
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5.0)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "response_time": 5000.0
                    })
        
        return results
    
    def _execute_single_request(self, test_function: Callable[[], Any]) -> Dict[str, Any]:
        """Execute a single test request"""
        
        start_time = time.time()
        
        try:
            result = test_function()
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": True,
                "response_time": response_time,
                "result": result
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }
    
    def _calculate_level_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics for a user level"""
        
        if not results:
            return {}
        
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        performance = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": (len(successful_requests) / len(results)) * 100 if results else 0,
            "error_rate": (len(failed_requests) / len(results)) * 100 if results else 0
        }
        
        if response_times:
            performance.update({
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99)
            })
        
        return performance
    
    def _calculate_performance_degradation(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> float:
        """Calculate performance degradation percentage"""
        
        baseline_response_time = baseline.get("avg_response_time", 0)
        current_response_time = current.get("avg_response_time", 0)
        
        if baseline_response_time == 0:
            return 0.0
        
        degradation = ((current_response_time - baseline_response_time) / baseline_response_time) * 100
        return max(0.0, degradation)  # Only positive degradation
    
    def _calculate_scalability_test_summary(
        self,
        test_results: List[Dict[str, Any]],
        metrics: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Calculate scalability test summary statistics"""
        
        if not test_results:
            return {}
        
        summary = {
            "user_levels_tested": len(test_results),
            "max_users_tested": max([r.get("user_count", 0) for r in test_results], default=0),
            "scalability_metrics": test_results
        }
        
        # Calculate overall trends
        response_times = [r.get("avg_response_time", 0) for r in test_results if r.get("avg_response_time")]
        success_rates = [r.get("success_rate", 0) for r in test_results if r.get("success_rate")]
        
        if response_times:
            summary["response_time_trend"] = {
                "min": min(response_times),
                "max": max(response_times),
                "avg": statistics.mean(response_times),
                "trend": "increasing" if len(response_times) > 1 and response_times[-1] > response_times[0] else "stable"
            }
        
        if success_rates:
            summary["success_rate_trend"] = {
                "min": min(success_rates),
                "max": max(success_rates),
                "avg": statistics.mean(success_rates),
                "trend": "decreasing" if len(success_rates) > 1 and success_rates[-1] < success_rates[0] else "stable"
            }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]


class PerformanceValidationEngine:
    """Main engine for performance validation"""
    
    def __init__(self):
        self.load_test_engine = LoadTestEngine()
        self.stress_test_engine = StressTestEngine()
        self.scalability_test_engine = ScalabilityTestEngine()
        self.test_history: List[PerformanceTestResult] = []
    
    async def run_load_test(
        self,
        target_users: int = 10,
        ramp_up_duration: int = 30,
        test_duration: int = 60,
        ramp_down_duration: int = 30,
        concurrent_requests: int = 5,
        request_timeout: float = 5.0,
        think_time: float = 1.0
    ) -> PerformanceTestResult:
        """Run load test with specified parameters"""
        
        config = LoadTestConfig(
            target_users=target_users,
            ramp_up_duration=ramp_up_duration,
            test_duration=test_duration,
            ramp_down_duration=ramp_down_duration,
            concurrent_requests=concurrent_requests,
            request_timeout=request_timeout,
            think_time=think_time
        )
        
        # Default test function (simplified)
        def test_function():
            # Simulate some work
            time.sleep(0.1)
            return {"status": "success", "timestamp": datetime.now().isoformat()}
        
        result = await self.load_test_engine.run_load_test(config, test_function)
        self.test_history.append(result)
        
        return result
    
    async def run_stress_test(
        self,
        start_users: int = 5,
        max_users: int = 50,
        increment_users: int = 5,
        increment_interval: int = 10,
        test_duration: int = 30,
        failure_threshold: float = 5.0,
        resource_threshold: float = 90.0
    ) -> PerformanceTestResult:
        """Run stress test with specified parameters"""
        
        config = StressTestConfig(
            start_users=start_users,
            max_users=max_users,
            increment_users=increment_users,
            increment_interval=increment_interval,
            test_duration=test_duration,
            failure_threshold=failure_threshold,
            resource_threshold=resource_threshold
        )
        
        # Default test function (simplified)
        def test_function():
            # Simulate some work
            time.sleep(0.1)
            return {"status": "success", "timestamp": datetime.now().isoformat()}
        
        result = await self.stress_test_engine.run_stress_test(config, test_function)
        self.test_history.append(result)
        
        return result
    
    async def run_scalability_test(
        self,
        min_users: int = 5,
        max_users: int = 25,
        user_increment: int = 5,
        test_duration_per_level: int = 30,
        performance_degradation_threshold: float = 50.0,
        resource_scaling_threshold: float = 80.0
    ) -> PerformanceTestResult:
        """Run scalability test with specified parameters"""
        
        config = ScalabilityTestConfig(
            min_users=min_users,
            max_users=max_users,
            user_increment=user_increment,
            test_duration_per_level=test_duration_per_level,
            performance_degradation_threshold=performance_degradation_threshold,
            resource_scaling_threshold=resource_scaling_threshold
        )
        
        # Default test function (simplified)
        def test_function():
            # Simulate some work
            time.sleep(0.1)
            return {"status": "success", "timestamp": datetime.now().isoformat()}
        
        result = await self.scalability_test_engine.run_scalability_test(config, test_function)
        self.test_history.append(result)
        
        return result
    
    def get_test_history(
        self,
        test_type: Optional[PerformanceTestType] = None,
        limit: int = 50
    ) -> List[PerformanceTestResult]:
        """Get performance test execution history"""
        
        history = self.test_history.copy()
        
        if test_type:
            history = [r for r in history if r.test_type == test_type]
        
        # Sort by start time (newest first)
        history.sort(key=lambda x: x.start_time, reverse=True)
        
        return history[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance testing statistics"""
        
        total_tests = len(self.test_history)
        if total_tests == 0:
            return {
                "total_tests": 0,
                "load_tests": 0,
                "stress_tests": 0,
                "scalability_tests": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0
            }
        
        load_tests = len([r for r in self.test_history if r.test_type == PerformanceTestType.LOAD])
        stress_tests = len([r for r in self.test_history if r.test_type == PerformanceTestType.STRESS])
        scalability_tests = len([r for r in self.test_history if r.test_type == PerformanceTestType.SCALABILITY])
        
        successful_tests = len([r for r in self.test_history if r.status == PerformanceTestStatus.COMPLETED])
        total_duration = sum(r.duration_seconds for r in self.test_history)
        
        return {
            "total_tests": total_tests,
            "load_tests": load_tests,
            "stress_tests": stress_tests,
            "scalability_tests": scalability_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests) * 100.0,
            "avg_duration": total_duration / total_tests
        }


# Global instance
_performance_engine: Optional[PerformanceValidationEngine] = None


def get_performance_engine() -> PerformanceValidationEngine:
    """Get the global performance validation engine instance"""
    global _performance_engine
    if _performance_engine is None:
        _performance_engine = PerformanceValidationEngine()
    return _performance_engine
