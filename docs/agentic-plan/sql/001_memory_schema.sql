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

