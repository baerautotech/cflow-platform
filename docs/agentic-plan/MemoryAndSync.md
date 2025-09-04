## Memory & Supabase Sync

- Local: ChromaDB collections for artifacts and episodic logs
- Remote: Supabase RDB for raw items + pgvector for embeddings
- Dual‑write: add/search perform local embedding → store in Chroma + RDB + vector
- Realtime: optional signals to trigger incremental pulls (off by default)

### Concrete Integration (ChromaDBSupabaseSyncService)

- Add Document flow:
  - Generate embedding with Apple Silicon accelerator; pad/truncate to dims
  - Chroma: `collection.add(ids, documents, metadatas, embeddings)`
  - Supabase: upsert to `knowledge_items`; upsert to `knowledge_embeddings` with `content_chunk`, `embedding`, `chunk_index=0`, `content_type`
  - Tenancy metadata: resolve `{tenant_id, user_id, project_id}` from env

- Search flow:
  - Embed query; attempt RPC `search_agentic_embeddings` with `{query_embedding, match_count, tenant_filter}`
  - On RPC failure/missing: fallback to Chroma `collection.query`

- Connectivity check CLI: `cflow-memory-check`
  - Loads `.env` and `.cerebraflow/.env`
  - Validates `SUPABASE_URL`/key presence and runs add→search probe

### Realtime (optional)

- Enable publication `supabase_realtime`; add `knowledge_*` tables
- Off by default; wire incremental pulls only when enabled

### Safety & Performance

- Never block on Supabase writes; Chroma path must succeed
- Index with HNSW (cosine) by default; consider IVFFlat for large datasets
- Record `model` and `dims` in vector rows; enforce dimension normalization in the service

References: see DatabaseSchema for SQL and docs links.

