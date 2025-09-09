from __future__ import annotations

import os
import time
import importlib
import pytest


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


def test_vector_padding_truncation_and_dims_metadata_roundtrip(monkeypatch):
    # Use the sync service to generate and normalize vectors; ensure dims metadata recorded
    from cflow_platform.core.services.chroma_sync_service import (
        ChromaDBSupabaseSyncService,
    )

    # Skip if chromadb is not installed
    if importlib.util.find_spec("chromadb") is None:  # type: ignore[attr-defined]
        pytest.skip("chromadb not available; skipping roundtrip metadata test")

    os.environ.setdefault("SUPABASE_VECTOR_DIMS", "64")
    svc = ChromaDBSupabaseSyncService(project_root=None)

    # Add document and fetch from Chroma to inspect metadata and embedding length
    import asyncio

    async def _run():
        # Use a fresh collection name to avoid existing dimension constraints
        collection_name = "cerebral_mem_test64"
        doc_id = await svc.add_document(
            collection_type=collection_name, content="test content", metadata={"source": "unit"}
        )
        collection = svc.get_collection(collection_name)
        res = collection.get(ids=[doc_id], include=["embeddings", "metadatas"])  # type: ignore[arg-type]
        return res

    res = asyncio.get_event_loop().run_until_complete(_run())
    emb = res["embeddings"][0]
    meta = res["metadatas"][0]
    # Accept numpy arrays or lists
    try:
        import numpy as _np  # type: ignore
        if hasattr(emb, "tolist"):
            emb = emb.tolist()
    except Exception:
        pass
    assert isinstance(emb, list) and len(emb) == 64
    # Metadata must include model and dims
    assert meta.get("embedding_model") is not None
    assert meta.get("embedding_dims") is not None
    assert meta.get("embedding_target_dims") == 64


def test_mps_perf_slo_best_effort():
    # Soft SLO: if on MPS, embedding for ~1KB text should be < 0.2s
    text = "x" * 1024
    os.environ["CFLOW_SKIP_APPLE_MPS"] = "0"
    from cflow_platform.core.embeddings.apple_silicon_accelerator import (
        get_apple_silicon_accelerator,
        generate_accelerated_embeddings,
    )

    accel = get_apple_silicon_accelerator()
    device = accel.get_device_string()
    # Warm up to avoid first-load costs
    _ = generate_accelerated_embeddings([text])  # type: ignore[arg-type]
    start = time.time()
    _ = generate_accelerated_embeddings([text])  # type: ignore[arg-type]
    elapsed = time.time() - start
    if device == "mps":
        assert elapsed < 0.4  # allow some CI variance


