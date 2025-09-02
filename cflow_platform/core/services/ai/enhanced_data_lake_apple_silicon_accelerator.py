from __future__ import annotations

"""
Enhanced Data Lake Apple Silicon Accelerator (Core)

Embeds data lake records using the core Apple Silicon accelerator.
Expects each record to contain a 'text' field; returns records with
an added 'embedding' list[float].
"""

from typing import List, Dict, Any, Optional
import logging

from cflow_platform.core.embeddings.apple_silicon_accelerator import (
    generate_accelerated_embeddings,
)

logger = logging.getLogger(__name__)


class EnhancedDataLakeAppleSiliconAccelerator:
    def __init__(self) -> None:
        self.security_service = None  # Optional: attach a concrete security service when available

    async def embed_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Async wrapper to avoid blocking loop
        import asyncio
        texts = [str(r.get("text", "")) for r in records]
        vecs = await asyncio.to_thread(generate_accelerated_embeddings, texts)
        if not isinstance(vecs, list) or len(vecs) != len(records):
            # Fallback to zeros if accelerator unavailable
            vecs = self._create_fallback_accelerator()(len(records))
        out: List[Dict[str, Any]] = []
        for r, v in zip(records, vecs):
            nr = dict(r)
            nr["embedding"] = v
            out.append(nr)
        self._track_acceleration_metrics(len(records), len(vecs))
        return out

    # Helpers adapted from enterprise implementation (minimal functional versions)
    def _create_fallback_accelerator(self):
        def _gen(n: int) -> List[List[float]]:
            try:
                import numpy as np  # type: ignore
                return [np.zeros(384).tolist() for _ in range(n)]
            except Exception:
                return [[0.0] * 384 for _ in range(n)]
        return _gen

    def validate_tenant_access(self, tenant_id: Optional[str]) -> bool:
        # Placeholder validation; integrate real tenant checks when available
        return True if tenant_id is None or isinstance(tenant_id, str) else False

    def _select_acceleration_strategy(self) -> str:
        try:
            from cflow_platform.core.embeddings.apple_silicon_accelerator import (
                get_apple_silicon_accelerator,
            )
            return get_apple_silicon_accelerator().get_device_string()
        except Exception:
            return "cpu"

    def _accelerated_vector_processing(self, texts: List[str]) -> List[List[float]]:
        vecs = generate_accelerated_embeddings(texts)
        if not isinstance(vecs, list) or not vecs:
            return self._create_fallback_accelerator()(len(texts))
        return vecs

    def accelerated_etl_transformation(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Simple transformation: normalize whitespace
        norm: List[Dict[str, Any]] = []
        for r in records:
            nr = dict(r)
            txt = str(nr.get("text", ""))
            nr["text"] = " ".join(txt.split())
            norm.append(nr)
        return norm

    def _accelerated_analytics(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Simple keyword frequency across records
        import re
        freq: Dict[str, int] = {}
        for r in records:
            for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", str(r.get("text", ""))):
                if len(token) > 2:
                    freq[token] = freq.get(token, 0) + 1
        return {"keywords": sorted(freq.items(), key=lambda x: x[1], reverse=True)[:50]}

    def _track_acceleration_metrics(self, records: int, vectors: int) -> None:
        logger.info("data_lake_accel processed=%d vectors=%d", records, vectors)

    def log_acceleration_operation(self, name: str, meta: Optional[Dict[str, Any]] = None) -> None:
        logger.info("op=%s meta=%s", name, (meta or {}))


