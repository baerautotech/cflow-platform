# BMAD-Method Advanced Features Handlers

import asyncio
from typing import Dict, Any, Optional
from cflow_platform.core.expansion_pack_manager import bmad_expansion_pack_manager
from cflow_platform.core.hil_integration_system import bmad_hil_integration_system
from cflow_platform.core.brownfield_greenfield_workflows import bmad_brownfield_greenfield_workflow_engine
from cflow_platform.core.advanced_monitoring_analytics import bmad_advanced_monitoring_analytics_system, MetricType

class BMADAdvancedFeaturesHandlers:
    """Handlers for BMAD-Method Advanced Features with Cerebral extensions"""
    
    def __init__(self):
        self.expansion_pack_manager = bmad_expansion_pack_manager
        self.hil_integration_system = bmad_hil_integration_system
        self.workflow_engine = bmad_brownfield_greenfield_workflow_engine
        self.monitoring_analytics = bmad_advanced_monitoring_analytics_system

# Expansion Pack Handlers
async def bmad_expansion_discover_packs(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Discover all BMAD-Method expansion packs"""
    try:
        kwargs = kwargs or {}
        packs = await bmad_expansion_pack_manager.discover_expansion_packs()
        return {
            'success': True,
            'total_packs': len(packs),
            'packs': [
                {
                    'id': pack.id,
                    'name': pack.name,
                    'description': pack.description,
                    'version': pack.version,
                    'category': pack.category,
                    'status': pack.status
                }
                for pack in packs.values()
            ],
            'message': f'Successfully discovered {len(packs)} expansion packs'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_expansion_install_pack(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Install a BMAD-Method expansion pack"""
    try:
        kwargs = kwargs or {}
        pack_id = kwargs.get('pack_id')
        if not pack_id:
            return {'success': False, 'error': 'pack_id is required'}
        
        result = await bmad_expansion_pack_manager.install_expansion_pack(pack_id)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_expansion_activate_pack(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Activate a BMAD-Method expansion pack"""
    try:
        kwargs = kwargs or {}
        pack_id = kwargs.get('pack_id')
        if not pack_id:
            return {'success': False, 'error': 'pack_id is required'}
        
        result = await bmad_expansion_pack_manager.activate_expansion_pack(pack_id)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_expansion_deactivate_pack(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Deactivate a BMAD-Method expansion pack"""
    try:
        kwargs = kwargs or {}
        pack_id = kwargs.get('pack_id')
        if not pack_id:
            return {'success': False, 'error': 'pack_id is required'}
        
        result = await bmad_expansion_pack_manager.deactivate_expansion_pack(pack_id)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_expansion_remove_pack(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Remove a BMAD-Method expansion pack"""
    try:
        kwargs = kwargs or {}
        pack_id = kwargs.get('pack_id')
        if not pack_id:
            return {'success': False, 'error': 'pack_id is required'}
        
        result = await bmad_expansion_pack_manager.remove_expansion_pack(pack_id)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_expansion_get_pack_status(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get expansion pack manager status"""
    try:
        kwargs = kwargs or {}
        status = await bmad_expansion_pack_manager.get_expansion_pack_status()
        return {'success': True, 'status': status}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# HIL Integration Handlers
async def bmad_hil_create_session(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a new HIL session"""
    try:
        kwargs = kwargs or {}
        user_id = kwargs.get('user_id')
        task_type = kwargs.get('task_type')
        context = kwargs.get('context', {})
        
        if not user_id or not task_type:
            return {'success': False, 'error': 'user_id and task_type are required'}
        
        result = await bmad_hil_integration_system.create_hil_session(user_id, task_type, context)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_hil_update_session(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update a HIL session"""
    try:
        kwargs = kwargs or {}
        session_id = kwargs.get('session_id')
        updates = kwargs.get('updates', {})
        
        if not session_id:
            return {'success': False, 'error': 'session_id is required'}
        
        result = await bmad_hil_integration_system.update_hil_session(session_id, updates)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_hil_complete_session(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Complete a HIL session"""
    try:
        kwargs = kwargs or {}
        session_id = kwargs.get('session_id')
        result = kwargs.get('result', {})
        
        if not session_id:
            return {'success': False, 'error': 'session_id is required'}
        
        result = await bmad_hil_integration_system.complete_hil_session(session_id, result)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_hil_cancel_session(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Cancel a HIL session"""
    try:
        kwargs = kwargs or {}
        session_id = kwargs.get('session_id')
        reason = kwargs.get('reason')
        
        if not session_id:
            return {'success': False, 'error': 'session_id is required'}
        
        result = await bmad_hil_integration_system.cancel_hil_session(session_id, reason)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_hil_get_status(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get HIL integration system status"""
    try:
        kwargs = kwargs or {}
        status = await bmad_hil_integration_system.get_hil_status()
        return {'success': True, 'status': status}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Workflow Engine Handlers
async def bmad_workflow_discover(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Discover all BMAD-Method workflows"""
    try:
        kwargs = kwargs or {}
        workflows = await bmad_brownfield_greenfield_workflow_engine.discover_workflows()
        return {
            'success': True,
            'total_workflows': len(workflows),
            'workflows': [
                {
                    'workflow_id': workflow.workflow_id,
                    'name': workflow.name,
                    'workflow_type': workflow.workflow_type.value,
                    'status': workflow.status.value,
                    'steps': len(workflow.steps),
                    'dependencies': workflow.dependencies
                }
                for workflow in workflows.values()
            ],
            'message': f'Successfully discovered {len(workflows)} workflows'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_workflow_start(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Start a BMAD-Method workflow"""
    try:
        kwargs = kwargs or {}
        workflow_id = kwargs.get('workflow_id')
        context = kwargs.get('context', {})
        
        if not workflow_id:
            return {'success': False, 'error': 'workflow_id is required'}
        
        result = await bmad_brownfield_greenfield_workflow_engine.start_workflow(workflow_id, context)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_workflow_execute_step(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a workflow step"""
    try:
        kwargs = kwargs or {}
        workflow_id = kwargs.get('workflow_id')
        step_index = kwargs.get('step_index')
        step_data = kwargs.get('step_data', {})
        
        if not workflow_id or step_index is None:
            return {'success': False, 'error': 'workflow_id and step_index are required'}
        
        result = await bmad_brownfield_greenfield_workflow_engine.execute_workflow_step(workflow_id, step_index, step_data)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_workflow_complete(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Complete a BMAD-Method workflow"""
    try:
        kwargs = kwargs or {}
        workflow_id = kwargs.get('workflow_id')
        result = kwargs.get('result', {})
        
        if not workflow_id:
            return {'success': False, 'error': 'workflow_id is required'}
        
        result = await bmad_brownfield_greenfield_workflow_engine.complete_workflow(workflow_id, result)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_workflow_get_status(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get workflow engine status"""
    try:
        kwargs = kwargs or {}
        status = await bmad_brownfield_greenfield_workflow_engine.get_workflow_status()
        return {'success': True, 'status': status}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Monitoring & Analytics Handlers
async def bmad_monitoring_collect_metric(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Collect a monitoring metric"""
    try:
        kwargs = kwargs or {}
        name = kwargs.get('name')
        value = kwargs.get('value')
        metric_type = kwargs.get('metric_type')
        tags = kwargs.get('tags', {})
        
        if not name or value is None or not metric_type:
            return {'success': False, 'error': 'name, value, and metric_type are required'}
        
        # Convert string metric type to enum
        try:
            metric_type_enum = MetricType(metric_type)
        except ValueError:
            return {'success': False, 'error': f'Invalid metric_type: {metric_type}'}
        
        result = await bmad_advanced_monitoring_analytics_system.collect_metric(name, value, metric_type_enum, tags)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_monitoring_generate_report(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate an analytics report"""
    try:
        kwargs = kwargs or {}
        report_type = kwargs.get('report_type')
        time_range = kwargs.get('time_range')
        
        if not report_type:
            return {'success': False, 'error': 'report_type is required'}
        
        result = await bmad_advanced_monitoring_analytics_system.generate_analytics_report(report_type, time_range)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_monitoring_get_alerts(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get monitoring alerts"""
    try:
        kwargs = kwargs or {}
        level = kwargs.get('level')
        
        alerts = await bmad_advanced_monitoring_analytics_system.get_alerts(level)
        return {
            'success': True,
            'alerts': alerts,
            'total_alerts': len(alerts)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def bmad_monitoring_get_status(kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get monitoring system status"""
    try:
        kwargs = kwargs or {}
        status = await bmad_advanced_monitoring_analytics_system.get_monitoring_status()
        return {'success': True, 'status': status}
    except Exception as e:
        return {'success': False, 'error': str(e)}
