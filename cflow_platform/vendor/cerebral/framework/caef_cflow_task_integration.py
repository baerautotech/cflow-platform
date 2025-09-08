from __future__ import annotations

from typing import Any, Dict, Optional

try:
    # Prefer local platform task manager when available
    from cflow_platform.core.local_task_manager import LocalTaskManager  # type: ignore
except Exception:  # pragma: no cover - defensive
    LocalTaskManager = None  # type: ignore


class CFlowTaskIntegration:
    """Minimal compatibility layer for CAEF → CFlow task lookups.

    The original implementation lived in the Cerebral monorepo. This shim maps
    CAEF's expectations to the local SQLite-backed `LocalTaskManager` so CAEF
    workflows can resolve task metadata without a hard dependency on Cerebral.
    """

    def __init__(self) -> None:
        self._tm = LocalTaskManager() if LocalTaskManager is not None else None

    async def find_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        if not task_id:
            return None
        try:
            if self._tm is None:
                return None
            data = self._tm.get_task(task_id)
            return data or None
        except Exception:
            return None

    async def find_task(self, *, title: Optional[str] = None, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            if self._tm is None:
                return None
            items = []
            if status:
                items = self._tm.list_by_status(status)
            else:
                items = self._tm.list_all()
            title_norm = (title or "").strip().lower()
            if title_norm:
                for it in items:
                    if str(it.get("title", "")).strip().lower() == title_norm:
                        return it
            return items[0] if items else None
        except Exception:
            return None


