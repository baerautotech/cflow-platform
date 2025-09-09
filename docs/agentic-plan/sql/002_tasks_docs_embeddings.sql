-- SOC2-safe migration: add JSONB embeddings columns for vector sync via REST/Edge
-- Apply this using Supabase CLI or Dashboard SQL editor, not from the app runtime.

ALTER TABLE IF EXISTS public.cerebraflow_tasks
  ADD COLUMN IF NOT EXISTS embeddings jsonb;

ALTER TABLE IF EXISTS public.documentation_files
  ADD COLUMN IF NOT EXISTS embeddings jsonb;


