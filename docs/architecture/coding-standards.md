## Coding Standards (Dev Agent Always-Load)

Purpose: Provide deterministic, minimal rules the `@dev` agent must follow to avoid hallucinations and produce production-quality code.

1. Read-Before-Write
   - Always open and read relevant files before proposing edits. Prefer exact file names from the story.
   - Use repository search to locate symbols instead of guessing. If unsure, ask for the exact file.

2. No Imaginary APIs
   - Do not invent endpoints, functions, classes, or settings. Confirm existence in the codebase or story. If missing, propose a minimal addition explicitly.

3. Code Citations
   - When referencing existing code, include CODE REFERENCES with start:end:filepath blocks. Do not quote code without a reference.

4. Minimal, High-Readability Edits
   - Prefer small, targeted edits over large rewrites. Keep changes localized. Match existing formatting.

5. Python (BMAD API, tooling)
   - Version: Python 3.11. Use type hints for public functions. Prefer FastAPI idioms for HTTP layers.
   - Control flow: early returns; avoid deep nesting; handle edge cases first.
   - Errors: never swallow exceptions; raise informative errors or return structured responses.

6. Tests and Lint
   - When adding non-trivial logic, include focused tests. Run linting where available. Fix introduced warnings.

7. Story-Driven Development
   - Implement only what the current story requires. If the story is ambiguous or in Draft, halt and request clarification.

8. Security & Config Discipline
   - Never hardcode secrets. Use environment or secret managers referenced by the story/infrastructure.
   - Respect Kyverno and security context requirements if making deployment-related changes.


