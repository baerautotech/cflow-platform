## Memory & Supabase Sync

- Local: ChromaDB collections for artifacts and episodic logs
- Remote: Supabase RDB for raw items + pgvector for embeddings
- Dual‑write: add/search perform local embedding → store in Chroma + RDB + vector
- Realtime: optional signals to trigger incremental pulls (off by default)

### Concrete Integration (Unified Memory)

- Add Document flow:
  - Generate embedding with Apple Silicon accelerator; pad/truncate to dims
  - Chroma: `collection.add(ids, documents, metadatas, embeddings)`
  - Supabase (SDK-only): upsert to `knowledge_items`; upsert to `knowledge_embeddings` with `content_chunk`, `embedding`, `chunk_index=0`, `content_type`
  - Tenancy metadata: resolve `{tenant_id, user_id, project_id}` from env

- Search flow:
  - Embed query; attempt RPC `search_agentic_embeddings` with `{query_embedding, match_count, tenant_filter}` via SDK
  - If vector path yields no rows, fallback to keyword search on `knowledge_items` via Postgrest SDK

- Connectivity check CLI: `cflow-memory-check`
  - Loads `.env` and `.cerebraflow/.env`
  - Validates `SUPABASE_URL`/key presence via SDK and RPC probe (no raw REST)

### Realtime (optional)

- Enable publication `supabase_realtime`; add `knowledge_*` tables
- Off by default; wire incremental pulls only when enabled
- Pre-commit and CI enforce preference for system LaunchAgent; vendored daemon is deprecated

### Realtime setup (macOS LaunchAgent)

- Install LaunchAgent and watchdog:
  - `uv run python -m cflow_platform.cli.sync_supervisor install-agent --project-root $(pwd)`
  - This writes `~/Library/LaunchAgents/com.cerebraflow.sync.plist` and a simple watchdog `com.cerebraflow.sync.watch.plist`.
- Start/ensure running:
  - `launchctl load -w ~/Library/LaunchAgents/com.cerebraflow.sync.plist`
  - `launchctl kickstart -k gui/$UID/com.cerebraflow.sync`
- Pre-commit/CI will block if vendored services are present and the system agent isn’t running.

### Safety & Performance

- Never block on Supabase writes; Chroma path must succeed
- Index with HNSW (cosine) by default; consider IVFFlat for large datasets
- Record `model` and `dims` in vector rows; enforce dimension normalization in the service

References: see DatabaseSchema for SQL and docs links.

