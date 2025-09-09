from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def _sdk():
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"supabase sdk missing: {e}"}))
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
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


def cli() -> int:
    p = argparse.ArgumentParser(description="One-time Supabase -> Chroma backfill for onboarding")
    p.add_argument("--docs", action="store_true", help="Backfill documentation files table into Chroma")
    args = p.parse_args()
    if args.docs:
        print(json.dumps(backfill_docs()))
        return 0
    print(json.dumps({"success": False, "error": "no action"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(cli())


