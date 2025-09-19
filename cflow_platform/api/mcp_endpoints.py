"""
MCP API Endpoints for Cerebral Platform

Provides REST API endpoints for end-users to access BMAD functionality
via MCP protocol without direct cluster access.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

# Import BMAD components
from cflow_platform.core.tool_registry import ToolRegistry
from cflow_platform.core.direct_client import execute_mcp_tool
from cflow_platform.core.redis_cluster_messaging import get_redis_cluster_messaging


class MCPRequest(BaseModel):
    """MCP tool execution request."""
    tool_name: str
    parameters: Dict[str, Any] = {}
    user_id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP tool execution response."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


class UserToken(BaseModel):
    """User Redis token information."""
    user_id: str
    redis_token: str
    redis_port: int
    expires_at: datetime
    created_at: datetime


class TokenRequest(BaseModel):
    """Token generation request."""
    user_id: str
    duration_hours: int = 24


# FastAPI app
app = FastAPI(
    title="Cerebral MCP API",
    description="MCP endpoints for BMAD platform access",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tool_registry = ToolRegistry()
redis_cluster = get_redis_cluster_messaging()


def verify_user_token(authorization: str = Header(None)) -> str:
    """Verify user token and return user_id."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Verify token with Redis cluster
    try:
        # Check if token exists and get user_id
        user_data = redis_cluster.redis_client.get(f"user_token:{token}")
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_info = json.loads(user_data)
        return user_info["user_id"]
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Cerebral MCP API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "tools": "/tools",
            "execute": "/execute",
            "health": "/health",
            "token": "/token"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        redis_status = redis_cluster.get_cluster_status()
        
        # Check tool registry
        tools_count = len(tool_registry.get_available_tools())
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis": {
                "connected": redis_status.get("connected", False),
                "version": redis_status.get("redis_version", "unknown")
            },
            "tools": {
                "available": tools_count
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        tools = tool_registry.get_available_tools()
        
        # Format tools for API response
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool.get("inputSchema", {})
            })
        
        return {
            "tools": formatted_tools,
            "count": len(formatted_tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@app.post("/execute", response_model=MCPResponse)
async def execute_tool(
    request: MCPRequest,
    user_id: str = Depends(verify_user_token)
):
    """Execute MCP tool with user authentication."""
    try:
        start_time = datetime.utcnow()
        
        # Add user_id to parameters
        request.parameters["user_id"] = user_id
        
        # Execute tool via direct client
        result = execute_mcp_tool(request.tool_name, request.parameters)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return MCPResponse(
            success=True,
            result=result,
            execution_time_ms=int(execution_time)
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return MCPResponse(
            success=False,
            error=str(e),
            execution_time_ms=int(execution_time)
        )


@app.post("/token", response_model=UserToken)
async def generate_user_token(request: TokenRequest):
    """Generate Redis token for user (admin only)."""
    try:
        # Generate unique Redis token
        redis_token = f"user_{request.user_id}_{uuid.uuid4().hex[:16]}"
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=request.duration_hours)
        
        # Store token in Redis cluster
        token_data = {
            "user_id": request.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "duration_hours": request.duration_hours
        }
        
        redis_cluster.redis_client.setex(
            f"user_token:{redis_token}",
            int(request.duration_hours * 3600),  # TTL in seconds
            json.dumps(token_data)
        )
        
        # Store user Redis credentials
        user_redis_data = {
            "token": redis_token,
            "port": 6380,  # Standard Redis port
            "host": "redis.cerebral.baerautotech.com",
            "ssl": True
        }
        
        redis_cluster.redis_client.setex(
            f"user_redis:{request.user_id}",
            int(request.duration_hours * 3600),
            json.dumps(user_redis_data)
        )
        
        return UserToken(
            user_id=request.user_id,
            redis_token=redis_token,
            redis_port=6380,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@app.get("/token/{user_id}")
async def get_user_token(user_id: str):
    """Get user's Redis token information."""
    try:
        # Get user Redis data
        user_data = redis_cluster.redis_client.get(f"user_redis:{user_id}")
        if not user_data:
            raise HTTPException(status_code=404, detail="User token not found")
        
        redis_info = json.loads(user_data)
        
        # Get token data
        token_data = redis_cluster.redis_client.get(f"user_token:{redis_info['token']}")
        if not token_data:
            raise HTTPException(status_code=404, detail="Token not found")
        
        token_info = json.loads(token_data)
        
        return {
            "user_id": user_id,
            "redis_token": redis_info["token"],
            "redis_port": redis_info["port"],
            "redis_host": redis_info["host"],
            "ssl_enabled": redis_info["ssl"],
            "expires_at": token_info["expires_at"],
            "created_at": token_info["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get token: {str(e)}")


@app.delete("/token/{user_id}")
async def revoke_user_token(user_id: str):
    """Revoke user's Redis token."""
    try:
        # Get user Redis data
        user_data = redis_cluster.redis_client.get(f"user_redis:{user_id}")
        if not user_data:
            raise HTTPException(status_code=404, detail="User token not found")
        
        redis_info = json.loads(user_data)
        
        # Delete both token entries
        redis_cluster.redis_client.delete(f"user_token:{redis_info['token']}")
        redis_cluster.redis_client.delete(f"user_redis:{user_id}")
        
        return {"message": "Token revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke token: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
