from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path


class TaskModificationHandlers:
    def __init__(self, task_manager):
        self.task_manager = task_manager

    async def handle_task_add(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        title = arguments.get("title", "Untitled")
        description = arguments.get("description", "")
        priority = arguments.get("priority", "medium")
        task_id = await self.task_manager.add_task(title, description, priority)
        return {"status": "success", "taskId": task_id}

    async def handle_task_update(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task_id = arguments.get("taskId")
        updates = arguments.get("updates", {})
        ok = await self.task_manager.update_task(task_id, updates)
        return {"status": "success" if ok else "error", "taskId": task_id}

    async def handle_task_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task_id = arguments.get("taskId")
        status = arguments.get("status", "pending")
        ok = await self.task_manager.update_task_status(task_id, status)
        return {"status": "success" if ok else "error", "taskId": task_id, "newStatus": status}


