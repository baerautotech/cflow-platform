## High‑Level Architecture

- Core Loop: `cflow_platform/core/agent_loop.py` orchestrates Plan → Verify (tests) with checkpoints.
- Test Runner: `cflow_platform/core/test_runner.py` provides in‑process and uv subprocess execution.
- Failure Parser: `cflow_platform/core/failure_parser.py` parses pytest output into structured failures.
- Minimal Edit Applier: `cflow_platform/core/minimal_edit_applier.py` applies scoped diffs (to integrate).
- Memory/Sync: Local Chroma; remote Supabase RDB + pgvector via vendor sync services.
- Apple Silicon: `core/embeddings/*` Vectorization path with MPS accelerator.

