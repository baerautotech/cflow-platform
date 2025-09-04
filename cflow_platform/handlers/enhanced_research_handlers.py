from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os

from dotenv import load_dotenv
from supabase import create_client, Client  # type: ignore

from cflow_platform.core.services.ai.embedding_service import (
    get_embedding_service,
)


class EnhancedResearchHandlers:
    """Package wrapper for enhanced research tools.

    Delegates to monorepo implementation when available while keeping
    imports package-safe.
    """

    def __init__(self, task_manager, project_root: Path):
        self.task_manager = task_manager
        self.project_root = project_root
        self._supabase: Optional[Client] = None

    # -------- Internal helpers --------
    def _ensure_supabase(self) -> Optional[Client]:
        """Create and cache a Supabase client using local .env when available.

        Returns None if credentials are missing to allow graceful fallback.
        """
        if self._supabase is not None:
            return self._supabase
        try:
            # Load env from repo root if present
            load_dotenv(dotenv_path=self.project_root / ".env", override=False)
        except Exception:
            # Best-effort only
            pass
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            return None
        try:
            self._supabase = create_client(url, key)
            return self._supabase
        except Exception:
            return None

    async def _vector_search(
        self, query_text: str, top_k: int = 8
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Run vector search via RPC match_memory_vectors; returns results and a flag indicating vector path used.
        Falls back to keyword search if RPC is unavailable.
        """
        client = self._ensure_supabase()
        if client is None:
            return [], False

        # Compute embedding locally using Apple Silicon accelerator
        embedder = get_embedding_service()
        try:
            embedding = (await embedder.generate_embeddings([query_text]))[0]
        except Exception:
            embedding = []

        # Prefer RPC if embedding is available
        if embedding:
            try:
                rpc_res = client.rpc(
                    "match_memory_vectors",
                    {"query_embedding": embedding, "match_count": top_k},
                ).execute()
                rows = getattr(rpc_res, "data", None) or []
                if isinstance(rows, list) and rows:
                    return rows, True
            except Exception:
                # Continue to keyword fallback
                pass

        # Keyword fallback across title/content
        try:
            pattern = f"%{query_text}%"
            q = (
                client.table("memory_items")
                .select("id,title,content,metadata,created_at")
                .or_(f"title.ilike.{pattern},content.ilike.{pattern}")
                .limit(top_k)
            )
            resp = q.execute()
            rows = getattr(resp, "data", None) or []
            return rows, False
        except Exception:
            return [], False

    async def handle_doc_research(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Try to delegate to monorepo enhanced implementation by path
        try:
            from importlib.util import spec_from_file_location, module_from_spec
            repo_root = Path(__file__).resolve().parents[4]
            mono_path = repo_root / ".cerebraflow" / "core" / "mcp" / "handlers" / "enhanced_research_handlers.py"
            spec = spec_from_file_location("mono_enhanced_research_handlers", str(mono_path))
            if spec and spec.loader:
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                MonoHandlers = getattr(mod, "EnhancedResearchHandlers")
                mono = MonoHandlers(task_manager=self.task_manager, project_root=self.project_root)
                result = await mono.handle_enhanced_research(arguments)
                # Normalize to structured response
                if isinstance(result, list):
                    text = "\n\n".join(getattr(x, "text", str(x)) for x in result)
                    return {
                        "status": "success",
                        "content": text,
                        "taskId": arguments.get("taskId"),
                        "autoCreateSubtasks": bool(arguments.get("autoCreateSubtasks", True)),
                        "createTDD": bool(arguments.get("createTDD", True)),
                    }
                if isinstance(result, dict):
                    # Ensure status and taskId present
                    out = {"status": result.get("status", "success"), **result}
                    out.setdefault("taskId", arguments.get("taskId"))
                    return out
        except Exception:
            # Fall back to minimal implementation
            pass

        # Supabase-backed fallback
        task_id = arguments.get("taskId")
        research_query = arguments.get("researchQuery", "").strip()
        top_k = int(arguments.get("topK", 8) or 8)
        auto_create = bool(arguments.get("autoCreateSubtasks", True))
        create_tdd = bool(arguments.get("createTDD", True))

        if not research_query:
            return {
                "status": "error",
                "message": "researchQuery is required",
                "taskId": task_id,
            }

        rows, used_vector = await self._vector_search(research_query, top_k=top_k)

        # Shape output consistently
        def _to_snippet(r: Dict[str, Any]) -> str:
            title = r.get("title") or ""
            content = r.get("content") or ""
            sim = r.get("similarity")
            sim_str = f" [sim={sim:.3f}]" if isinstance(sim, (int, float)) else ""
            if title and content:
                return f"{title}{sim_str}\n{content}"
            return (title or content)[:2048]

        snippets = [
            _to_snippet(r)
            for r in rows
            if isinstance(r, dict)
        ]
        content = "\n\n---\n\n".join(snippets) if snippets else "No matching memory found."

        return {
            "status": "success",
            "taskId": task_id,
            "autoCreateSubtasks": auto_create,
            "createTDD": create_tdd,
            "content": content,
            "metadata": {
                "query": research_query,
                "topK": top_k,
                "vectorSearch": used_vector,
                "matches": len(rows),
            },
        }

    async def handle_research(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generic enhanced research entrypoint matching tool name 'research'."""
        # Reuse the same implementation but accept 'query' as the canonical field
        if "researchQuery" not in arguments and "query" in arguments:
            arguments = {**arguments, "researchQuery": arguments.get("query", "")}
        return await self.handle_doc_research(arguments)


