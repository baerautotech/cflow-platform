from __future__ import annotations

"""
Specialized AI Services (Accelerated, Core)

Provides simple accelerated embedding endpoints for specialized tasks.
"""

from typing import List
from cflow_platform.core.services.ai.embedding_service import get_embedding_service


class SpecializedAIServicesAccelerated:
    def __init__(self) -> None:
        self._svc = get_embedding_service()

    async def embed_snippets(self, snippets: List[str]) -> List[List[float]]:
        return await self._svc.generate_embeddings(snippets)


