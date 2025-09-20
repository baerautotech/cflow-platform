"""
Enhanced WebMCP Server with Performance Infrastructure

This module provides a high-performance WebMCP server implementation that uses
the new async infrastructure for improved scalability and performance.

Features:
- Async tool execution with priority queuing
- Connection pooling for external services
- Response streaming for long-running operations
- Performance monitoring and metrics
- Configuration management with hot-reload
- Health checking and circuit breakers
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from .async_tool_executor import (
    AsyncToolExecutor,
    ToolPriority,
    ToolExecutionResult,
    get_executor,
    get_performance_metrics,
    get_health_status
)
from .connection_pool import (
    ConnectionPoolManager,
    get_pool_manager,
    get_connection_metrics
)
from .response_streaming import (
    StreamResponse,
    StreamManager,
    StreamEventType,
    create_stream,
    stream_tool_execution,
    list_streams
)
from .performance_monitor import (
    PerformanceMonitor,
    get_performance_monitor,
    get_performance_summary
)
from .performance_config import (
    PerformanceConfigManager,
    get_config_manager,
    get_performance_config,
    update_performance_config
)
from .direct_client import execute_mcp_tool_enhanced
from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


# Request/Response Models
class ToolCallRequest(BaseModel):
    """Request model for tool execution"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    priority: str = Field(default="normal", description="Execution priority (critical, high, normal, low)")
    timeout_seconds: Optional[float] = Field(default=None, description="Execution timeout in seconds")
    stream_response: bool = Field(default=False, description="Whether to stream the response")


class ToolCallResponse(BaseModel):
    """Response model for tool execution"""
    request_id: str = Field(..., description="Unique request identifier")
    tool_name: str = Field(..., description="Name of the executed tool")
    result: Dict[str, Any] = Field(..., description="Tool execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    success: bool = Field(..., description="Whether execution was successful")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    memory_used_mb: float = Field(..., description="Memory used in MB")


class StreamRequest(BaseModel):
    """Request model for streaming tool execution"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    timeout_seconds: float = Field(default=300.0, description="Stream timeout in seconds")


class BatchToolRequest(BaseModel):
    """Request model for batch tool execution"""
    tools: List[ToolCallRequest] = Field(..., description="List of tools to execute")
    max_concurrent: int = Field(default=5, description="Maximum concurrent executions")
    fail_fast: bool = Field(default=False, description="Stop on first failure")


class BatchToolResponse(BaseModel):
    """Response model for batch tool execution"""
    results: List[ToolCallResponse] = Field(..., description="Individual tool results")
    total_execution_time: float = Field(..., description="Total execution time")
    success_count: int = Field(..., description="Number of successful executions")
    failure_count: int = Field(..., description="Number of failed executions")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: float = Field(..., description="Health check timestamp")
    components: Dict[str, Any] = Field(..., description="Component health status")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    updates: Dict[str, Any] = Field(..., description="Configuration updates")
    save_to_file: bool = Field(default=True, description="Whether to save changes to file")


# Global instances
_executor: Optional[AsyncToolExecutor] = None
_pool_manager: Optional[ConnectionPoolManager] = None
_stream_manager: Optional[StreamManager] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_config_manager: Optional[PerformanceConfigManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _executor, _pool_manager, _stream_manager, _performance_monitor, _config_manager
    
    logger.info("Starting Enhanced WebMCP Server...")
    
    try:
        # Initialize configuration manager
        _config_manager = get_config_manager()
        await _config_manager.start_file_watcher()
        
        # Initialize performance monitor
        _performance_monitor = await get_performance_monitor()
        
        # Initialize connection pool manager
        _pool_manager = await get_pool_manager()
        
        # Initialize stream manager
        _stream_manager = StreamManager()
        await _stream_manager.start()
        
        # Initialize async tool executor
        _executor = await get_executor()
        
        logger.info("Enhanced WebMCP Server started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Enhanced WebMCP Server: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down Enhanced WebMCP Server...")
        
        if _executor:
            await _executor.stop()
        if _stream_manager:
            await _stream_manager.stop()
        if _pool_manager:
            await _pool_manager.stop()
        if _performance_monitor:
            await _performance_monitor.stop()
        if _config_manager:
            await _config_manager.stop_file_watcher()
        
        logger.info("Enhanced WebMCP Server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Enhanced WebMCP Server",
    description="High-performance WebMCP server with async infrastructure",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility functions
def _get_priority(priority_str: str) -> ToolPriority:
    """Convert string priority to ToolPriority enum"""
    priority_map = {
        "critical": ToolPriority.CRITICAL,
        "high": ToolPriority.HIGH,
        "normal": ToolPriority.NORMAL,
        "low": ToolPriority.LOW
    }
    return priority_map.get(priority_str.lower(), ToolPriority.NORMAL)


def _convert_result_to_response(result: ToolExecutionResult, request_id: str) -> ToolCallResponse:
    """Convert ToolExecutionResult to ToolCallResponse"""
    return ToolCallResponse(
        request_id=request_id,
        tool_name=result.tool_name,
        result=result.result,
        execution_time=result.execution_time,
        success=result.success,
        error=result.error,
        memory_used_mb=result.memory_used / 1024 / 1024 if result.memory_used else 0.0
    )


# API Endpoints

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with server information"""
    return {
        "name": "Enhanced WebMCP Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": time.time(),
        "features": [
            "async_tool_execution",
            "connection_pooling",
            "response_streaming",
            "performance_monitoring",
            "configuration_management",
            "health_checking",
            "circuit_breakers"
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Get component health status
        executor_health = await get_health_status()
        connection_metrics = await get_connection_metrics()
        performance_summary = await get_performance_summary()
        
        # Determine overall status
        overall_status = "healthy"
        if executor_health["status"] != "healthy":
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=time.time(),
            components={
                "async_executor": executor_health,
                "connection_pools": connection_metrics,
                "performance_monitor": performance_summary
            },
            performance=performance_summary
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/tools", response_model=Dict[str, Any])
async def list_tools():
    """List all available tools"""
    try:
        registry = ToolRegistry()
        tools = registry.get_tools()
        
        return {
            "tools": tools,
            "count": len(tools),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Execute a single tool"""
    try:
        # Get priority
        priority = _get_priority(request.priority)
        
        # Execute tool
        result = await _executor.execute_tool(
            tool_name=request.tool_name,
            kwargs=request.arguments,
            priority=priority,
            timeout_seconds=request.timeout_seconds or 30.0
        )
        
        # Convert to response
        response = _convert_result_to_response(result, result.request_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@app.post("/tools/call/enhanced", response_model=ToolCallResponse)
async def call_tool_enhanced(request: ToolCallRequest):
    """Execute a tool using enhanced infrastructure"""
    try:
        # Use enhanced execution
        result_dict = await execute_mcp_tool_enhanced(
            tool_name=request.tool_name,
            **request.arguments
        )
        
        # Create response
        response = ToolCallResponse(
            request_id=f"{request.tool_name}_{int(time.time() * 1000)}",
            tool_name=request.tool_name,
            result=result_dict,
            execution_time=result_dict.get("execution_time", 0.0),
            success=result_dict.get("status") != "error",
            error=result_dict.get("message") if result_dict.get("status") == "error" else None,
            memory_used_mb=0.0  # Will be updated by performance monitor
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Enhanced tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced tool execution failed: {str(e)}")


@app.post("/tools/stream")
async def stream_tool(request: StreamRequest):
    """Execute a tool with streaming response"""
    try:
        # Create streaming execution
        stream = await stream_tool_execution(
            tool_name=request.tool_name,
            kwargs=request.arguments,
            timeout_seconds=request.timeout_seconds
        )
        
        async def stream_generator():
            # Subscribe to stream events
            queue = stream.subscribe()
            
            try:
                while not stream._is_complete and not stream._is_error:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=1.0)
                        yield f"data: {event}\n\n"
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        yield f"data: {{'event_type': 'heartbeat', 'timestamp': {time.time()}}}\n\n"
            finally:
                stream.unsubscribe(queue)
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming tool execution failed: {str(e)}")


@app.post("/tools/batch", response_model=BatchToolResponse)
async def batch_call_tools(request: BatchToolRequest):
    """Execute multiple tools in batch"""
    try:
        start_time = time.time()
        results = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def execute_single_tool(tool_request: ToolCallRequest):
            async with semaphore:
                priority = _get_priority(tool_request.priority)
                
                result = await _executor.execute_tool(
                    tool_name=tool_request.tool_name,
                    kwargs=tool_request.arguments,
                    priority=priority,
                    timeout_seconds=tool_request.timeout_seconds or 30.0
                )
                
                return _convert_result_to_response(result, result.request_id)
        
        # Execute tools
        tasks = [execute_single_tool(tool_req) for tool_req in request.tools]
        
        if request.fail_fast:
            # Execute sequentially, stopping on first failure
            for task in tasks:
                result = await task
                results.append(result)
                if not result.success:
                    break
        else:
            # Execute all tools concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error responses
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = ToolCallResponse(
                        request_id=f"error_{int(time.time() * 1000)}",
                        tool_name=request.tools[i].tool_name,
                        result={"status": "error", "message": str(result)},
                        execution_time=0.0,
                        success=False,
                        error=str(result),
                        memory_used_mb=0.0
                    )
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        return BatchToolResponse(
            results=results,
            total_execution_time=total_time,
            success_count=success_count,
            failure_count=failure_count
        )
        
    except Exception as e:
        logger.error(f"Batch tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch tool execution failed: {str(e)}")


@app.get("/streams", response_model=List[Dict[str, Any]])
async def list_active_streams():
    """List all active streams"""
    try:
        streams = await list_streams()
        return streams
        
    except Exception as e:
        logger.error(f"Failed to list streams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list streams: {str(e)}")


@app.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get performance metrics"""
    try:
        executor_metrics = await get_performance_metrics()
        connection_metrics = await get_connection_metrics()
        performance_summary = await get_performance_summary()
        
        return {
            "executor": executor_metrics,
            "connections": connection_metrics,
            "performance": performance_summary,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/config", response_model=Dict[str, Any])
async def get_configuration():
    """Get current configuration"""
    try:
        config = get_performance_config()
        config_dict = {
            "async_executor": config.async_executor.__dict__,
            "connection_pool": config.connection_pool.__dict__,
            "streaming": config.streaming.__dict__,
            "performance_monitor": config.performance_monitor.__dict__,
            "caching": config.caching.__dict__,
            "load_balancing": config.load_balancing.__dict__,
            "environment": config.environment,
            "debug_mode": config.debug_mode,
            "hot_reload_enabled": config.hot_reload_enabled,
            "last_updated": config.last_updated.isoformat() if config.last_updated else None
        }
        
        return config_dict
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@app.post("/config", response_model=Dict[str, str])
async def update_configuration(request: ConfigUpdateRequest):
    """Update configuration"""
    try:
        update_performance_config(request.updates)
        
        if request.save_to_file:
            config_manager = get_config_manager()
            config_manager.save_config()
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@app.get("/config/validate", response_model=Dict[str, Any])
async def validate_configuration():
    """Validate current configuration"""
    try:
        config_manager = get_config_manager()
        issues = config_manager.validate_config()
        
        return {
            "valid": len(issues["errors"]) == 0,
            "issues": issues,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": time.time()
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    return app


def main():
    """Main entry point for the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced WebMCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Set configuration file if provided
    if args.config:
        os.environ["CFLOW_PERFORMANCE_CONFIG"] = args.config
    
    # Run server
    uvicorn.run(
        "cflow_platform.core.enhanced_webmcp_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()
