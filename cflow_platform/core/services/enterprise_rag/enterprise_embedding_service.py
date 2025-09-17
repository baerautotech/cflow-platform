from __future__ import annotations

"""
Enterprise Embedding Service (Core)

Provides high-level embedding APIs for enterprise RAG flows using the unified
embedding service with Apple Silicon acceleration.
"""

from typing import List, Dict, Any
import logging

from cflow_platform.core.services.ai.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class EnterpriseEmbeddingService:
    """Enterprise wrapper around the unified embedding service."""
    
    def __init__(self) -> None:
        self._svc = get_embedding_service()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return await self._svc.generate_embeddings(texts)

    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts (synchronous)."""
        return self._svc.embed_documents(texts)

    async def embed_corpus(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for a corpus of documents."""
        contents = [d.get("content", "") for d in docs]
        vecs = await self.embed_texts(contents)
        out: List[Dict[str, Any]] = []
        for d, v in zip(docs, vecs):
            out.append({**d, "embedding": v})
        return out

    def embed_corpus_sync(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for a corpus of documents (synchronous)."""
        contents = [d.get("content", "") for d in docs]
        vecs = self.embed_texts_sync(contents)
        out: List[Dict[str, Any]] = []
        for d, v in zip(docs, vecs):
            out.append({**d, "embedding": v})
        return out

    def get_model_info(self) -> Dict[str, Any]:
        """Get model and service information."""
        return self._svc.get_model_info()


