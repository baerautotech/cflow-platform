from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict


class DesktopHandlers:
    async def handle_desktop_notify(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send a local desktop notification.

        Safety and policy:
        - Disabled by default. Enable with CFLOW_DESKTOP_NOTIFICATIONS=1
        - macOS only via osascript; no arbitrary command execution
        - Minimal, scoped surface: title, subtitle, message
        """
        enabled_flag = str(os.environ.get("CFLOW_DESKTOP_NOTIFICATIONS", "")).strip().lower()
        if enabled_flag not in {"1", "true", "yes", "on"}:
            return {
                "status": "error",
                "message": "desktop notifications are disabled; set CFLOW_DESKTOP_NOTIFICATIONS=1 to enable",
            }

        message: str = str(arguments.get("message") or "").strip()
        if not message:
            return {"status": "error", "message": "message is required"}

        title: str = str(arguments.get("title") or "CFlow").strip() or "CFlow"
        subtitle: str = str(arguments.get("subtitle") or "").strip()

        if sys.platform != "darwin":
            return {"status": "error", "message": "desktop notifications supported only on macOS"}

        # Use AppleScript via osascript; safe string encoding via json.dumps
        script_parts = [
            "display notification",
            json.dumps(message),
            "with title",
            json.dumps(title),
        ]
        if subtitle:
            script_parts += ["subtitle", json.dumps(subtitle)]
        script = " ".join(script_parts)

        try:
            proc = subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                check=False,
            )
            if proc.returncode == 0:
                return {"status": "success", "provider": "osascript"}
            return {"status": "error", "message": proc.stderr.strip() or "osascript failed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


