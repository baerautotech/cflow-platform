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
    # Precedence: repo .env, then .cerebraflow/.env overrides, then defaults
    root = Path.cwd() / ".env"
    local = Path.cwd() / ".cerebraflow" / ".env"
    if root.exists():
        load_dotenv(dotenv_path=str(root))
    if local.exists():
        load_dotenv(dotenv_path=str(local), override=True)
    # Fallback to default search on cwd/home
    load_dotenv()


def _validate_supabase_url(url: str | None) -> bool:
    return bool(url and url.startswith("http"))


def _supabase_headers() -> Dict[str, str] | None:
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not key:
        return None
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "count=exact",
    }


def _http_get(url: str, headers: Dict[str, str] | None, timeout: float = 6.0) -> tuple[bool, int | None, str | None]:
    try:
        import httpx  # type: ignore
    except Exception:
        return False, None, "httpx not installed"
    try:
        resp = httpx.get(url, headers=headers or {}, timeout=timeout)
        return True, resp.status_code, None
    except Exception as e:
        return False, None, str(e)


def _http_post(url: str, json_body: Dict[str, Any], headers: Dict[str, str] | None, timeout: float = 12.0) -> tuple[bool, int | None, Any | None, str | None]:
    try:
        import httpx  # type: ignore
    except Exception:
        return False, None, None, "httpx not installed"
    try:
        resp = httpx.post(url, json=json_body, headers=headers or {}, timeout=timeout)
        data: Any | None = None
        try:
            data = resp.json()
        except Exception:
            data = None
        return True, resp.status_code, data, None
    except Exception as e:
        return False, None, None, str(e)


def cli() -> int:
    _load_env()

    # Fast env checks
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    issues: Dict[str, Any] = {}
    if not _validate_supabase_url(supa_url):
        issues["SUPABASE_URL"] = "invalid_or_missing"
    if not supa_key:
        issues["SUPABASE_KEY"] = "missing"

    # Reachability check (REST)
    http_status: Dict[str, Any] = {"reachable": False, "status_code": None, "error": None}
    if _validate_supabase_url(supa_url):
        ok, code, err = _http_get(supa_url.rstrip("/") + "/rest/v1/", _supabase_headers(), timeout=6.0)
        http_status = {"reachable": ok, "status_code": code, "error": err}
        if not ok:
            issues["REST_unreachable"] = err or f"status={code}"

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

    # Verify write via REST read-back when possible
    write_readback: Dict[str, Any] = {"items_found": None, "error": None}
    if _validate_supabase_url(supa_url) and supa_key and out.get("doc_id"):
        headers = _supabase_headers() or {}
        # knowledge_items read-back (id equality)
        get_ok, get_code, _ = _http_get(
            supa_url.rstrip("/") + f"/rest/v1/knowledge_items?id=eq.{out['doc_id']}&select=id", headers, timeout=8.0
        )
        # If reachable, infer presence from status and optional content-range header via another request
        items_found: int | None = None
        if get_ok and get_code and get_code < 400:
            # Use count=exact to try to fetch Content-Range
            try:
                import httpx  # type: ignore
                resp = httpx.get(
                    supa_url.rstrip("/") + "/rest/v1/knowledge_items",
                    params={"id": f"eq.{out['doc_id']}", "select": "id", "limit": 1},
                    headers=headers,
                    timeout=8.0,
                )
                cr = resp.headers.get("Content-Range") or resp.headers.get("content-range")
                if cr and "/" in cr:
                    total = cr.split("/")[-1]
                    items_found = int(total) if total.isdigit() else None
            except Exception as e:
                write_readback["error"] = str(e)
        write_readback["items_found"] = items_found

    # RPC availability probe
    rpc_status: Dict[str, Any] = {"available": False, "status_code": None, "error": None, "result_len": None}
    if _validate_supabase_url(supa_url) and supa_key:
        headers = _supabase_headers() or {}
        # Build a small embedding vector of expected dims
        try:
            dims = int(os.getenv("SUPABASE_VECTOR_DIMS", "1536"))
        except Exception:
            dims = 1536
        query_embedding = [0.0] * max(1, min(dims, 1536))
        tenant = os.getenv("CEREBRAL_TENANT_ID") or os.getenv("CEREBRAFLOW_TENANT_ID")
        payload: Dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_threshold": 0.0,
            "match_count": 1,
            "tenant_filter": tenant,
            "content_types": None,
        }
        rpc_ok, rpc_code, rpc_data, rpc_err = _http_post(
            supa_url.rstrip("/") + "/rest/v1/rpc/search_agentic_embeddings",
            payload,
            headers,
            timeout=12.0,
        )
        rpc_status = {
            "available": bool(rpc_ok and rpc_code and rpc_code < 400),
            "status_code": rpc_code,
            "error": rpc_err,
            "result_len": (len(rpc_data) if isinstance(rpc_data, list) else None),
        }
        if not rpc_status["available"]:
            issues["RPC_missing_or_unreachable"] = rpc_err or f"status={rpc_code}"

    status = {
        "env": {
            "SUPABASE_URL_valid": _validate_supabase_url(supa_url),
            "SUPABASE_KEY_present": bool(supa_key),
            "loaded_env": [
                str(Path.cwd() / ".env") if (Path.cwd() / ".env").exists() else None,
                str(Path.cwd() / ".cerebraflow" / ".env") if (Path.cwd() / ".cerebraflow" / ".env").exists() else None,
            ],
        },
        "rest": http_status,
        "rpc": rpc_status,
        "probe": {
            "doc_id": out.get("doc_id"),
            "hit_count": len(out.get("results", [])) if out else 0,
        },
        "write_readback": write_readback,
        "issues": issues,
    }
    print(json.dumps(status, indent=2))
    ok = (
        status["env"]["SUPABASE_URL_valid"]
        and status["env"]["SUPABASE_KEY_present"]
        and status["rest"]["reachable"]
        and status["rpc"]["available"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(cli())


