-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Tables
CREATE TABLE IF NOT EXISTS public.memory_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type text NOT NULL,
  scope text NOT NULL,
  classification text,
  title text,
  content text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.memory_vectors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id uuid NOT NULL REFERENCES public.memory_items(id) ON DELETE CASCADE,
  embedding vector(1536) NOT NULL,
  dims int NOT NULL DEFAULT 1536,
  model text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Helpful composite view
CREATE OR REPLACE VIEW public.memory_items_with_vectors AS
SELECT i.*, v.embedding, v.model, v.created_at AS vector_created_at
FROM public.memory_items i
LEFT JOIN public.memory_vectors v ON v.item_id = i.id;

-- RLS
ALTER TABLE public.memory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_vectors ENABLE ROW LEVEL SECURITY;

-- Development policies (adjust for production)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'memory_items' AND policyname = 'anon_select_insert_items'
  ) THEN
    CREATE POLICY anon_select_insert_items ON public.memory_items
      FOR SELECT TO anon USING (true);
    CREATE POLICY anon_insert_items ON public.memory_items
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'memory_vectors' AND policyname = 'anon_select_insert_vectors'
  ) THEN
    CREATE POLICY anon_select_insert_vectors ON public.memory_vectors
      FOR SELECT TO anon USING (true);
    CREATE POLICY anon_insert_vectors ON public.memory_vectors
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

-- HNSW index (recommended default; cosine)
CREATE INDEX IF NOT EXISTS mv_embedding_hnsw
ON public.memory_vectors USING hnsw (embedding vector_cosine_ops);

-- Optional: IVFFlat for very large datasets (cosine), tune lists
-- CREATE INDEX IF NOT EXISTS mv_embedding_ivfflat
-- ON public.memory_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Match RPC (cosine distance)
CREATE OR REPLACE FUNCTION public.match_memory_vectors(
  query_embedding vector(1536),
  match_count int DEFAULT 10
)
RETURNS TABLE(
  item_id uuid,
  title text,
  content text,
  metadata jsonb,
  similarity float4
) LANGUAGE sql STABLE AS $$
  SELECT
    i.id AS item_id,
    i.title,
    i.content,
    i.metadata,
    1 - (v.embedding <=> query_embedding) AS similarity
  FROM public.memory_vectors v
  JOIN public.memory_items i ON i.id = v.item_id
  ORDER BY v.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION public.match_memory_vectors(vector, int) TO anon;

-- =============================================
-- Knowledge Graph Schema (preferred)
-- =============================================

-- Tables: knowledge_items and knowledge_embeddings
CREATE TABLE IF NOT EXISTS public.knowledge_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  tenant_id uuid,
  title text,
  content text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.knowledge_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_item_id uuid NOT NULL REFERENCES public.knowledge_items(id) ON DELETE CASCADE,
  content_chunk text NOT NULL,
  embedding vector(1536) NOT NULL,
  chunk_index int NOT NULL DEFAULT 0,
  content_type text,
  metadata jsonb,
  tenant_id uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- RLS (development defaults; tighten for production)
ALTER TABLE public.knowledge_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_embeddings ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_items' AND policyname = 'anon_select_items'
  ) THEN
    CREATE POLICY anon_select_items ON public.knowledge_items
      FOR SELECT TO anon USING (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_items' AND policyname = 'anon_insert_items'
  ) THEN
    CREATE POLICY anon_insert_items ON public.knowledge_items
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_embeddings' AND policyname = 'anon_select_embeddings'
  ) THEN
    CREATE POLICY anon_select_embeddings ON public.knowledge_embeddings
      FOR SELECT TO anon USING (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_embeddings' AND policyname = 'anon_insert_embeddings'
  ) THEN
    CREATE POLICY anon_insert_embeddings ON public.knowledge_embeddings
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

-- Indexes (cosine): HNSW by default; IVFFlat optional for large datasets
CREATE INDEX IF NOT EXISTS ke_embedding_hnsw
ON public.knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

-- Optional for very large datasets (tune lists)
-- CREATE INDEX IF NOT EXISTS ke_embedding_ivfflat
-- ON public.knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RPC: search_agentic_embeddings with tenant/content filters and match threshold
CREATE OR REPLACE FUNCTION public.search_agentic_embeddings(
  query_embedding vector(1536),
  match_count int DEFAULT 10,
  tenant_filter uuid DEFAULT NULL,
  content_types text[] DEFAULT NULL,
  match_threshold float8 DEFAULT 0.0
)
RETURNS TABLE(
  knowledge_item_id uuid,
  knowledge_embedding_id uuid,
  title text,
  content text,
  metadata jsonb,
  content_type text,
  chunk_index int,
  similarity float4
) LANGUAGE sql STABLE AS $$
  SELECT
    ki.id AS knowledge_item_id,
    ke.id AS knowledge_embedding_id,
    ki.title,
    ki.content,
    COALESCE(ke.metadata, ki.metadata) AS metadata,
    ke.content_type,
    ke.chunk_index,
    1 - (ke.embedding <=> query_embedding) AS similarity
  FROM public.knowledge_embeddings ke
  JOIN public.knowledge_items ki ON ki.id = ke.knowledge_item_id
  WHERE
    (tenant_filter IS NULL OR ke.tenant_id = tenant_filter OR ki.tenant_id = tenant_filter)
    AND (content_types IS NULL OR ke.content_type = ANY(content_types))
    AND (1 - (ke.embedding <=> query_embedding)) >= match_threshold
  ORDER BY ke.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION public.search_agentic_embeddings(vector, int, uuid, text[], float8) TO anon;

-- Optional: create legacy-compatibility views only if memory_* tables are absent
DO $$
BEGIN
  -- memory_items view
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'memory_items'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'memory_items'
  ) THEN
    EXECUTE $$
      CREATE VIEW public.memory_items AS
      SELECT
        ki.id,
        NULL::text AS type,
        NULL::text AS scope,
        NULL::text AS classification,
        ki.title,
        ki.content,
        ki.metadata,
        ki.created_at,
        ki.created_at AS updated_at
      FROM public.knowledge_items ki
    $$;
  END IF;

  -- memory_vectors view
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'memory_vectors'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'memory_vectors'
  ) THEN
    EXECUTE $$
      CREATE VIEW public.memory_vectors AS
      SELECT
        ke.id,
        ke.knowledge_item_id AS item_id,
        ke.embedding,
        1536::int AS dims,
        NULL::text AS model,
        ke.created_at
      FROM public.knowledge_embeddings ke
    $$;
  END IF;
END
$$;

-- Note: For large bulk loads, run ANALYZE to help the planner. This is intentionally left manual.
-- ANALYZE public.knowledge_embeddings;

-- ------------------------------------------------------------
-- Enterprise Knowledge Graph schema (preferred)
-- Tables: knowledge_items, knowledge_embeddings
-- RPC: search_agentic_embeddings
-- ------------------------------------------------------------

-- Tables
CREATE TABLE IF NOT EXISTS public.knowledge_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  tenant_id uuid,
  title text,
  content text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.knowledge_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_item_id uuid NOT NULL REFERENCES public.knowledge_items(id) ON DELETE CASCADE,
  content_chunk text,
  embedding vector(1536) NOT NULL,
  chunk_index int NOT NULL DEFAULT 0,
  content_type text,
  metadata jsonb,
  tenant_id uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- RLS (development defaults; tighten for production)
ALTER TABLE public.knowledge_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_embeddings ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_items' AND policyname = 'anon_select_items'
  ) THEN
    CREATE POLICY anon_select_items ON public.knowledge_items
      FOR SELECT TO anon USING (true);
    CREATE POLICY anon_insert_items ON public.knowledge_items
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'knowledge_embeddings' AND policyname = 'anon_select_embeddings'
  ) THEN
    CREATE POLICY anon_select_embeddings ON public.knowledge_embeddings
      FOR SELECT TO anon USING (true);
    CREATE POLICY anon_insert_embeddings ON public.knowledge_embeddings
      FOR INSERT TO anon WITH CHECK (true);
  END IF;
END $$;

-- HNSW index (cosine) for agentic knowledge search
CREATE INDEX IF NOT EXISTS ke_embedding_hnsw
ON public.knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

-- Optional: IVFFlat for very large datasets
-- CREATE INDEX IF NOT EXISTS ke_embedding_ivfflat
-- ON public.knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Agentic search RPC (pgvector cosine); supports optional tenant and content type filters
CREATE OR REPLACE FUNCTION public.search_agentic_embeddings(
  query_embedding vector(1536),
  match_threshold float4 DEFAULT 0.0,
  match_count int DEFAULT 10,
  tenant_filter uuid DEFAULT NULL,
  content_types text[] DEFAULT NULL
)
RETURNS TABLE(
  knowledge_item_id uuid,
  title text,
  content text,
  metadata jsonb,
  similarity float4,
  content_type text
) LANGUAGE sql STABLE AS $$
  SELECT
    i.id AS knowledge_item_id,
    i.title,
    i.content,
    i.metadata,
    1 - (e.embedding <=> query_embedding) AS similarity,
    e.content_type
  FROM public.knowledge_embeddings e
  JOIN public.knowledge_items i ON i.id = e.knowledge_item_id
  WHERE (tenant_filter IS NULL OR e.tenant_id = tenant_filter)
    AND (content_types IS NULL OR e.content_type = ANY(content_types))
    AND (1 - (e.embedding <=> query_embedding)) >= match_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION public.search_agentic_embeddings(vector, float4, int, uuid, text[]) TO anon;

-- Optional: Realtime publication for incremental sync (off by default)
-- begin; drop publication if exists supabase_realtime; create publication supabase_realtime; commit;
-- alter publication supabase_realtime add table public.knowledge_items;
-- alter publication supabase_realtime add table public.knowledge_embeddings;

