## Database Schema (Supabase + pgvector)

### Tables
- memory_items(id uuid pk, type text, scope text, classification text, title text, content text, metadata jsonb, created_at timestamptz, updated_at timestamptz)
- memory_vectors(id uuid pk, item_id uuid fk -> memory_items(id) on delete cascade, embedding vector(1536), dims int, model text, created_at timestamptz)

### Indexing
- Distance metrics
  - Cosine: `vector_cosine_ops` (default for semantic embeddings)
  - L2: `vector_l2_ops`
  - IP (dot product): `vector_ip_ops`

- Choice guidelines
  - Small sets (<100k rows): HNSW with cosine
  - Medium (100k–10M rows): start with HNSW; switch to IVFFlat if memory pressure or build time is high
  - Large (≥10M rows): IVFFlat with tuned `lists` and runtime `probes`; batch ANALYZE after bulk load

- Recommended defaults for this project (assume cosine, 1.5k dims)
  - HNSW (fast recall, smaller sets):
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS mv_embedding_hnsw
ON memory_vectors USING hnsw (embedding vector_cosine_ops);
```
  - IVFFlat (large scale):
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS mv_embedding_ivfflat
ON memory_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- Tune lists by dataset size (rule of thumb: sqrt(n) to n/100), and set probes at query time
```

### Policies
- Row-Level Security scoped to project; anon insert/select with project key.
- RPC: `match_memory_vectors(query_embedding vector, match_count int)` for similarity search.

