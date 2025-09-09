from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os
import json
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client, Client  # type: ignore

from cflow_platform.core.services.ai.embedding_service import (
    get_embedding_service,
)
from cflow_platform.core.security.secret_store import SecretStore


class EnhancedResearchHandlers:
    """Package wrapper for enhanced research tools.

    Delegates to monorepo implementation when available while keeping
    imports package-safe.
    """

    def __init__(self, task_manager, project_root: Path):
        self.task_manager = task_manager
        self.project_root = project_root
        self._supabase: Optional[Client] = None
        self._secret_store = SecretStore(base_dir=project_root / ".cerebraflow")

    # -------- Security/profile helpers --------
    def _is_secure_mode(self) -> bool:
        """Return True when running in production/secure mode.

        Controlled via CFLOW_SECURE_MODE env (1/true/yes). Default: False.
        """
        val = os.getenv("CFLOW_SECURE_MODE", "").strip().lower()
        return val in {"1", "true", "yes", "on"}

    def _get_secret(self, key: str) -> Optional[str]:
        # Prefer SecretStore; then environment
        return self._secret_store.get(key) or os.getenv(key)

    def _load_envs(self) -> None:
        """Load env from repo-level and .cerebraflow/.env (non-fatal)."""
        try:
            load_dotenv(dotenv_path=self.project_root / ".env", override=False)
        except Exception:
            pass

    def _normalize_supabase_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        u = url.strip()
        # If a Postgres connection string was provided, derive REST base
        if u.startswith("postgres://") or u.startswith("postgresql://"):
            try:
                from urllib.parse import urlparse
                p = urlparse(u)
                host = p.hostname or ""
                if host.startswith("db.") and host.endswith(".supabase.co"):
                    host = host[len("db."):]
                if host.endswith(".supabase.co"):
                    return f"https://{host}"
            except Exception:
                pass
            # Fallback to env override if present
            rest_override = os.getenv("SUPABASE_REST_URL")
            if rest_override:
                return rest_override
            return None
        # Ensure scheme for REST URL
        if not u.startswith("http://") and not u.startswith("https://"):
            u = f"https://{u}"
        # Convert db.<proj>.supabase.co -> <proj>.supabase.co
        try:
            from urllib.parse import urlparse, urlunparse
            p = urlparse(u)
            host = p.netloc
            if host.startswith("db.") and host.endswith(".supabase.co"):
                host = host[len("db."):]
                p = p._replace(netloc=host)
            # Strip any path; REST client wants root domain
            p = p._replace(path="", params="", query="", fragment="")
            return urlunparse(p)
        except Exception:
            return u
        try:
            load_dotenv(dotenv_path=self.project_root / ".cerebraflow" / ".env", override=False)
        except Exception:
            pass

    def _audit_event(self, event: str, payload: Dict[str, Any]) -> None:
        try:
            logs_dir = self.project_root / ".cerebraflow" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            path = logs_dir / "audit.jsonl"
            record = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "event": event,
                **payload,
            }
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            # Best-effort only; never raise from auditing
            pass

    # -------- Internal helpers --------
    def _ensure_supabase(self) -> Optional[Client]:
        """Create and cache a Supabase client using local .env when available.

        Returns None if credentials are missing to allow graceful fallback.
        """
        if self._supabase is not None:
            return self._supabase
        # Load envs (repo + .cerebraflow override)
        self._load_envs()
        # Prefer secret store; fall back to env
        # Support both SUPABASE_* and CEREBRAL_SUPABASE_* naming
        url = self._normalize_supabase_url(
            self._get_secret("SUPABASE_URL")
            or self._get_secret("CEREBRAL_SUPABASE_URL")
            or self._get_secret("SUPABASE_REST_URL")
            or self._get_secret("CEREBRAL_SUPABASE_REST_URL")
        )
        # In secure mode, prefer service role; otherwise allow anon for dev
        key = None
        if self._is_secure_mode():
            key = (
                self._get_secret("SUPABASE_SERVICE_ROLE_KEY")
                or self._get_secret("CEREBRAL_SUPABASE_SERVICE_ROLE_KEY")
            )
        if not key:
            key = (
                self._get_secret("SUPABASE_SERVICE_ROLE_KEY")
                or self._get_secret("CEREBRAL_SUPABASE_SERVICE_ROLE_KEY")
                or self._get_secret("SUPABASE_ANON_KEY")
                or self._get_secret("CEREBRAL_SUPABASE_ANON_KEY")
            )
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
        """Run vector search via RPC (KG first), optionally fall back in dev mode.

        Order:
        1) KG RPC (search_agentic_embeddings) if tenant_id available
        2) Legacy RPC (match_memory_vectors)
        3) Dev-only keyword fallback on memory_items(title/content)
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
            # 1) KG RPC with tenant filter (prefer CEREBRAL_TENANT_ID; fallback to CFLOW_TENANT_ID)
            tenant_id = (
                self._get_secret("CEREBRAL_TENANT_ID")
                or os.getenv("CEREBRAL_TENANT_ID")
                or self._get_secret("CFLOW_TENANT_ID")
                or os.getenv("CFLOW_TENANT_ID")
            )
            if tenant_id:
                try:
                    kg_rpc = os.getenv("SUPABASE_KG_SEARCH_RPC", "search_agentic_embeddings")
                    kg_res = client.rpc(
                        kg_rpc,
                        {"query_embedding": embedding, "match_count": top_k, "tenant_filter": tenant_id},
                    ).execute()
                    kg_rows = getattr(kg_res, "data", None) or []
                    if isinstance(kg_rows, list) and kg_rows:
                        # Normalize KG rows to a common shape
                        norm: List[Dict[str, Any]] = []
                        for r in kg_rows:
                            if isinstance(r, dict):
                                content = r.get("content_chunk") or r.get("content") or ""
                                score = r.get("score")
                                md = r.get("metadata") or {}
                                norm.append({
                                    "title": md.get("title"),
                                    "content": content,
                                    "similarity": float(score) if isinstance(score, (int, float)) else None,
                                    "metadata": md,
                                })
                        if norm:
                            return norm, True
                except Exception:
                    # Continue to legacy RPC
                    pass

            # 2) Legacy RPC
            try:
                rpc_name = os.getenv("SUPABASE_MATCH_RPC", "match_memory_vectors")
                rpc_res = client.rpc(
                    rpc_name,
                    {"query_embedding": embedding, "match_count": top_k},
                ).execute()
                rows = getattr(rpc_res, "data", None) or []
                if isinstance(rows, list) and rows:
                    return rows, True
            except Exception:
                # Continue to keyword fallback
                pass

        # Keyword fallback across title/content (dev-only)
        if self._is_secure_mode():
            # In secure mode, do not fall back to broad keyword search
            return [], False
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

        result = {
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
        # Audit
        try:
            self._audit_event("research_query", {
                "secure_mode": self._is_secure_mode(),
                "vector_path": used_vector,
                "matches": len(rows),
                "query_preview": research_query[:128],
            })
        except Exception:
            pass
        return result

    async def handle_research(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generic enhanced research entrypoint matching tool name 'research'."""
        # Reuse the same implementation but accept 'query' as the canonical field
        if "researchQuery" not in arguments and "query" in arguments:
            arguments = {**arguments, "researchQuery": arguments.get("query", "")}
        return await self.handle_doc_research(arguments)


