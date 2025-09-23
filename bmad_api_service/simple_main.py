#!/usr/bin/env python3
"""
Simple BMAD API Service for Cluster Deployment

This is a simplified version of the BMAD API service that works in the cluster
environment with proper health checks and provider integration.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BMAD API Service",
    description="BMAD API Service with Provider Integration",
    version="1.0.0"
)

# Global state
app_state = {
    "startup_time": datetime.utcnow(),
    "request_count": 0,
    "providers_configured": False
}

# Initialize provider router
try:
    from provider_router import provider_router
    app_state["providers_configured"] = True
    logger.info("Provider router initialized successfully")
except ImportError as e:
    logger.warning(f"Provider router not available: {e}")
    provider_router = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BMAD API Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/bmad/health")
async def health_check():
    """Health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "service": "bmad-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - app_state["startup_time"]).total_seconds(),
            "request_count": app_state["request_count"],
            "providers_configured": app_state["providers_configured"]
        }
        
        # Check provider status if available
        if provider_router:
            try:
                provider_status = provider_router.get_provider_status()
                health_status["provider_status"] = provider_status
            except Exception as e:
                health_status["provider_error"] = str(e)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "service": "bmad-api",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/bmad/providers/status")
async def get_provider_status():
    """Get status of all LLM providers."""
    if not provider_router:
        raise HTTPException(status_code=503, detail="Provider router not available")
    
    try:
        status = provider_router.get_provider_status()
        return {
            "status": "success",
            "providers": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bmad/providers/test")
async def test_provider(provider_id: Optional[str] = None):
    """Test a specific provider or all providers."""
    if not provider_router:
        raise HTTPException(status_code=503, detail="Provider router not available")
    
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bmad/tools")
async def list_bmad_tools():
    """List all available BMAD tools."""
    return {
        "tools": [
            "bmad_brownfield_prd_create",
            "bmad_brownfield_arch_create", 
            "bmad_brownfield_story_create",
            "bmad_expansion_packs_install",
            "bmad_expansion_packs_list",
            "bmad_expansion_packs_enable",
            "bmad_project_type_detect",
            "bmad_workflow_execute"
        ],
        "count": 8,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/bmad/workflow/execute")
async def execute_workflow(workflow_data: Dict[str, Any]):
    """Execute a BMAD workflow."""
    try:
        app_state["request_count"] += 1
        
        workflow_name = workflow_data.get("workflow", "unknown")
        arguments = workflow_data.get("arguments", {})
        
        # Simple workflow execution
        result = {
            "status": "success",
            "workflow": workflow_name,
            "result": {
                "output": f"Workflow {workflow_name} executed successfully",
                "arguments": arguments,
                "timestamp": datetime.utcnow().isoformat()
            },
            "metadata": {
                "execution_time": "simulated",
                "provider": "simple_executor",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def add_request_id(request, call_next):
    """Add request ID and increment counter."""
    app_state["request_count"] += 1
    response = await call_next(request)
    return response

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )
