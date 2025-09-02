## Next Steps (Sync, Vectors, Memory)

- [ ] Vector DB wiring (Supabase pgvector)
  - [ ] Define tables/columns for embeddings
  - [ ] Push/pull pgvector; compute or load vectors
  - [ ] Consistency gate: local Chroma vs remote counts

- [ ] cflowMemory integration
  - [ ] Promote `project_memory.py`/`memory_api.py`
  - [ ] Add memory collections + scalar metadata mappings
  - [ ] Include in sync loop with parity checks

- [ ] Supabase Realtime
  - [ ] Subscribe to updates; trigger incremental pulls
  - [ ] Exit‑on‑converge CLI mode for one‑shot syncs

- [ ] Consistency gates (RDB + VDB)
  - [ ] `cflow-sync status` parity report
  - [ ] CI drift check

