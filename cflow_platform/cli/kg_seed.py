from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from cflow_platform.core.config.supabase_config import get_rest_url, get_api_key


def _client():
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"supabase sdk missing: {e}"}))
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".cerebraflow", ".env"), override=True)
    url = get_rest_url() or ""
    key = get_api_key() or ""
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


