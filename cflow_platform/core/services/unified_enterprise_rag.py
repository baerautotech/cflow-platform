from __future__ import annotations

"""
Unified Enterprise RAG (Core)

High-level RAG orchestration using the core enterprise embedding service.
"""

from typing import List, Dict, Any, Tuple
import logging

from cflow_platform.core.services.enterprise_rag.enterprise_embedding_service import (
    EnterpriseEmbeddingService,
)

logger = logging.getLogger(__name__)


class UnifiedEnterpriseRAG:
    def __init__(self) -> None:
        self._emb = EnterpriseEmbeddingService()

    async def embed_corpus(self, corpus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return await self._emb.embed_corpus(corpus)

    async def embed_queries(self, queries: List[str]) -> List[List[float]]:
        return await self._emb.embed_texts(queries)

    async def build_index_payload(
        self, corpus: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[List[float]], List[Dict[str, Any]]]:
        contents = [d.get("content", "") for d in corpus]
        vecs = await self._emb.embed_texts(contents)
        metadatas = [{k: v for k, v in d.items() if k != "content"} for d in corpus]
        return contents, vecs, metadatas
