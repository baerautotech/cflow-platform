from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from cflow_platform.core.code_intel.function_extractor import extract_functions, FunctionInfo
from cflow_platform.core.code_intel.function_summarizer import summarize_function, embed_summaries, summary_id


try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False

try:
    from supabase import create_client  # type: ignore
    SUPABASE_SDK = True
except Exception:
    SUPABASE_SDK = False


@dataclass
class IndexedFunction:
    id: str
    fn: FunctionInfo
    summary: str
    embedding: Optional[List[float]]


class FunctionIndexer:
    def __init__(self, chroma_path: Optional[str] = None) -> None:
        self.collection = None
        self._supa = None
        if CHROMA_AVAILABLE:
            path = chroma_path or ".cerebraflow/core/storage/chromadb"
            client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False, is_persistent=True))  # type: ignore
            self.collection = client.get_or_create_collection(name="cflow_functions", metadata={"description": "Function-level semantics"})  # type: ignore

    def _ensure_supabase(self) -> Optional[Any]:
        if self._supa is not None:
            return self._supa
        if not SUPABASE_SDK:
            return None
        # Load envs
        from dotenv import load_dotenv  # local import to avoid hard dep at import time
        try:
            load_dotenv(dotenv_path=Path.cwd() / ".env")
            load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")
        except Exception:
            pass
        url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_REST_URL") or "").strip()
        key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
        if not (url and key):
            return None
        try:
            self._supa = create_client(url, key)
            return self._supa
        except Exception:
            return None

    def _supa_find_or_create_function(self, supa: Any, f: FunctionInfo, summary: str) -> Optional[str]:
        try:
            sel = supa.table("code_functions").select("id").eq("path", f.file_path).eq("name", f.name).eq("start_line", f.start_line).eq("end_line", f.end_line).limit(1).execute()
            data = getattr(sel, "data", None) or []
            if data:
                return str(data[0]["id"])  # type: ignore[index]
            tenant_id = os.getenv("CFLOW_TENANT_ID") or None
            user_id = os.getenv("CFLOW_USER_ID") or None
            project_id = os.getenv("CFLOW_PROJECT_ID") or None
            ins = supa.table("code_functions").insert({
                "repo": os.getenv("CFLOW_REPO_NAME", ""),
                "path": f.file_path,
                "name": f.name,
                "language": f.language,
                "signature": f.signature,
                "start_line": f.start_line,
                "end_line": f.end_line,
                "summary": summary,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "project_id": project_id,
                "metadata": {
                    "source": "cflow",
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "project_id": project_id,
                },
            }).execute()
            data2 = getattr(ins, "data", None) or []
            if data2:
                return str(data2[0]["id"])  # type: ignore[index]
            return None
        except Exception:
            return None

    def _supa_insert_embedding(self, supa: Any, function_id: str, embedding: List[float]) -> None:
        try:
            tenant_id = os.getenv("CFLOW_TENANT_ID") or None
            user_id = os.getenv("CFLOW_USER_ID") or None
            project_id = os.getenv("CFLOW_PROJECT_ID") or None
            supa.table("code_function_embeddings").insert({
                "function_id": function_id,
                "embedding": embedding,
                "dims": len(embedding),
                "model": os.getenv("CFLOW_EMBED_MODEL", "mps-local-384"),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "project_id": project_id,
            }).execute()
        except Exception:
            pass

    def index_paths(self, paths: List[Path]) -> Dict[str, int]:
        indexed = 0
        functions = 0
        fns: List[FunctionInfo] = []
        for p in paths:
            if not p.exists() or not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            funcs = extract_functions(p)
            if not funcs:
                continue
            fns.extend(funcs)
        if not fns:
            return {"indexed": 0, "functions": 0}

        summaries = [summarize_function(f) for f in fns]
        embeddings = embed_summaries(summaries)
        ids = [summary_id(f) for f in fns]
        metadatas: List[Dict[str, object]] = []
        documents: List[str] = []
        for f, s in zip(fns, summaries):
            meta: Dict[str, object] = {
                "file_path": f.file_path,
                "language": f.language,
                "name": f.name,
                "signature": f.signature,
                "start": f.start_line,
                "end": f.end_line,
                "ts": datetime.utcnow().isoformat() + "Z",
            }
            documents.append(s)
            metadatas.append(meta)
        if self.collection is not None:
            # best-effort add (ignore duplicates)
            try:
                self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)  # type: ignore
            except Exception:
                pass
        # Dual-write to Supabase when available
        supa = self._ensure_supabase()
        if supa is not None:
            for f, s, e in zip(fns, summaries, embeddings):
                fid = self._supa_find_or_create_function(supa, f, s)
                if fid:
                    self._supa_insert_embedding(supa, fid, e)
        indexed = len(ids)
        functions = len(fns)
        return {"indexed": indexed, "functions": functions}


