from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import importlib

from .supabase_task_manager import supabase_task_manager


def _load_task_manager_class() -> Any:
    """Resolve TaskManager class using Supabase-only implementation."""
    return supabase_task_manager


class TaskManagerAdapter:
    """Adapter exposing simple methods used by package handlers, backed by monorepo TaskManager."""

    def __init__(self, tenant_id: Optional[str] = None):
        # Use Supabase task manager directly
        self._manager = supabase_task_manager
        self._tenant_id = tenant_id

    async def get_task_stats(self) -> Dict[str, int]:
        # Get comprehensive stats from Supabase task manager
        stats = self._manager.get_stats()
        return {
            "total": stats.get("total_tasks", 0),
            "supabase_available": stats.get("supabase_available", False),
            **stats.get("status_breakdown", {})
        }

    async def list_tasks(self, status: Optional[str] = None, include_subtasks: bool = False) -> List[Dict[str, Any]]:
        # Default to pending if no status requested
        status_to_use = status or "pending"
        if status_to_use:
            return self._manager.list_by_status(status_to_use)
        return self._manager.list_all()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._manager.get_task(task_id)

    async def next_task(self) -> Optional[Dict[str, Any]]:
        pending = self._manager.list_by_status("pending")
        return pending[0] if pending else None

    async def update_task_status(self, task_id: str, status: str) -> bool:
        return self._manager.update_status(task_id, status)

    async def add_task(self, title: str, description: str, priority: str = "medium") -> str:
        return self._manager.add_task(title, description, priority)

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        return self._manager.update_task(task_id, updates)

    async def delete_task(self, task_id: str) -> bool:
        return self._manager.delete_task(task_id)


