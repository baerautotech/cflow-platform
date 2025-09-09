from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
import os

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception:  # pragma: no cover
    chromadb = None  # type: ignore
    Settings = None  # type: ignore

from cflow_platform.core.embeddings.apple_silicon_accelerator import (
    generate_accelerated_embeddings,
)


class ChromaDBSupabaseSyncService:
    """Local service for embedding dims/metadata roundtrip and collection access."""

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        base = self.project_root / ".cerebraflow" / "core" / "storage" / "chromadb"
        base.mkdir(parents=True, exist_ok=True)
        if chromadb is None or Settings is None:
            raise RuntimeError("chromadb not available")
        self._client = chromadb.PersistentClient(
            path=str(base), settings=Settings(anonymized_telemetry=False, allow_reset=False)
        )

    def get_collection(self, name: str):  # type: ignore[no-untyped-def]
        return self._client.get_or_create_collection(name=name)

    async def add_document(
        self,
        collection_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        col = self.get_collection(collection_type)
        vec = generate_accelerated_embeddings([content])[0]
        dims = len(vec)
        raw = (metadata or {}).get("embedding_target_dims") or (os.getenv("SUPABASE_VECTOR_DIMS") or dims)
        try:
            target_dims = int(raw)  # type: ignore[arg-type]
        except Exception:
            target_dims = dims
        if dims < target_dims:
            vec = vec + [0.0] * (target_dims - dims)
        elif dims > target_dims:
            vec = vec[:target_dims]
        meta = dict(metadata or {})
        meta.setdefault("embedding_model", "apple_mps")
        meta["embedding_dims"] = dims
        meta["embedding_target_dims"] = target_dims
        doc_id = f"doc_{abs(hash(content)) % 10_000_000}"
        col.add(ids=[doc_id], documents=[content], embeddings=[vec], metadatas=[meta])  # type: ignore[arg-type]
        return doc_id


