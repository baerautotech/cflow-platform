from __future__ import annotations

"""
Unified Embedding Service - Core Implementation

Centralized service for generating vector embeddings using Apple Silicon
accelerator with caching and thread-safe singleton access pattern.
Consolidates all embedding functionality into a single service.
"""

import hashlib
import logging
import threading
from typing import List, Dict, Optional, Any

from cflow_platform.core.embeddings.enhanced_apple_silicon_accelerator import (
    EnhancedAppleSiliconAccelerator,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Unified embedding service with thread-safe singleton pattern."""
    
    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()
    _accelerator: Optional[EnhancedAppleSiliconAccelerator] = None
    _embedding_cache: Dict[str, List[float]] = {}
    _initialized = False

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[return-value]

    def __init__(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            logger.info("Initializing Unified Embedding Service...")
            self._accelerator = EnhancedAppleSiliconAccelerator()
            self._initialized = True
            logger.info("Unified Embedding Service initialized.")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts (async interface)."""
        return self.embed_documents(texts)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts (sync interface)."""
        if not self._accelerator:
            raise RuntimeError("EmbeddingService is not initialized.")

        results: List[Optional[List[float]]] = []
        texts_to_process: List[str] = []
        indices_to_process: List[int] = []

        # Cache lookup
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._embedding_cache:
                results.append(self._embedding_cache[text_hash])
            else:
                results.append(None)
                texts_to_process.append(text)
                indices_to_process.append(i)

        # Generate for missing
        if texts_to_process:
            logger.info("Generating embeddings for %d texts", len(texts_to_process))
            new_embeddings = self._accelerator.generate_embeddings(texts_to_process)
            if not new_embeddings or len(new_embeddings) != len(texts_to_process):
                raise RuntimeError("Failed to generate embeddings for all texts.")
            for i, embedding in enumerate(new_embeddings):
                original_index = indices_to_process[i]
                results[original_index] = embedding
                text_hash = hashlib.md5(texts_to_process[i].encode()).hexdigest()
                self._embedding_cache[text_hash] = embedding

        if any(r is None for r in results):
            raise RuntimeError("Failed to generate embeddings for some texts.")
        return [r for r in results if r is not None]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        return self.embed_documents([text])[0]

    def get_model_info(self) -> Dict[str, Any]:
        """Get model and cache information."""
        return {
            "cache_size": len(self._embedding_cache),
            "accelerator_type": "EnhancedAppleSiliconAccelerator",
            "initialized": self._initialized
        }


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    return EmbeddingService()
