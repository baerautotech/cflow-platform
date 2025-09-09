-- Code Intelligence schema (Supabase Postgres + pgvector)

create table if not exists code_functions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid,
  user_id uuid,
  project_id uuid,
  repo text,
  path text not null,
  name text not null,
  language text not null,
  signature text,
  start_line int not null,
  end_line int not null,
  summary text,
  metadata jsonb,
  created_at timestamptz default now()
);

create table if not exists code_function_embeddings (
  id uuid primary key default gen_random_uuid(),
  function_id uuid not null references code_functions(id) on delete cascade,
  embedding vector(1536) not null,
  dims int default 1536,
  model text,
  tenant_id uuid,
  user_id uuid,
  project_id uuid,
  created_at timestamptz default now()
);

-- Optional call graph in Postgres
create table if not exists code_calls (
  caller_function_id uuid not null references code_functions(id) on delete cascade,
  callee_name text not null,
  tenant_id uuid,
  user_id uuid,
  project_id uuid
);

create index if not exists idx_code_functions_path on code_functions(path);
create index if not exists idx_code_functions_name on code_functions(name);
create index if not exists idx_code_calls_callee on code_calls(callee_name);

-- Vector index (adjust opclass as needed)
create index if not exists cfe_hnsw on code_function_embeddings using hnsw (embedding vector_cosine_ops);

-- RLS (development defaults; adjust for production)
alter table code_functions enable row level security;
alter table code_function_embeddings enable row level security;
alter table code_calls enable row level security;

do $$ begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='code_functions' and policyname='anon_select_insert_code_functions'
  ) then
    create policy anon_select_insert_code_functions on public.code_functions
      for select to anon using (true);
    create policy anon_insert_code_functions on public.code_functions
      for insert to anon with check (true);
  end if;
end $$;

do $$ begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='code_function_embeddings' and policyname='anon_select_insert_code_function_embeddings'
  ) then
    create policy anon_select_insert_code_function_embeddings on public.code_function_embeddings
      for select to anon using (true);
    create policy anon_insert_code_function_embeddings on public.code_function_embeddings
      for insert to anon with check (true);
  end if;
end $$;

do $$ begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='code_calls' and policyname='anon_select_insert_code_calls'
  ) then
    create policy anon_select_insert_code_calls on public.code_calls
      for select to anon using (true);
    create policy anon_insert_code_calls on public.code_calls
      for insert to anon with check (true);
  end if;
end $$;


