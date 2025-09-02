from __future__ import annotations

"""
Enterprise Embedding Service (Core)

Provides high-level embedding APIs for enterprise RAG flows using the core
Apple Silicon accelerator and core embedding service.
"""

from typing import List, Dict, Any
import logging

from cflow_platform.core.services.ai.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class EnterpriseEmbeddingService:
    def __init__(self) -> None:
        self._svc = get_embedding_service()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return await self._svc.generate_embeddings(texts)

    async def embed_corpus(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        contents = [d.get("content", "") for d in docs]
        vecs = await self.embed_texts(contents)
        out: List[Dict[str, Any]] = []
        for d, v in zip(docs, vecs):
            out.append({**d, "embedding": v})
        return out


