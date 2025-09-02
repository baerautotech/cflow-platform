from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec


class MemoryHandlers:
    """MCP handlers bridging to CerebralProjectMemory (unified ChromaDB/Supabase).

    Loads vendor memory module by file path to avoid import issues with hyphenated dirs.
    """

    def __init__(self) -> None:
        self._memory = None

    def _get_memory(self):
        if self._memory is not None:
            return self._memory
        here = Path(__file__).resolve()
        pkg_root = here.parents[1]  # .../cflow_platform
        repo_root = here.parents[2]  # repo root
        candidates = [
            pkg_root / "vendor" / "cerebral" / "backend-python" / "shared" / "project_memory.py",
            repo_root / "cflow_platform" / "vendor" / "cerebral" / "backend-python" / "shared" / "project_memory.py",
            repo_root / ".cerebraflow" / "core" / "mcp" / "backend-python" / "shared" / "project_memory.py",
        ]
        pm_path = next((p for p in candidates if p.exists()), candidates[0])
        # Ensure services path for sync service is importable by vendor module
        services_path = (pkg_root / "vendor" / "cerebral" / "services").resolve()
        sys_path_added = False
        import sys
        if str(services_path) not in sys.path:
            sys.path.append(str(services_path))
            sys_path_added = True
        spec = spec_from_file_location("vendor_project_memory", str(pm_path))
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load project_memory from {pm_path}")
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        get_project_memory = getattr(mod, "get_project_memory")
        self._memory = get_project_memory()
        return self._memory

    async def handle_memory_add(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        mem = self._get_memory()
        content = str(arguments.get("content", "")).strip()
        if not content:
            return {"success": False, "error": "content is required"}
        user_id = str(arguments.get("userId", "system"))
        metadata = arguments.get("metadata") or {}
        memory_id = await mem.add_memory(content=content, user_id=user_id, metadata=metadata)
        return {"success": True, "memoryId": memory_id}

    async def handle_memory_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        mem = self._get_memory()
        query = str(arguments.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "query is required"}
        user_id = str(arguments.get("userId", "system"))
        limit = int(arguments.get("limit", 20))
        results = await mem.search_memories(query=query, user_id=user_id, limit=limit)
        return {"success": True, "count": len(results), "results": results}

    async def handle_memory_store_procedure(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
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
        mem = self._get_memory()
        stats = await mem.get_stats()
        return {"success": True, "stats": stats}


