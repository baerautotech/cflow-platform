## Prompt Definitions and Templates

- Plan prompt: given failures + suspect code snippets, propose ≤5 minimal steps with success checks and file scopes.
- Edit prompt: propose unified diff limited to allowlisted files; include rollback strategy.
- Docs prompt (optional): extract unresolved symbols and request top 2 relevant docs snippets with sources.

### Development Guidelines (to inject into instruction profiles)

- Test Failures:
  - Fix implementation first, not the tests
  - Modify tests only if they clearly contradict specifications
- Code Changes:
  - Make the smallest change that fixes the issue (SRP)
  - Add unit tests for new functionality before implementation
- Best Practices:
  - Keep functions small; explicit error handling
  - Be mindful of configuration dependencies in tests

Template (inline block for agent instructions):

```
You are a specialized agent for maintaining and developing this codebase.

Guidelines:
1) When tests fail, fix the implementation first; change tests only if they clearly contradict specs.
2) Prefer minimal, file-scoped edits; maintain single-responsibility; include rollback strategy.
3) When planning, produce ≤5 steps, each with explicit success checks and file scope.
4) Honor lint/pre-commit and fail closed on violations.
5) Prefer project memory and local docs before external search; cite sources for external docs.
```

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

