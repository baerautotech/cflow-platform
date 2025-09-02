from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")


def fetch_supabase_docs(max_rows: int = 20000) -> List[Dict[str, Any]]:
    import httpx  # type: ignore

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or key in environment")

    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "count=exact"}
    params = {
        "select": "id,title,content",
        "limit": str(max_rows),
    }
    r = httpx.get(url.rstrip("/") + "/rest/v1/documentation_files", headers=headers, params=params, timeout=30.0)
    if r.status_code == 400:
        # Fallback to minimal select
        params = {"select": "id,content", "limit": str(max_rows)}
        r = httpx.get(url.rstrip("/") + "/rest/v1/documentation_files", headers=headers, params=params, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return data


def get_chroma_client(path: Path):
    from chromadb import PersistentClient  # type: ignore
    from chromadb.config import Settings  # type: ignore

    path.mkdir(parents=True, exist_ok=True)
    return PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False, allow_reset=False))


def backfill_docs_into_chroma(docs: List[Dict[str, Any]], chroma_path: Path) -> Dict[str, int]:
    client = get_chroma_client(chroma_path)
    collection = client.get_or_create_collection(name="cerebral_docs")

    added = 0
    skipped = 0
    B = 100
    for i in range(0, len(docs), B):
        batch = docs[i:i + B]
        ids: List[str] = []
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        for row in batch:
            doc_id = str(row.get("id"))
            content = row.get("content") or ""
            title = row.get("title")
            if not doc_id or not isinstance(content, str) or not content.strip():
                skipped += 1
                continue
            ids.append(doc_id)
            texts.append(content)
            metas.append({"title": title, "source": "supabase.documentation_files"})
        if not ids:
            continue
        try:
            collection.add(ids=ids, documents=texts, metadatas=metas)
            added += len(ids)
        except Exception:
            for j, doc_id in enumerate(ids):
                try:
                    collection.add(ids=[doc_id], documents=[texts[j]], metadatas=[metas[j]])
                    added += 1
                except Exception:
                    skipped += 1
    return {"added": added, "skipped": skipped}


def enforce_local_matches_supabase(chroma_path: Path, supabase_ids: Set[str]) -> Dict[str, int]:
    client = get_chroma_client(chroma_path)
    col = client.get_or_create_collection(name="cerebral_docs")
    # Fetch all local ids in chunks
    removed = 0
    fetched = 0
    offset = 0
    page = 1000
    # Chroma Python API get() supports where and include; many clients need pagination by slicing ids not supported; we use count then get by n_results via query workaround
    try:
        data = col.get()
        local_ids = set(data.get("ids", [])) if isinstance(data, dict) else set()
    except Exception:
        local_ids = set()
    extraneous = list(local_ids - supabase_ids)
    B = 200
    for i in range(0, len(extraneous), B):
        try:
            col.delete(ids=extraneous[i:i + B])
            removed += len(extraneous[i:i + B])
        except Exception:
            # best-effort per id
            for idv in extraneous[i:i + B]:
                try:
                    col.delete(ids=[idv])
                    removed += 1
                except Exception:
                    pass
    return {"removed": removed, "local_before": len(local_ids), "local_after": len(local_ids) - removed}


def run_one_shot_sync(project_root: Path) -> Dict[str, Any]:
    import subprocess
    env = os.environ.copy()
    env["CFLOW_VECTOR_SYNC_ENABLED"] = env.get("CFLOW_VECTOR_SYNC_ENABLED", "1")
    env["CFLOW_VECTOR_COLUMN"] = env.get("CFLOW_VECTOR_COLUMN", "embeddings")
    cmd = [
        os.environ.get("PYTHON", "python"),
        str(project_root / "cflow_platform" / "vendor" / "cerebral" / "services" / "unified_realtime_sync_service.py"),
        "once",
        "--project-root",
        str(project_root),
    ]
    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.stdout else {}
    except Exception:
        data = {"stdout": proc.stdout, "stderr": proc.stderr}
    return data


def cli() -> int:
    parser = argparse.ArgumentParser(description="Backfill documentation files from Supabase into local Chroma and trigger one-shot vector sync")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args = parser.parse_args()

    load_env()
    project_root = Path(args.project_root)
    chroma_path = project_root / ".cerebraflow" / "core" / "storage" / "chromadb"

    try:
        docs = fetch_supabase_docs()
    except Exception as e:
        print(json.dumps({"success": False, "error": f"fetch_docs: {e}"}))
        return 1

    sup_ids = {str(d.get("id")) for d in docs if d.get("id")}
    res = backfill_docs_into_chroma(docs, chroma_path)
    enforce = enforce_local_matches_supabase(chroma_path, sup_ids)
    sync_report = run_one_shot_sync(project_root)
    print(json.dumps({"success": True, "backfill": res, "enforce": enforce, "sync": sync_report}))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
