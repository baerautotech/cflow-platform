Title: cflow-tasks-backfill

Description: Pull cerebraflow_tasks from Supabase, add to local Chroma `cerebral_tasks`, enforce parity, then run one-shot vector sync.

Usage:

```
uv run cflow-tasks-backfill
```

Outcome:
- Local Chroma tasks == Supabase tasks; vectors pushed on next one-shot sync.

