-- RPC for call-path queries using recursive CTE (name-based)

create or replace function public.call_paths_to(target_name text, max_depth int default 6)
returns table(path text) language sql as $$
with recursive callers as (
  -- base: functions that call target_name
  select cf.path as caller_path,
         cf.name as caller_name,
         1 as depth,
         (cf.name || ' -> ' || target_name) as path
  from code_functions cf
  join code_calls cc on cc.caller_function_id = cf.id
  where cc.callee_name = target_name

  union all
  -- step: functions that call the previous caller by name
  select cf2.path as caller_path,
         cf2.name as caller_name,
         c.depth + 1 as depth,
         (cf2.name || ' -> ' || c.path) as path
  from callers c
  join code_functions cf2 on cf2.name = c.caller_name
  join code_calls cc2 on cc2.callee_name = cf2.name
  where c.depth < max_depth
)
select path from callers;
$$;

grant execute on function public.call_paths_to(text, int) to anon, authenticated;


