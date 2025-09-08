Title: cflow-codegen

Summary: Run `codegen.generate_edits` to produce minimal edits and write `.cerebraflow/edits.json`.

Usage:

```bash
# Required: OpenRouter API key
export OPENROUTER_API_KEY=sk-or-...

# Provide task via env or file
export CFLOW_TASK="Make foo() return 2 instead of 1 in app/foo.py and update tests"
# or: export CFLOW_TASK_FILE=task.txt

# Optional context file hints (comma/semicolon-separated paths)
export CFLOW_CONTEXT_FILES="app/foo.py,tests/test_foo.py"

# Enforce AEMI/VEG constraints (defaults already strict)
export CFLOW_EDIT_ALLOWLIST=$(pwd)
export CFLOW_MAX_EDITS=10
export CFLOW_MAX_SNIPPET_CHARS=4000

# Run the CLI
uv run cflow-codegen --json | jq .

# Then apply (dry-run by default) via agent loop
CFLOW_ENABLE_CODEGEN=1 uv run cflow-agent-loop --profile quick --max-iter 1 --json | jq .
```

Notes:
- Output is written to `.cerebraflow/edits.json`. The agent loop will apply edits (dry-run unless `CFLOW_APPLY_EDITS=1`).
- AEMI/VEG enforcement: allowlist, atomic, strict single match, and size caps are enforced in the handler and by the minimal edit applier.

