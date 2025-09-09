from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from cflow_platform.core.code_intel.function_indexer import FunctionIndexer
from cflow_platform.core.code_intel.callgraph_builder import build_call_edges
from cflow_platform.core.code_intel.callgraph_store import FileCallGraphStore, StoredEdge
import os


def _cmd_index(args: argparse.Namespace) -> int:
    idx = FunctionIndexer()
    paths: List[Path] = []
    if args.changed_only:
        # Best-effort: use git to list changed files relative to HEAD
        import subprocess
        try:
            out = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True).strip()
            for line in out.splitlines():
                p = Path(line)
                if p.exists() and p.is_file():
                    paths.append(p)
        except Exception:
            pass
    else:
        root = Path.cwd()
        for p in root.rglob("*"):
            if p.is_file():
                paths.append(p)
    res = idx.index_paths(paths)
    print({"status": "success", **res})
    return 0


def _cmd_build_graph(args: argparse.Namespace) -> int:
    root = Path.cwd()
    edges: List[StoredEdge] = []
    for p in root.rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for e in build_call_edges(p, content):
            edges.append(StoredEdge(
                caller_id=e.caller_id,
                caller_name=e.caller.name,
                caller_path=e.caller.file_path,
                callee_name=e.callee_name,
            ))
    # Include TS/JS if helper available
    for p in list(root.rglob("*.ts")) + list(root.rglob("*.tsx")) + list(root.rglob("*.js")) + list(root.rglob("*.jsx")):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for e in build_call_edges(p, content):
            edges.append(StoredEdge(
                caller_id=e.caller_id,
                caller_name=e.caller.name,
                caller_path=e.caller.file_path,
                callee_name=e.callee_name,
            ))
    store = FileCallGraphStore()
    store.save_edges(edges)
    # Optional: dual-write call edges to Supabase (with tenancy metadata)
    try:
        from supabase import create_client  # type: ignore
        url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_REST_URL") or "").strip()
        key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
        if url and key:
            supa = create_client(url, key)
            # Map (path,name) -> id
            id_cache = {}
            added = 0
            tenant_id = os.getenv("CFLOW_TENANT_ID") or None
            user_id = os.getenv("CFLOW_USER_ID") or None
            project_id = os.getenv("CFLOW_PROJECT_ID") or None
            for e in edges:
                keypair = (e.caller_path, e.caller_name)
                fid = id_cache.get(keypair)
                if fid is None:
                    try:
                        sel = supa.table("code_functions").select("id").eq("path", e.caller_path).eq("name", e.caller_name).limit(1).execute()
                        data = getattr(sel, "data", None) or []
                        if data:
                            fid = str(data[0]["id"])  # type: ignore[index]
                            id_cache[keypair] = fid
                    except Exception:
                        fid = None
                if fid:
                    try:
                        supa.table("code_calls").insert({
                            "caller_function_id": fid,
                            "callee_name": e.callee_name,
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "project_id": project_id,
                        }).execute()
                        added += 1
                    except Exception:
                        pass
            print({"status": "success", "edges": len(edges), "remote_upserts": added})
            return 0
    except Exception:
        pass
    print({"status": "success", "edges": len(edges)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cflow-code-intel", description="Code intelligence utilities")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_index = sub.add_parser("index-functions", help="Index functions and embed summaries")
    p_index.add_argument("--changed-only", action="store_true", help="Index only changed files (git)")
    p_index.set_defaults(func=_cmd_index)
    p_graph = sub.add_parser("build-callgraph", help="Build a call graph and persist to local store")
    p_graph.set_defaults(func=_cmd_build_graph)
    return p


def cli() -> None:
    parser = build_parser()
    args = parser.parse_args()
    exit(args.func(args))


