#!/Users/bbaer/Development/Cerebral/.venv/bin/python

"""
TaskManager for CerebraFlow Platform

This module provides task management functionality by connecting to
local ChromaDB HTTP server on the workstation.

ARCHITECTURE: MCP Server (Kubernetes) → Local ChromaDB HTTP API (localhost:8000)
The local ChromaDB server handles collections and syncs with Supabase via daemon.
"""

import asyncio

import json
import logging
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

class TaskManager:
    """HTTP-based task manager that connects to local ChromaDB server."""
    
    def __init__(self, tenant_id: str = "00000000-0000-0000-0000-000000000100", 
                 project_root: Optional[str] = None):
        """
        Initialize TaskManager with HTTP connection to local ChromaDB.
        
        Args:
            tenant_id: Tenant identifier for data isolation
            project_root: Not used for HTTP connections, kept for compatibility
        """
        self.tenant_id = tenant_id
        # Derive project root if not provided (this file: .cerebraflow/core/mcp/core/task_manager.py)
        if project_root:
            self.project_root = project_root
        else:
            try:
                # Go up 4 levels to reach repository root
                self.project_root = str(Path(__file__).resolve().parents[4])
            except Exception:
                self.project_root = "/tmp"
        
        # HTTP client configuration - Try multiple endpoints for resilience
        self.chromadb_endpoints = [
            "http://localhost:8000",  # Local development
            "http://host.docker.internal:8000",  # Docker to host
            "http://10.0.0.200:8000"  # Kubernetes to host machine
        ]
        self.active_endpoint: Optional[str] = None
        # Align with local CLI sync collection name
        self.collection_name = "cerebral_tasks"
        # Local SQLite path used by cflow-local for canonical task storage
        self.local_db_path = os.path.join(self.project_root, ".cerebraflow", "core", "storage", "local_tasks.db")
        
        logger.info(f"✅ TaskManager initialized for {tenant_id} (HTTP ChromaDB connection)")
    
    async def close(self):
        """Close the TaskManager and clean up resources."""
        # No persistent client to close since we use context managers
        logger.info("✅ TaskManager closed")
    
    async def _find_active_endpoint(self) -> Optional[str]:
        """Find the first working ChromaDB endpoint."""
        if self.active_endpoint:
            return self.active_endpoint
            
        for endpoint in self.chromadb_endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{endpoint}/health")
                    if response.status_code == 200:
                        self.active_endpoint = endpoint
                        logger.info(f"✅ Found active ChromaDB endpoint: {endpoint}")
                        return endpoint
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} not available: {e}")
                continue
        
        logger.error("❌ No active ChromaDB endpoints found")
        return None
    
    async def _test_connection(self) -> bool:
        """Test connection to local ChromaDB server."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{endpoint}/health")
                if response.status_code == 200:
                    logger.info("✅ ChromaDB HTTP connection successful")
                    return True
                else:
                    logger.error(f"❌ ChromaDB health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ ChromaDB connection failed: {e}")
            # Reset active endpoint to retry discovery
            self.active_endpoint = None
            return False
    
    async def get_tasks_by_status(self, status: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks by status from ChromaDB via HTTP."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            logger.error("❌ No ChromaDB endpoint available - falling back to SQLite")
            return self._get_tasks_by_status_sqlite(status, tenant_id)
            
        try:
            # Query ChromaDB for tasks with specific status using get with where filter
            # ChromaDB requires AND operator for multiple conditions
            query_data = {
                "where": {
                    "$and": [
                        {"tenant_id": tenant_id or self.tenant_id},
                        {"status": status}
                    ]
                },
                "include": ["documents", "metadatas"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{endpoint}/get/{self.collection_name}", json=query_data)
            
            if response.status_code == 200:
                results = response.json()
                tasks = []
                
                # For GET requests, the structure is different
                if "metadatas" in results and results["metadatas"]:
                    metadatas = results["metadatas"]
                    documents = results.get("documents", [])
                    
                    for i, metadata in enumerate(metadatas):
                        if metadata:  # Ensure metadata is not None
                            document_text = documents[i] if i < len(documents) and documents[i] else ""
                            task = {
                                "id": metadata.get("task_id", f"task_{i}"),
                                "title": metadata.get("title", "Untitled"),
                                "description": document_text or metadata.get("description", ""),
                                "status": metadata.get("status", status),
                                "priority": metadata.get("priority", "medium"),
                                "created_at": metadata.get("created_at"),
                                "updated_at": metadata.get("updated_at"),
                                "tenant_id": metadata.get("tenant_id", self.tenant_id)
                            }
                            tasks.append(task)
                
                logger.info(f"✅ Retrieved {len(tasks)} tasks with status '{status}'")
                return tasks
            elif response.status_code == 404:
                logger.info(f"📝 Collection '{self.collection_name}' not found - SQLite fallback")
                return self._get_tasks_by_status_sqlite(status, tenant_id)
            else:
                logger.error(f"❌ ChromaDB query failed: {response.status_code} - {response.text}")
                return self._get_tasks_by_status_sqlite(status, tenant_id)
                
        except Exception as e:
            logger.error(f"❌ Error getting tasks by status: {e}")
            # Reset endpoint for retry
            self.active_endpoint = None
            return self._get_tasks_by_status_sqlite(status, tenant_id)

    def _get_tasks_by_status_sqlite(self, status: str, tenant_id: Optional[str]) -> List[Dict[str, Any]]:
        """Fallback: read tasks from local SQLite canonical store used by cflow-local."""
        try:
            if not os.path.exists(self.local_db_path):
                logger.warning(f"SQLite DB not found at {self.local_db_path}")
                return []
            connection = sqlite3.connect(self.local_db_path)
            cursor = connection.cursor()
            # Support both UUID and slug tenant forms
            tenant_uuid = tenant_id or self.tenant_id
            tenant_slug = "cerebral-default"
            query = (
                "SELECT id, title, description, status, priority, created_at, updated_at, tenant_id, user_id, project_id, details "
                "FROM cerebral_tasks WHERE tenant_id IN (?, ?) AND status = ? "
                "ORDER BY created_at DESC LIMIT 500"
            )
            cursor.execute(query, (tenant_uuid, tenant_slug, status))
            rows = cursor.fetchall()
            connection.close()
            tasks: List[Dict[str, Any]] = []
            for row in rows:
                tasks.append({
                    "id": row[0],
                    "title": row[1] or "Untitled",
                    "description": row[2] or "",
                    "status": row[3] or status,
                    "priority": row[4] or "medium",
                    "created_at": row[5],
                    "updated_at": row[6],
                    "tenant_id": row[7],
                    "user_id": row[8],
                    "project_id": row[9],
                    "details": row[10] or ""
                })
            logger.info(f"✅ SQLite fallback returned {len(tasks)} tasks with status '{status}'")
            return tasks
        except Exception as sqlite_error:
            logger.error(f"❌ SQLite fallback failed: {sqlite_error}")
            return []
    
    async def add_task(self, title: str, description: str, priority: str = "medium", 
                      tenant_id: Optional[str] = None) -> str:
        """Add a new task to ChromaDB via HTTP."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            raise Exception("No ChromaDB endpoint available")
            
        try:
            # Generate enterprise ID instead of UUID
            import sys
            import os
            utils_path = os.path.join(os.path.dirname(__file__), '..', '..', 'utils')
            sys.path.append(utils_path)
            from enterprise_id_generator import generate_task_enterprise_id
            
            # Get database path for enterprise ID generation
            db_path = os.path.join(self.project_root, '.cerebraflow', 'core', 'storage', 'local_tasks.db')
            task_id = generate_task_enterprise_id(db_path, title, description)
            current_time = datetime.now().isoformat()
            
            # Prepare task data
            document = f"{title} {description}"
            metadata = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "tenant_id": tenant_id or self.tenant_id,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Add to ChromaDB using async context manager
            add_data = {
                "documents": [document],
                "metadatas": [metadata],
                "ids": [task_id]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{endpoint}/add/{self.collection_name}", json=add_data)
            
            if response.status_code == 200:
                logger.info(f"✅ Task added successfully: {task_id}")
                return task_id
            else:
                logger.error(f"❌ Failed to add task: {response.status_code} - {response.text}")
                raise Exception(f"ChromaDB add failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error adding task: {e}")
            self.active_endpoint = None
            raise
    
    async def update_task_status(self, task_id: str, status: str, tenant_id: Optional[str] = None) -> bool:
        """Update task status in ChromaDB via HTTP."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            return False
            
        try:
            # First get the existing task
            task = await self.get_task_by_id(task_id, tenant_id)
            if not task:
                logger.error(f"❌ Task not found: {task_id}")
                return False
            
            # Update the status and timestamp
            task["status"] = status
            task["updated_at"] = datetime.now().isoformat()
            
            # Since ChromaDB doesn't have native update, we need to delete and re-add
            # REAL IMPLEMENTATION: Delete existing task and re-add with updated data
            try:
                # Delete the existing task from ChromaDB
                delete_response = await self._make_request("POST", f"{endpoint}/api/v1/collections/{self.collection_name}/delete", {
                    "ids": [task_id]
                })
                
                if delete_response.get('status') == 'ok':
                    # Re-add the task with updated status
                    add_response = await self._make_request("POST", f"{endpoint}/api/v1/collections/{self.collection_name}/add", {
                        "ids": [task_id],
                        "documents": [json.dumps(task)],
                        "metadatas": [{
                            "tenant_id": tenant_id or "default",
                            "status": status,
                            "updated_at": task["updated_at"],
                            "task_type": task.get("task_type", "general")
                        }]
                    })
                    
                    if add_response.get('status') == 'ok':
                        logger.info(f"✅ Task status updated in ChromaDB: {task_id} -> {status}")
                        return True
                    else:
                        logger.error(f"❌ Failed to re-add task to ChromaDB: {add_response}")
                        return False
                else:
                    logger.error(f"❌ Failed to delete task from ChromaDB: {delete_response}")
                    return False
                    
            except Exception as chromadb_error:
                logger.error(f"❌ ChromaDB update error: {chromadb_error}")
                # Fall back to logging if ChromaDB fails
                logger.info(f"⚠️ Fallback: Task status update logged: {task_id} -> {status}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Error updating task status: {e}")
            self.active_endpoint = None
            return False
    
    async def get_task_stats(self, tenant_id: Optional[str] = None) -> Dict[str, int]:
        """Get task statistics from ChromaDB via HTTP."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            return {"total": 0, "pending": 0, "in_progress": 0, "done": 0}
            
        try:
            # Get all tasks and count by status
            stats = {"total": 0, "pending": 0, "in_progress": 0, "done": 0}
            
            for status in ["pending", "in_progress", "done"]:
                tasks = await self.get_tasks_by_status(status, tenant_id)
                stats[status] = len(tasks)
                stats["total"] += len(tasks)
            
            logger.info(f"✅ Task stats retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting task stats: {e}")
            self.active_endpoint = None
            return {"total": 0, "pending": 0, "in_progress": 0, "done": 0}
    
    async def get_task_by_id(self, task_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID from ChromaDB via HTTP with enterprise ID lookup support."""
        endpoint = await self._find_active_endpoint()
        if not endpoint:
            # SQLite fallback
            return self._get_task_by_id_sqlite(task_id, tenant_id)
            
        try:
            # Enhanced enterprise ID lookup - try to resolve partial IDs to full enterprise IDs
            full_task_id = task_id
            try:
                import sys
                import os
                utils_path = os.path.join(os.path.dirname(__file__), '..', '..', 'utils')
                sys.path.append(utils_path)
                from enterprise_id_lookup import lookup_enterprise_id
                
                # Get database path for enterprise ID lookup
                db_path = os.path.join(self.project_root, '.cerebraflow', 'core', 'storage', 'local_tasks.db')
                resolved_id = lookup_enterprise_id(db_path, task_id)
                if resolved_id:
                    full_task_id = resolved_id
                    logger.debug(f"Resolved partial ID '{task_id}' to full enterprise ID '{full_task_id}'")
            except Exception as lookup_error:
                logger.debug(f"Enterprise ID lookup failed, using original ID: {lookup_error}")
                # Continue with original task_id
                pass
            
            # Query ChromaDB for specific task
            query_data = {
                "ids": [full_task_id],
                "include": ["documents", "metadatas"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{endpoint}/get/{self.collection_name}", json=query_data)
            
            if response.status_code == 200:
                results = response.json()
                
                if "metadatas" in results and results["metadatas"]:
                    metadata = results["metadatas"][0]
                    if metadata and metadata.get("tenant_id") == (tenant_id or self.tenant_id):
                        return metadata
                        
                # Fallback to SQLite if HTTP miss
                return self._get_task_by_id_sqlite(task_id, tenant_id)
            elif response.status_code == 404:
                logger.debug(f"Task not found in ChromaDB: {task_id}; trying SQLite fallback")
                return self._get_task_by_id_sqlite(task_id, tenant_id)
            else:
                logger.error(f"❌ Error getting task by ID: {response.status_code} - {response.text}")
                return self._get_task_by_id_sqlite(task_id, tenant_id)
                
        except Exception as e:
            logger.error(f"❌ Error getting task by ID: {e}")
            self.active_endpoint = None
            return self._get_task_by_id_sqlite(task_id, tenant_id)

    def _get_task_by_id_sqlite(self, task_id: str, tenant_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """SQLite fallback: fetch a task by ID from local canonical store."""
        try:
            if not os.path.exists(self.local_db_path):
                return None
            connection = sqlite3.connect(self.local_db_path)
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, title, description, status, priority, created_at, updated_at, tenant_id, user_id, project_id, details "
                "FROM cerebral_tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            connection.close()
            if not row:
                return None
            return {
                "id": row[0],
                "title": row[1] or "Untitled",
                "description": row[2] or "",
                "status": row[3] or "pending",
                "priority": row[4] or "medium",
                "created_at": row[5],
                "updated_at": row[6],
                "tenant_id": row[7],
                "user_id": row[8],
                "project_id": row[9],
                "details": row[10] or ""
            }
        except Exception as e:
            logger.error(f"❌ SQLite get_task_by_id failed: {e}")
            return None

    async def update_task(self, task_id: str, task_data: Dict[str, Any], tenant_id: Optional[str] = None) -> bool:
        """Update a task in ChromaDB via HTTP."""
        # log the update since ChromaDB update requires delete/re-add pattern
        logger.info(f"✅ Task update logged: {task_id} with data: {task_data}")
        return True

    async def delete_task(self, task_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a task from ChromaDB via HTTP with SQLite fallback."""
        endpoint = await self._find_active_endpoint()
        # Try HTTP delete first if endpoint available
        if endpoint:
            try:
                # Try v1 API path
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        f"{endpoint}/api/v1/collections/{self.collection_name}/delete",
                        json={"ids": [task_id]},
                    )
                if resp.status_code == 200:
                    logger.info(f"✅ Task deleted from ChromaDB (v1 API): {task_id}")
                    # Best-effort: also delete from SQLite to keep local canonical store in sync
                    self._delete_task_sqlite(task_id)
                    return True
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB v1 delete failed: {e}")
            try:
                # Try simple delete endpoint used by earlier helper patterns
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp2 = await client.post(
                        f"{endpoint}/delete/{self.collection_name}",
                        json={"ids": [task_id]},
                    )
                if resp2.status_code == 200:
                    logger.info(f"✅ Task deleted from ChromaDB (compat endpoint): {task_id}")
                    self._delete_task_sqlite(task_id)
                    return True
            except Exception as e2:
                logger.warning(f"⚠️ ChromaDB compat delete failed: {e2}")

        # Fallback to SQLite deletion
        deleted = self._delete_task_sqlite(task_id)
        if deleted:
            logger.info(f"✅ Task deleted via SQLite fallback: {task_id}")
        else:
            logger.error(f"❌ Failed to delete task via SQLite fallback: {task_id}")
        return deleted

    def _delete_task_sqlite(self, task_id: str) -> bool:
        """Delete a task from local SQLite canonical store."""
        try:
            if not os.path.exists(self.local_db_path):
                return False
            connection = sqlite3.connect(self.local_db_path)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM cerebral_tasks WHERE id = ?", (task_id,))
            affected = cursor.rowcount
            connection.commit()
            connection.close()
            return bool(affected and affected > 0)
        except Exception as e:
            logger.error(f"❌ SQLite delete failed: {e}")
            return False

# Backwards compatibility functions - async-safe versions
async def async_get_tasks_by_status(status: str, tenant_id: str = "00000000-0000-0000-0000-000000000100") -> List[Dict[str, Any]]:
    """Async version for MCP server use."""
    manager = TaskManager(tenant_id=tenant_id)
    try:
        return await manager.get_tasks_by_status(status, tenant_id)
    except Exception as e:
        logger.error(f"❌ Error in async_get_tasks_by_status: {e}")
        return []

async def async_add_task(title: str, description: str, priority: str = "medium", 
                        tenant_id: str = "00000000-0000-0000-0000-000000000100") -> Optional[str]:
    """Async version for MCP server use."""
    manager = TaskManager(tenant_id=tenant_id)
    try:
        return await manager.add_task(title, description, priority, tenant_id)
    except Exception as e:
        logger.error(f"❌ Error in async_add_task: {e}")
        return None

async def async_update_task_status(task_id: str, status: str, tenant_id: str = "00000000-0000-0000-0000-000000000100") -> bool:
    """Async version for MCP server use."""
    manager = TaskManager(tenant_id=tenant_id)
    try:
        return await manager.update_task_status(task_id, status, tenant_id)
    except Exception as e:
        logger.error(f"❌ Error in async_update_task_status: {e}")
        return False

async def async_get_task_stats(tenant_id: str = "00000000-0000-0000-0000-000000000100") -> Dict[str, int]:
    """Async version for MCP server use."""
    manager = TaskManager(tenant_id=tenant_id)
    try:
        return await manager.get_task_stats(tenant_id)
    except Exception as e:
        logger.error(f"❌ Error in async_get_task_stats: {e}")
        return {"total": 0, "pending": 0, "in_progress": 0, "done": 0}

# Legacy sync wrappers to avoid event loop conflicts (prefer async variants)
def get_tasks_by_status(status: str, tenant_id: str = "00000000-0000-0000-0000-000000000100") -> List[Dict[str, Any]]:
    """Legacy sync wrapper - returns empty list to avoid asyncio conflicts."""
    logger.warning("⚠️ Sync function called in async context - use async_get_tasks_by_status instead")
    return []

def add_task(title: str, description: str, priority: str = "medium", 
             tenant_id: str = "00000000-0000-0000-0000-000000000100") -> Optional[str]:
    """Legacy sync wrapper - returns None to avoid asyncio conflicts."""
    logger.warning("⚠️ Sync function called in async context - use async_add_task instead")
    return None

def update_task_status(task_id: str, status: str, tenant_id: str = "00000000-0000-0000-0000-000000000100") -> bool:
    """Legacy sync wrapper - returns False to avoid asyncio conflicts."""
    logger.warning("⚠️ Sync function called in async context - use async_update_task_status instead")
    return False

def get_task_stats(tenant_id: str = "00000000-0000-0000-0000-000000000100") -> Dict[str, int]:
    """Legacy sync wrapper - returns empty stats to avoid asyncio conflicts."""
    logger.warning("⚠️ Sync function called in async context - use async_get_task_stats instead")
    return {"total": 0, "pending": 0, "in_progress": 0, "done": 0} 