## Apple Silicon Accelerator

- Implemented: core accelerator, MPS embedder, embedding service; pre‑commit emoji guard
- Remaining ports: singleton_embedding_service, enterprise RAG services, vectorization service, enhanced data lake accelerator
- Wiring: vendor services should call core `cflow_platform/core/...` modules only
- Tests: unit smoke test verifies vector generation without HF/network

