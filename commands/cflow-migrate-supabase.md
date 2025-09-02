Title: cflow-migrate-supabase

Description: Apply Supabase memory schema (tables, RLS, pgvector index, RPC) or print SQL for manual apply.

Usage:

```
uv run cflow-migrate-supabase           # print SQL
uv run cflow-migrate-supabase --apply   # apply to SUPABASE_DB_URL from .cerebraflow/.env
```

Notes:
- Loads .env and .cerebraflow/.env for credentials.
- Uses psycopg if applying directly; otherwise copy the printed SQL into Supabase SQL editor.

