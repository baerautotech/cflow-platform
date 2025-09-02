from __future__ import annotations

"""
AI Embedding Service - Core Implementation

Centralized service for generating vector embeddings using Apple Silicon
accelerator with caching and a singleton access pattern.
"""

import hashlib
import logging
from typing import List, Dict, Optional, Any

from cflow_platform.core.embeddings.enhanced_apple_silicon_accelerator import (
    EnhancedAppleSiliconAccelerator,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _accelerator: Optional[EnhancedAppleSiliconAccelerator] = None
    _embedding_cache: Dict[str, List[float]] = {}

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance  # type: ignore[return-value]

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):  # type: ignore[attr-defined]
            return
        logger.info("Initializing Core AI Embedding Service...")
        self._accelerator = EnhancedAppleSiliconAccelerator()
        self._initialized = True  # type: ignore[attr-defined]
        logger.info("Core AI Embedding Service initialized.")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
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


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
