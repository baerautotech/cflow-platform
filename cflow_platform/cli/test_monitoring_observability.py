#!/usr/bin/env python3
"""
Test script for BMAD Monitoring & Observability Framework

This script validates the monitoring and observability engine and MCP tools
for production monitoring, alerting system, and observability dashboard.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.direct_client import execute_mcp_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_monitoring_observability():
    """Test the monitoring and observability framework"""
    
    print("📊 BMAD Monitoring & Observability Framework Test")
    print("=" * 60)
    
    try:
        # Test 1: System Health Monitoring
        print("\n🏥 Testing System Health Monitoring...")
        health_result = await execute_mcp_tool(
            'bmad_monitoring_system_health',
            start_monitoring=False,
            interval_seconds=30.0
        )
        
        print(f"✅ System Health Result: {health_result.get('success', False)}")
        if health_result.get('system_health'):
            health = health_result['system_health']
            print(f"   Overall Status: {health.get('overall_status', 'unknown')}")
            print(f"   Health Score: {health.get('health_score', 0):.1f}%")
            print(f"   Total Checks: {health.get('total_checks', 0)}")
            print(f"   Critical Checks: {health.get('critical_checks', 0)}")
        
        # Test 2: Performance Metrics Collection
        print("\n⚡ Testing Performance Metrics Collection...")
        metrics_result = await execute_mcp_tool(
            'bmad_monitoring_performance_metrics',
            metric_names=['cpu_percent', 'memory_percent', 'disk_percent'],
            include_history=True,
            history_limit=5
        )
        
        print(f"✅ Performance Metrics Result: {metrics_result.get('success', False)}")
        if metrics_result.get('performance_metrics'):
            metrics = metrics_result['performance_metrics']
            print(f"   Metrics Collected: {len(metrics)}")
            for metric_name, metric_data in metrics.items():
                print(f"   {metric_name}: {metric_data.get('value', 0):.1f} {metric_data.get('unit', '')}")
        
        # Test 3: Resource Utilization Monitoring
        print("\n💻 Testing Resource Utilization Monitoring...")
        resource_result = await execute_mcp_tool(
            'bmad_monitoring_resource_utilization',
            include_trends=True,
            trend_hours=1
        )
        
        print(f"✅ Resource Utilization Result: {resource_result.get('success', False)}")
        if resource_result.get('resource_utilization'):
            resources = resource_result['resource_utilization']
            print(f"   Resources Monitored: {len(resources)}")
            for resource_name, resource_data in resources.items():
                print(f"   {resource_name}: {resource_data.get('value', 0):.1f} {resource_data.get('unit', '')}")
        
        # Test 4: Alerting Configuration
        print("\n🚨 Testing Alerting Configuration...")
        alert_rules = [
            {
                "rule_id": "test_cpu_alert",
                "metric_name": "CPU Usage",
                "threshold": 70.0,
                "severity": "medium",
                "description": "Test CPU Alert"
            },
            {
                "rule_id": "test_memory_alert",
                "metric_name": "Memory Usage",
                "threshold": 80.0,
                "severity": "high",
                "description": "Test Memory Alert"
            }
        ]
        
        alerting_config_result = await execute_mcp_tool(
            'bmad_alerting_configure',
            alert_rules=alert_rules
        )
        
        print(f"✅ Alerting Configuration Result: {alerting_config_result.get('success', False)}")
        print(f"   Rules Configured: {alerting_config_result.get('rules_configured', 0)}")
        print(f"   Total Rules: {alerting_config_result.get('total_rules', 0)}")
        
        # Test 5: Alerting System Test
        print("\n🔔 Testing Alerting System...")
        alerting_test_result = await execute_mcp_tool(
            'bmad_alerting_test',
            create_test_alert=True
        )
        
        print(f"✅ Alerting Test Result: {alerting_test_result.get('success', False)}")
        if alerting_test_result.get('test_result'):
            test_result = alerting_test_result['test_result']
            print(f"   Test Alert Created: {test_result.get('test_alert_created', False)}")
            print(f"   Active Alerts Count: {test_result.get('active_alerts_count', 0)}")
        
        # Test 6: Observability Dashboard
        print("\n📈 Testing Observability Dashboard...")
        dashboard_result = await execute_mcp_tool(
            'bmad_observability_dashboard',
            include_alerts=True,
            include_logs=True,
            log_limit=20
        )
        
        print(f"✅ Observability Dashboard Result: {dashboard_result.get('success', False)}")
        if dashboard_result.get('dashboard_data'):
            dashboard = dashboard_result['dashboard_data']
            system_health = dashboard.get('system_health', {})
            print(f"   Health Score: {system_health.get('health_score', 0):.1f}%")
            print(f"   Overall Status: {system_health.get('overall_status', 'unknown')}")
        
        # Test 7: Centralized Logging
        print("\n📝 Testing Centralized Logging...")
        logging_result = await execute_mcp_tool(
            'bmad_logging_centralized',
            level=None,
            component=None,
            limit=10,
            include_statistics=True
        )
        
        print(f"✅ Centralized Logging Result: {logging_result.get('success', False)}")
        print(f"   Logs Retrieved: {logging_result.get('total_returned', 0)}")
        if logging_result.get('statistics'):
            stats = logging_result['statistics']
            print(f"   Total Logs: {stats.get('total_logs', 0)}")
            print(f"   Level Distribution: {stats.get('level_distribution', {})}")
        
        # Test 8: Monitoring Report Generation
        print("\n📋 Testing Monitoring Report Generation...")
        report_result = await execute_mcp_tool(
            'bmad_monitoring_report_generate',
            hours_back=1,
            include_recommendations=True
        )
        
        print(f"✅ Monitoring Report Result: {report_result.get('success', False)}")
        if report_result.get('report_data'):
            report = report_result['report_data']
            system_health = report.get('system_health', {})
            print(f"   Health Score: {system_health.get('health_score', 0):.1f}%")
            print(f"   Active Alerts: {len(report.get('active_alerts', []))}")
            print(f"   Recommendations: {len(report.get('recommendations', []))}")
        
        # Summary
        print("\n🎉 Monitoring & Observability Framework Test Summary")
        print("=" * 60)
        
        test_results = [
            ("System Health Monitoring", health_result.get('success', False)),
            ("Performance Metrics Collection", metrics_result.get('success', False)),
            ("Resource Utilization Monitoring", resource_result.get('success', False)),
            ("Alerting Configuration", alerting_config_result.get('success', False)),
            ("Alerting System Test", alerting_test_result.get('success', False)),
            ("Observability Dashboard", dashboard_result.get('success', False)),
            ("Centralized Logging", logging_result.get('success', False)),
            ("Monitoring Report Generation", report_result.get('success', False))
        ]
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All monitoring and observability tests passed!")
            return True
        else:
            print("⚠️  Some monitoring and observability tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    
    print("Starting BMAD Monitoring & Observability Framework Test...")
    
    success = await test_monitoring_observability()
    
    if success:
        print("\n✅ Monitoring & Observability Framework is ready!")
        sys.exit(0)
    else:
        print("\n❌ Monitoring & Observability Framework has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
