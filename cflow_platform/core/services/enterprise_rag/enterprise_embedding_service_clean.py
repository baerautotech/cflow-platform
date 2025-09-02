from __future__ import annotations

from typing import List, Dict, Any
from cflow_platform.core.services.enterprise_rag.enterprise_embedding_service import (
    EnterpriseEmbeddingService,
)


class EnterpriseEmbeddingServiceClean:
    """
    Clean variant backed by the core enterprise embedding service.
    """

    def __init__(self) -> None:
        self._svc = EnterpriseEmbeddingService()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return await self._svc.embed_texts(texts)

    async def embed_corpus(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return await self._svc.embed_corpus(docs)


