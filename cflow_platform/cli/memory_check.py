from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def _load_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    root = Path.cwd() / ".env"
    local = Path.cwd() / ".cerebraflow" / ".env"
    if root.exists():
        load_dotenv(dotenv_path=str(root))
    if local.exists():
        load_dotenv(dotenv_path=str(local), override=True)
    load_dotenv()


def _validate_supabase_url(url: str | None) -> bool:
    return bool(url and url.startswith("http"))


def cli() -> int:
    _load_env()

    # Fast env checks
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_ANON_KEY")
    issues: Dict[str, Any] = {}
    if not _validate_supabase_url(supa_url):
        issues["SUPABASE_URL"] = "invalid_or_missing"
    if not supa_key:
        issues["SUPABASE_ANON_KEY"] = "missing"

    # Attempt end-to-end write/search using the sync service
    sys.path.append(str((Path(__file__).resolve().parents[2] / "vendor" / "cerebral" / "services").resolve()))
    from cflow_platform.vendor.cerebral.services.chromadb_supabase_sync_service import (
        ChromaDBSupabaseSyncService,  # type: ignore
    )

    svc = ChromaDBSupabaseSyncService()
    import asyncio

    async def _run() -> Dict[str, Any]:
        doc_id = await svc.add_document(
            collection_type="cerebral_mem",
            content="cflow memory check probe",
            metadata={"type": "context", "source": "memory-check"},
        )
        results = await svc.search_documents(
            collection_type="cerebral_mem",
            query="memory check probe",
            limit=3,
        )
        return {"doc_id": doc_id, "results": results}

    out: Dict[str, Any] = {}
    try:
        out = asyncio.get_event_loop().run_until_complete(_run())
    except Exception as e:
        issues["runtime_error"] = str(e)

    status = {
        "env": {
            "SUPABASE_URL_valid": _validate_supabase_url(supa_url),
            "SUPABASE_ANON_KEY_present": bool(supa_key),
        },
        "probe": {
            "doc_id": out.get("doc_id"),
            "hit_count": len(out.get("results", [])) if out else 0,
        },
        "issues": issues,
    }
    print(json.dumps(status, indent=2))
    ok = status["env"]["SUPABASE_URL_valid"] and status["env"]["SUPABASE_ANON_KEY_present"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(cli())


