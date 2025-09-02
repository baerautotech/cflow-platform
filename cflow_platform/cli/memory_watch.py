from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ARTIFACT_PATTERNS: Tuple[str, ...] = (
    "AGENTS.md",
    ".cursor/rules/**/*.json",
    ".cursor/rules/**/*.md",
    "docs/**/*.mdc",
    "commands/**/*.md",
)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    root = Path.cwd() / ".env"
    local = Path.cwd() / ".cerebraflow" / ".env"
    if root.exists():
        load_dotenv(dotenv_path=str(root))
    if local.exists():
        load_dotenv(dotenv_path=str(local), override=True)
    load_dotenv()


def _glob_many(patterns: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    for pat in patterns:
        paths.extend(Path.cwd().glob(pat))
    # Remove duplicates and non-files
    uniq: List[Path] = []
    seen: set = set()
    for p in paths:
        if not p.is_file():
            continue
        sp = str(p)
        if sp not in seen:
            seen.add(sp)
            uniq.append(p)
    return uniq


def _classify_artifact(path: Path) -> Tuple[str, Dict[str, str]]:
    sp = str(path)
    meta: Dict[str, str] = {"artifact_path": sp}
    if sp.endswith("AGENTS.md"):
        return "rule", {**meta, "cursor_kind": "agents_md"}
    if "/.cursor/rules/" in sp:
        return "rule", {**meta, "cursor_kind": "cursor_rule"}
    if "/commands/" in sp:
        return "procedure", {**meta, "cursor_kind": "cursor_command"}
    if sp.endswith(".mdc"):
        return "context", {**meta, "cursor_kind": "mdc"}
    return "context", meta


async def _ingest_file(exec_fn, path: Path) -> Dict[str, object]:
    kind, meta = _classify_artifact(path)
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"status": "error", "file": str(path), "error": str(e)}
    # Route to memory_add with metadata
    res = await exec_fn(
        "memory_add",
        content=content,
        metadata={
            **meta,
            "type": kind,
            "source": "cflow-memory-watch",
        },
    )
    return {"status": "success", "file": str(path), "result": res}


async def _run_once(paths: List[Path]) -> Dict[str, object]:
    from cflow_platform.core.public_api import get_direct_client_executor

    exec_fn = get_direct_client_executor()
    results: List[Dict[str, object]] = []
    for p in paths:
        results.append(await _ingest_file(exec_fn, p))
    return {"ingested": len(results), "results": results}


def _watch_loop(interval_sec: float = 2.0) -> None:
    from cflow_platform.core.public_api import get_direct_client_executor

    async def _tick(state: Dict[str, float]) -> None:
        exec_fn = get_direct_client_executor()
        to_scan = _glob_many(ARTIFACT_PATTERNS)
        for p in to_scan:
            m = p.stat().st_mtime
            sp = str(p)
            if state.get(sp, 0) < m:
                try:
                    asyncio.get_event_loop().run_until_complete(_ingest_file(exec_fn, p))
                    state[sp] = m
                except Exception:
                    # non-fatal
                    pass

    state: Dict[str, float] = {}
    # Initialize state
    for p in _glob_many(ARTIFACT_PATTERNS):
        try:
            state[str(p)] = p.stat().st_mtime
        except Exception:
            continue
    print("Watching Cursor artifacts for ingestion → CerebralMemory (Ctrl-C to stop)…")
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(_tick(state))
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("Stopped.")
            return


def cli() -> int:
    import argparse

    _load_env()

    parser = argparse.ArgumentParser(description="Ingest Cursor artifacts into CerebralMemory (and optional watch mode)")
    parser.add_argument("--watch", action="store_true", help="Watch files for changes and ingest on modify")
    parser.add_argument("--json", action="store_true", help="Emit JSON status for one-shot mode")
    args = parser.parse_args()

    if args.watch:
        _watch_loop()
        return 0

    paths = _glob_many(ARTIFACT_PATTERNS)
    out = asyncio.get_event_loop().run_until_complete(_run_once(paths))
    if args.json:
        print(json.dumps(out))
    else:
        print(f"Ingested {out.get('ngested', len(paths))} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


