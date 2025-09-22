# BMAD-Method Advanced Monitoring & Analytics System

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class MetricType(Enum):
    PERFORMANCE = "performance"
    USAGE = "usage"
    ERROR = "error"
    SECURITY = "security"
    BUSINESS = "business"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MonitoringMetric:
    """Represents a monitoring metric"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    cerebral_extensions: Dict[str, Any] = None

@dataclass
class AnalyticsReport:
    """Represents an analytics report"""
    report_id: str
    name: str
    report_type: str
    generated_at: datetime
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    cerebral_extensions: Dict[str, Any] = None

class BMADAdvancedMonitoringAnalyticsSystem:
    """Advanced Monitoring & Analytics System for BMAD-Method with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.metrics: List[MonitoringMetric] = []
        self.reports: List[AnalyticsReport] = []
        self.alerts: List[Dict[str, Any]] = []
        self.cerebral_extensions: Dict[str, Any] = {}
        
        # Monitoring categories from vendor/bmad
        self.monitoring_categories = {
            'performance': 'Performance monitoring metrics',
            'usage': 'Usage analytics and statistics',
            'error': 'Error tracking and analysis',
            'security': 'Security monitoring and alerts',
            'business': 'Business metrics and KPIs'
        }
    
    async def collect_metric(self, name: str, value: float, metric_type: MetricType, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Collect a monitoring metric"""
        try:
            metric_id = f"metric_{name}_{int(datetime.now().timestamp())}"
            
            metric = MonitoringMetric(
                metric_id=metric_id,
                name=name,
                metric_type=metric_type,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True,
                    'real_time_processing': True
                }
            )
            
            self.metrics.append(metric)
            
            # Check for alerts
            await self._check_metric_alerts(metric)
            
            return {
                'success': True,
                'metric_id': metric_id,
                'name': name,
                'value': value,
                'metric_type': metric_type.value,
                'message': f'Successfully collected metric: {name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _check_metric_alerts(self, metric: MonitoringMetric):
        """Check if metric triggers any alerts"""
        # Simple alert logic - can be enhanced
        if metric.metric_type == MetricType.ERROR and metric.value > 0:
            alert = {
                'alert_id': f"alert_{metric.metric_id}",
                'level': AlertLevel.ERROR.value,
                'message': f'Error metric detected: {metric.name} = {metric.value}',
                'metric_id': metric.metric_id,
                'timestamp': datetime.now().isoformat()
            }
            self.alerts.append(alert)
        elif metric.metric_type == MetricType.PERFORMANCE and metric.value > 1000:  # Example threshold
            alert = {
                'alert_id': f"alert_{metric.metric_id}",
                'level': AlertLevel.WARNING.value,
                'message': f'Performance threshold exceeded: {metric.name} = {metric.value}',
                'metric_id': metric.metric_id,
                'timestamp': datetime.now().isoformat()
            }
            self.alerts.append(alert)
    
    async def get_metrics(self, metric_type: MetricType = None, time_range: timedelta = None) -> List[MonitoringMetric]:
        """Get metrics with optional filtering"""
        filtered_metrics = self.metrics
        
        if metric_type:
            filtered_metrics = [m for m in filtered_metrics if m.metric_type == metric_type]
        
        if time_range:
            cutoff_time = datetime.now() - time_range
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= cutoff_time]
        
        return filtered_metrics
    
    async def generate_analytics_report(self, report_type: str, time_range: timedelta = None) -> Dict[str, Any]:
        """Generate an analytics report"""
        try:
            report_id = f"report_{report_type}_{int(datetime.now().timestamp())}"
            
            # Get metrics for the time range
            metrics = await self.get_metrics(time_range=time_range)
            
            # Generate report data based on type
            if report_type == 'performance':
                data = await self._generate_performance_report(metrics)
            elif report_type == 'usage':
                data = await self._generate_usage_report(metrics)
            elif report_type == 'error':
                data = await self._generate_error_report(metrics)
            elif report_type == 'security':
                data = await self._generate_security_report(metrics)
            elif report_type == 'business':
                data = await self._generate_business_report(metrics)
            else:
                data = await self._generate_general_report(metrics)
            
            # Generate insights and recommendations
            insights = await self._generate_insights(data)
            recommendations = await self._generate_recommendations(data)
            
            report = AnalyticsReport(
                report_id=report_id,
                name=f'{report_type.title()} Analytics Report',
                report_type=report_type,
                generated_at=datetime.now(),
                data=data,
                insights=insights,
                recommendations=recommendations,
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True,
                    'automated_insights': True
                }
            )
            
            self.reports.append(report)
            
            return {
                'success': True,
                'report_id': report_id,
                'report_type': report_type,
                'data': data,
                'insights': insights,
                'recommendations': recommendations,
                'message': f'Successfully generated {report_type} analytics report'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_performance_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate performance analytics report"""
        perf_metrics = [m for m in metrics if m.metric_type == MetricType.PERFORMANCE]
        
        if not perf_metrics:
            return {'message': 'No performance metrics available'}
        
        values = [m.value for m in perf_metrics]
        
        return {
            'total_metrics': len(perf_metrics),
            'average_value': sum(values) / len(values),
            'min_value': min(values),
            'max_value': max(values),
            'metrics_by_name': {
                name: [m.value for m in perf_metrics if m.name == name]
                for name in set(m.name for m in perf_metrics)
            }
        }
    
    async def _generate_usage_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate usage analytics report"""
        usage_metrics = [m for m in metrics if m.metric_type == MetricType.USAGE]
        
        if not usage_metrics:
            return {'message': 'No usage metrics available'}
        
        return {
            'total_usage_events': len(usage_metrics),
            'unique_users': len(set(m.tags.get('user_id', 'unknown') for m in usage_metrics)),
            'usage_by_hour': self._group_metrics_by_hour(usage_metrics)
        }
    
    async def _generate_error_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate error analytics report"""
        error_metrics = [m for m in metrics if m.metric_type == MetricType.ERROR]
        
        if not error_metrics:
            return {'message': 'No error metrics available'}
        
        return {
            'total_errors': len(error_metrics),
            'error_rate': len(error_metrics) / len(metrics) if metrics else 0,
            'errors_by_type': {
                error_type: len([m for m in error_metrics if m.tags.get('error_type') == error_type])
                for error_type in set(m.tags.get('error_type', 'unknown') for m in error_metrics)
            }
        }
    
    async def _generate_security_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate security analytics report"""
        security_metrics = [m for m in metrics if m.metric_type == MetricType.SECURITY]
        
        if not security_metrics:
            return {'message': 'No security metrics available'}
        
        return {
            'total_security_events': len(security_metrics),
            'security_alerts': len([m for m in security_metrics if m.value > 0]),
            'threat_level': 'low' if len(security_metrics) < 10 else 'medium' if len(security_metrics) < 50 else 'high'
        }
    
    async def _generate_business_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate business analytics report"""
        business_metrics = [m for m in metrics if m.metric_type == MetricType.BUSINESS]
        
        if not business_metrics:
            return {'message': 'No business metrics available'}
        
        return {
            'total_business_metrics': len(business_metrics),
            'kpis': {
                name: sum(m.value for m in business_metrics if m.name == name)
                for name in set(m.name for m in business_metrics)
            }
        }
    
    async def _generate_general_report(self, metrics: List[MonitoringMetric]) -> Dict[str, Any]:
        """Generate general analytics report"""
        return {
            'total_metrics': len(metrics),
            'metrics_by_type': {
                metric_type.value: len([m for m in metrics if m.metric_type == metric_type])
                for metric_type in MetricType
            },
            'time_range': {
                'start': min(m.timestamp for m in metrics).isoformat() if metrics else None,
                'end': max(m.timestamp for m in metrics).isoformat() if metrics else None
            }
        }
    
    def _group_metrics_by_hour(self, metrics: List[MonitoringMetric]) -> Dict[int, int]:
        """Group metrics by hour of day"""
        hourly_counts = {}
        for metric in metrics:
            hour = metric.timestamp.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        return hourly_counts
    
    async def _generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from report data"""
        insights = []
        
        if 'average_value' in data:
            if data['average_value'] > 1000:
                insights.append('Performance metrics indicate high resource usage')
            elif data['average_value'] < 100:
                insights.append('Performance metrics indicate efficient resource usage')
        
        if 'total_errors' in data:
            if data['total_errors'] > 10:
                insights.append('High error rate detected - investigation recommended')
            elif data['total_errors'] == 0:
                insights.append('No errors detected - system running smoothly')
        
        if 'security_alerts' in data:
            if data['security_alerts'] > 0:
                insights.append('Security alerts detected - immediate attention required')
        
        return insights
    
    async def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from report data"""
        recommendations = []
        
        if 'average_value' in data and data['average_value'] > 1000:
            recommendations.append('Consider optimizing performance-critical components')
        
        if 'total_errors' in data and data['total_errors'] > 10:
            recommendations.append('Implement error monitoring and alerting system')
        
        if 'security_alerts' in data and data['security_alerts'] > 0:
            recommendations.append('Review and strengthen security measures')
        
        return recommendations
    
    async def get_alerts(self, level: AlertLevel = None) -> List[Dict[str, Any]]:
        """Get alerts with optional level filtering"""
        if level:
            return [alert for alert in self.alerts if alert['level'] == level.value]
        return self.alerts
    
    async def get_reports(self, report_type: str = None) -> List[AnalyticsReport]:
        """Get reports with optional type filtering"""
        if report_type:
            return [report for report in self.reports if report.report_type == report_type]
        return self.reports
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            'total_metrics': len(self.metrics),
            'total_reports': len(self.reports),
            'total_alerts': len(self.alerts),
            'monitoring_categories': len(self.monitoring_categories),
            'cerebral_extensions': {
                'mcp_integration': True,
                'context_preservation': True,
                'session_management': True,
                'webmcp_routing': True,
                'real_time_processing': True,
                'automated_insights': True
            },
            'system_version': '1.0',
            'last_update': datetime.now().isoformat()
        }

# Global monitoring analytics system instance
bmad_advanced_monitoring_analytics_system = BMADAdvancedMonitoringAnalyticsSystem()
