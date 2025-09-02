## Context Management Strategy

- Cursor artifacts: `AGENTS.md`, `.cursor/rules/**`, `docs/**/*.mdc`, `commands/**`
- Checkpointing: `.cerebraflow/progress/iteration_<n>.mdc` and CerebralMemory episodic entries
- Retrieval: prefer CerebralMemory before external RAG; map artifacts to memories with rich metadata

