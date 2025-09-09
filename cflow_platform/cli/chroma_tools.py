from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict


def _client():
    try:
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(json.dumps({"success": False, "error": f"chromadb missing: {e}"}))
    base = Path.cwd() / ".cerebraflow" / "core" / "storage" / "chromadb"
    base.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(base), settings=Settings(anonymized_telemetry=False, allow_reset=False))


def purge_collection(name: str) -> Dict[str, Any]:
    client = _client()
    try:
        col = client.get_or_create_collection(name=name)
        # There is no drop in older clients; delete known ids is expensive; rely on reset() where allowed
        try:
            col.delete(where={})  # type: ignore[arg-type]
        except Exception:
            pass
        return {"success": True, "collection": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


def drop_collection(name: str) -> Dict[str, Any]:
    client = _client()
    try:
        client.delete_collection(name=name)
        return {"success": True, "collection": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


def ensure_collection(name: str, hnsw_m: int | None = None, hnsw_ef: int | None = None) -> Dict[str, Any]:
    client = _client()
    try:
        metadata = {}
        if hnsw_m is not None:
            metadata["hnsw:M"] = int(hnsw_m)
        if hnsw_ef is not None:
            metadata["hnsw:efConstruction"] = int(hnsw_ef)
        col = client.get_or_create_collection(name=name, metadata=metadata or None)
        return {"success": True, "collection": name, "metadata": metadata}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cli() -> int:
    p = argparse.ArgumentParser(description="Chroma operational tools (purge/drop/ensure)")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_purge = sub.add_parser("purge")
    p_purge.add_argument("name")
    p_drop = sub.add_parser("drop")
    p_drop.add_argument("name")
    p_ensure = sub.add_parser("ensure")
    p_ensure.add_argument("name")
    p_ensure.add_argument("--hnsw-m", type=int)
    p_ensure.add_argument("--hnsw-ef", type=int)
    args = p.parse_args()
    if args.cmd == "purge":
        print(json.dumps(purge_collection(args.name)))
        return 0
    if args.cmd == "drop":
        print(json.dumps(drop_collection(args.name)))
        return 0
    if args.cmd == "ensure":
        print(json.dumps(ensure_collection(args.name, args.hnsw_m, args.hnsw_ef)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(cli())


