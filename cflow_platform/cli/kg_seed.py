from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv


def _client():
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"supabase sdk missing: {e}"}))
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".cerebraflow", ".env"), override=True)
    # Normalize URL (handles REST host or Postgres DSN)
    raw_url = (
        os.getenv("SUPABASE_URL", "").strip()
        or os.getenv("CEREBRAL_SUPABASE_URL", "").strip()
        or os.getenv("SUPABASE_REST_URL", "").strip()
        or os.getenv("CEREBRAL_SUPABASE_REST_URL", "").strip()
    )
    def _normalize(u: str) -> str:
        if not u:
            return u
        s = u.strip()
        # If this looks like a Postgres DSN (with or without http prefix), derive REST base
        if s.startswith("postgres://") or s.startswith("postgresql://") or "://postgres" in s:
            try:
                # Strip any accidental http(s) prefix before the DSN
                if s.startswith("http://") or s.startswith("https://"):
                    s = s.split("://", 1)[1]
                    # Now s starts with 'postgresql://...' or similar without scheme; add back for parsing
                    if not s.startswith("postgres"):
                        s = "postgresql://" + s
                from urllib.parse import urlparse
                p = urlparse(s)
                host = p.hostname or ""
                if host.startswith("db.") and host.endswith(".supabase.co"):
                    host = host[len("db."):]
                if host.endswith(".supabase.co"):
                    return f"https://{host}"
            except Exception:
                pass
            # Fallback to an explicit override if provided
            ov = os.getenv("SUPABASE_REST_URL", "").strip()
            if ov:
                return ov
            return ""
        # Otherwise treat as REST base
        if not s.startswith("http://") and not s.startswith("https://"):
            s = f"https://{s}"
        try:
            from urllib.parse import urlparse, urlunparse
            p = urlparse(s)
            host = p.netloc
            if host.startswith("db.") and host.endswith(".supabase.co"):
                host = host[len("db."):]
                p = p._replace(netloc=host)
            p = p._replace(path="", params="", query="", fragment="")
            return urlunparse(p)
        except Exception:
            return s
    url = _normalize(raw_url)
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("CEREBRAL_SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("CEREBRAL_SUPABASE_ANON_KEY")
        or ""
    ).strip()
    if not (url and key):
        raise SystemExit(json.dumps({"success": False, "error": "missing SUPABASE_URL or key"}))
    return create_client(url, key)


def seed_knowledge_item(*, tenant_id: str, title: str, content: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    client = _client()
    try:
        ki = client.table("knowledge_items").insert({
            "tenant_id": tenant_id,
            "title": title,
            "content": content,
            "metadata": metadata or {},
        }).execute()
        row = (getattr(ki, "data", None) or [{}])[0]
        kid = row.get("id")
        if not kid:
            return {"success": False, "error": "insert returned no id"}
        # Generate embedding locally using core service
        try:
            import asyncio
            from cflow_platform.core.services.ai.embedding_service import get_embedding_service  # type: ignore
            async def _emb(txt: str):
                svc = get_embedding_service()
                vecs = await svc.generate_embeddings([txt])
                return vecs[0] if vecs else []
            embedding = asyncio.run(_emb(content))
        except Exception as e:
            return {"success": False, "error": f"embedding failed: {e}"}
        # Insert embedding row
        try:
            ke = client.table("knowledge_embeddings").insert({
                "knowledge_item_id": kid,
                "tenant_id": tenant_id,
                "content_chunk": content,
                "embedding": embedding,
                "chunk_index": 0,
                "content_type": "text",
                "metadata": {"title": title, **(metadata or {})},
            }).execute()
            _ = getattr(ke, "data", None)
        except Exception as e:
            return {"success": False, "error": f"embedding insert failed: {e}"}
        return {"success": True, "id": kid}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cli() -> int:
    p = argparse.ArgumentParser(description="Seed a minimal knowledge item for vector search validation")
    p.add_argument("tenant_id", help="Tenant UUID for RLS scoping")
    p.add_argument("title")
    p.add_argument("content")
    p.add_argument("--meta", default="{}", help="JSON metadata")
    args = p.parse_args()
    try:
        md = json.loads(args.meta)
    except Exception:
        md = {}
    res = seed_knowledge_item(tenant_id=args.tenant_id, title=args.title, content=args.content, metadata=md)
    print(json.dumps(res))
    return 0 if res.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(cli())


