from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from cflow_platform.core.config.supabase_config import get_rest_url, get_api_key, get_tenant_id


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
    from supabase import create_client  # type: ignore
    return create_client(url, key)


def _embed_text(text: str) -> List[float]:
    import asyncio
    from cflow_platform.core.services.ai.embedding_service import get_embedding_service  # type: ignore

    async def _go(t: str):
        svc = get_embedding_service()
        vecs = await svc.generate_embeddings([t])
        return vecs[0] if vecs else []

    return asyncio.run(_go(text))


def run_etl(limit: int = 100) -> Dict[str, Any]:
    client = _client()
    tenant_id = get_tenant_id()
    try:
        resp = client.table("cerebraflow_tasks").select("id,title,description,metadata").limit(limit).execute()
        rows: List[Dict[str, Any]] = getattr(resp, "data", None) or []
    except Exception as e:
        return {"success": False, "error": f"fetch_tasks: {e}"}
    inserted = 0
    errors: List[str] = []
    for r in rows:
        try:
            tid = str(r.get("id"))
            title = (r.get("title") or "").strip()
            content = (r.get("description") or "").strip()
            meta = r.get("metadata") or {}
            if not content:
                continue
            # upsert knowledge_item by source id
            ki = client.table("knowledge_items").upsert({
                "tenant_id": tenant_id,
                "title": title,
                "content": content,
                "metadata": {"source_table": "cerebraflow_tasks", "source_id": tid, **(meta if isinstance(meta, dict) else {})},
            }, on_conflict="title").execute()
            ki_rows = getattr(ki, "data", None) or []
            kid = (ki_rows[0] or {}).get("id") if ki_rows else None
            if not kid:
                continue
            emb = _embed_text(content)
            client.table("knowledge_embeddings").insert({
                "knowledge_item_id": kid,
                "tenant_id": tenant_id,
                "content_chunk": content,
                "embedding": emb,
                "chunk_index": 0,
                "content_type": "task",
                "metadata": {"title": title, "source_table": "cerebraflow_tasks", "source_id": tid},
            }).execute()
            inserted += 1
        except Exception as e:
            errors.append(str(e))
    return {"success": True, "inserted": inserted, "errors": errors}


def cli() -> int:
    p = argparse.ArgumentParser(description="Incremental ETL from cerebraflow_tasks to knowledge_* tables")
    p.add_argument("--limit", type=int, default=100)
    args = p.parse_args()
    res = run_etl(limit=args.limit)
    print(json.dumps(res))
    return 0 if res.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(cli())
