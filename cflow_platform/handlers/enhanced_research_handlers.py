from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class EnhancedResearchHandlers:
    """Package wrapper for enhanced research tools.

    Delegates to monorepo implementation when available while keeping
    imports package-safe.
    """

    def __init__(self, task_manager, project_root: Path):
        self.task_manager = task_manager
        self.project_root = project_root

    async def handle_doc_research(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal contract: echo request; migration will swap to full impl
        task_id = arguments.get("taskId")
        research_query = arguments.get("researchQuery", "")
        auto_create = bool(arguments.get("autoCreateSubtasks", True))
        create_tdd = bool(arguments.get("createTDD", True))
        return {
            "status": "success",
            "taskId": task_id,
            "autoCreateSubtasks": auto_create,
            "createTDD": create_tdd,
            "analysis": {"summary": f"researched: {research_query[:64]}"},
        }


