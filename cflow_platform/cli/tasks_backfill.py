from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")


def fetch_supabase_tasks(max_rows: int = 50000) -> List[Dict[str, Any]]:
    """Fetch tasks via Supabase SDK (no raw REST)."""
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"supabase sdk missing: {e}")
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or key in environment")
    client = create_client(url, key)
    try:
        resp = client.table("cerebraflow_tasks").select("id,title,description").limit(max_rows).execute()
        data = getattr(resp, "data", None) or []
        return data if isinstance(data, list) else []
    except Exception:
        resp = client.table("cerebraflow_tasks").select("id,description").limit(max_rows).execute()
        data = getattr(resp, "data", None) or []
        return data if isinstance(data, list) else []


def get_chroma_client(path: Path):
    from chromadb import PersistentClient  # type: ignore
    from chromadb.config import Settings  # type: ignore
    path.mkdir(parents=True, exist_ok=True)
    return PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False, allow_reset=False))


def backfill_tasks_into_chroma(rows: List[Dict[str, Any]], chroma_path: Path) -> Dict[str, int]:
    client = get_chroma_client(chroma_path)
    col = client.get_or_create_collection(name="cerebral_tasks")
    added = 0
    skipped = 0
    B = 200
    for i in range(0, len(rows), B):
        batch = rows[i:i + B]
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        for r in batch:
            tid = str(r.get("id"))
            title = r.get("title")
            desc = r.get("description") or ""
            content = f"{title or ''}\n{desc}".strip()
            if not tid or not content:
                skipped += 1
                continue
            ids.append(tid)
            docs.append(content)
            metas.append({"title": title, "source": "supabase.cerebraflow_tasks"})
        if not ids:
            continue
        try:
            col.add(ids=ids, documents=docs, metadatas=metas)
            added += len(ids)
        except Exception:
            for j, tid in enumerate(ids):
                try:
                    col.add(ids=[tid], documents=[docs[j]], metadatas=[metas[j]])
                    added += 1
                except Exception:
                    skipped += 1
    return {"added": added, "skipped": skipped}


def enforce_local_matches_supabase(chroma_path: Path, sup_ids: Set[str]) -> Dict[str, int]:
    client = get_chroma_client(chroma_path)
    col = client.get_or_create_collection(name="cerebral_tasks")
    try:
        data = col.get()
        local_ids = set(data.get("ids", [])) if isinstance(data, dict) else set()
    except Exception:
        local_ids = set()
    extraneous = list(local_ids - sup_ids)
    removed = 0
    B = 500
    for i in range(0, len(extraneous), B):
        try:
            col.delete(ids=extraneous[i:i + B])
            removed += len(extraneous[i:i + B])
        except Exception:
            for idv in extraneous[i:i + B]:
                try:
                    col.delete(ids=[idv])
                    removed += 1
                except Exception:
                    pass
    return {"removed": removed, "local_before": len(local_ids), "local_after": len(local_ids) - removed}


def run_one_shot_sync(project_root: Path) -> Dict[str, Any]:
    return {"status": "skipped", "mode": "sdk_only", "message": "vendor realtime sync disabled"}


def cli() -> int:
    parser = argparse.ArgumentParser(description="Backfill tasks from Supabase into local Chroma and trigger one-shot vector sync")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args = parser.parse_args()

    load_env()
    project_root = Path(args.project_root)
    chroma_path = project_root / ".cerebraflow" / "core" / "storage" / "chromadb"

    try:
        tasks = fetch_supabase_tasks()
    except Exception as e:
        print(json.dumps({"success": False, "error": f"fetch_tasks: {e}"}))
        return 1

    sup_ids = {str(t.get("id")) for t in tasks if t.get("id")}
    res = backfill_tasks_into_chroma(tasks, chroma_path)
    enforce = enforce_local_matches_supabase(chroma_path, sup_ids)
    sync_report = run_one_shot_sync(project_root)
    print(json.dumps({"success": True, "backfill": res, "enforce": enforce, "sync": sync_report}))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
