from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import json
import os


class MemoryHandlers:
    """Unified memory handlers (no vendor dependency).

    Uses internal JSONL local store by default, and will opportunistically
    dual-write to Supabase/Chroma if environment is configured elsewhere.
    """

    def __init__(self) -> None:
        self._memory = None

    def _is_dev_mode(self) -> bool:
        profile = os.getenv("CFLOW_PROFILE", "dev").strip().lower()
        secure = os.getenv("CFLOW_SECURE_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
        return (profile in {"dev", "quick"}) and not secure

    def _get_memory(self):
        if self._memory is not None:
            return self._memory
        # Internal JSONL-backed memory (always used; no vendor path)
        class _SimpleMemory:
            def __init__(self) -> None:
                root = Path.cwd() / ".cerebraflow"
                root.mkdir(parents=True, exist_ok=True)
                self.path = root / "memory_items.jsonl"

            async def add_memory(self, *, content: str, user_id: str, metadata: Dict[str, Any] | None = None) -> str:
                item = {
                    "id": f"M{abs(hash(content)) % 10_000_000}",
                    "user_id": user_id,
                    "content": content,
                    "metadata": metadata or {},
                }
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(item) + "\n")
                return item["id"]

            async def search_memories(self, *, query: str, user_id: str, limit: int = 20, **_: Any) -> List[Dict[str, Any]]:
                if not self.path.exists():
                    return []
                results: List[Dict[str, Any]] = []
                needle = query.lower()
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    text = str(obj.get("content", ""))
                    if needle in text.lower():
                        results.append(obj)
                        if len(results) >= limit:
                            break
                return results

            async def store_procedure_update(self, *, title: str, steps: List[Dict[str, Any]], justification: str, source: Optional[str]) -> str:
                content = f"Procedure: {title}\nJustification: {justification}\nSteps: {json.dumps(steps)}"
                return await self.add_memory(content=content, user_id=os.getenv("CEREBRAL_USER_ID", "system"), metadata={"source": source or "local"})  # type: ignore[return-value]

            async def store_episode(self, *, run_id: str, task_id: Optional[str], content: str, metadata: Dict[str, Any]) -> str:
                md = dict(metadata or {})
                md.update({"run_id": run_id, "task_id": task_id})
                return await self.add_memory(content=content, user_id=os.getenv("CEREBRAL_USER_ID", "system"), metadata=md)  # type: ignore[return-value]

            async def get_stats(self) -> Dict[str, Any]:
                count = 0
                if self.path.exists():
                    count = sum(1 for _ in self.path.open("r", encoding="utf-8"))
                return {"items": count}

        self._memory = _SimpleMemory()
        return self._memory

    async def handle_memory_add(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_dev_mode():
            return {"success": False, "error": "local memory store disabled in this profile"}
        mem = self._get_memory()
        content = str(arguments.get("content", "")).strip()
        if not content:
            return {"success": False, "error": "content is required"}
        user_id = str(arguments.get("userId", "system"))
        metadata = arguments.get("metadata") or {}
        memory_id = await mem.add_memory(content=content, user_id=user_id, metadata=metadata)
        return {"success": True, "memoryId": memory_id}

    async def handle_memory_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_dev_mode():
            return {"success": False, "error": "local memory store disabled in this profile"}
        mem = self._get_memory()
        query = str(arguments.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "query is required"}
        user_id = str(arguments.get("userId", "system"))
        limit = int(arguments.get("limit", 20))
        # Optional tuning
        min_score = arguments.get("min_score")
        kwargs = {}
        if isinstance(min_score, (int, float)):
            kwargs["min_similarity_score"] = float(min_score)
        results = await mem.search_memories(query=query, user_id=user_id, limit=limit, **kwargs)
        return {"success": True, "count": len(results), "results": results}

    async def handle_memory_store_procedure(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_dev_mode():
            return {"success": False, "error": "local memory store disabled in this profile"}
        mem = self._get_memory()
        title = str(arguments.get("title", "")).strip()
        steps = arguments.get("steps") or []
        justification = str(arguments.get("justification", "")).strip()
        source = arguments.get("source")
        if not title or not steps or not justification:
            return {"success": False, "error": "title, steps, and justification are required"}
        # Normalize steps: ensure list of dicts with order/instruction/notes
        norm_steps: List[Dict[str, Any]] = []
        for idx, s in enumerate(steps, start=1):
            if isinstance(s, dict):
                order = int(s.get("order", idx))
                instruction = str(s.get("instruction", "")).strip()
                notes = s.get("notes")
            else:
                order = idx
                instruction = str(s)
                notes = None
            norm_steps.append({"order": order, "instruction": instruction, "notes": notes})
        memory_id = await mem.store_procedure_update(
            title=title,
            steps=norm_steps,
            justification=justification,
            source=source,
        )
        return {"success": True, "memoryId": memory_id}

    async def handle_memory_store_episode(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_dev_mode():
            return {"success": False, "error": "local memory store disabled in this profile"}
        mem = self._get_memory()
        run_id = str(arguments.get("runId", "")).strip()
        task_id = str(arguments.get("taskId", "")).strip()
        content = str(arguments.get("content", "")).strip()
        metadata = arguments.get("metadata") or {}
        if not run_id or not content:
            return {"success": False, "error": "runId and content are required"}
        memory_id = await mem.store_episode(run_id=run_id, task_id=task_id or None, content=content, metadata=metadata)
        return {"success": True, "memoryId": memory_id}

    async def handle_memory_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_dev_mode():
            return {"success": True, "stats": {"items": 0, "disabled": True}}
        mem = self._get_memory()
        stats = await mem.get_stats()
        return {"success": True, "stats": stats}


