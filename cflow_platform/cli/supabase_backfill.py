from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv


def _sdk():
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"supabase sdk missing: {e}"}))
    url = os.getenv("SUPABASE_URL", "").strip() or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    # Guard: if a DB URL was mistakenly set in SUPABASE_URL, derive REST URL
    if url.startswith("postgresql://"):
        rest = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip()
        if not rest:
            pref = os.getenv("SUPABASE_PROJECT_REF", "").strip()
            rest = f"https://{pref}.supabase.co" if pref else ""
        url = rest
    if not (url and key):
        raise SystemExit(json.dumps({"success": False, "error": "missing SUPABASE_URL or key"}))
    return create_client(url, key)


def _chroma():
    try:
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"chromadb missing: {e}"}))
    base = Path.cwd() / ".cerebraflow" / "core" / "storage" / "chromadb"
    base.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(base), settings=Settings(anonymized_telemetry=False, allow_reset=False))
    return client


def _fetch_all_rows_sdk(table: str, select: str = "*") -> List[Dict[str, Any]]:
    client = _sdk()
    rows: List[Dict[str, Any]] = []
    try:
        resp = client.table(table).select(select).execute()
        data = getattr(resp, "data", None) or []
        if isinstance(data, list):
            rows = data
    except Exception as e:
        raise SystemExit(json.dumps({"success": False, "error": f"supabase sdk error: {e}"}))
    return rows


def backfill_docs() -> Dict[str, Any]:
    table = os.getenv("CFLOW_SUPABASE_DOCS_TABLE", "documentation_files").strip()
    rows = _fetch_all_rows_sdk(table)
    client = _chroma()
    col = client.get_or_create_collection(name="cerebral_docs")
    added = 0
    for r in rows:
        try:
            doc_id = str(r.get("id") or r.get("doc_id") or "").strip()
            if not doc_id:
                continue
            title = str(r.get("title") or "").strip()
            content = str(r.get("content") or r.get("text") or r.get("body") or "").strip()
            meta = {k: ("" if v is None else v) for k, v in r.items() if k not in {"content", "text", "body"}}
            col.upsert(ids=[doc_id], documents=[f"{title}\n{content}"], metadatas=[meta])  # type: ignore[attr-defined]
            added += 1
        except Exception:
            continue
    return {"success": True, "added": added}


def backfill_tasks_to_memory() -> Dict[str, Any]:
    """Mirror tasks into memory via memory_add (Edge-friendly)."""
    try:
        from cflow_platform.core.public_api import get_direct_client_executor
    except Exception as e:
        return {"success": False, "error": f"public_api import: {e}"}
    rows = _fetch_all_rows_sdk(os.getenv("CFLOW_SUPABASE_TASKS_TABLE", "cerebraflow_tasks"))
    added = 0
    skipped = 0
    import asyncio
    async def _run():
        nonlocal added, skipped
        dc = get_direct_client_executor()
        for r in rows:
            title = (r.get("title") or "").strip()
            desc = (r.get("description") or "").strip()
            if not title:
                skipped += 1
                continue
            content = f"TASK: {title}\n{desc}".strip()
            try:
                await dc("memory_add", content=content, userId=os.getenv("CEREBRAL_USER_ID", "system"), metadata={"type": "task", "source": "supabase"})
                added += 1
            except Exception:
                skipped += 1
    asyncio.get_event_loop().run_until_complete(_run())
    return {"success": True, "added": added, "skipped": skipped}


def cli() -> int:
    # Load env from project files before parsing/acting
    try:
        load_dotenv(dotenv_path=Path.cwd() / ".env")
        load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Backfill utilities (Edge-friendly)")
    p.add_argument("--docs", action="store_true", help="Backfill documentation files table into Chroma")
    p.add_argument("--tasks-memory", action="store_true", help="Mirror tasks into memory via memory_add (no direct DB)")
    args = p.parse_args()
    if args.docs:
        print(json.dumps(backfill_docs()))
        return 0
    if args.tasks_memory:
        print(json.dumps(backfill_tasks_to_memory()))
        return 0
    print(json.dumps({"success": False, "error": "no action"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(cli())


