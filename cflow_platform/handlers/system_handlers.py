import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


logger = logging.getLogger(__name__)


class SystemHandlers:
    def __init__(self, task_manager, project_root: Path):
        self.task_manager = task_manager
        self.project_root = project_root

    async def handle_test_connection(self, arguments: Dict[str, Any]) -> List[Dict[str, str]]:
        try:
            connection_info = {
                "status": "connected",
                "server": "CFlow-stdio",
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
            }
            try:
                stats = await self.task_manager.get_task_stats()
                connection_info["task_system"] = {
                    "status": "operational",
                    "total_tasks": stats.get("total", 0),
                }
            except Exception as e:
                connection_info["task_system"] = {"status": "error", "error": str(e)}

            return [{"type": "text", "text": json_dump(connection_info)}]
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return [{"type": "text", "text": f"error: {e}"}]


def json_dump(data: Dict[str, Any]) -> str:
    import json
    return json.dumps(data)


