from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from cflow_platform.core.code_intel.function_indexer import FunctionIndexer
from cflow_platform.core.services.shared.singleton_embedding_service import get_embedding_service
from cflow_platform.core.code_intel.callgraph_store import FileCallGraphStore


class CodeIntelHandlers:
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.indexer = FunctionIndexer()

    async def handle_index_functions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        files: List[str] = args.get("files") or []
        paths = [self.project_root / f for f in files] if files else [p for p in self.project_root.rglob("*") if p.is_file()]
        res = self.indexer.index_paths(paths)
        return {"status": "success", **res}

    async def handle_search_functions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        description: str = args.get("description") or ""
        top_k: int = int(args.get("topK") or 8)
        svc = get_embedding_service()
        query_vec = svc.embed_query(description)
        if not self.indexer.collection:
            return {"status": "error", "message": "Vector collection not available"}
        try:
            # type: ignore[attr-defined]
            results = self.indexer.collection.query(query_embeddings=[query_vec], n_results=top_k)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        # Return minimal metadata for precision
        out: List[Dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        docs = results.get("documents", [[]])[0]
        use_classifier = str(os.getenv("CFLOW_CODE_CLASSIFY", "0")).strip() == "1"
        for i in range(min(len(ids), len(metas))):
            meta = metas[i]
            summary = docs[i] if i < len(docs) else ""
            out.append({
                "id": ids[i],
                "file_path": meta.get("file_path"),
                "language": meta.get("language"),
                "name": meta.get("name"),
                "signature": meta.get("signature"),
                "start": meta.get("start"),
                "end": meta.get("end"),
                "summary": summary,
            })
        # Optional LLM gate
        if use_classifier and out:
            try:
                from cflow_platform.core.public_api import get_direct_client_executor
                import asyncio
                dc = get_direct_client_executor()
                payload = {
                    "description": description,
                    "candidates": [{"name": r["name"], "path": r["file_path"], "summary": r["summary"], "signature": r["signature"]} for r in out],
                }
                # Reuse existing reasoning tool (or future classifier handler)
                res = asyncio.get_event_loop().run_until_complete(dc("code_reasoning.plan", prompt="classify", context=payload))
                # Expect res to contain a list of accepted indices or names; if not, keep all
                accepted = set()
                try:
                    for item in res.get("accepted", []):
                        accepted.add(item.get("name") or item.get("path"))
                except Exception:
                    accepted = set()
                if accepted:
                    out = [r for r in out if (r["name"] in accepted or r["file_path"] in accepted)]
            except Exception:
                pass
        return {"status": "success", "results": out}

    async def handle_call_paths(self, args: Dict[str, Any]) -> Dict[str, Any]:
        target: str = args.get("to") or ""
        max_depth: int = int(args.get("maxDepth") or 6)
        if not target:
            return {"status": "error", "message": "Missing 'to' target function name"}
        store = FileCallGraphStore()
        graph = store.load_graph()
        paths = graph.call_paths_to(target, max_depth=max_depth)
        # Serialize as list of caller chains (file:name)
        out: List[List[dict]] = []
        for chain in paths:
            out.append([
                {
                    "caller_id": e.caller_id,
                    "caller": e.caller_name,
                    "path": e.caller_path,
                    "calls": e.callee_name,
                }
                for e in chain
            ])
        return {"status": "success", "paths": out}


