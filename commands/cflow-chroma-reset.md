Title: cflow-chroma-reset

Description: Drop and recreate specific Chroma collections under `.cerebraflow/core/storage/chromadb`.

Usage:

```
uv run cflow-chroma-reset --collections cerebral_docs cerebral_tasks
```

Notes:
- Use before backfill to clear corrupted or stale local state.

