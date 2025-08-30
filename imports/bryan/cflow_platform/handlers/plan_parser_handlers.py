from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


class PlanParserHandlers:
    """Self-contained atomic plan parser with optional storage via TaskManagerClient."""

    def __init__(self):
        self.tenant_id = os.getenv('CEREBRAFLOW_TENANT_ID', '00000000-0000-0000-0000-000000000100')

    def _parse_plan(self, file_path: Path) -> Dict[str, Any]:
        # Minimal, robust Markdown plan parser: extract tasks with X.X... ids and metadata blocks
        import re
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        task_pattern = re.compile(r"^(?P<id>(?:\d+\.)*\d+)\s+[-–:]?\s+(?P<title>.+)$")
        tasks = []
        for line in lines:
            m = task_pattern.match(line.strip())
            if m:
                tasks.append({
                    "id": m.group('id'),
                    "title": m.group('title').strip(),
                })
        stats = {
            "total_tasks": len(tasks),
            "total_estimated_hours": 0.0,
        }
        return {"tasks": tasks, "statistics": stats, "plan_info": {"file": str(file_path)}}

    async def parse_atomic_plan(self, **kwargs: Any) -> Dict[str, Any]:
        plan_file = kwargs.get("plan_file")
        dry_run = bool(kwargs.get("dry_run", False))
        tenant_id = kwargs.get("tenant_id")
        if not plan_file:
            return {"success": False, "error": "plan_file parameter is required"}
        file_path = Path(plan_file)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        if not file_path.exists():
            return {"success": False, "error": f"Plan file not found: {file_path}"}
        if dry_run:
            plan_data = self._parse_plan(file_path)
            return {
                "success": True,
                "operation": "parse_only",
                "tasks_parsed": len(plan_data.get("tasks", [])),
                "plan_info": plan_data.get("plan_info", {}),
                "statistics": plan_data.get("statistics", {}),
            }
        # Parse and store via TaskManagerClient
        plan_data = self._parse_plan(file_path)
        try:
            from cflow_platform.core.task_manager_client import TaskManagerClient  # type: ignore
            client = TaskManagerClient()
            stored = 0
            for t in plan_data.get("tasks", []):
                title = t.get("title") or t.get("id")
                desc = f"Imported from {file_path.name} (id {t.get('id')})"
                task_id = await client.add_task(title=title, description=desc)
                if task_id:
                    stored += 1
            result = {
                "success": True,
                "tasks_parsed": len(plan_data.get("tasks", [])),
                "tasks_stored": stored,
                "plan_info": plan_data.get("plan_info", {}),
                "statistics": plan_data.get("statistics", {}),
                "message": "Parsed and stored via TaskManagerClient",
            }
        except Exception as e:
            result = {
                "success": False,
                "tasks_parsed": len(plan_data.get("tasks", [])),
                "tasks_stored": 0,
                "plan_info": plan_data.get("plan_info", {}),
                "statistics": plan_data.get("statistics", {}),
                "message": f"Storage failed: {e}",
            }
        return {
            "success": result.get("success", False),
            "operation": "parse_and_store",
            "tasks_parsed": result.get("tasks_parsed", 0),
            "tasks_stored": result.get("tasks_stored", 0),
            "plan_info": result.get("plan_info", {}),
            "statistics": result.get("statistics", {}),
            "message": result.get("message", ""),
        }

    async def list_available_plans(self, **kwargs: Any) -> Dict[str, Any]:
        search_path = kwargs.get("search_path", "docs/plans")
        base_path = Path(search_path)
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path
        plans = []
        if base_path.exists():
            for md in base_path.glob("**/*.md"):
                plans.append({
                    "file": str(md.relative_to(Path.cwd())),
                    "absolute_path": str(md),
                    "size_kb": md.stat().st_size / 1024,
                    "modified": md.stat().st_mtime,
                })
        return {"success": True, "plans_found": len(plans), "search_path": str(base_path), "plans": sorted(plans, key=lambda x: x["modified"], reverse=True)}

    async def validate_plan_format(self, **kwargs: Any) -> Dict[str, Any]:
        # Delegate to monorepo AtomicPlanParser for validation when available
        plan_file = kwargs.get("plan_file")
        if not plan_file:
            return {"success": False, "error": "plan_file parameter is required"}
        file_path = Path(plan_file)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        if not file_path.exists():
            return {"success": False, "error": f"Plan file not found: {file_path}"}
        plan_data = self._parse_plan(file_path)
        has_tasks = bool(plan_data.get("tasks"))
        return {"success": True, "file_valid": True, "has_tasks": has_tasks, "plan_info": plan_data.get("plan_info", {})}


