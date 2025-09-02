## Memory & Supabase Sync

- Local: ChromaDB collections for artifacts and episodic logs
- Remote: Supabase RDB for raw items + pgvector for embeddings
- Dual‑write: add/search perform local embedding → store in Chroma + RDB + vector
- Realtime: optional signals to trigger incremental pulls (off by default)

