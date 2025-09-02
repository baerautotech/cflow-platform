#/Users/bbaer/Development/Cerebral/.venv/bin/python
"""
Memory Management API Endpoints
FastAPI integration for Cerebral Project Memory system

UNIFIED IMPLEMENTATION: Uses ChromaDBSupabaseSyncService (100% Python, no Mem0)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from shared.project_memory import (
    get_project_memory,
    CerebralProjectMemory,
    MemoryType,
    MemoryScope,
    MemoryClassification,
)
from shared.database_security import SecurityContext
from shared.secure_database import SecureSupabaseManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/memory", tags=["memory"])


# Pydantic models for API
class MemoryRequest(BaseModel):
    """Base memory request model."""

    content: str = Field(..., description="Memory content")
    user_id: str = Field(default="system", description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ArchitecturalDecisionRequest(MemoryRequest):
    """Request model for architectural decisions."""

    title: str = Field(..., description="Decision title")
    decision: str = Field(..., description="The decision made")
    context: str = Field(..., description="Context and background")
    rationale: str = Field(..., description="Reasoning behind decision")
    alternatives: Optional[List[str]] = Field(default=None, description="Alternatives considered")


class SecurityPatternRequest(MemoryRequest):
    """Request model for security patterns."""

    pattern_name: str = Field(..., description="Security pattern name")
    description: str = Field(..., description="Pattern description")
    implementation: str = Field(..., description="Implementation details")
    classification: MemoryClassification = Field(default=MemoryClassification.CONFIDENTIAL)


class DevelopmentPreferenceRequest(MemoryRequest):
    """Request model for development preferences."""

    preference_name: str = Field(..., description="Preference name")
    value: str = Field(..., description="Preference value")
    justification: str = Field(..., description="Justification for preference")
    scope: MemoryScope = Field(default=MemoryScope.USER)


class MemorySearchRequest(BaseModel):
    """Request model for memory searches."""

    query: str = Field(..., description="Search query")
    user_id: str = Field(default="system", description="User ID")
    limit: int = Field(default=20, description="Maximum results")


# === UNIFIED MEMORY API ENDPOINTS ===

@router.post("/add")
async def add_memory(request: MemoryRequest) -> Dict[str, Any]:
    """Add memory using unified cerebralMemory system."""
    try:
        memory_system = get_project_memory()
        memory_id = await memory_system.add_memory(
            content=request.content,
            user_id=request.user_id,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "storage_type": "unified_chromadb_supabase"
        }
        
    except Exception as e:
        logger.error(f"❌ Memory add failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_memories(request: MemorySearchRequest) -> Dict[str, Any]:
    """Search memories using unified cerebralMemory system."""
    try:
        memory_system = get_project_memory()
        results = await memory_system.search_memories(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "storage_type": "unified_chromadb_supabase"
        }
        
    except Exception as e:
        logger.error(f"❌ Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/architectural-decision")
async def store_architectural_decision(request: ArchitecturalDecisionRequest) -> Dict[str, Any]:
    """Store architectural decision using unified system."""
    try:
        memory_system = get_project_memory()
        memory_id = await memory_system.store_architectural_decision(
            title=request.title,
            decision=request.decision,
            context=request.context,
            rationale=request.rationale,
            alternatives=request.alternatives,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "type": "architectural_decision"
        }
        
    except Exception as e:
        logger.error(f"❌ Architectural decision storage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security-pattern")
async def store_security_pattern(request: SecurityPatternRequest) -> Dict[str, Any]:
    """Store security pattern using unified system."""
    try:
        memory_system = get_project_memory()
        memory_id = await memory_system.store_security_pattern(
            pattern_name=request.pattern_name,
            description=request.description,
            implementation=request.implementation,
            classification=request.classification,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "type": "security_pattern"
        }
        
    except Exception as e:
        logger.error(f"❌ Security pattern storage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/development-preference")
async def store_development_preference(request: DevelopmentPreferenceRequest) -> Dict[str, Any]:
    """Store development preference using unified system."""
    try:
        memory_system = get_project_memory()
        memory_id = await memory_system.store_development_preference(
            preference_name=request.preference_name,
            value=request.value,
            justification=request.justification,
            scope=request.scope,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "type": "development_preference"
        }
        
    except Exception as e:
        logger.error(f"❌ Development preference storage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-type/{memory_type}")
async def get_memories_by_type(
    memory_type: MemoryType,
    user_id: str = Query(default="system")
) -> Dict[str, Any]:
    """Get memories filtered by type."""
    try:
        memory_system = get_project_memory()
        results = await memory_system.get_memories_by_type(
            memory_type=memory_type,
            user_id=user_id
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "memory_type": memory_type.value
        }
        
    except Exception as e:
        logger.error(f"❌ Memory retrieval by type failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """Get memory system statistics."""
    try:
        memory_system = get_project_memory()
        stats = await memory_system.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Memory stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === HEALTH CHECK ===

@router.get("/health")
async def memory_health_check() -> Dict[str, Any]:
    """Health check for unified memory system."""
    try:
        memory_system = get_project_memory()
        
        # Test basic functionality
        test_id = await memory_system.add_memory(
            content="Health check test memory",
            user_id="health_check",
            metadata={"test": True}
        )
        
        search_results = await memory_system.search_memories(
            query="health check",
            user_id="health_check",
            limit=1
        )
        
        return {
            "success": True,
            "health": "healthy",
            "storage_type": "unified_chromadb_supabase",
            "mem0_dependency": False,
            "test_memory_id": test_id,
            "search_results_count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"❌ Memory health check failed: {e}")
        return {
            "success": False,
            "health": "unhealthy", 
            "error": str(e)
        }
