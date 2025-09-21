#!/usr/bin/env python3
"""
Cerebral Backend API Server
Main backend service for the Cerebral Platform
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cerebral Backend API",
    version="1.0.0",
    description="Main backend service for the Cerebral Platform"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cerebral-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Cerebral Backend API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# API endpoints
@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "cerebral-backend",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/health",
            "/api/status",
            "/api/config",
            "/api/services"
        ]
    }

@app.get("/api/config")
async def api_config():
    """API configuration endpoint"""
    return {
        "backend_host": os.getenv("BACKEND_HOST", "0.0.0.0"),
        "backend_port": os.getenv("BACKEND_PORT", "8000"),
        "log_level": os.getenv("BACKEND_LOG_LEVEL", "info"),
        "workers": os.getenv("BACKEND_WORKERS", "1"),
        "timeout": os.getenv("BACKEND_TIMEOUT", "30"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/services")
async def api_services():
    """List available services"""
    return {
        "services": [
            {
                "name": "cerebral-backend",
                "type": "api",
                "status": "running",
                "port": 8000
            },
            {
                "name": "webmcp",
                "type": "mcp-server",
                "status": "external",
                "port": 8000
            }
        ],
        "total_services": 2
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint {request.url.path} was not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    workers = int(os.getenv("BACKEND_WORKERS", "1"))
    log_level = os.getenv("BACKEND_LOG_LEVEL", "info")
    
    logger.info(f"Starting Cerebral Backend API on {host}:{port}")
    logger.info(f"Workers: {workers}, Log Level: {log_level}")
    
    # Run the application
    uvicorn.run(
        "cerebral_backend:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level.lower(),
        access_log=True
    )
