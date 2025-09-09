from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
import os

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

try:
    from cflow_platform.core.local_task_manager import LocalTaskManager  # type: ignore
except Exception:  # pragma: no cover
    LocalTaskManager = None  # type: ignore


def _safe_get(d: Dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def handle_pg_event(event: Dict[str, Any]) -> None:
    """Best-effort mapping from Supabase Realtime payloads to local stores.

    Supported tables (by convention):
    - cerebraflow_tasks → LocalTaskManager (SQLite)
    - documentation_files → ChromaDB collection 'cerebral_docs'
    """
    try:
        topic = str(event.get("topic", ""))
        payload: Dict[str, Any] = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
        evt = str(event.get("event", payload.get("event") or "")).upper() or ""
        schema = str(payload.get("schema", ""))
        table = str(payload.get("table", "")) or topic.split(":")[-1]
        rec = payload.get("record") or payload.get("new") or payload.get("old") or {}
        if not isinstance(rec, dict):
            rec = {}

        if table == "cerebraflow_tasks":
            _apply_task_event(evt, rec)
        elif table == "documentation_files":
            _apply_doc_event(evt, rec)
    except Exception:
        # Best-effort only
        return


def _apply_task_event(evt: str, rec: Dict[str, Any]) -> None:
    if LocalTaskManager is None:
        return
    tm = LocalTaskManager()
    task_id = str(rec.get("id") or rec.get("task_id") or "").strip()
    title = str(rec.get("title") or rec.get("name") or "").strip()
    description = str(rec.get("description") or rec.get("content") or "").strip()
    status = str(rec.get("status") or "pending").strip()
    priority = str(rec.get("priority") or "medium").strip()
    if not task_id:
        return
    try:
        if evt == "DELETE":
            tm.delete_task(task_id)
            return
        # Upsert-like behavior
        existing = tm.get_task(task_id)
        if existing:
            tm.update_task(task_id, {"title": title or existing.get("title"), "description": description or existing.get("description"), "status": status or existing.get("status"), "priority": priority or existing.get("priority")})
        else:
            # add_task generates id; to preserve id, do insert via update path
            tm.add_task(title or f"Task {task_id}", description or "", priority=priority)
            tm.update_task(task_id, {"task_id": task_id})  # ensure id alignment if schema differs
    except Exception:
        return


def _apply_doc_event(evt: str, rec: Dict[str, Any]) -> None:
    try:
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore
    except Exception:
        return


def supabase_upsert(table: str, record: Dict[str, Any]) -> bool:
    """Best-effort REST upsert into Supabase when service role or anon key exists.

    Uses PK id if present. This is a thin compatibility helper for bidirectional sync.
    """
    if httpx is None:
        return False
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not (url and key and table and isinstance(record, dict)):
        return False
    try:
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        resp = httpx.post(url.rstrip("/") + f"/rest/v1/{table}", headers=headers, json=record, timeout=10.0)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False
    try:
        root = Path.cwd() / ".cerebraflow" / "core" / "storage" / "chromadb"
        client = chromadb.PersistentClient(path=str(root), settings=Settings(anonymized_telemetry=False, allow_reset=False))
        collection = client.get_or_create_collection(name="cerebral_docs")
        doc_id = str(rec.get("id") or rec.get("doc_id") or "").strip()
        title = str(rec.get("title") or "").strip()
        content = str(rec.get("content") or rec.get("text") or rec.get("body") or "").strip()
        if not doc_id:
            return
        if evt == "DELETE":
            try:
                collection.delete(ids=[doc_id])  # type: ignore[attr-defined]
            except Exception:
                pass
            return
        metadata = {k: ("" if v is None else v) for k, v in rec.items() if k not in {"content", "text", "body"}}
        # Upsert
        try:
            collection.update(ids=[doc_id], documents=[f"{title}\n{content}"], metadatas=[metadata])  # type: ignore[attr-defined]
        except Exception:
            collection.add(ids=[doc_id], documents=[f"{title}\n{content}"], metadatas=[metadata])  # type: ignore[attr-defined]
    except Exception:
        return


