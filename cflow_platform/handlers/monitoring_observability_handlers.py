"""
MCP Handlers for Monitoring & Observability

This module provides MCP tool handlers for monitoring, alerting, and observability functionality
including production monitoring, alerting system, and observability dashboard.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.monitoring_observability_engine import (
    MonitoringObservabilityEngine,
    AlertSeverity,
    AlertStatus,
    get_monitoring_engine
)
from ..core.git_workflow_manager import get_git_workflow_manager

logger = logging.getLogger(__name__)


async def bmad_monitoring_system_health(
    start_monitoring: bool = False,
    interval_seconds: float = 30.0
) -> Dict[str, Any]:
    """
    Monitor overall system health and status.
    
    Args:
        start_monitoring: Whether to start continuous monitoring
        interval_seconds: Monitoring interval in seconds
        
    Returns:
        Dict containing system health status
    """
    try:
        engine = get_monitoring_engine()
        
        # Start monitoring if requested
        if start_monitoring:
            await engine.start_monitoring(interval_seconds)
        
        # Get system health
        health_data = engine.get_system_health()
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="monitoring_system_health",
            test_results={
                "overall_status": health_data.get("overall_status", "unknown"),
                "health_score": health_data.get("health_score", 0),
                "total_checks": health_data.get("total_checks", 0),
                "critical_checks": health_data.get("critical_checks", 0),
                "monitoring_active": start_monitoring
            }
        )
        
        return {
            "success": True,
            "system_health": health_data,
            "monitoring_active": start_monitoring,
            "git_workflow_result": git_result,
            "message": f"System health monitoring {'started' if start_monitoring else 'checked'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to monitor system health: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to monitor system health: {e}"
        }


async def bmad_monitoring_performance_metrics(
    metric_names: Optional[List[str]] = None,
    include_history: bool = False,
    history_limit: int = 10
) -> Dict[str, Any]:
    """
    Collect and analyze performance metrics.
    
    Args:
        metric_names: List of metric names to collect (optional)
        include_history: Whether to include metric history
        history_limit: Number of historical data points to include
        
    Returns:
        Dict containing performance metrics
    """
    try:
        engine = get_monitoring_engine()
        
        # Get performance metrics
        metrics_data = engine.get_performance_metrics(metric_names)
        
        # Include history if requested
        history_data = {}
        if include_history:
            for metric_name in (metric_names or ["cpu_percent", "memory_percent", "disk_percent"]):
                history = engine.monitoring_engine.get_metric_history(metric_name, limit=history_limit)
                history_data[metric_name] = [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "value": m.value,
                        "unit": m.unit
                    }
                    for m in history
                ]
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="monitoring_performance_metrics",
            test_results={
                "metrics_collected": len(metrics_data),
                "metric_names": list(metrics_data.keys()),
                "include_history": include_history,
                "history_points": sum(len(h) for h in history_data.values()) if history_data else 0
            }
        )
        
        return {
            "success": True,
            "performance_metrics": metrics_data,
            "metric_history": history_data if include_history else None,
            "git_workflow_result": git_result,
            "message": f"Collected {len(metrics_data)} performance metrics"
        }
        
    except Exception as e:
        logger.error(f"Failed to collect performance metrics: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to collect performance metrics: {e}"
        }


async def bmad_monitoring_resource_utilization(
    include_trends: bool = True,
    trend_hours: int = 1
) -> Dict[str, Any]:
    """
    Monitor resource usage (CPU, memory, disk, network).
    
    Args:
        include_trends: Whether to include resource utilization trends
        trend_hours: Number of hours for trend analysis
        
    Returns:
        Dict containing resource utilization data
    """
    try:
        engine = get_monitoring_engine()
        
        # Get resource utilization
        resource_data = engine.get_resource_utilization()
        
        # Include trends if requested
        trends_data = {}
        if include_trends:
            # Calculate trends over the specified time period
            trend_limit = max(10, trend_hours * 2)  # Approximate data points per hour
            for metric_name in ["cpu_percent", "memory_percent", "disk_percent"]:
                history = engine.monitoring_engine.get_metric_history(metric_name, limit=trend_limit)
                if history:
                    values = [m.value for m in history]
                    trends_data[metric_name] = {
                        "current": values[-1] if values else 0,
                        "average": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "decreasing" if len(values) > 1 else "stable"
                    }
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="monitoring_resource_utilization",
            test_results={
                "resources_monitored": len(resource_data),
                "include_trends": include_trends,
                "trend_hours": trend_hours,
                "trends_analyzed": len(trends_data)
            }
        )
        
        return {
            "success": True,
            "resource_utilization": resource_data,
            "resource_trends": trends_data if include_trends else None,
            "git_workflow_result": git_result,
            "message": f"Monitored {len(resource_data)} resource metrics"
        }
        
    except Exception as e:
        logger.error(f"Failed to monitor resource utilization: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to monitor resource utilization: {e}"
        }


async def bmad_alerting_configure(
    alert_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Configure alerting rules and thresholds.
    
    Args:
        alert_rules: List of alert rule configurations
        
    Returns:
        Dict containing alerting configuration results
    """
    try:
        engine = get_monitoring_engine()
        
        # Configure alerting rules
        engine.configure_alerting(alert_rules)
        
        # Get current alert rules
        current_rules = list(engine.alerting_system.alert_rules.keys())
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="alerting_configure",
            test_results={
                "rules_configured": len(alert_rules),
                "total_rules": len(current_rules),
                "rule_ids": [rule["rule_id"] for rule in alert_rules]
            }
        )
        
        return {
            "success": True,
            "rules_configured": len(alert_rules),
            "total_rules": len(current_rules),
            "configured_rule_ids": [rule["rule_id"] for rule in alert_rules],
            "git_workflow_result": git_result,
            "message": f"Configured {len(alert_rules)} alerting rules"
        }
        
    except Exception as e:
        logger.error(f"Failed to configure alerting: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to configure alerting: {e}"
        }


async def bmad_alerting_test(
    create_test_alert: bool = True
) -> Dict[str, Any]:
    """
    Test alerting system functionality.
    
    Args:
        create_test_alert: Whether to create a test alert
        
    Returns:
        Dict containing alerting test results
    """
    try:
        engine = get_monitoring_engine()
        
        # Test alerting system
        test_result = engine.test_alerting()
        
        # Get active alerts
        active_alerts = engine.alerting_system.get_active_alerts()
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="alerting_test",
            test_results={
                "test_alert_created": test_result.get("test_alert_created", False),
                "active_alerts_count": len(active_alerts),
                "test_alert_id": test_result.get("alert_id", "unknown")
            }
        )
        
        return {
            "success": True,
            "test_result": test_result,
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            "git_workflow_result": git_result,
            "message": "Alerting system test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to test alerting system: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to test alerting system: {e}"
        }


async def bmad_observability_dashboard(
    include_alerts: bool = True,
    include_logs: bool = True,
    log_limit: int = 50
) -> Dict[str, Any]:
    """
    Generate observability dashboard data.
    
    Args:
        include_alerts: Whether to include alert information
        include_logs: Whether to include recent logs
        log_limit: Number of recent logs to include
        
    Returns:
        Dict containing observability dashboard data
    """
    try:
        engine = get_monitoring_engine()
        
        # Get dashboard data
        dashboard_data = engine.get_observability_dashboard()
        
        # Include alerts if requested
        alerts_data = None
        if include_alerts:
            active_alerts = engine.alerting_system.get_active_alerts()
            alerts_data = {
                "active_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "status": alert.status.value,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts
                ],
                "alert_summary": dashboard_data.get("alert_summary", {})
            }
        
        # Include logs if requested
        logs_data = None
        if include_logs:
            logs = engine.logging.get_logs(limit=log_limit)
            logs_data = {
                "recent_logs": logs,
                "log_statistics": engine.logging.get_log_statistics()
            }
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="observability_dashboard",
            test_results={
                "dashboard_generated": True,
                "include_alerts": include_alerts,
                "include_logs": include_logs,
                "health_score": dashboard_data.get("system_health", {}).get("health_score", 0),
                "overall_status": dashboard_data.get("system_health", {}).get("overall_status", "unknown")
            }
        )
        
        return {
            "success": True,
            "dashboard_data": dashboard_data,
            "alerts_data": alerts_data,
            "logs_data": logs_data,
            "git_workflow_result": git_result,
            "message": "Observability dashboard generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate observability dashboard: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate observability dashboard: {e}"
        }


async def bmad_logging_centralized(
    level: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 100,
    include_statistics: bool = True
) -> Dict[str, Any]:
    """
    Centralized logging and log analysis.
    
    Args:
        level: Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        component: Filter logs by component
        limit: Maximum number of logs to return
        include_statistics: Whether to include log statistics
        
    Returns:
        Dict containing centralized logs and analysis
    """
    try:
        engine = get_monitoring_engine()
        
        # Get centralized logs
        logs_data = engine.get_centralized_logs(
            level=level,
            component=component,
            limit=limit
        )
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="logging_centralized",
            test_results={
                "logs_retrieved": logs_data.get("total_returned", 0),
                "level_filter": level,
                "component_filter": component,
                "include_statistics": include_statistics
            }
        )
        
        return {
            "success": True,
            "logs": logs_data.get("logs", []),
            "statistics": logs_data.get("statistics", {}) if include_statistics else None,
            "total_returned": logs_data.get("total_returned", 0),
            "filters": {
                "level": level,
                "component": component,
                "limit": limit
            },
            "git_workflow_result": git_result,
            "message": f"Retrieved {logs_data.get('total_returned', 0)} centralized logs"
        }
        
    except Exception as e:
        logger.error(f"Failed to get centralized logs: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get centralized logs: {e}"
        }


async def bmad_monitoring_report_generate(
    hours_back: int = 24,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Generate comprehensive monitoring reports.
    
    Args:
        hours_back: Number of hours to include in report
        include_recommendations: Whether to include monitoring recommendations
        
    Returns:
        Dict containing comprehensive monitoring report
    """
    try:
        engine = get_monitoring_engine()
        
        # Generate monitoring report
        report_data = engine.generate_monitoring_report(hours_back=hours_back)
        
        # Auto-commit and push results
        git_manager = get_git_workflow_manager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="monitoring_report_generate",
            test_results={
                "report_generated": True,
                "hours_back": hours_back,
                "include_recommendations": include_recommendations,
                "health_score": report_data.get("system_health", {}).get("health_score", 0),
                "active_alerts_count": len(report_data.get("active_alerts", [])),
                "recommendations_count": len(report_data.get("recommendations", []))
            }
        )
        
        return {
            "success": True,
            "report_data": report_data,
            "git_workflow_result": git_result,
            "message": f"Generated comprehensive monitoring report for {hours_back} hours"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate monitoring report: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate monitoring report: {e}"
        }
