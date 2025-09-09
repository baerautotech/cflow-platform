-- Read-only compatibility views mapping legacy memory_* to knowledge_*

CREATE OR REPLACE VIEW public.memory_items AS
SELECT
  ki.id,
  /* legacy fields with safe defaults */
  'note'::text AS type,
  'project'::text AS scope,
  NULL::text AS classification,
  ki.title,
  ki.content,
  coalesce(ki.metadata, '{}'::jsonb) AS metadata,
  ki.created_at,
  ki.updated_at
FROM public.knowledge_items ki;

CREATE OR REPLACE VIEW public.memory_vectors AS
SELECT
  ke.id,
  ke.knowledge_item_id AS item_id,
  ke.embedding,
  1536::int AS dims,
  'unknown'::text AS model,
  coalesce(ke.metadata, '{}'::jsonb) AS metadata,
  ke.created_at
FROM public.knowledge_embeddings ke;

-- Optional: helper view joining items with vectors for convenience
CREATE OR REPLACE VIEW public.memory_items_with_vectors AS
SELECT i.*, v.embedding, v.created_at AS vector_created_at
FROM public.memory_items i
LEFT JOIN public.memory_vectors v ON v.item_id = i.id;


