"""
Supabase-only Task Manager

This module provides a complete Supabase-based task management system,
replacing the legacy SQLite LocalTaskManager with direct Supabase integration.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SupabaseTaskManager:
    """
    Complete Supabase-based task manager.
    
    This class provides all task management functionality using
    the cerebraflow_tasks table in Supabase as the single source of truth.
    """
    
    def __init__(self):
        """Initialize the Supabase task manager."""
        self.supabase_client = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client."""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase SDK not available - using mock mode")
            return
        
        url = os.getenv("SUPABASE_URL", "").strip()
        key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
               os.getenv("SUPABASE_ANON_KEY") or "").strip()
        
        if not url or not key:
            # PRODUCTION GATE: Hard fail instead of mock mode fallback
            if os.getenv("BMAD_PRODUCTION_MODE", "false").lower() == "true":
                raise RuntimeError("PRODUCTION GATE VIOLATION: Supabase credentials not found in production mode. Mock mode is UNACCEPTABLE!")
            logger.warning("Supabase credentials not found - using mock mode")
            return
        
        try:
            self.supabase_client = create_client(url, key)
            logger.info("Supabase task manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase_client = None
    
    def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        """List tasks by status."""
        if not self.supabase_client:
            logger.warning("Supabase not available - returning empty list")
            return []
        
        try:
            response = self.supabase_client.table("cerebraflow_tasks").select("*").eq("status", status).order("created_at", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to list tasks by status: {e}")
            return []
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        if not self.supabase_client:
            logger.warning("Supabase not available - returning empty list")
            return []
        
        try:
            response = self.supabase_client.table("cerebraflow_tasks").select("*").order("created_at", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to list all tasks: {e}")
            return []
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a specific task."""
        if not self.supabase_client:
            logger.warning("Supabase not available - returning empty dict")
            return {}
        
        try:
            response = self.supabase_client.table("cerebraflow_tasks").select("*").eq("id", task_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return {}
    
    def add_task(self, title: str, description: str, priority: str = "medium") -> str:
        """Add a new task."""
        if not self.supabase_client:
            logger.warning("Supabase not available - task not created")
            return ""
        
        try:
            task_data = {
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "supabase_task_manager",
                    "created_by": "system"
                }
            }
            
            response = self.supabase_client.table("cerebraflow_tasks").insert(task_data).execute()
            
            if response.data:
                task_id = response.data[0].get("id")
                logger.info(f"Created task: {task_id} - {title}")
                return str(task_id)
            else:
                logger.error("Failed to create task - no data returned")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return ""
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task."""
        if not self.supabase_client:
            logger.warning("Supabase not available - task not updated")
            return False
        
        try:
            update_data = dict(updates)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.supabase_client.table("cerebraflow_tasks").update(update_data).eq("id", task_id).execute()
            
            if response.data:
                logger.info(f"Updated task {task_id}")
                return True
            else:
                logger.error(f"Failed to update task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False
    
    def update_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        return self.update_task(task_id, {"status": status})
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if not self.supabase_client:
            logger.warning("Supabase not available - task not deleted")
            return False
        
        try:
            response = self.supabase_client.table("cerebraflow_tasks").delete().eq("id", task_id).execute()
            
            if response.data is not None:  # Supabase returns [] for successful deletes
                logger.info(f"Deleted task {task_id}")
                return True
            else:
                logger.error(f"Failed to delete task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task management statistics."""
        if not self.supabase_client:
            return {
                "supabase_available": False,
                "total_tasks": 0,
                "status_breakdown": {}
            }
        
        try:
            # Get total count
            total_response = self.supabase_client.table("cerebraflow_tasks").select("id", count="exact").execute()
            total_tasks = total_response.count if hasattr(total_response, 'count') else 0
            
            # Get status breakdown
            status_breakdown = {}
            for status in ["pending", "in_progress", "completed", "cancelled"]:
                status_response = self.supabase_client.table("cerebraflow_tasks").select("id", count="exact").eq("status", status).execute()
                count = status_response.count if hasattr(status_response, 'count') else 0
                status_breakdown[status] = count
            
            return {
                "supabase_available": True,
                "total_tasks": total_tasks,
                "status_breakdown": status_breakdown,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            return {
                "supabase_available": True,
                "error": str(e),
                "total_tasks": 0,
                "status_breakdown": {}
            }


# Global Supabase task manager instance
supabase_task_manager = SupabaseTaskManager()
