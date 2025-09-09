from __future__ import annotations

from typing import List
import hashlib

from cflow_platform.core.code_intel.function_extractor import FunctionInfo
from cflow_platform.core.services.shared.singleton_embedding_service import (
    get_embedding_service,
)


def summarize_function(fn: FunctionInfo) -> str:
    # Compact, deterministic summary string used for embeddings and search
    doc = (fn.docstring or "").strip().replace("\n", " ")
    base = f"name: {fn.name}\nfile: {fn.file_path}\nlanguage: {fn.language}\nsignature: {fn.signature}\nspan: {fn.start_line}-{fn.end_line}"
    if doc:
        base += f"\ndoc: {doc[:400]}"
    return base


def embed_summaries(summaries: List[str]) -> List[List[float]]:
    # Use shared Apple Silicon accelerator path
    svc = get_embedding_service()
    return svc.embed_documents(summaries)


def summary_id(fn: FunctionInfo) -> str:
    payload = f"{fn.file_path}:{fn.name}:{fn.start_line}:{fn.end_line}:{fn.language}"
    return hashlib.md5(payload.encode()).hexdigest()


