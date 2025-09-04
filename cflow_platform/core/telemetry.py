from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


def telemetry_enabled() -> bool:
    """Return True when telemetry is explicitly enabled via environment.

    Opt-in only. Defaults to disabled.
    CFLOW_TELEMETRY values considered true: {"1", "true", "yes", "on"}.
    """
    val = os.getenv("CFLOW_TELEMETRY", "").strip().lower()
    return val in {"1", "true", "yes", "on"}


def _ensure_parent_dir(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def telemetry_log_path() -> Path:
    """Resolve the path where telemetry JSONL will be written.

    CFLOW_TELEMETRY_FILE can override the destination; otherwise default to
    .cerebraflow/logs/telemetry.jsonl under the current working directory.
    """
    override = os.getenv("CFLOW_TELEMETRY_FILE", "").strip()
    if override:
        p = Path(override)
    else:
        p = Path(".cerebraflow") / "logs" / "telemetry.jsonl"
    _ensure_parent_dir(p)
    return p


def log_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """Write a single structured telemetry event as JSONL if enabled.

    Never throws. If disabled or any error occurs, it silently returns.
    """
    if not telemetry_enabled():
        return
    try:
        record = {
            "ts": time.time(),
            "event": str(event),
            "payload": payload or {},
        }
        out_path = telemetry_log_path()
        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Best-effort only
        return


