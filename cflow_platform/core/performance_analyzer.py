"""
Performance Analysis System for WebMCP Performance Enhancement

This module provides comprehensive performance analysis including:
- Real-time performance metrics collection
- Statistical analysis and trend detection
- Performance bottleneck identification
- Optimization recommendations
- Performance reporting and visualization
"""

import asyncio
import logging
import statistics
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import math

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    category: str = "general"


@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0.0 to 1.0
    change_percentage: float
    confidence: float  # 0.0 to 1.0
    time_window: str


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""
    bottleneck_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_metrics: List[str]
    recommendations: List[str]
    impact_score: float  # 0.0 to 1.0


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    report_id: str
    generated_at: float
    time_window: str
    summary: Dict[str, Any]
    trends: List[PerformanceTrend]
    bottlenecks: List[PerformanceBottleneck]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]
    health_score: float  # 0.0 to 1.0


class PerformanceAnalyzer:
    """
    Advanced performance analysis system with real-time monitoring and insights.
    
    Features:
    - Real-time metrics collection and analysis
    - Statistical analysis and trend detection
    - Bottleneck identification
    - Performance optimization recommendations
    - Historical analysis and reporting
    - Alert generation for performance issues
    """
    
    def __init__(
        self,
        analysis_interval_seconds: float = 60.0,
        trend_window_minutes: int = 30,
        report_interval_minutes: int = 60,
        max_metrics_history: int = 10000
    ):
        self.analysis_interval_seconds = analysis_interval_seconds
        self.trend_window_minutes = trend_window_minutes
        self.report_interval_minutes = report_interval_minutes
        self.max_metrics_history = max_metrics_history
        
        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_history))
        self._metric_categories: Dict[str, set] = defaultdict(set)
        
        # Analysis results
        self._trends: Dict[str, PerformanceTrend] = {}
        self._bottlenecks: List[PerformanceBottleneck] = []
        self._reports: deque = deque(maxlen=100)
        
        # Background tasks
        self._analysis_task: Optional[asyncio.Task] = None
        self._report_task: Optional[asyncio.Task] = None
        
        # Performance thresholds
        self._thresholds = {
            "execution_time_ms": {"warning": 500, "critical": 1000},
            "memory_usage_mb": {"warning": 400, "critical": 500},
            "cpu_usage_percent": {"warning": 80, "critical": 95},
            "error_rate_percent": {"warning": 5, "critical": 10},
            "throughput_per_second": {"warning": 10, "critical": 5}
        }
        
        # Alert callbacks
        self._alert_callbacks: List[callable] = []
    
    async def start(self):
        """Start performance analysis"""
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._report_task = asyncio.create_task(self._report_generation_loop())
        logger.info("PerformanceAnalyzer started")
    
    async def stop(self):
        """Stop performance analysis"""
        if self._analysis_task:
            self._analysis_task.cancel()
        if self._report_task:
            self._report_task.cancel()
        logger.info("PerformanceAnalyzer stopped")
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "",
        category: str = "general"
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            unit=unit,
            category=category
        )
        
        self._metrics[name].append(metric)
        self._metric_categories[category].add(name)
    
    def get_metric_history(
        self,
        name: str,
        time_window_minutes: Optional[int] = None
    ) -> List[PerformanceMetric]:
        """Get metric history within time window"""
        if name not in self._metrics:
            return []
        
        metrics = list(self._metrics[name])
        
        if time_window_minutes:
            cutoff_time = time.time() - (time_window_minutes * 60)
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        return metrics
    
    def get_metric_stats(
        self,
        name: str,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, float]:
        """Get statistical summary for a metric"""
        metrics = self.get_metric_history(name, time_window_minutes)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99),
            "latest": values[-1],
            "time_window_minutes": time_window_minutes
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def analyze_trends(self, time_window_minutes: Optional[int] = None) -> Dict[str, PerformanceTrend]:
        """Analyze performance trends"""
        if time_window_minutes is None:
            time_window_minutes = self.trend_window_minutes
        
        trends = {}
        
        for metric_name in self._metrics:
            trend = self._analyze_metric_trend(metric_name, time_window_minutes)
            if trend:
                trends[metric_name] = trend
        
        self._trends = trends
        return trends
    
    def _analyze_metric_trend(self, metric_name: str, time_window_minutes: int) -> Optional[PerformanceTrend]:
        """Analyze trend for a specific metric"""
        metrics = self.get_metric_history(metric_name, time_window_minutes)
        
        if len(metrics) < 10:  # Need minimum data points
            return None
        
        values = [m.value for m in metrics]
        timestamps = [m.timestamp for m in metrics]
        
        # Simple linear regression
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(timestamps[i] * values[i] for i in range(n))
        sum_x2 = sum(t * t for t in timestamps)
        
        # Calculate slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend direction
        if slope > 0.01:
            direction = "degrading"
        elif slope < -0.01:
            direction = "improving"
        else:
            direction = "stable"
        
        # Calculate trend strength
        trend_strength = min(abs(slope) * 1000, 1.0)  # Normalize
        
        # Calculate change percentage
        if values[0] != 0:
            change_percentage = ((values[-1] - values[0]) / values[0]) * 100
        else:
            change_percentage = 0.0
        
        # Calculate confidence (based on R-squared)
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        ss_res = sum((values[i] - (slope * timestamps[i] + (sum_y - slope * sum_x) / n)) ** 2 for i in range(n))
        
        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
            confidence = max(0.0, min(1.0, r_squared))
        else:
            confidence = 0.0
        
        return PerformanceTrend(
            metric_name=metric_name,
            trend_direction=direction,
            trend_strength=trend_strength,
            change_percentage=change_percentage,
            confidence=confidence,
            time_window=f"{time_window_minutes}m"
        )
    
    def identify_bottlenecks(self) -> List[PerformanceBottleneck]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Analyze each metric category
        for category in self._metric_categories:
            category_bottlenecks = self._analyze_category_bottlenecks(category)
            bottlenecks.extend(category_bottlenecks)
        
        # Cross-metric analysis
        cross_bottlenecks = self._analyze_cross_metric_bottlenecks()
        bottlenecks.extend(cross_bottlenecks)
        
        # Sort by impact score
        bottlenecks.sort(key=lambda b: b.impact_score, reverse=True)
        
        self._bottlenecks = bottlenecks
        return bottlenecks
    
    def _analyze_category_bottlenecks(self, category: str) -> List[PerformanceBottleneck]:
        """Analyze bottlenecks within a category"""
        bottlenecks = []
        metrics = self._metric_categories[category]
        
        for metric_name in metrics:
            stats = self.get_metric_stats(metric_name, self.trend_window_minutes)
            
            if not stats:
                continue
            
            # Check against thresholds
            threshold_key = metric_name.replace("_", "_").lower()
            if threshold_key in self._thresholds:
                thresholds = self._thresholds[threshold_key]
                
                latest_value = stats["latest"]
                p95_value = stats["p95"]
                
                # Determine severity
                if latest_value >= thresholds["critical"] or p95_value >= thresholds["critical"]:
                    severity = "critical"
                elif latest_value >= thresholds["warning"] or p95_value >= thresholds["warning"]:
                    severity = "high"
                else:
                    continue
                
                # Calculate impact score
                impact_score = min(latest_value / thresholds["critical"], 1.0)
                
                # Generate recommendations
                recommendations = self._generate_recommendations(metric_name, severity, stats)
                
                bottleneck = PerformanceBottleneck(
                    bottleneck_type=f"{category}_performance",
                    severity=severity,
                    description=f"{metric_name} is {severity}: {latest_value:.2f} {stats.get('unit', '')}",
                    affected_metrics=[metric_name],
                    recommendations=recommendations,
                    impact_score=impact_score
                )
                
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _analyze_cross_metric_bottlenecks(self) -> List[PerformanceBottleneck]:
        """Analyze bottlenecks across multiple metrics"""
        bottlenecks = []
        
        # Memory vs Performance correlation
        memory_metrics = [name for name in self._metrics if "memory" in name.lower()]
        performance_metrics = [name for name in self._metrics if any(
            term in name.lower() for term in ["execution_time", "response_time", "throughput"]
        )]
        
        if memory_metrics and performance_metrics:
            correlation = self._calculate_correlation(memory_metrics[0], performance_metrics[0])
            
            if correlation > 0.7:  # Strong positive correlation
                bottleneck = PerformanceBottleneck(
                    bottleneck_type="memory_performance_correlation",
                    severity="medium",
                    description=f"Memory usage strongly correlates with performance degradation (r={correlation:.2f})",
                    affected_metrics=memory_metrics + performance_metrics,
                    recommendations=[
                        "Optimize memory usage",
                        "Implement memory pooling",
                        "Review memory-intensive operations"
                    ],
                    impact_score=correlation
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _calculate_correlation(self, metric1: str, metric2: str) -> float:
        """Calculate correlation between two metrics"""
        m1_values = [m.value for m in self.get_metric_history(metric1, self.trend_window_minutes)]
        m2_values = [m.value for m in self.get_metric_history(metric2, self.trend_window_minutes)]
        
        if len(m1_values) != len(m2_values) or len(m1_values) < 5:
            return 0.0
        
        # Simple correlation calculation
        n = len(m1_values)
        mean1 = statistics.mean(m1_values)
        mean2 = statistics.mean(m2_values)
        
        numerator = sum((m1_values[i] - mean1) * (m2_values[i] - mean2) for i in range(n))
        denominator = math.sqrt(
            sum((m1_values[i] - mean1) ** 2 for i in range(n)) *
            sum((m2_values[i] - mean2) ** 2 for i in range(n))
        )
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _generate_recommendations(self, metric_name: str, severity: str, stats: Dict[str, float]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if "execution_time" in metric_name.lower():
            recommendations.extend([
                "Consider caching frequently accessed data",
                "Optimize algorithm complexity",
                "Use async/await for I/O operations",
                "Implement connection pooling"
            ])
        
        elif "memory" in metric_name.lower():
            recommendations.extend([
                "Implement memory pooling",
                "Use weak references where appropriate",
                "Clear unused objects regularly",
                "Monitor for memory leaks"
            ])
        
        elif "cpu" in metric_name.lower():
            recommendations.extend([
                "Optimize CPU-intensive operations",
                "Use multiprocessing for parallel tasks",
                "Implement caching to reduce computation",
                "Profile code for hotspots"
            ])
        
        elif "error_rate" in metric_name.lower():
            recommendations.extend([
                "Implement circuit breakers",
                "Add retry logic with exponential backoff",
                "Improve error handling",
                "Monitor external service health"
            ])
        
        # Add severity-specific recommendations
        if severity == "critical":
            recommendations.insert(0, "URGENT: Immediate action required")
        elif severity == "high":
            recommendations.insert(0, "HIGH PRIORITY: Address within 24 hours")
        
        return recommendations
    
    def generate_performance_report(self, time_window_minutes: int = 60) -> PerformanceReport:
        """Generate comprehensive performance report"""
        report_id = f"report_{int(time.time())}"
        
        # Analyze trends and bottlenecks
        trends = self.analyze_trends(time_window_minutes)
        bottlenecks = self.identify_bottlenecks()
        
        # Generate summary
        summary = self._generate_summary(time_window_minutes)
        
        # Generate recommendations
        recommendations = self._generate_overall_recommendations(bottlenecks)
        
        # Calculate health score
        health_score = self._calculate_health_score(trends, bottlenecks)
        
        # Generate metrics summary
        metrics_summary = self._generate_metrics_summary(time_window_minutes)
        
        report = PerformanceReport(
            report_id=report_id,
            generated_at=time.time(),
            time_window=f"{time_window_minutes}m",
            summary=summary,
            trends=list(trends.values()),
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            metrics_summary=metrics_summary,
            health_score=health_score
        )
        
        self._reports.append(report)
        return report
    
    def _generate_summary(self, time_window_minutes: int) -> Dict[str, Any]:
        """Generate performance summary"""
        total_metrics = sum(len(metrics) for metrics in self._metrics.values())
        active_metrics = len(self._metrics)
        
        # Count trends by direction
        trend_counts = {"improving": 0, "degrading": 0, "stable": 0}
        for trend in self._trends.values():
            trend_counts[trend.trend_direction] += 1
        
        # Count bottlenecks by severity
        bottleneck_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for bottleneck in self._bottlenecks:
            bottleneck_counts[bottleneck.severity] += 1
        
        return {
            "total_metrics_collected": total_metrics,
            "active_metrics": active_metrics,
            "time_window_minutes": time_window_minutes,
            "trend_summary": trend_counts,
            "bottleneck_summary": bottleneck_counts,
            "overall_status": "healthy" if bottleneck_counts["critical"] == 0 else "degraded"
        }
    
    def _generate_overall_recommendations(self, bottlenecks: List[PerformanceBottleneck]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        # Prioritize by severity
        critical_bottlenecks = [b for b in bottlenecks if b.severity == "critical"]
        high_bottlenecks = [b for b in bottlenecks if b.severity == "high"]
        
        if critical_bottlenecks:
            recommendations.append("URGENT: Address critical performance bottlenecks immediately")
        
        if high_bottlenecks:
            recommendations.append("HIGH PRIORITY: Address high-severity bottlenecks within 24 hours")
        
        # General recommendations
        recommendations.extend([
            "Monitor performance trends regularly",
            "Implement automated performance testing",
            "Set up performance alerts for key metrics",
            "Regularly review and optimize performance-critical code paths"
        ])
        
        return recommendations
    
    def _calculate_health_score(self, trends: Dict[str, PerformanceTrend], bottlenecks: List[PerformanceBottleneck]) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        score = 1.0
        
        # Deduct for bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity == "critical":
                score -= 0.3
            elif bottleneck.severity == "high":
                score -= 0.2
            elif bottleneck.severity == "medium":
                score -= 0.1
            else:
                score -= 0.05
        
        # Deduct for degrading trends
        degrading_trends = [t for t in trends.values() if t.trend_direction == "degrading" and t.confidence > 0.5]
        score -= len(degrading_trends) * 0.05
        
        # Bonus for improving trends
        improving_trends = [t for t in trends.values() if t.trend_direction == "improving" and t.confidence > 0.5]
        score += len(improving_trends) * 0.02
        
        return max(0.0, min(1.0, score))
    
    def _generate_metrics_summary(self, time_window_minutes: int) -> Dict[str, Any]:
        """Generate metrics summary"""
        summary = {}
        
        for metric_name in self._metrics:
            stats = self.get_metric_stats(metric_name, time_window_minutes)
            if stats:
                summary[metric_name] = {
                    "latest": stats["latest"],
                    "average": stats["mean"],
                    "p95": stats["p95"],
                    "trend": self._trends.get(metric_name, {}).get("trend_direction", "unknown")
                }
        
        return summary
    
    async def _analysis_loop(self):
        """Background task for continuous analysis"""
        while True:
            try:
                await asyncio.sleep(self.analysis_interval_seconds)
                
                # Analyze trends
                trends = self.analyze_trends()
                
                # Identify bottlenecks
                bottlenecks = self.identify_bottlenecks()
                
                # Check for critical issues
                critical_bottlenecks = [b for b in bottlenecks if b.severity == "critical"]
                if critical_bottlenecks:
                    await self._trigger_alerts(critical_bottlenecks)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance analysis error: {e}")
    
    async def _report_generation_loop(self):
        """Background task for report generation"""
        while True:
            try:
                await asyncio.sleep(self.report_interval_minutes * 60)
                
                # Generate performance report
                report = self.generate_performance_report()
                
                # Log report summary
                logger.info(
                    f"Performance Report {report.report_id}: "
                    f"Health Score: {report.health_score:.2f}, "
                    f"Bottlenecks: {len(report.bottlenecks)}, "
                    f"Trends: {len(report.trends)}"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Report generation error: {e}")
    
    async def _trigger_alerts(self, bottlenecks: List[PerformanceBottleneck]):
        """Trigger alerts for critical issues"""
        for callback in self._alert_callbacks:
            try:
                await callback(bottlenecks)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def add_alert_callback(self, callback: callable):
        """Add alert callback"""
        self._alert_callbacks.append(callback)
    
    def get_latest_report(self) -> Optional[PerformanceReport]:
        """Get the latest performance report"""
        return self._reports[-1] if self._reports else None
    
    def get_all_reports(self) -> List[PerformanceReport]:
        """Get all performance reports"""
        return list(self._reports)


# Global performance analyzer
_performance_analyzer: Optional[PerformanceAnalyzer] = None


async def get_performance_analyzer() -> PerformanceAnalyzer:
    """Get the global performance analyzer"""
    global _performance_analyzer
    if _performance_analyzer is None:
        _performance_analyzer = PerformanceAnalyzer()
        await _performance_analyzer.start()
    return _performance_analyzer


def record_performance_metric(
    name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None,
    unit: str = "",
    category: str = "general"
):
    """Record a performance metric"""
    if _performance_analyzer:
        _performance_analyzer.record_metric(name, value, tags, unit, category)


async def get_performance_report(time_window_minutes: int = 60) -> PerformanceReport:
    """Get performance report"""
    analyzer = await get_performance_analyzer()
    return analyzer.generate_performance_report(time_window_minutes)
