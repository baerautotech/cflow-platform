from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
from .local_task_manager import LocalTaskManager
import os


class TaskManagerClient:
    """Package-native HTTP client for ChromaDB-backed tasks.

    Decouples the package from the monorepo TaskManager.
    """

    def __init__(self, base_urls: Optional[List[str]] = None, collection: str = "cerebral_tasks"):
        self.base_urls = base_urls or [
            "http://localhost:8000",
            "http://host.docker.internal:8000",
        ]
        self.collection = collection
        self._active: Optional[str] = None

    async def _endpoint(self) -> Optional[str]:
        if self._active:
            return self._active
        for url in self.base_urls:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(f"{url}/health")
                    if r.status_code == 200:
                        self._active = url
                        return url
            except Exception:
                continue
        return None

    async def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        ep = await self._endpoint()
        if not ep:
            # Local-first fallback: SQLite
            try:
                ltm = LocalTaskManager()
                return ltm.list_by_status(status)
            except Exception:
                pass
            # Secondary fallback: ChromaDB (read-only)
            try:
                chroma_path = os.environ.get(
                    "CFLOW_CHROMADB_PATH",
                    str(os.getcwd()) if os.getcwd() else "."
                )
                # Attempt default canonical path if not provided
                if not chroma_path or chroma_path == ".":
                    chroma_path = str(
                        (os.path.abspath("."))
                    )
                from chromadb import PersistentClient  # type: ignore
                from chromadb.config import Settings  # type: ignore
                client = PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False, allow_reset=False))
                col = client.get_or_create_collection(name=self.collection)
                result = col.get(where={"status": status}, include=["metadatas"])  # type: ignore
                items: List[Dict[str, Any]] = []
                for md in (result.get("metadatas") or [[]])[0]:
                    if isinstance(md, dict):
                        items.append(md)
                return items
            except Exception:
                return []
        payload = {"where": {"status": status}, "include": ["documents", "metadatas"]}
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{ep}/get/{self.collection}", json=payload)
        if r.status_code != 200:
            return []
        data = r.json()
        items: List[Dict[str, Any]] = []
        metas = data.get("metadatas") or []
        for m in metas:
            if m:
                items.append(m)
        return items

    # Contract-level convenience methods used by handlers
    async def list_tasks(self, status: str | None = None, include_subtasks: bool = False) -> List[Dict[str, Any]]:
        if status:
            return await self.list_by_status(status)
        # If no status provided, attempt a simple aggregate of common states
        aggregated: List[Dict[str, Any]] = []
        for s in ["pending", "in-progress", "done"]:
            aggregated.extend(await self.list_by_status(s))
        return aggregated

    async def get_task(self, task_id: str | None) -> Dict[str, Any]:
        if task_id:
            # SQLite first
            try:
                ltm = LocalTaskManager()
                return ltm.get_task(task_id)
            except Exception:
                pass
            # ChromaDB fallback
            try:
                chroma_path = os.environ.get("CFLOW_CHROMADB_PATH")
                from chromadb import PersistentClient  # type: ignore
                from chromadb.config import Settings  # type: ignore
                if chroma_path:
                    client = PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False, allow_reset=False))
                    col = client.get_or_create_collection(name=self.collection)
                    result = col.get(ids=[task_id], include=["metadatas"])  # type: ignore
                    md = (result.get("metadatas") or [[]])[0]
                    if md and isinstance(md[0], dict):
                        return md[0]
            except Exception:
                pass
            return {"task_id": task_id}
        return {}

    async def next_task(self) -> Dict[str, Any]:
        # Minimal fallback selection policy
        tasks = await self.list_tasks(status="pending")
        return tasks[0] if tasks else {}

    async def add_task(self, title: str, description: str, priority: str = "medium") -> str | None:
        ep = await self._endpoint()
        if not ep:
            try:
                ltm = LocalTaskManager()
                return ltm.add_task(title, description, priority)
            except Exception:
                return None
        return await self.add(title, description, priority)

    async def update_task(self, task_id: str | None, updates: Dict[str, Any]) -> bool:
        ep = await self._endpoint()
        if not ep and task_id:
            try:
                ltm = LocalTaskManager()
                return ltm.update_task(task_id, updates)
            except Exception:
                return False
        return bool(task_id)

    async def update_task_status(self, task_id: str | None, status: str) -> bool:
        ep = await self._endpoint()
        if not ep and task_id and status:
            try:
                ltm = LocalTaskManager()
                return ltm.update_status(task_id, status)
            except Exception:
                return False
        return bool(task_id and status)

    async def delete_task(self, task_id: str | None) -> bool:
        ep = await self._endpoint()
        if not ep and task_id:
            try:
                ltm = LocalTaskManager()
                return ltm.delete_task(task_id)
            except Exception:
                return False
        return bool(task_id)

    async def get_task_stats(self) -> Dict[str, Any]:
        # Minimal stats based on list calls
        pending = len(await self.list_by_status("pending"))
        in_progress = len(await self.list_by_status("in-progress"))
        done = len(await self.list_by_status("done"))
        total = pending + in_progress + done
        return {"pending": pending, "in_progress": in_progress, "done": done, "total": total}

    async def add(self, title: str, description: str, priority: str = "medium") -> Optional[str]:
        ep = await self._endpoint()
        if not ep:
            return None
        task_id = f"T{int(datetime.now().timestamp())}"
        meta = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        payload = {"documents": [f"{title} {description}"], "metadatas": [meta], "ids": [task_id]}
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{ep}/add/{self.collection}", json=payload)
        return task_id if r.status_code == 200 else None


