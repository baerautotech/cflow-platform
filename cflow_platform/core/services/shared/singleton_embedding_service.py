from __future__ import annotations

"""
Singleton Embedding Service (Core)

Provides cached, singleton access to the core Apple Silicon accelerator for
embedding generation without external dependencies.
"""

import hashlib
import logging
import threading
from typing import List, Optional, Dict

from cflow_platform.core.embeddings.apple_silicon_accelerator import (
    generate_accelerated_embeddings,
)

logger = logging.getLogger(__name__)


class SingletonEmbeddingService:
    _instance: Optional["SingletonEmbeddingService"] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "SingletonEmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[return-value]

    def __init__(self) -> None:
        if self._initialized:
            return
        self._embedding_cache: Dict[str, List[float]] = {}
        self._initialized = True
        logger.info("SingletonEmbeddingService initialized")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results: List[Optional[List[float]]] = []
        to_process: List[str] = []
        indices: List[int] = []

        for i, t in enumerate(texts):
            h = hashlib.md5(t.encode()).hexdigest()
            if h in self._embedding_cache:
                results.append(self._embedding_cache[h])
            else:
                results.append(None)
                to_process.append(t)
                indices.append(i)

        if to_process:
            new_vecs = generate_accelerated_embeddings(to_process)
            if not new_vecs or len(new_vecs) != len(to_process):
                raise RuntimeError("Embedding generation failed for some texts")
            for i, vec in enumerate(new_vecs):
                orig = indices[i]
                results[orig] = vec
                h = hashlib.md5(to_process[i].encode()).hexdigest()
                self._embedding_cache[h] = vec

        return [r for r in results if r is not None]  # type: ignore[list-item]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def get_model_info(self) -> dict:
        # Core accelerator is stateless here; expose cache stats
        return {
            "cache_size": len(self._embedding_cache),
        }


def get_embedding_service() -> SingletonEmbeddingService:
    return SingletonEmbeddingService()
