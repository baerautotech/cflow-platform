Title: cflow-docs-backfill

Description: Pull documentation_files from Supabase, add to local Chroma `cerebral_docs`, enforce parity, then run one-shot vector sync.

Usage:

```
uv run cflow-docs-backfill
```

Requirements:
- SUPABASE_URL and key in .cerebraflow/.env

Outcome:
- Local Chroma docs == Supabase docs; vectors pushed on next one-shot sync.

