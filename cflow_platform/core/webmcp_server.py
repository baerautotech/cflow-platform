"""
FastAPI-based WebMCP Server for Cerebral Cluster

This server provides HTTP-based MCP (Model Context Protocol) access
with FastAPI + Uvicorn, designed for production deployment with nginx
reverse proxy and cert-manager TLS certificates.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .tool_registry import ToolRegistry
from .direct_client import execute_mcp_tool
from .bmad_tool_router import BMADToolRouter
from .tool_group_manager import ToolGroupManager
from .client_tool_config import ClientToolConfigManager
from .project_tool_filter import ProjectToolFilterManager
from .master_tool_base import MasterToolManager
from .bmad_master_tools import BMADTaskMasterTool, BMADPlanMasterTool, BMADDocMasterTool, BMADWorkflowMasterTool
from .bmad_advanced_master_tools import BMADHILMasterTool, BMADGitMasterTool, BMADOrchestratorMasterTool, BMADExpansionMasterTool
from .bmad_expansion_master_tools import BMADGameDevMasterTool, BMADDevOpsMasterTool, BMADCreativeMasterTool
from .async_tool_executor import AsyncToolExecutor
from .performance_cache import PerformanceCache, CacheConfig
from .fault_tolerance import CircuitBreaker, CircuitBreakerConfig
from .load_balancer import LoadBalancer, LoadBalancerConfig
from .plugin_architecture import PluginLoader, HotReloadManager
from .legacy_tool_migration import LegacyToolMigrationManager
from .migration_validator import MigrationValidator
from .legacy_tool_removal import LegacyToolRemovalManager
from .performance_optimizer import PerformanceOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CFlow WebMCP Server",
    description="HTTP-based MCP server for Cerebral Platform",
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

# Global tool registry
tool_registry = ToolRegistry.get_tools_for_mcp()

# Tool management components
tool_group_manager = ToolGroupManager()
client_config_manager = ClientToolConfigManager()
project_filter_manager = ProjectToolFilterManager()

# BMAD tool routing
bmad_tool_router = BMADToolRouter()

# Master tool management system
master_tool_manager = MasterToolManager()

# Performance components
async_executor = AsyncToolExecutor()
performance_cache = PerformanceCache(CacheConfig())
load_balancer = LoadBalancer(LoadBalancerConfig())

# Migration components
legacy_migration_manager = None
migration_validator = None

# Removal and optimization components
legacy_removal_manager = None
performance_optimizer = None

# Initialize master tools
def _initialize_master_tools():
    """Initialize all master tools with performance components"""
    try:
        # Core BMAD Master Tools
        master_tool_manager.register_tool(BMADTaskMasterTool())
        master_tool_manager.register_tool(BMADPlanMasterTool())
        master_tool_manager.register_tool(BMADDocMasterTool())
        master_tool_manager.register_tool(BMADWorkflowMasterTool())
        
        # Advanced BMAD Master Tools
        master_tool_manager.register_tool(BMADHILMasterTool())
        master_tool_manager.register_tool(BMADGitMasterTool())
        master_tool_manager.register_tool(BMADOrchestratorMasterTool())
        master_tool_manager.register_tool(BMADExpansionMasterTool())
        
        # Expansion Pack Master Tools
        master_tool_manager.register_tool(BMADGameDevMasterTool())
        master_tool_manager.register_tool(BMADDevOpsMasterTool())
        master_tool_manager.register_tool(BMADCreativeMasterTool())
        
        # Inject performance components
        master_tool_manager.inject_performance_components(
            cache=performance_cache,
            circuit_breaker=None,  # Will be injected per tool
            metrics=None  # Will be injected per tool
        )
        
        logger.info(f"Initialized {len(master_tool_manager.registry.tools)} master tools")
        
    except Exception as e:
        logger.error(f"Error initializing master tools: {e}")
        raise

def _initialize_migration_system():
    """Initialize legacy tool migration system"""
    global legacy_migration_manager, migration_validator
    
    try:
        legacy_migration_manager = LegacyToolMigrationManager(master_tool_manager)
        migration_validator = MigrationValidator(legacy_migration_manager)
        
        logger.info("Initialized legacy tool migration system")
        
    except Exception as e:
        logger.error(f"Error initializing migration system: {e}")
        raise

def _initialize_removal_and_optimization_system():
    """Initialize legacy tool removal and performance optimization system"""
    global legacy_removal_manager, performance_optimizer
    
    try:
        legacy_removal_manager = LegacyToolRemovalManager(legacy_migration_manager)
        performance_optimizer = PerformanceOptimizer(master_tool_manager)
        
        logger.info("Initialized legacy tool removal and performance optimization system")
        
    except Exception as e:
        logger.error(f"Error initializing removal and optimization system: {e}")
        raise

# Initialize all systems on startup
_initialize_master_tools()
_initialize_migration_system()
_initialize_removal_and_optimization_system()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cflow-webmcp",
        "timestamp": datetime.utcnow().isoformat(),
        "tools_count": len(tool_registry),
        "master_tools_count": len(master_tool_manager.registry.tools),
        "master_operations_count": len(master_tool_manager.registry.list_operations())
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "cflow-webmcp",
        "timestamp": datetime.utcnow().isoformat(),
        "tools_count": len(tool_registry),
        "master_tools_count": len(master_tool_manager.registry.tools),
        "master_operations_count": len(master_tool_manager.registry.list_operations()),
        "version": "1.0.0"
    }

@app.get("/help")
async def help():
    """Comprehensive help documentation for all available tools and endpoints"""
    master_tools_docs = {}
    
    # Get detailed documentation for each master tool
    for tool_name, tool in master_tool_manager.registry.tools.items():
        tool_schema = tool.get_tool_schema()
        operations_docs = {}
        
        for operation_name in tool.list_operations():
            operation_schema = tool.get_operation_schema(operation_name)
            operations_docs[operation_name] = {
                "description": operation_schema.get("description", ""),
                "input_schema": operation_schema.get("input_schema", {}),
                "output_schema": operation_schema.get("output_schema", {}),
                "examples": operation_schema.get("examples", [])
            }
        
        master_tools_docs[tool_name] = {
            "name": tool_schema.get("name", tool_name),
            "description": tool_schema.get("description", ""),
            "version": tool_schema.get("version", "1.0.0"),
            "operations": operations_docs,
            "total_operations": len(operations_docs)
        }
    
    return {
        "service": "CFlow WebMCP Server",
        "version": "3.0.0",
        "description": "HTTP-based MCP server for Cerebral Platform with Master Tool Pattern",
        "documentation": {
            "overview": "This server provides access to BMAD master tools through a unified API. Each master tool consolidates multiple related operations into a single, efficient interface.",
            "master_tools": master_tools_docs,
            "total_master_tools": len(master_tools_docs),
            "total_operations": sum(tool["total_operations"] for tool in master_tools_docs.values())
        },
        "endpoints": {
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Service health check with tool counts"
            },
            "help": {
                "path": "/help",
                "method": "GET", 
                "description": "This comprehensive help documentation"
            },
            "master_tools": {
                "path": "/mcp/master-tools",
                "method": "GET",
                "description": "List all available master tools"
            },
            "master_tool_info": {
                "path": "/mcp/master-tools/{tool_name}",
                "method": "GET",
                "description": "Get detailed information about a specific master tool"
            },
            "master_tool_operations": {
                "path": "/mcp/master-tools/{tool_name}/operations",
                "method": "GET",
                "description": "Get all operations for a specific master tool"
            },
            "master_tool_operation_info": {
                "path": "/mcp/master-tools/{tool_name}/operations/{operation_name}",
                "method": "GET",
                "description": "Get detailed information about a specific master tool operation"
            },
            "execute_master_tool_operation": {
                "path": "/mcp/master-tools/{tool_name}/operations/{operation_name}/execute",
                "method": "POST",
                "description": "Execute a master tool operation"
            },
            "legacy_tools": {
                "path": "/mcp/tools",
                "method": "GET",
                "description": "List legacy MCP tools (deprecated - use master tools instead)"
            },
            "legacy_tool_call": {
                "path": "/mcp/tools/call",
                "method": "POST",
                "description": "Call a legacy MCP tool (deprecated - use master tools instead)"
            },
            "migration_status": {
                "path": "/mcp/migration/status",
                "method": "GET",
                "description": "Get status of legacy tool migrations to master tools"
            },
            "performance_metrics": {
                "path": "/mcp/performance/metrics",
                "method": "GET",
                "description": "Get current performance metrics"
            },
            "api_docs": {
                "path": "/docs",
                "method": "GET",
                "description": "Interactive API documentation (Swagger UI)"
            },
            "redoc": {
                "path": "/redoc",
                "method": "GET",
                "description": "Alternative API documentation (ReDoc)"
            }
        },
        "usage_examples": {
            "list_master_tools": "GET /mcp/master-tools",
            "get_task_tool_info": "GET /mcp/master-tools/bmad_task",
            "get_task_operations": "GET /mcp/master-tools/bmad_task/operations",
            "create_task": "POST /mcp/master-tools/bmad_task/operations/create/execute",
            "get_plan_tool_info": "GET /mcp/master-tools/bmad_plan",
            "execute_plan": "POST /mcp/master-tools/bmad_plan/operations/execute/execute"
        },
        "master_tool_categories": {
            "core": ["bmad_task", "bmad_plan", "bmad_doc", "bmad_workflow"],
            "advanced": ["bmad_hil", "bmad_git", "bmad_orchestrator", "bmad_expansion"],
            "expansion_packs": ["bmad_gamedev", "bmad_devops", "bmad_creative"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/mcp/initialize")
async def initialize_mcp(request: Request):
    """Initialize MCP client with filtered tools based on client and project configuration"""
    try:
        body = await request.json()
        client_info = body.get("clientInfo", {})
        
        # Extract client configuration
        client_type = client_info.get("client_type", "web")
        project_type = client_info.get("project_type", "greenfield")
        project_id = client_info.get("project_id")
        
        logger.info(f"MCP initialization request from client_type={client_type}, project_type={project_type}")
        
        # Get filtered tools for client and project
        filtered_tools = _filter_tools_for_client_and_project(
            client_type, project_type, project_id
        )
        
        # Get client configuration
        client_config = client_config_manager.get_config_for_client(client_type)
        
        return {
            "protocolVersion": "2024-11-05",
            "tools": filtered_tools,
            "client_config": {
                "client_type": client_type,
                "project_type": project_type,
                "max_tools": client_config.capabilities.max_tools if client_config else 100,
                "enabled_groups": client_config.enabled_groups if client_config else [],
                "project_specific": client_config.project_specific if client_config else False,
                "tools_count": len(filtered_tools)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in MCP initialization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": tool_registry,
        "count": len(tool_registry)
    }

@app.get("/mcp/tools/filtered")
async def list_filtered_tools(client_type: str = "web", project_type: str = "greenfield", project_id: str = None):
    """List filtered MCP tools based on client and project configuration"""
    try:
        filtered_tools = _filter_tools_for_client_and_project(client_type, project_type, project_id)
        
        return {
            "tools": filtered_tools,
            "count": len(filtered_tools),
            "client_type": client_type,
            "project_type": project_type,
            "project_id": project_id
        }
        
    except Exception as e:
        logger.error(f"Error filtering tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Execute an MCP tool"""
    try:
        body = await request.json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # Validate tool exists
        tool_exists = any(tool["name"] == tool_name for tool in tool_registry)
        if not tool_exists:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Execute tool with BMAD routing
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        # Check if this is a BMAD tool and route accordingly
        if bmad_tool_router.is_bmad_tool(tool_name):
            logger.info(f"Routing BMAD tool: {tool_name}")
            result = await bmad_tool_router.route_bmad_tool(tool_name, arguments)
        else:
            # Execute non-BMAD tools normally
            result = await execute_mcp_tool(tool_name, **arguments)
        
        return {
            "result": result,
            "tool": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.post("/mcp/initialize")
async def initialize_mcp(request: Request):
    """MCP initialization endpoint"""
    try:
        body = await request.json()
        client_info = body.get("clientInfo", {})
        
        logger.info(f"MCP initialization request from: {client_info}")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "cflow-webmcp",
                "version": "1.0.0"
            },
            "tools": tool_registry
        }
        
    except Exception as e:
        logger.error(f"MCP initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@app.get("/mcp/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get information about a specific tool"""
    tool = next((t for t in tool_registry if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return tool

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    master_tool_stats = master_tool_manager.get_manager_stats()
    bmad_routing_stats = bmad_tool_router.get_routing_stats()
    
    return {
        "tools_count": len(tool_registry),
        "master_tools_count": len(master_tool_manager.registry.tools),
        "master_operations_count": len(master_tool_manager.registry.list_operations()),
        "uptime": "N/A",  # Could implement proper uptime tracking
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cflow-webmcp",
        "master_tool_stats": master_tool_stats,
        "bmad_routing_stats": bmad_routing_stats
    }

# BMAD Tool Routing Endpoints

@app.get("/bmad/routing/info/{tool_name}")
async def get_bmad_routing_info(tool_name: str):
    """Get routing information for a BMAD tool"""
    try:
        routing_info = await bmad_tool_router.get_routing_info(tool_name)
        return routing_info
    except Exception as e:
        logger.error(f"Error getting BMAD routing info for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bmad/routing/stats")
async def get_bmad_routing_stats():
    """Get BMAD tool routing statistics"""
    try:
        stats = bmad_tool_router.get_routing_stats()
        return {
            "routing_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting BMAD routing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bmad/routing/reset-stats")
async def reset_bmad_routing_stats():
    """Reset BMAD tool routing statistics"""
    try:
        bmad_tool_router.reset_routing_stats()
        return {
            "message": "BMAD routing statistics reset successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting BMAD routing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bmad/health")
async def get_bmad_api_health():
    """Get BMAD API service health status"""
    try:
        health_info = await bmad_tool_router.health_checker.get_detailed_health()
        return health_info
    except Exception as e:
        logger.error(f"Error getting BMAD API health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Master Tool Endpoints

@app.get("/mcp/master-tools")
async def list_master_tools():
    """List all available master tools"""
    return {
        "master_tools": master_tool_manager.registry.get_registry_stats(),
        "count": len(master_tool_manager.registry.tools)
    }

@app.get("/mcp/master-tools/filtered")
async def list_filtered_master_tools(client_type: str = "web", project_type: str = "greenfield"):
    """List filtered master tools based on client and project configuration"""
    try:
        # Get enabled master tools for client
        enabled_tools = client_config_manager.get_enabled_master_tools_for_client(client_type)
        
        # Filter by project type if needed
        if project_type != "greenfield":
            project_tools = tool_group_manager.get_master_tools_for_project_type(project_type)
            enabled_tools = [tool for tool in enabled_tools if tool in project_tools]
        
        # Get tool schemas
        filtered_tools = []
        for tool_name in enabled_tools:
            tool_schema = tool_group_manager.get_master_tool_schema(tool_name)
            if tool_schema:
                filtered_tools.append(tool_schema)
        
        return {
            "master_tools": filtered_tools,
            "count": len(filtered_tools),
            "client_type": client_type,
            "project_type": project_type
        }
        
    except Exception as e:
        logger.error(f"Error filtering master tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/master-tools/{tool_name}")
async def get_master_tool_info(tool_name: str):
    """Get information about a specific master tool"""
    tool = master_tool_manager.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Master tool '{tool_name}' not found")
    
    return tool.get_tool_schema()

@app.get("/mcp/master-tools/{tool_name}/operations")
async def get_master_tool_operations(tool_name: str):
    """Get all operations for a specific master tool"""
    tool = master_tool_manager.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Master tool '{tool_name}' not found")
    
    operations = {}
    for operation_name in tool.list_operations():
        operations[operation_name] = tool.get_operation_schema(operation_name)
    
    return {
        "tool_name": tool_name,
        "operations": operations,
        "operation_count": len(operations)
    }

@app.get("/mcp/master-tools/{tool_name}/operations/{operation_name}")
async def get_master_tool_operation_info(tool_name: str, operation_name: str):
    """Get information about a specific master tool operation"""
    tool = master_tool_manager.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Master tool '{tool_name}' not found")
    
    operation_schema = tool.get_operation_schema(operation_name)
    if not operation_schema:
        raise HTTPException(status_code=404, detail=f"Operation '{operation_name}' not found in master tool '{tool_name}'")
    
    return operation_schema

@app.post("/mcp/master-tools/{tool_name}/operations/{operation_name}/execute")
async def execute_master_tool_operation(tool_name: str, operation_name: str, request: Request):
    """Execute a master tool operation with load balancing"""
    try:
        body = await request.json()
        arguments = body.get("arguments", {})
        client_info = body.get("client_info", {})
        
        # Validate master tool exists
        tool = master_tool_manager.registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Master tool '{tool_name}' not found")
        
        # Validate operation exists
        operation = tool.get_operation(operation_name)
        if not operation:
            raise HTTPException(status_code=404, detail=f"Operation '{operation_name}' not found in master tool '{tool_name}'")
        
        # Check client permissions
        client_type = client_info.get("client_type", "web")
        if not client_config_manager.is_master_tool_operation_enabled(client_type, tool_name, operation_name):
            raise HTTPException(status_code=403, detail=f"Operation '{operation_name}' not enabled for client type '{client_type}'")
        
        # Execute master tool operation
        logger.info(f"Executing master tool operation: {tool_name}.{operation_name} with args: {arguments}")
        
        # Execute directly through master tool manager
        execution_result = await master_tool_manager.execute_operation(
            tool_name=tool_name,
            operation_name=operation_name,
            arguments=arguments,
            request_id=f"{tool_name}_{operation_name}_{int(time.time() * 1000)}"
        )
        
        return {
            "result": execution_result.result,
            "success": execution_result.success,
            "execution_time": execution_result.execution_time,
            "tool": tool_name,
            "operation": operation_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": execution_result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Master tool operation execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Master tool operation execution failed: {str(e)}")

@app.get("/mcp/master-tools/{tool_name}/stats")
async def get_master_tool_stats(tool_name: str):
    """Get statistics for a specific master tool"""
    tool = master_tool_manager.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Master tool '{tool_name}' not found")
    
    return tool.get_stats()

@app.get("/mcp/master-tools/registry/stats")
async def get_master_tool_registry_stats():
    """Get master tool registry statistics"""
    return master_tool_manager.get_manager_stats()

@app.post("/mcp/master-tools/migrate-legacy")
async def migrate_legacy_tool_request(request: Request):
    """Migrate legacy tool request to master tool"""
    try:
        body = await request.json()
        legacy_tool_name = body.get("legacy_tool_name")
        arguments = body.get("arguments", {})
        
        if not legacy_tool_name:
            raise HTTPException(status_code=400, detail="legacy_tool_name is required")
        
        # Execute migration using migration manager
        logger.info(f"Migrating legacy tool request: {legacy_tool_name}")
        result = await legacy_migration_manager.migrate_legacy_tool(legacy_tool_name, arguments)
        
        return {
            "result": result.result,
            "success": result.success,
            "execution_time": result.execution_time,
            "performance_improvement": result.performance_improvement,
            "validation_passed": result.validation_passed,
            "legacy_tool": legacy_tool_name,
            "master_tool": result.master_tool_name,
            "master_operation": result.master_operation_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legacy tool migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Legacy tool migration failed: {str(e)}")

# Migration Management Endpoints

@app.get("/mcp/migration/status")
async def get_migration_status():
    """Get overall migration status"""
    return legacy_migration_manager.get_all_migration_status()

@app.get("/mcp/migration/status/{legacy_tool_name}")
async def get_legacy_tool_migration_status(legacy_tool_name: str):
    """Get migration status for a specific legacy tool"""
    status = legacy_migration_manager.get_migration_status(legacy_tool_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"No migration mapping found for {legacy_tool_name}")
    
    return status

@app.get("/mcp/migration/statistics")
async def get_migration_statistics():
    """Get migration statistics"""
    return legacy_migration_manager.get_migration_statistics()

@app.get("/mcp/migration/ready-for-removal")
async def get_tools_ready_for_removal():
    """Get list of legacy tools ready for removal"""
    return {
        "ready_for_removal": legacy_migration_manager.get_legacy_tools_ready_for_removal(),
        "count": len(legacy_migration_manager.get_legacy_tools_ready_for_removal())
    }

@app.post("/mcp/migration/validate/{legacy_tool_name}")
async def validate_legacy_tool_migration(legacy_tool_name: str):
    """Validate migration for a specific legacy tool"""
    try:
        result = await migration_validator.validate_legacy_tool_migration(legacy_tool_name)
        return result
    except Exception as e:
        logger.error(f"Migration validation error for {legacy_tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Migration validation failed: {str(e)}")

@app.post("/mcp/migration/validate-all")
async def validate_all_migrations():
    """Validate all legacy tool migrations"""
    try:
        result = await migration_validator.validate_all_migrations()
        return result
    except Exception as e:
        logger.error(f"Migration validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration validation failed: {str(e)}")

@app.post("/mcp/migration/performance-regression-tests")
async def run_performance_regression_tests():
    """Run performance regression tests on all migrations"""
    try:
        result = await migration_validator.run_performance_regression_tests()
        return result
    except Exception as e:
        logger.error(f"Performance regression tests error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance regression tests failed: {str(e)}")

@app.get("/mcp/migration/validation-summary")
async def get_validation_summary():
    """Get validation test summary"""
    return migration_validator.get_validation_summary()

@app.post("/mcp/migration/rollback/{legacy_tool_name}")
async def rollback_migration(legacy_tool_name: str):
    """Rollback migration for a legacy tool"""
    try:
        success = await legacy_migration_manager.rollback_migration(legacy_tool_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"No migration found for {legacy_tool_name}")
        
        return {
            "legacy_tool": legacy_tool_name,
            "rollback_success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Migration rollback error for {legacy_tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Migration rollback failed: {str(e)}")

# Legacy Tool Removal Endpoints

@app.get("/mcp/removal/status")
async def get_removal_status():
    """Get overall legacy tool removal status"""
    return legacy_removal_manager.get_all_removal_status()

@app.get("/mcp/removal/status/{legacy_tool_name}")
async def get_legacy_tool_removal_status(legacy_tool_name: str):
    """Get removal status for a specific legacy tool"""
    status = legacy_removal_manager.get_removal_status(legacy_tool_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"No removal record found for {legacy_tool_name}")
    
    return status

@app.get("/mcp/removal/statistics")
async def get_removal_statistics():
    """Get removal statistics"""
    return legacy_removal_manager.get_removal_statistics()

@app.get("/mcp/removal/ready-for-removal")
async def get_tools_ready_for_removal():
    """Get list of legacy tools ready for removal"""
    return {
        "ready_for_removal": legacy_removal_manager.get_tools_ready_for_removal(),
        "count": len(legacy_removal_manager.get_tools_ready_for_removal())
    }

@app.get("/mcp/removal/removed-tools")
async def get_removed_tools():
    """Get list of successfully removed legacy tools"""
    return {
        "removed_tools": legacy_removal_manager.get_removed_tools(),
        "count": len(legacy_removal_manager.get_removed_tools())
    }

@app.post("/mcp/removal/validate/{legacy_tool_name}")
async def validate_legacy_tool_for_removal(legacy_tool_name: str):
    """Validate that a legacy tool is ready for removal"""
    try:
        result = await legacy_removal_manager.validate_legacy_tool_for_removal(legacy_tool_name)
        return result
    except Exception as e:
        logger.error(f"Removal validation error for {legacy_tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Removal validation failed: {str(e)}")

@app.post("/mcp/removal/remove/{legacy_tool_name}")
async def remove_legacy_tool(legacy_tool_name: str, create_backup: bool = True):
    """Remove a legacy tool after validation"""
    try:
        result = await legacy_removal_manager.remove_legacy_tool(legacy_tool_name, create_backup)
        return {
            "legacy_tool": result.legacy_tool_name,
            "removal_success": result.success,
            "removal_time": result.removal_time,
            "files_removed": result.files_removed,
            "registry_entries_removed": result.registry_entries_removed,
            "performance_impact": result.performance_impact,
            "error": result.error,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Legacy tool removal error for {legacy_tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Legacy tool removal failed: {str(e)}")

@app.post("/mcp/removal/batch-remove")
async def batch_remove_legacy_tools(request: Request):
    """Batch remove multiple legacy tools"""
    try:
        body = await request.json()
        legacy_tool_names = body.get("legacy_tool_names", [])
        create_backups = body.get("create_backups", True)
        
        if not legacy_tool_names:
            raise HTTPException(status_code=400, detail="legacy_tool_names is required")
        
        results = await legacy_removal_manager.batch_remove_legacy_tools(legacy_tool_names, create_backups)
        
        return {
            "batch_removal_results": [
                {
                    "legacy_tool": r.legacy_tool_name,
                    "success": r.success,
                    "removal_time": r.removal_time,
                    "error": r.error
                }
                for r in results
            ],
            "total_tools": len(legacy_tool_names),
            "successful_removals": sum(1 for r in results if r.success),
            "failed_removals": sum(1 for r in results if not r.success),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch removal error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch removal failed: {str(e)}")

@app.post("/mcp/removal/rollback/{legacy_tool_name}")
async def rollback_legacy_tool_removal(legacy_tool_name: str):
    """Rollback removal of a legacy tool"""
    try:
        success = await legacy_removal_manager.rollback_legacy_tool_removal(legacy_tool_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"No removal record found for {legacy_tool_name}")
        
        return {
            "legacy_tool": legacy_tool_name,
            "rollback_success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Removal rollback error for {legacy_tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Removal rollback failed: {str(e)}")

# Performance Optimization Endpoints

@app.get("/mcp/performance/metrics")
async def get_performance_metrics():
    """Get current performance metrics"""
    try:
        metrics = await performance_optimizer.collect_performance_metrics()
        return {
            "timestamp": metrics.timestamp,
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "memory_available": metrics.memory_available,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "cache_hit_rate": metrics.cache_hit_rate,
            "cache_size": metrics.cache_size,
            "active_connections": metrics.active_connections,
            "response_time_avg": metrics.response_time_avg,
            "throughput": metrics.throughput
        }
    except Exception as e:
        logger.error(f"Performance metrics collection error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics collection failed: {str(e)}")

@app.get("/mcp/performance/bottlenecks")
async def analyze_performance_bottlenecks():
    """Analyze performance bottlenecks and recommend optimizations"""
    try:
        result = await performance_optimizer.analyze_performance_bottlenecks()
        return result
    except Exception as e:
        logger.error(f"Performance bottleneck analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance bottleneck analysis failed: {str(e)}")

@app.post("/mcp/performance/optimize")
async def run_performance_optimization(request: Request):
    """Run performance optimization"""
    try:
        body = await request.json()
        optimization_type = body.get("optimization_type", "comprehensive")
        
        if optimization_type == "cache":
            result = await performance_optimizer.optimize_cache_performance()
        elif optimization_type == "memory":
            result = await performance_optimizer.optimize_memory_usage()
        elif optimization_type == "concurrency":
            result = await performance_optimizer.optimize_concurrency()
        elif optimization_type == "comprehensive":
            result = await performance_optimizer.run_comprehensive_optimization()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown optimization type: {optimization_type}")
        
        return {
            "optimization_type": optimization_type,
            "optimization_success": result.get("optimization_success", result.success),
            "performance_improvement": result.get("total_performance_improvement", result.performance_improvement),
            "optimization_time": result.get("optimization_time", 0),
            "optimization_results": result.get("optimization_results", []),
            "error": result.get("error", result.error),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance optimization failed: {str(e)}")

@app.get("/mcp/performance/optimization-history")
async def get_optimization_history():
    """Get optimization history and statistics"""
    return performance_optimizer.get_optimization_history()

@app.get("/mcp/performance/trends")
async def get_performance_trends():
    """Get performance trends over time"""
    return performance_optimizer.get_performance_trends()

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

def _filter_tools_for_client_and_project(client_type: str, project_type: str, project_id: str = None) -> List[Dict[str, Any]]:
    """Filter tools based on client type and project requirements"""
    try:
        # Get client configuration
        client_config = client_config_manager.get_config_for_client(client_type)
        if not client_config:
            logger.warning(f"Unknown client type: {client_type}, using default web config")
            client_config = client_config_manager.get_config_for_client("web")
        
        # Get project filter configuration
        project_filter = project_filter_manager.get_filter_for_project_type(project_type)
        if not project_filter:
            logger.warning(f"Unknown project type: {project_type}, using default greenfield config")
            project_filter = project_filter_manager.get_filter_for_project_type("greenfield")
        
        # Combine client and project enabled groups
        client_enabled_groups = set(client_config.enabled_groups)
        project_enabled_groups = set(project_filter.enabled_groups)
        final_enabled_groups = client_enabled_groups.intersection(project_enabled_groups)
        
        # Combine disabled tools
        client_disabled_tools = set(client_config.disabled_tools)
        project_disabled_tools = set(project_filter.disabled_tools)
        final_disabled_tools = client_disabled_tools.union(project_disabled_tools)
        
        # Filter tools
        filtered_tools = []
        max_tools = client_config.capabilities.max_tools
        
        for tool in tool_registry:
            tool_name = tool["name"]
            
            # Check if tool is disabled
            if _is_tool_disabled(tool_name, final_disabled_tools):
                continue
            
            # Check if tool is in enabled groups
            if _is_tool_in_enabled_groups(tool_name, final_enabled_groups):
                filtered_tools.append(tool)
            
            # Stop if we've reached the max tool limit
            if len(filtered_tools) >= max_tools:
                break
        
        logger.info(f"Filtered {len(filtered_tools)} tools for client_type={client_type}, project_type={project_type}")
        return filtered_tools
        
    except Exception as e:
        logger.error(f"Error filtering tools: {e}")
        # Return all tools as fallback
        return tool_registry

def _is_tool_disabled(tool_name: str, disabled_tools: set) -> bool:
    """Check if a tool is disabled based on patterns"""
    for disabled_pattern in disabled_tools:
        if disabled_pattern.endswith("*"):
            # Wildcard pattern matching
            if tool_name.startswith(disabled_pattern[:-1]):
                return True
        elif tool_name == disabled_pattern:
            return True
    return False

def _is_tool_in_enabled_groups(tool_name: str, enabled_groups: set) -> bool:
    """Check if a tool belongs to any of the enabled groups"""
    for group_name in enabled_groups:
        try:
            # Convert string to ToolGroup enum
            from .tool_group_manager import ToolGroup
            group = ToolGroup(group_name)
            if tool_group_manager.is_tool_in_group(tool_name, group):
                return True
        except ValueError:
            # Handle case where group_name doesn't match enum
            continue
    return False

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    return app

def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 1,
    log_level: str = "info"
):
    """Run the WebMCP server"""
    logger.info(f"Starting WebMCP server on {host}:{port}")
    
    uvicorn.run(
        "cflow_platform.core.webmcp_server:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        access_log=True,
        reload=False  # Set to True for development
    )

if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("WEBMCP_HOST", "0.0.0.0")
    port = int(os.getenv("WEBMCP_PORT", "8000"))
    workers = int(os.getenv("WEBMCP_WORKERS", "1"))
    log_level = os.getenv("WEBMCP_LOG_LEVEL", "info")
    
    run_server(host, port, workers, log_level)
