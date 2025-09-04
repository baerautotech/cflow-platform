## Governance: Documentation, Ownership, and Changes

### Scope

This document establishes how examples and developer documentation are authored, reviewed, and evolved in this repository to avoid duplication and ensure reliability.

### Ownership

- Primary owners: Core maintainers listed in `AGENTS.md`.
- Contributors: All changes go through PR with pre-commit hooks and green CI.

### Source of Truth

- The canonical plan and validation gates live under `docs/agentic-plan/`.
- Operational command references live in `README.md` and `docs/ProjectBuildGuide.md`.
- Examples consolidate in `docs/agentic-plan/Examples.md` and are linked from the index.

### Change Workflow

1. Propose edits using minimal edits aligned with `CodeStyle.md`.
2. Run lint and tests locally via `cflow-test-runner`.
3. Update `docs/agentic-plan/TaskTracker.md` if tasks or gates change.
4. Ensure Validation Gates remain satisfied (see `ValidationGates.md`).
5. Submit PR; require green pre-commit and CI before merge.

### Duplication Rules

- Do not duplicate CLI examples across multiple documents. Use `Examples.md` and link to it.
- If an example needs additional context, reference `README.md` rather than copying content.

### Versioning and Compatibility Notes

- Note breaking changes in `CHANGELOG.md`.
- Keep instructions compatible with the current `pyproject.toml` dependencies.

### Documentation Style

- Follow `CodeStyle.md` for code blocks and naming.
- Prefer short, runnable examples over long narratives.
- Use fenced code blocks with language hints and avoid inline setup that cannot run.

### Validation

- Changes to docs that affect behavior must include a demonstration in `Examples.md` or tests in `cflow_platform/tests`.


