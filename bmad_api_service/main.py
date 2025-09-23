"""
BMAD API Service

This service provides HTTP endpoints for all BMAD tools,
integrating with vendor BMAD workflows and providing
authentication, validation, and error handling.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .auth_service import JWTAuthService, get_current_user
from .vendor_bmad_integration import VendorBMADIntegration, ProductionModeViolationError
from .error_handler import ErrorHandler
from .performance_monitor import PerformanceMonitor
from .performance_optimizer import performance_optimizer, cached, rate_limited, circuit_breaker
from .analytics_engine import analytics_engine, track_api_request, track_workflow_start, track_workflow_complete, track_workflow_fail
from .supabase_task_integration import (
    bmad_supabase_task_manager, 
    create_bmad_prd_task, 
    create_bmad_architecture_task, 
    create_bmad_story_task,
    track_bmad_workflow_execution
)
from .yaml_task_templates import bmad_template_manager
from .persona_endpoints import router as persona_router
from .provider_router import provider_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BMAD API Service",
    description="HTTP API service for BMAD tool execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure based on deployment
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance optimization middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Performance optimization middleware."""
    start_time = time.time()
    
    # Add optimizer to request state
    request.state.optimizer = performance_optimizer
    
    # Update request statistics
    performance_optimizer._stats['total_requests'] += 1
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        performance_optimizer._stats['avg_response_time'] = (
            (performance_optimizer._stats['avg_response_time'] * 
             (performance_optimizer._stats['total_requests'] - 1) + process_time) /
            performance_optimizer._stats['total_requests']
        )
        
        # Track API request analytics
        try:
            user_id = getattr(request.state, 'user_id', None)
            session_id = getattr(request.state, 'session_id', None)
            track_api_request(
                user_id=user_id,
                session_id=session_id,
                endpoint=request.url.path,
                duration_ms=process_time * 1000,
                success=response.status_code < 400
            )
        except Exception as e:
            logger.warning(f"Failed to track API request analytics: {e}")
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Cache-Hit-Rate"] = str(
            performance_optimizer.get_stats()['cache']['hit_rate']
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Performance middleware error: {e}")
        return await call_next(request)

# Initialize services
auth_service = JWTAuthService()
vendor_bmad = VendorBMADIntegration()
error_handler = ErrorHandler()
performance_monitor = PerformanceMonitor()

# BMAD tool registry - maps tool names to vendor BMAD workflows
BMAD_TOOLS = {
    # Core BMAD Tools
    "bmad_prd_create": "vendor/bmad/bmad-core/workflows/greenfield-prd.yaml",
    "bmad_prd_update": "vendor/bmad/bmad-core/workflows/greenfield-prd.yaml",
    "bmad_prd_get": "vendor/bmad/bmad-core/workflows/greenfield-prd.yaml",
    "bmad_arch_create": "vendor/bmad/bmad-core/workflows/greenfield-arch.yaml",
    "bmad_arch_update": "vendor/bmad/bmad-core/workflows/greenfield-arch.yaml",
    "bmad_arch_get": "vendor/bmad/bmad-core/workflows/greenfield-arch.yaml",
    "bmad_story_create": "vendor/bmad/bmad-core/workflows/greenfield-story.yaml",
    "bmad_story_update": "vendor/bmad/bmad-core/workflows/greenfield-story.yaml",
    "bmad_story_get": "vendor/bmad/bmad-core/workflows/greenfield-story.yaml",
    
    # Workflow Testing Tools
    "bmad_workflow_test_run_complete": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_create_suite": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_run_suite": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_list_suites": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_get_history": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_get_statistics": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    "bmad_workflow_test_validate_step": "vendor/bmad/bmad-core/workflows/workflow-testing.yaml",
    
    # Scenario Testing Tools
    "bmad_scenario_create": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    "bmad_scenario_execute": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    "bmad_scenario_list": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    "bmad_scenario_validate": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    "bmad_scenario_report": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    "bmad_scenario_get_history": "vendor/bmad/bmad-core/workflows/scenario-testing.yaml",
    
    # Regression Testing Tools
    "bmad_regression_test_run": "vendor/bmad/bmad-core/workflows/regression-testing.yaml",
    "bmad_regression_baseline_establish": "vendor/bmad/bmad-core/workflows/regression-testing.yaml",
    "bmad_regression_baseline_list": "vendor/bmad/bmad-core/workflows/regression-testing.yaml",
    "bmad_regression_report_generate": "vendor/bmad/bmad-core/workflows/regression-testing.yaml",
    "bmad_regression_history_get": "vendor/bmad/bmad-core/workflows/regression-testing.yaml",
    
    # Git Workflow Tools
    "bmad_git_auto_commit": "vendor/bmad/bmad-core/workflows/git-workflow.yaml",
    "bmad_git_auto_push": "vendor/bmad/bmad-core/workflows/git-workflow.yaml",
    "bmad_git_workflow_status": "vendor/bmad/bmad-core/workflows/git-workflow.yaml",
    "bmad_git_workflow_configure": "vendor/bmad/bmad-core/workflows/git-workflow.yaml",
    
    # Performance Validation Tools
    "bmad_performance_load_test": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_stress_test": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_scalability_test": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_metrics_collect": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_slo_validate": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_report_generate": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    "bmad_performance_history_get": "vendor/bmad/bmad-core/workflows/performance-validation.yaml",
    
    # Integration Testing Tools
    "bmad_integration_cross_component_test": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    "bmad_integration_api_test": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    "bmad_integration_database_test": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    "bmad_integration_full_suite": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    "bmad_integration_report_generate": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    "bmad_integration_history_get": "vendor/bmad/bmad-core/workflows/integration-testing.yaml",
    
    # User Acceptance Testing Tools
    "bmad_uat_scenario_test": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    "bmad_uat_usability_test": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    "bmad_uat_accessibility_test": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    "bmad_uat_full_suite": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    "bmad_uat_report_generate": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    "bmad_uat_history_get": "vendor/bmad/bmad-core/workflows/user-acceptance-testing.yaml",
    
    # Monitoring & Observability Tools
    "bmad_monitoring_system_health": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_monitoring_performance_metrics": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_monitoring_resource_utilization": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_alerting_configure": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_alerting_test": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_observability_dashboard": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_logging_centralized": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    "bmad_monitoring_report_generate": "vendor/bmad/bmad-core/workflows/monitoring-observability.yaml",
    
    # Expansion Pack Tools
    "bmad_expansion_system_status": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_install": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_uninstall": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_list": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_activate": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_deactivate": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_update": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    "bmad_expansion_pack_validate": "vendor/bmad/bmad-core/workflows/expansion-pack-system.yaml",
    
    # HIL Integration Tools
    "bmad_hil_start_session": "vendor/bmad/bmad-core/workflows/hil-integration.yaml",
    "bmad_hil_continue_session": "vendor/bmad/bmad-core/workflows/hil-integration.yaml",
    "bmad_hil_end_session": "vendor/bmad/bmad-core/workflows/hil-integration.yaml",
    "bmad_hil_session_status": "vendor/bmad/bmad-core/workflows/hil-integration.yaml",
    
    # Brownfield Support Tools
    "bmad_project_type_detect": "vendor/bmad/bmad-core/workflows/project-type-detection.yaml",
    "bmad_brownfield_document_project": "vendor/bmad/bmad-core/tasks/document-project.md",
    "bmad_brownfield_prd_create": "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
    "bmad_brownfield_arch_create": "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
    "bmad_brownfield_story_create": "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
    
    # Expansion Pack Management Tools
    "bmad_expansion_packs_list_available": "vendor/bmad/tools/installer/lib/resource-locator.js",
    "bmad_expansion_packs_get_details": "vendor/bmad/tools/installer/lib/resource-locator.js",
    "bmad_expansion_packs_install": "vendor/bmad/tools/installer/lib/installer.js",
    "bmad_expansion_packs_enable": "vendor/bmad/tools/installer/lib/installer.js",
    "bmad_expansion_packs_uninstall": "vendor/bmad/tools/installer/lib/installer.js",
    "bmad_expansion_packs_list_installed": "vendor/bmad/tools/installer/lib/installer.js",
}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bmad-api",
        "timestamp": datetime.utcnow().isoformat(),
        "tools_count": len(BMAD_TOOLS),
        "version": "1.0.0"
    }


@app.get("/bmad/analytics")
async def get_analytics_report():
    """Get comprehensive analytics report"""
    try:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics_engine.get_comprehensive_report()
        }
    except Exception as e:
        logger.error(f"Analytics report failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics report")


@app.get("/bmad/analytics/real-time")
async def get_real_time_analytics():
    """Get real-time analytics metrics"""
    try:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": analytics_engine.get_real_time_metrics()
        }
    except Exception as e:
        logger.error(f"Real-time analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time analytics")


@app.get("/bmad/analytics/user/{user_id}")
async def get_user_analytics(user_id: str):
    """Get analytics for a specific user"""
    try:
        user_analytics = analytics_engine.get_user_analytics(user_id)
        if not user_analytics:
            raise HTTPException(status_code=404, detail="User analytics not found")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "user_analytics": user_analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")


@app.get("/bmad/analytics/workflow/{workflow_name}")
async def get_workflow_analytics(workflow_name: str):
    """Get analytics for a specific workflow"""
    try:
        workflow_analytics = analytics_engine.get_workflow_analytics(workflow_name)
        if not workflow_analytics:
            raise HTTPException(status_code=404, detail="Workflow analytics not found")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_analytics": workflow_analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow analytics")


@app.get("/bmad/tasks")
async def list_bmad_tasks(
    project_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    workflow_type: Optional[str] = None
):
    """List BMAD tasks from Supabase"""
    try:
        tasks = await bmad_supabase_task_manager.list_bmad_tasks(
            project_id=project_id,
            tenant_id=tenant_id,
            status=status,
            workflow_type=workflow_type
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "tasks": tasks,
            "count": len(tasks),
            "filters": {
                "project_id": project_id,
                "tenant_id": tenant_id,
                "status": status,
                "workflow_type": workflow_type
            }
        }
    except Exception as e:
        logger.error(f"Failed to list BMAD tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list BMAD tasks")


@app.get("/bmad/tasks/{task_id}")
async def get_bmad_task(task_id: str):
    """Get a specific BMAD task"""
    try:
        task = await bmad_supabase_task_manager.get_bmad_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="BMAD task not found")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "task": task
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get BMAD task: {e}")
        raise HTTPException(status_code=500, detail="Failed to get BMAD task")


@app.post("/bmad/tasks/{task_id}/status")
async def update_bmad_task_status(
    task_id: str,
    request_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update BMAD task status"""
    try:
        status = request_data.get("status")
        metadata = request_data.get("metadata", {})
        
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Add user info to metadata
        metadata["updated_by"] = current_user.get("user_id")
        metadata["updated_at"] = datetime.utcnow().isoformat()
        
        success = await bmad_supabase_task_manager.update_bmad_task_status(
            task_id=task_id,
            status=status,
            metadata=metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task status")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Task {task_id} status updated to {status}",
            "task_id": task_id,
            "new_status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update BMAD task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")


@app.get("/bmad/templates")
async def list_bmad_templates():
    """List available BMAD task templates"""
    try:
        templates = bmad_template_manager.list_templates()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "templates": templates,
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Failed to list BMAD templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@app.post("/bmad/templates/{template_id}/create-task")
async def create_task_from_template(
    template_id: str,
    request_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a task from a BMAD template"""
    try:
        project_id = request_data.get("project_id")
        tenant_id = request_data.get("tenant_id")
        parameters = request_data.get("parameters", {})
        
        if not project_id or not tenant_id:
            raise HTTPException(status_code=400, detail="project_id and tenant_id are required")
        
        # Add user info to parameters
        parameters["created_by"] = current_user.get("user_id")
        parameters["created_at"] = datetime.utcnow().isoformat()
        
        task_id = await bmad_supabase_task_manager.create_bmad_task_from_template(
            template_id=template_id,
            project_id=project_id,
            tenant_id=tenant_id,
            parameters=parameters
        )
        
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to create task from template")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Task created from template {template_id}",
            "task_id": task_id,
            "template_id": template_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task from template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task from template")


@app.get("/bmad/task-management/stats")
async def get_bmad_task_stats():
    """Get BMAD task management statistics"""
    try:
        stats = bmad_supabase_task_manager.get_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get BMAD task stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task stats")


@app.get("/bmad/analytics/provider/{provider_name}")
async def get_provider_analytics(provider_name: str):
    """Get analytics for a specific provider"""
    try:
        provider_analytics = analytics_engine.get_provider_analytics(provider_name)
        if not provider_analytics:
            raise HTTPException(status_code=404, detail="Provider analytics not found")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "provider_analytics": provider_analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provider analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider analytics")


@app.get("/bmad/performance")
async def get_performance_stats():
    """Get performance statistics"""
    try:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": performance_optimizer.get_stats()
        }
    except Exception as e:
        logger.error(f"Performance stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance stats")


@app.get("/bmad/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check vendor BMAD integration
        vendor_status = await vendor_bmad.health_check()
        
        return {
            "status": "healthy",
            "service": "bmad-api",
            "timestamp": datetime.utcnow().isoformat(),
            "tools_count": len(BMAD_TOOLS),
            "vendor_bmad_status": vendor_status,
            "provider_router": provider_router.get_provider_status(),
            "performance": performance_optimizer.get_stats(),
            "analytics": analytics_engine.get_real_time_metrics(),
            "task_management": bmad_supabase_task_manager.get_stats(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "bmad-api",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }


@app.get("/bmad/providers/status")
async def get_provider_status():
    """Get status of all LLM providers."""
    try:
        status = provider_router.get_provider_status()
        return {
            "status": "success",
            "providers": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/bmad/providers/test")
async def test_provider(provider_id: str = None):
    """Test a specific provider or all providers."""
    try:
        if provider_id:
            # Test specific provider
            test_request = {
                "messages": [{"role": "user", "content": "Hello, this is a test message."}],
                "max_tokens": 10
            }
            result = await provider_router.route_request(test_request, provider_id)
            return {
                "status": "success",
                "provider_id": provider_id,
                "test_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Test all providers
            status = provider_router.get_provider_status()
            return {
                "status": "success",
                "message": "Provider status retrieved",
                "providers": status,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Provider test failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/bmad/tools")
async def list_bmad_tools():
    """List all available BMAD tools"""
    return {
        "tools": list(BMAD_TOOLS.keys()),
        "count": len(BMAD_TOOLS),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/bmad/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get information about a specific BMAD tool"""
    if tool_name not in BMAD_TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    workflow_path = BMAD_TOOLS[tool_name]
    
    return {
        "tool_name": tool_name,
        "workflow_path": workflow_path,
        "available": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/bmad/tools/{tool_name}/execute")
async def execute_bmad_tool(
    tool_name: str, 
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute a BMAD tool via vendor BMAD workflows"""
    start_time = time.time()
    
    try:
        # Validate tool exists
        if tool_name not in BMAD_TOOLS:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        logger.info(f"Executing BMAD tool: {tool_name} for user: {current_user.get('user_id', 'unknown')}")
        
        # Execute vendor BMAD workflow
        workflow_path = BMAD_TOOLS[tool_name]
        result = await vendor_bmad.execute_workflow(workflow_path, arguments, current_user)
        
        # Record performance metrics
        execution_time = time.time() - start_time
        await performance_monitor.record_execution_time(tool_name, execution_time)
        
        logger.info(f"BMAD tool execution successful: {tool_name} (took {execution_time:.2f}s)")
        
        return {
            "result": result,
            "success": True,
            "tool": tool_name,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user.get("user_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        error_result = await error_handler.handle_error(e, {
            "tool_name": tool_name,
            "user_id": current_user.get("user_id"),
            "execution_time": execution_time
        })
        
        logger.error(f"BMAD tool execution failed: {tool_name} - {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "success": False,
                "tool": tool_name,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user.get("user_id")
            }
        )


@app.get("/bmad/stats")
async def get_stats():
    """Get service statistics"""
    try:
        performance_stats = await performance_monitor.get_stats()
        
        return {
            "service": "bmad-api",
            "tools_count": len(BMAD_TOOLS),
            "performance_stats": performance_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bmad/metrics")
async def get_metrics():
    """Get performance metrics"""
    try:
        metrics = await performance_monitor.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BMAD BROWFIELD SUPPORT ENDPOINTS
# ============================================================================

@app.post("/bmad/project-type/detect")
async def detect_project_type(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Detect if project is greenfield or brownfield"""
    try:
        body = await request.json()
        project_info = body.get("project_info", {})
        
        # Analyze project characteristics to determine type
        is_brownfield = await vendor_bmad.detect_project_type(project_info)
        project_type = "brownfield" if is_brownfield else "greenfield"
        
        return {
            "project_type": project_type,
            "confidence": 0.85,  # Confidence score
            "analysis": {
                "has_existing_code": project_info.get("has_existing_code", False),
                "has_documentation": project_info.get("has_documentation", False),
                "has_tests": project_info.get("has_tests", False),
                "project_size": project_info.get("project_size", "unknown")
            },
            "recommended_workflow": f"bmad_{project_type}_workflow",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Project type detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/brownfield/document-project")
async def document_existing_project(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Document an existing project for brownfield development"""
    try:
        body = await request.json()
        project_path = body.get("project_path")
        focus_areas = body.get("focus_areas", [])
        output_format = body.get("output_format", "single_document")
        
        if not project_path:
            raise HTTPException(status_code=400, detail="project_path is required")
        
        # Execute document-project workflow
        result = await vendor_bmad.execute_workflow(
            "vendor/bmad/bmad-core/tasks/document-project.md",
            {
                "project_path": project_path,
                "focus_areas": focus_areas,
                "output_format": output_format,
                "user_id": current_user.get("user_id")
            },
            current_user
        )
        
        return {
            "success": True,
            "documentation": result,
            "project_path": project_path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Project documentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/brownfield/prd-create")
async def create_brownfield_prd(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create PRD for brownfield project enhancement"""
    try:
        body = await request.json()
        project_name = body.get("project_name")
        enhancement_scope = body.get("enhancement_scope", {})
        existing_analysis = body.get("existing_analysis", {})
        
        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        
        # Execute brownfield PRD workflow
        result = await vendor_bmad.execute_workflow(
            "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
            {
                "project_name": project_name,
                "enhancement_scope": enhancement_scope,
                "existing_analysis": existing_analysis,
                "template": "brownfield-prd-tmpl",
                "user_id": current_user.get("user_id")
            },
            current_user
        )
        
        return {
            "success": True,
            "prd": result,
            "project_name": project_name,
            "type": "brownfield",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Brownfield PRD creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/brownfield/arch-create")
async def create_brownfield_architecture(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create architecture for brownfield project enhancement"""
    try:
        body = await request.json()
        project_name = body.get("project_name")
        prd_reference = body.get("prd_reference")
        integration_strategy = body.get("integration_strategy", {})
        
        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        
        # Execute brownfield architecture workflow
        result = await vendor_bmad.execute_workflow(
            "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
            {
                "project_name": project_name,
                "prd_reference": prd_reference,
                "integration_strategy": integration_strategy,
                "template": "brownfield-architecture-tmpl",
                "user_id": current_user.get("user_id")
            },
            current_user
        )
        
        return {
            "success": True,
            "architecture": result,
            "project_name": project_name,
            "type": "brownfield",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Brownfield architecture creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/brownfield/story-create")
async def create_brownfield_story(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create user stories for brownfield project enhancement"""
    try:
        body = await request.json()
        project_name = body.get("project_name")
        architecture_reference = body.get("architecture_reference")
        enhancement_focus = body.get("enhancement_focus", {})
        
        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        
        # Execute brownfield story workflow
        result = await vendor_bmad.execute_workflow(
            "vendor/bmad/bmad-core/workflows/brownfield-service.yaml",
            {
                "project_name": project_name,
                "architecture_reference": architecture_reference,
                "enhancement_focus": enhancement_focus,
                "user_id": current_user.get("user_id")
            },
            current_user
        )
        
        return {
            "success": True,
            "stories": result,
            "project_name": project_name,
            "type": "brownfield",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Brownfield story creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BMAD EXPANSION PACK ENDPOINTS
# ============================================================================

@app.get("/bmad/expansion-packs/list")
async def list_expansion_packs():
    """List all available BMAD expansion packs"""
    try:
        expansion_packs = await vendor_bmad.list_expansion_packs()
        
        return {
            "expansion_packs": expansion_packs,
            "count": len(expansion_packs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list expansion packs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bmad/expansion-packs/{pack_id}")
async def get_expansion_pack(pack_id: str):
    """Get details about a specific expansion pack"""
    try:
        pack_details = await vendor_bmad.get_expansion_pack(pack_id)
        
        if not pack_details:
            raise HTTPException(status_code=404, detail=f"Expansion pack '{pack_id}' not found")
        
        return {
            "expansion_pack": pack_details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get expansion pack {pack_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/expansion-packs/install")
async def install_expansion_pack(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Install a BMAD expansion pack"""
    try:
        body = await request.json()
        pack_id = body.get("pack_id")
        version = body.get("version", "latest")
        
        if not pack_id:
            raise HTTPException(status_code=400, detail="pack_id is required")
        
        # Install expansion pack
        result = await vendor_bmad.install_expansion_pack(pack_id, version, current_user)
        
        return {
            "success": True,
            "pack_id": pack_id,
            "version": version,
            "installation": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expansion pack installation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/expansion-packs/enable")
async def enable_expansion_pack(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enable an installed expansion pack for a project"""
    try:
        body = await request.json()
        pack_id = body.get("pack_id")
        project_id = body.get("project_id")
        
        if not pack_id:
            raise HTTPException(status_code=400, detail="pack_id is required")
        
        # Enable expansion pack
        result = await vendor_bmad.enable_expansion_pack(pack_id, project_id, current_user)
        
        return {
            "success": True,
            "pack_id": pack_id,
            "project_id": project_id,
            "activation": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expansion pack enablement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/bmad/expansion-packs/{pack_id}")
async def uninstall_expansion_pack(
    pack_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Uninstall a BMAD expansion pack"""
    try:
        # Uninstall expansion pack
        result = await vendor_bmad.uninstall_expansion_pack(pack_id, current_user)
        
        return {
            "success": True,
            "pack_id": pack_id,
            "uninstallation": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expansion pack uninstallation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bmad/expansion-packs/installed")
async def list_installed_expansion_packs():
    """List all installed expansion packs"""
    try:
        installed_packs = await vendor_bmad.list_installed_expansion_packs()
        
        return {
            "installed_packs": installed_packs,
            "count": len(installed_packs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list installed expansion packs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRODUCTION MODE CONTROL ENDPOINTS
# ============================================================================

@app.get("/bmad/production-mode/status")
async def get_production_mode_status():
    """Get current production mode status"""
    try:
        return {
            "production_mode": vendor_bmad.PRODUCTION_MODE,
            "allow_mock_mode": vendor_bmad.ALLOW_MOCK_MODE,
            "mock_mode_explicitly_requested": vendor_bmad.MOCK_MODE_EXPLICITLY_REQUESTED,
            "stats": vendor_bmad.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get production mode status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/production-mode/enforce")
async def enforce_production_mode(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Enforce production mode - disable mock mode completely"""
    try:
        vendor_bmad.enforce_production_mode()
        
        logger.warning(f"🚨 PRODUCTION MODE ENFORCED by user: {current_user.get('user_id', 'unknown')}")
        
        return {
            "status": "success",
            "message": "Production mode enforced - mock mode disabled",
            "production_mode": vendor_bmad.PRODUCTION_MODE,
            "allow_mock_mode": vendor_bmad.ALLOW_MOCK_MODE,
            "mock_mode_explicitly_requested": vendor_bmad.MOCK_MODE_EXPLICITLY_REQUESTED,
            "enforced_by": current_user.get("user_id"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to enforce production mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bmad/production-mode/request-mock")
async def request_mock_mode(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Explicitly request mock mode for testing/development"""
    try:
        body = await request.json()
        reason = body.get("reason", "User explicitly requested mock mode")
        
        # This is the ONLY way to enable mock mode in production
        mock_enabled = vendor_bmad.request_mock_mode(reason)
        
        logger.warning(f"🚨 MOCK MODE REQUESTED by user: {current_user.get('user_id', 'unknown')} - Reason: {reason}")
        
        return {
            "status": "success",
            "mock_mode_enabled": mock_enabled,
            "message": f"Mock mode {'enabled' if mock_enabled else 'not available'}",
            "reason": reason,
            "production_mode": vendor_bmad.PRODUCTION_MODE,
            "allow_mock_mode": vendor_bmad.ALLOW_MOCK_MODE,
            "mock_mode_explicitly_requested": vendor_bmad.MOCK_MODE_EXPLICITLY_REQUESTED,
            "requested_by": current_user.get("user_id"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to request mock mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


@app.exception_handler(ProductionModeViolationError)
async def production_mode_violation_handler(request: Request, exc: ProductionModeViolationError):
    """Handle production mode violations"""
    logger.error(f"🚨 PRODUCTION MODE VIOLATION: {exc}")
    return JSONResponse(
        status_code=403,
        content={
            "error": "Production Mode Violation",
            "message": str(exc),
            "code": "PRODUCTION_MODE_VIOLATION",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8001,
    workers: int = 1,
    log_level: str = "info"
):
    """Run the BMAD API server"""
    logger.info(f"Starting BMAD API server on {host}:{port}")
    
    uvicorn.run(
        "bmad_api_service.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        access_log=True,
        reload=False  # Set to True for development
    )


# Include persona management router
app.include_router(persona_router)

if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("BMAD_API_HOST", "0.0.0.0")
    port = int(os.getenv("BMAD_API_PORT", "8001"))
    workers = int(os.getenv("BMAD_API_WORKERS", "1"))
    log_level = os.getenv("BMAD_API_LOG_LEVEL", "info")
    
    run_server(host, port, workers, log_level)
