from __future__ import annotations

from typing import Any, Dict


class LintingHandlers:
    async def handle_lint_full(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "message": "lint_full executed"}

    async def handle_lint_bg(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "message": "lint_bg started"}

    async def handle_lint_supa(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "message": "lint_supa executed"}

    async def handle_lint_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "state": "idle"}

    async def handle_lint_trigger(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "triggered": True, "reason": arguments.get("reason", "manual_trigger")}

    async def handle_watch_start(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "watching": True}

    async def handle_watch_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "watching": False}


