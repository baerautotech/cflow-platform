"""CFlow pre-commit runner (Phase 1)

Selected hook logic migrated from bash into Python for reuse across repos:
- File organization validation for root files
- RAG chunk commit guard

Exit codes:
- 0: all checks passed
- 1: file organization violation
- 2: RAG chunk guard violation
- 4: realtime agent health failed
- 5: gate registry not green
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List


def run(cmd: List[str]) -> str:
    out = subprocess.check_output(cmd, text=True)
    return out.strip()


def get_repo_root() -> Path:
    try:
        root = run(["git", "rev-parse", "--show-toplevel"]) or "."
        return Path(root)
    except Exception:
        return Path.cwd()


def get_staged_files(filter_flags: str) -> List[str]:
    try:
        out = run(["git", "%s" % "diff", "--cached", "--name-only", filter_flags])
        return [line for line in out.splitlines() if line]
    except Exception:
        return []


def check_file_org_violations(repo_root: Path) -> List[str]:
    # Check added files in root directory only (no slash in path)
    added = get_staged_files("--diff-filter=A")
    root_added = [f for f in added if "/" not in f]
    if not root_added:
        return []

    allowlist = re.compile(
        r"^(README\.md|AGENTS\.md|LICENSE|CHANGELOG\.md|package\.json|package-lock\.json|pyproject\.toml|uv\.lock|"
        r"tsconfig.*\.json|activate\.(sh|bat)|components\.json|cerebraflow_.*\.json|.*\.lock)$"
    )
    violations = [f for f in root_added if not allowlist.match(f)]
    return violations


def check_rag_chunk_guard(staged_all: List[str]) -> bool:
    chunks = [f for f in staged_all if f.startswith("autodoc/rag/chunks/")]
    if not chunks:
        return True
    if os.environ.get("ALLOW_RAG_CHUNK_COMMIT") == "1":
        print("WARNING: autodoc/rag/chunks staged but allowed via ALLOW_RAG_CHUNK_COMMIT=1")
        return True
    print("\nRAG chunk files detected in commit:")
    for f in chunks:
        print(f"   {f}")
    print("\nThese files are generated artifacts and should not be committed.")
    print("If you intentionally need to commit them (rare):")
    print("  ALLOW_RAG_CHUNK_COMMIT=1 git commit -m '...'")
    return False


def check_realtime_health(repo_root: Path) -> bool:
    script = repo_root / ".cerebraflow" / "scripts" / "realtime_agent_health.py"
    if not script.exists():
        return True
    try:
        proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=8)
        if proc.returncode != 0:
            try:
                print("REALTIME AGENT HEALTH:", proc.stdout.strip() or proc.stderr.strip())
            except Exception:
                pass
            return False
        # Log summary
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
            print("Realtime agent:", payload)
        except Exception:
            pass
        return True
    except Exception:
        return False


def check_gate_registry(repo_root: Path) -> bool:
    """Check gates from .cerebraflow/validation/gates.json; return True if all gates are True.

    Absent file -> do not block (return True).
    """
    gates_file = repo_root / ".cerebraflow" / "validation" / "gates.json"
    try:
        if not gates_file.exists():
            return True
        data = json.loads(gates_file.read_text(encoding="utf-8"))
        gates = data.get("gates", {}) if isinstance(data, dict) else {}
        if not gates:
            return True
        failed = [k for k, v in gates.items() if not bool(v)]
        if failed:
            print("GATE REGISTRY NOT GREEN:")
            for g in failed:
                print(f"  {g}: false")
            return False
        return True
    except Exception as e:
        print("Gate registry check error:", e)
        # Fail safe: block commit if gates file is unreadable
        return False


def main() -> int:
    repo_root = get_repo_root()

    # File organization
    violations = check_file_org_violations(repo_root)
    if violations:
        print("FILE ORGANIZATION VIOLATION: Files being added to root directory")
        print("   Violating files:")
        for v in violations:
            print(f"     {v}")
        print("")
        print("   These files must be placed in appropriate directories:")
        print("     - Python files: backend-python/, scripts/, .cerebraflow/")
        print("     - JSON files: config/, data/, backend-python/config/")
        print("     - SQL files: database/migrations/, migrations/, supabase/migrations/")
        print("     - Documentation: docs/ (CEREBRAL_XXX_TOPIC.md format)")
        print("     - Shell scripts: scripts/, infrastructure/scripts/")
        print("")
        return 1

    # Emoji guard (no emojis in code artifacts)
    staged_all = get_staged_files("--diff-filter=ACM")
    emoji_detected: List[str] = []
    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
    code_exts = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt"}
    MAX_SCAN_BYTES = 512 * 1024  # skip very large files
    for rel in staged_all:
        p = repo_root / rel
        try:
            if not p.exists() or not p.is_file():
                continue
            if p.suffix.lower() not in code_exts:
                continue
            try:
                if p.stat().st_size > MAX_SCAN_BYTES:
                    continue
            except Exception:
                pass
            text = p.read_text(encoding="utf-8", errors="ignore")
            if emoji_pattern.search(text):
                emoji_detected.append(rel)
        except Exception:
            continue
    if emoji_detected:
        print("EMOJI DETECTED IN CODE FILES:")
        for f in emoji_detected:
            print(f"  {f}")
        print("")
        print("Remove emoji characters from source files. Logs at runtime may include emojis, but source must not.")
        return 3

    # RAG chunk guard
    staged_all = staged_all or get_staged_files("--diff-filter=ACM")
    if not check_rag_chunk_guard(staged_all):
        return 2

    # Realtime agent health
    if not check_realtime_health(repo_root):
        return 4

    # Gate registry enforcement
    if not check_gate_registry(repo_root):
        return 5

    # Ingest changed Cursor artifacts into CerebralMemory (best-effort, non-blocking failure)
    try:
        artifact_like = []
        for f in staged_all:
            if f == "AGENTS.md" or f.startswith(".cursor/rules/") or f.startswith("docs/") or f.startswith("commands/"):
                artifact_like.append(str(repo_root / f))
        if artifact_like:
            # Use the CLI helper to ingest specific paths
            from cflow_platform.cli import memory_watch as _mw  # type: ignore
            _ = _mw.ingest_paths(artifact_like)
    except Exception:
        # Non-fatal; continue commit
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())


