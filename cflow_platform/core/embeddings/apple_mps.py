from __future__ import annotations

import os
from typing import Any, Iterable, Optional
from cflow_platform.core.embeddings.apple_silicon_accelerator import (
    generate_accelerated_embeddings,
)


def get_embedder() -> Optional[Any]:
    """Return an embedding callable using Cerebral's Apple Silicon service.

    - Prioritizes vendor accelerator for exact behavior parity
    - Skips any embedding during pre-commit if CFLOW_SKIP_APPLE_MPS=1
    - Does NOT fetch remote models or use HF tokens
    """
    if os.environ.get("CFLOW_SKIP_APPLE_MPS", "0").lower() in {"1", "true", "yes"}:
        return None

    # Use core accelerator
    def _embed(inputs: Iterable[str] | str):
        texts = [inputs] if isinstance(inputs, str) else list(inputs)
        vecs = generate_accelerated_embeddings(texts)
        return vecs

    class _CoreEmbedder:
        name = "cflow_core_apple_silicon"
        def __call__(self, inputs: Iterable[str] | str):
            return _embed(inputs)

    return _CoreEmbedder()

    # As a last resort, disable embedding to avoid unexpected dependencies in this path
    return None


