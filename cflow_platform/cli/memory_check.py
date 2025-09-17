from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from cflow_platform.core.config.supabase_config import get_rest_url, get_api_key, get_tenant_id


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


def cli() -> int:
    _load_env()

    # Initialize variables
    supa_url = ""
    supa_key = ""
    client = None

    # SDK client
    try:
        from supabase import create_client  # type: ignore
        supa_url = get_rest_url() or ""
        supa_key = get_api_key() or ""
        client = create_client(supa_url, supa_key) if (supa_url and supa_key) else None
    except Exception:
        pass

    issues: Dict[str, Any] = {}

    # Reachability via SDK (auth + a light table call)
    rest_status: Dict[str, Any] = {"reachable": False, "status_code": None, "error": None}
    try:
        if client is not None:
            _ = client.table("knowledge_items").select("id").limit(1).execute()
            rest_status = {"reachable": True, "status_code": 200, "error": None}
        else:
            issues["SDK_client_unavailable"] = True
    except Exception as e:
        rest_status = {"reachable": False, "status_code": None, "error": str(e)}
        issues["REST_unreachable"] = str(e)

    # RPC availability via SDK
    rpc_status: Dict[str, Any] = {"available": False, "status_code": None, "error": None, "result_len": None}
    try:
        if client is not None:
            query_embedding = [0.0] * 1536
            tenant = get_tenant_id()
            payload: Dict[str, Any] = {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,
                "match_count": 1,
                "tenant_filter": tenant,
                "content_types": None,
            }
            resp = client.rpc("search_agentic_embeddings", payload).execute()
            data = getattr(resp, "data", None) or []
            rpc_status = {"available": True, "status_code": 200, "error": None, "result_len": len(data) if isinstance(data, list) else None}
        else:
            issues["SDK_client_unavailable_for_rpc"] = True
    except Exception as e:
        rpc_status = {"available": False, "status_code": None, "error": str(e), "result_len": None}
        issues["RPC_missing_or_unreachable"] = str(e)

    status = {
        "env": {
            "SUPABASE_URL_valid": bool(supa_url),
            "SUPABASE_KEY_present": bool(supa_key),
            "loaded_env": [
                str(Path.cwd() / ".env") if (Path.cwd() / ".env").exists() else None,
                str(Path.cwd() / ".cerebraflow" / ".env") if (Path.cwd() / ".cerebraflow" / ".env").exists() else None,
            ],
        },
        "rest": rest_status,
        "rpc": rpc_status,
        "probe": {"doc_id": None, "hit_count": 0},
        "write_readback": {"items_found": None, "error": None},
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


