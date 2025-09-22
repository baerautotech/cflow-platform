# BMAD Master Health Monitoring System

import asyncio
import json
import os
import psutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    PERSONA_WRAPPER = "persona_wrapper"
    TOOL_WRAPPER = "tool_wrapper"
    TESTING_FRAMEWORK = "testing_framework"
    ADVANCED_FEATURES = "advanced_features"
    MONITORING = "monitoring"
    MCP_INTEGRATION = "mcp_integration"
    CEREBRAL_INTEGRATION = "cerebral_integration"

@dataclass
class HealthMetric:
    """Represents a health metric"""
    component: str
    metric_name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime
    status: HealthStatus

@dataclass
class ComponentHealth:
    """Represents the health status of a component"""
    component_type: ComponentType
    status: HealthStatus
    metrics: List[HealthMetric]
    last_check: datetime
    error_count: int = 0
    uptime: str = "0:00:00"

class BMADMasterHealthMonitoring:
    """Health monitoring system for BMAD Master"""
    
    def __init__(self):
        self.components = {}
        self.metrics_history = []
        self.alerts = []
        self.start_time = datetime.now()
        self.check_interval = 30  # seconds
        self.monitoring_active = False
        
        # Health thresholds
        self.thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0},
            'response_time': {'warning': 1000.0, 'critical': 5000.0},  # milliseconds
            'error_rate': {'warning': 5.0, 'critical': 10.0},  # percentage
            'uptime': {'warning': 3600.0, 'critical': 1800.0}  # seconds
        }
        
        # Initialize component monitoring
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize component monitoring"""
        self.components = {
            ComponentType.PERSONA_WRAPPER: ComponentHealth(
                component_type=ComponentType.PERSONA_WRAPPER,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            ),
            ComponentType.TOOL_WRAPPER: ComponentHealth(
                component_type=ComponentType.TOOL_WRAPPER,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            ),
            ComponentType.TESTING_FRAMEWORK: ComponentHealth(
                component_type=ComponentType.TESTING_FRAMEWORK,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            ),
            ComponentType.ADVANCED_FEATURES: ComponentHealth(
                component_type=ComponentType.ADVANCED_FEATURES,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                uptime="0:00:00"
            ),
            ComponentType.MONITORING: ComponentHealth(
                component_type=ComponentType.MONITORING,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            ),
            ComponentType.MCP_INTEGRATION: ComponentHealth(
                component_type=ComponentType.MCP_INTEGRATION,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            ),
            ComponentType.CEREBRAL_INTEGRATION: ComponentHealth(
                component_type=ComponentType.CEREBRAL_INTEGRATION,
                status=HealthStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                error_count=0,
                uptime="0:00:00"
            )
        }
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """Start health monitoring"""
        try:
            print('🏥 BMAD Master: Starting health monitoring...')
            
            self.monitoring_active = True
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            print('✅ BMAD Master: Health monitoring started!')
            
            return {
                'success': True,
                'monitoring_active': self.monitoring_active,
                'check_interval': self.check_interval,
                'message': 'Health monitoring started successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to start health monitoring'
            }
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop health monitoring"""
        try:
            print('🛑 BMAD Master: Stopping health monitoring...')
            
            self.monitoring_active = False
            
            print('✅ BMAD Master: Health monitoring stopped!')
            
            return {
                'success': True,
                'monitoring_active': self.monitoring_active,
                'message': 'Health monitoring stopped successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to stop health monitoring'
            }
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._check_all_components()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f'❌ BMAD Master: Monitoring loop error: {e}')
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_components(self):
        """Check health of all components"""
        try:
            # Check system metrics
            await self._check_system_metrics()
            
            # Check BMAD components
            await self._check_bmad_components()
            
            # Check MCP integration
            await self._check_mcp_integration()
            
            # Check Cerebral integration
            await self._check_cerebral_integration()
            
            # Update component statuses
            await self._update_component_statuses()
            
        except Exception as e:
            print(f'❌ BMAD Master: Component check error: {e}')
    
    async def _check_system_metrics(self):
        """Check system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_metric = HealthMetric(
                component='system',
                metric_name='cpu_usage',
                value=cpu_percent,
                unit='percent',
                threshold_warning=self.thresholds['cpu_usage']['warning'],
                threshold_critical=self.thresholds['cpu_usage']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status(cpu_percent, 'cpu_usage')
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = HealthMetric(
                component='system',
                metric_name='memory_usage',
                value=memory.percent,
                unit='percent',
                threshold_warning=self.thresholds['memory_usage']['warning'],
                threshold_critical=self.thresholds['memory_usage']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status(memory.percent, 'memory_usage')
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_metric = HealthMetric(
                component='system',
                metric_name='disk_usage',
                value=(disk.used / disk.total) * 100,
                unit='percent',
                threshold_warning=self.thresholds['disk_usage']['warning'],
                threshold_critical=self.thresholds['disk_usage']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status((disk.used / disk.total) * 100, 'disk_usage')
            )
            
            # Store metrics
            self.metrics_history.extend([cpu_metric, memory_metric, disk_metric])
            
        except Exception as e:
            print(f'❌ BMAD Master: System metrics check error: {e}')
    
    async def _check_bmad_components(self):
        """Check BMAD component health"""
        try:
            # Check persona wrapper
            await self._check_persona_wrapper()
            
            # Check tool wrapper
            await self._check_tool_wrapper()
            
            # Check testing framework
            await self._check_testing_framework()
            
            # Check advanced features
            await self._check_advanced_features()
            
        except Exception as e:
            print(f'❌ BMAD Master: BMAD components check error: {e}')
    
    async def _check_persona_wrapper(self):
        """Check persona wrapper health"""
        try:
            from cflow_platform.core.bmad_persona_wrapper import bmad_persona_wrapper
            
            start_time = time.time()
            status = await bmad_persona_wrapper.get_status()
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Create response time metric
            response_metric = HealthMetric(
                component='persona_wrapper',
                metric_name='response_time',
                value=response_time,
                unit='milliseconds',
                threshold_warning=self.thresholds['response_time']['warning'],
                threshold_critical=self.thresholds['response_time']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status(response_time, 'response_time')
            )
            
            # Create functionality metric
            functionality_metric = HealthMetric(
                component='persona_wrapper',
                metric_name='functionality',
                value=100.0 if status.get('success', False) else 0.0,
                unit='percent',
                threshold_warning=90.0,
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=self._get_metric_status(100.0 if status.get('success', False) else 0.0, 'error_rate')
            )
            
            # Update component
            self.components[ComponentType.PERSONA_WRAPPER].metrics = [response_metric, functionality_metric]
            self.components[ComponentType.PERSONA_WRAPPER].last_check = datetime.now()
            
            if not status.get('success', False):
                self.components[ComponentType.PERSONA_WRAPPER].error_count += 1
            
            self.metrics_history.extend([response_metric, functionality_metric])
            
        except Exception as e:
            print(f'❌ BMAD Master: Persona wrapper check error: {e}')
            self.components[ComponentType.PERSONA_WRAPPER].error_count += 1
    
    async def _check_tool_wrapper(self):
        """Check tool wrapper health"""
        try:
            from cflow_platform.core.bmad_tool_wrapper import bmad_tool_wrapper
            
            start_time = time.time()
            status = await bmad_tool_wrapper.get_status()
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Create response time metric
            response_metric = HealthMetric(
                component='tool_wrapper',
                metric_name='response_time',
                value=response_time,
                unit='milliseconds',
                threshold_warning=self.thresholds['response_time']['warning'],
                threshold_critical=self.thresholds['response_time']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status(response_time, 'response_time')
            )
            
            # Create functionality metric
            functionality_metric = HealthMetric(
                component='tool_wrapper',
                metric_name='functionality',
                value=100.0 if status.get('success', False) else 0.0,
                unit='percent',
                threshold_warning=90.0,
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=self._get_metric_status(100.0 if status.get('success', False) else 0.0, 'error_rate')
            )
            
            # Update component
            self.components[ComponentType.TOOL_WRAPPER].metrics = [response_metric, functionality_metric]
            self.components[ComponentType.TOOL_WRAPPER].last_check = datetime.now()
            
            if not status.get('success', False):
                self.components[ComponentType.TOOL_WRAPPER].error_count += 1
            
            self.metrics_history.extend([response_metric, functionality_metric])
            
        except Exception as e:
            print(f'❌ BMAD Master: Tool wrapper check error: {e}')
            self.components[ComponentType.TOOL_WRAPPER].error_count += 1
    
    async def _check_testing_framework(self):
        """Check testing framework health"""
        try:
            # Simulate testing framework health check
            functionality_metric = HealthMetric(
                component='testing_framework',
                metric_name='functionality',
                value=100.0,  # Assume healthy
                unit='percent',
                threshold_warning=90.0,
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=HealthStatus.HEALTHY
            )
            
            # Update component
            self.components[ComponentType.TESTING_FRAMEWORK].metrics = [functionality_metric]
            self.components[ComponentType.TESTING_FRAMEWORK].last_check = datetime.now()
            
            self.metrics_history.append(functionality_metric)
            
        except Exception as e:
            print(f'❌ BMAD Master: Testing framework check error: {e}')
            self.components[ComponentType.TESTING_FRAMEWORK].error_count += 1
    
    async def _check_advanced_features(self):
        """Check advanced features health"""
        try:
            # Simulate advanced features health check
            functionality_metric = HealthMetric(
                component='advanced_features',
                metric_name='functionality',
                value=100.0,  # Assume healthy
                unit='percent',
                threshold_warning=90.0,
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=HealthStatus.HEALTHY
            )
            
            # Update component
            self.components[ComponentType.ADVANCED_FEATURES].metrics = [functionality_metric]
            self.components[ComponentType.ADVANCED_FEATURES].last_check = datetime.now()
            
            self.metrics_history.append(functionality_metric)
            
        except Exception as e:
            print(f'❌ BMAD Master: Advanced features check error: {e}')
            self.components[ComponentType.ADVANCED_FEATURES].error_count += 1
    
    async def _check_mcp_integration(self):
        """Check MCP integration health"""
        try:
            from cflow_platform.core.tool_registry import ToolRegistry
            
            start_time = time.time()
            tools = ToolRegistry.get_tools_for_mcp()
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Create response time metric
            response_metric = HealthMetric(
                component='mcp_integration',
                metric_name='response_time',
                value=response_time,
                unit='milliseconds',
                threshold_warning=self.thresholds['response_time']['warning'],
                threshold_critical=self.thresholds['response_time']['critical'],
                timestamp=datetime.now(),
                status=self._get_metric_status(response_time, 'response_time')
            )
            
            # Create tool count metric
            tool_count_metric = HealthMetric(
                component='mcp_integration',
                metric_name='tool_count',
                value=len(tools),
                unit='count',
                threshold_warning=100.0,  # Minimum expected tools
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=self._get_metric_status(len(tools), 'error_rate')
            )
            
            # Update component
            self.components[ComponentType.MCP_INTEGRATION].metrics = [response_metric, tool_count_metric]
            self.components[ComponentType.MCP_INTEGRATION].last_check = datetime.now()
            
            self.metrics_history.extend([response_metric, tool_count_metric])
            
        except Exception as e:
            print(f'❌ BMAD Master: MCP integration check error: {e}')
            self.components[ComponentType.MCP_INTEGRATION].error_count += 1
    
    async def _check_cerebral_integration(self):
        """Check Cerebral integration health"""
        try:
            # Simulate Cerebral integration health check
            functionality_metric = HealthMetric(
                component='cerebral_integration',
                metric_name='functionality',
                value=100.0,  # Assume healthy
                unit='percent',
                threshold_warning=90.0,
                threshold_critical=50.0,
                timestamp=datetime.now(),
                status=HealthStatus.HEALTHY
            )
            
            # Update component
            self.components[ComponentType.CEREBRAL_INTEGRATION].metrics = [functionality_metric]
            self.components[ComponentType.CEREBRAL_INTEGRATION].last_check = datetime.now()
            
            self.metrics_history.append(functionality_metric)
            
        except Exception as e:
            print(f'❌ BMAD Master: Cerebral integration check error: {e}')
            self.components[ComponentType.CEREBRAL_INTEGRATION].error_count += 1
    
    async def _update_component_statuses(self):
        """Update component statuses based on metrics"""
        try:
            for component_type, component in self.components.items():
                if not component.metrics:
                    component.status = HealthStatus.UNKNOWN
                    continue
                
                # Determine status based on metrics
                critical_count = sum(1 for metric in component.metrics if metric.status == HealthStatus.CRITICAL)
                warning_count = sum(1 for metric in component.metrics if metric.status == HealthStatus.WARNING)
                
                if critical_count > 0:
                    component.status = HealthStatus.CRITICAL
                elif warning_count > 0:
                    component.status = HealthStatus.WARNING
                else:
                    component.status = HealthStatus.HEALTHY
                
                # Update uptime
                uptime_delta = datetime.now() - self.start_time
                component.uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
                
        except Exception as e:
            print(f'❌ BMAD Master: Component status update error: {e}')
    
    def _get_metric_status(self, value: float, metric_type: str) -> HealthStatus:
        """Get health status for a metric value"""
        try:
            thresholds = self.thresholds.get(metric_type, {'warning': 0, 'critical': 0})
            
            if value >= thresholds['critical']:
                return HealthStatus.CRITICAL
            elif value >= thresholds['warning']:
                return HealthStatus.WARNING
            else:
                return HealthStatus.HEALTHY
                
        except Exception:
            return HealthStatus.UNKNOWN
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        try:
            # Calculate overall status
            status_counts = {}
            for component in self.components.values():
                status = component.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Determine overall status
            if status_counts.get('critical', 0) > 0:
                overall_status = HealthStatus.CRITICAL
            elif status_counts.get('warning', 0) > 0:
                overall_status = HealthStatus.WARNING
            elif status_counts.get('unknown', 0) > 0:
                overall_status = HealthStatus.UNKNOWN
            else:
                overall_status = HealthStatus.HEALTHY
            
            # Get recent metrics (last 10)
            recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
            
            return {
                'success': True,
                'overall_status': overall_status.value,
                'status_counts': status_counts,
                'components': {
                    component_type.value: {
                        'status': component.status.value,
                        'error_count': component.error_count,
                        'uptime': component.uptime,
                        'last_check': component.last_check.isoformat(),
                        'metrics_count': len(component.metrics)
                    }
                    for component_type, component in self.components.items()
                },
                'recent_metrics': [
                    {
                        'component': metric.component,
                        'metric_name': metric.metric_name,
                        'value': metric.value,
                        'unit': metric.unit,
                        'status': metric.status.value,
                        'timestamp': metric.timestamp.isoformat()
                    }
                    for metric in recent_metrics
                ],
                'monitoring_active': self.monitoring_active,
                'uptime': str(datetime.now() - self.start_time).split('.')[0],
                'message': 'Health status retrieved successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get health status'
            }
    
    async def get_component_health(self, component_type: ComponentType) -> Dict[str, Any]:
        """Get health status for a specific component"""
        try:
            if component_type not in self.components:
                return {
                    'success': False,
                    'error': f'Component {component_type.value} not found',
                    'message': 'Component not found'
                }
            
            component = self.components[component_type]
            
            return {
                'success': True,
                'component_type': component_type.value,
                'status': component.status.value,
                'error_count': component.error_count,
                'uptime': component.uptime,
                'last_check': component.last_check.isoformat(),
                'metrics': [
                    {
                        'metric_name': metric.metric_name,
                        'value': metric.value,
                        'unit': metric.unit,
                        'status': metric.status.value,
                        'timestamp': metric.timestamp.isoformat()
                    }
                    for metric in component.metrics
                ],
                'message': f'Health status for {component_type.value} retrieved successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to get health status for {component_type.value}'
            }
    
    async def get_metrics_history(self, component: str = None, metric_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get metrics history with optional filtering"""
        try:
            # Filter metrics by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_metrics = [
                metric for metric in self.metrics_history
                if metric.timestamp >= cutoff_time
            ]
            
            # Filter by component
            if component:
                filtered_metrics = [
                    metric for metric in filtered_metrics
                    if metric.component == component
                ]
            
            # Filter by metric name
            if metric_name:
                filtered_metrics = [
                    metric for metric in filtered_metrics
                    if metric.metric_name == metric_name
                ]
            
            return {
                'success': True,
                'metrics': [
                    {
                        'component': metric.component,
                        'metric_name': metric.metric_name,
                        'value': metric.value,
                        'unit': metric.unit,
                        'status': metric.status.value,
                        'timestamp': metric.timestamp.isoformat()
                    }
                    for metric in filtered_metrics
                ],
                'total_metrics': len(filtered_metrics),
                'time_range_hours': hours,
                'message': 'Metrics history retrieved successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get metrics history'
            }

# Global health monitoring instance
bmad_master_health_monitoring = BMADMasterHealthMonitoring()
