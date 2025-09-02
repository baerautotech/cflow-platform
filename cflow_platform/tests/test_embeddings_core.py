from __future__ import annotations

import os


def test_core_accelerator_generates_embeddings_without_hf_optin():
    # Ensure embedder path uses core accelerator
    os.environ.pop("CFLOW_ALLOW_HF", None)
    os.environ["CFLOW_SKIP_APPLE_MPS"] = "0"
    from cflow_platform.core.embeddings.apple_silicon_accelerator import (
        generate_accelerated_embeddings,
    )

    vecs = generate_accelerated_embeddings(["hello", "world"])  # type: ignore[arg-type]
    assert isinstance(vecs, list)
    assert len(vecs) == 2
    assert isinstance(vecs[0], list)
    assert len(vecs[0]) > 0


