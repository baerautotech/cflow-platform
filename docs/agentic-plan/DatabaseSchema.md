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


### Enterprise Knowledge Graph Schema (preferred for knowledgeRAG/GRAPH)

- knowledge_items(id uuid pk, user_id uuid, tenant_id uuid, title text, content text, metadata jsonb, created_at timestamptz)
- knowledge_embeddings(id uuid pk, knowledge_item_id uuid fk -> knowledge_items(id) on delete cascade, content_chunk text, embedding vector(1536), chunk_index int, content_type text, metadata jsonb, tenant_id uuid, created_at timestamptz)
- RPC: `search_agentic_embeddings(query_embedding vector(1536), match_count int, tenant_filter uuid, content_types text[]) returns setof record` (server-side similarity search)

Indexes (cosine recommended):
```sql
create extension if not exists vector;
create index if not exists ke_embedding_hnsw
on public.knowledge_embeddings using hnsw (embedding vector_cosine_ops);
-- For very large datasets, consider IVFFlat
-- create index if not exists ke_embedding_ivfflat
-- on public.knowledge_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);
```

RLS (development defaults; tighten for production):
```sql
alter table public.knowledge_items enable row level security;
alter table public.knowledge_embeddings enable row level security;

-- Minimal dev policy (adjust later): allow service/anon inserts and selects
create policy if not exists anon_select_items on public.knowledge_items for select to anon using (true);
create policy if not exists anon_insert_items on public.knowledge_items for insert to anon with check (true);
create policy if not exists anon_select_embeddings on public.knowledge_embeddings for select to anon using (true);
create policy if not exists anon_insert_embeddings on public.knowledge_embeddings for insert to anon with check (true);
```

Realtime (optional):
```sql
begin; drop publication if exists supabase_realtime; create publication supabase_realtime; commit;
alter publication supabase_realtime add table public.knowledge_items;
alter publication supabase_realtime add table public.knowledge_embeddings;
```

Notes:
- Vector dimensions default to 1536; configure via `SUPABASE_VECTOR_DIMS`. Apple Silicon MPS vectors must be padded/truncated to match column dims.
- Use cosine ops per Supabase docs. HNSW is generally recommended; IVFFlat for very large datasets.

References:
- HNSW/IVFFlat and operator classes: `https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/ai/vector-indexes/hnsw-indexes.mdx`
- IVFFlat indexes: `https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/ai/vector-indexes/ivf-indexes.mdx`
- pgvector extension: `https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/database/extensions/pgvector.mdx`
- RLS basics: `https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/database/postgres/row-level-security.mdx`
- Realtime publication: `https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/realtime/postgres-changes.mdx`
