from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, Dict

from cflow_platform.core.direct_client import execute_mcp_tool


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CFlow Desktop Notifications (optional)")
    p.add_argument("message", help="Notification message")
    p.add_argument("--title", default="CFlow", help="Notification title")
    p.add_argument("--subtitle", default="", help="Notification subtitle")
    return p.parse_args()


async def _amain(ns: argparse.Namespace) -> int:
    # Require explicit enable flag to avoid surprises
    enabled = str(os.environ.get("CFLOW_DESKTOP_NOTIFICATIONS", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not enabled:
        print("desktop notifications disabled; set CFLOW_DESKTOP_NOTIFICATIONS=1")
        return 2

    payload: Dict[str, Any] = {
        "title": ns.title,
        "subtitle": ns.subtitle,
        "message": ns.message,
    }
    result = await execute_mcp_tool("desktop.notify", **payload)
    if result.get("status") == "success":
        print("ok")
        return 0
    print(f"error: {result.get('message', 'unknown')}")
    return 1


def cli() -> None:
    ns = _parse_args()
    raise SystemExit(asyncio.run(_amain(ns)))


