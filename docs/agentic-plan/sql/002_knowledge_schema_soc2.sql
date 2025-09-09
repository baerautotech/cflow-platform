-- SOC2-oriented Knowledge Graph schema with tenant-scoped RLS
-- Run with service role; review and tailor policies per environment.

CREATE EXTENSION IF NOT EXISTS vector;

-- Base tables
CREATE TABLE IF NOT EXISTS public.knowledge_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  user_id uuid,
  title text,
  content text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.knowledge_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_item_id uuid NOT NULL REFERENCES public.knowledge_items(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL,
  content_chunk text,
  embedding vector(1536) NOT NULL,
  chunk_index int NOT NULL DEFAULT 0,
  content_type text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS ki_tenant_idx ON public.knowledge_items(tenant_id);
CREATE INDEX IF NOT EXISTS ke_tenant_idx ON public.knowledge_embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS ke_item_idx ON public.knowledge_embeddings(knowledge_item_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ke_embedding_hnsw ON public.knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

-- RLS
ALTER TABLE public.knowledge_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_embeddings ENABLE ROW LEVEL SECURITY;

-- Tenant-scoped read for authenticated users (expects JWT tenant_id claim)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='knowledge_items' AND policyname='ki_tenant_select'
  ) THEN
    CREATE POLICY ki_tenant_select ON public.knowledge_items
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='knowledge_embeddings' AND policyname='ke_tenant_select'
  ) THEN
    CREATE POLICY ke_tenant_select ON public.knowledge_embeddings
      FOR SELECT TO authenticated
      USING (tenant_id::text = coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb ->> 'tenant_id');
  END IF;
END $$;

-- Writes restricted to service role
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='knowledge_items' AND policyname='ki_service_insert'
  ) THEN
    CREATE POLICY ki_service_insert ON public.knowledge_items
      FOR INSERT TO service_role
      WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='knowledge_embeddings' AND policyname='ke_service_insert'
  ) THEN
    CREATE POLICY ke_service_insert ON public.knowledge_embeddings
      FOR INSERT TO service_role
      WITH CHECK (true);
  END IF;
END $$;

-- Optional: secure RPC for similarity search (expects tenant_filter)
-- Replace body with your implementation; example signature only
CREATE OR REPLACE FUNCTION public.search_agentic_embeddings(query_embedding vector(1536), match_count int, tenant_filter uuid)
RETURNS TABLE(knowledge_item_id uuid, content_chunk text, score float4, metadata jsonb) AS $$
  SELECT ke.knowledge_item_id, ke.content_chunk,
         1 - (ke.embedding <=> query_embedding) AS score,
         ke.metadata
  FROM public.knowledge_embeddings ke
  WHERE ke.tenant_id = tenant_filter
  ORDER BY ke.embedding <=> query_embedding
  LIMIT greatest(1, coalesce(match_count, 8));
$$ LANGUAGE sql STABLE;

REVOKE ALL ON FUNCTION public.search_agentic_embeddings(vector, int, uuid) FROM public;
GRANT EXECUTE ON FUNCTION public.search_agentic_embeddings(vector, int, uuid) TO authenticated, service_role;


