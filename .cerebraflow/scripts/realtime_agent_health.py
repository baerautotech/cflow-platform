#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def is_system_agent_running(label: str = "com.cerebral.unified-sync") -> bool:
    try:
        proc = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5)
        if proc.returncode != 0:
            return False
        for line in proc.stdout.splitlines():
            if label in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    return True
        return False
    except Exception:
        return False

def main() -> int:
    # Check for deprecated vendor daemon scripts
    project_root = Path.cwd()
    vendored = list((project_root / "cflow_platform" / "vendor" / "cerebral" / "services").glob("*.py"))
    sys_agent = is_system_agent_running()
    out = {
        "system_agent_running": sys_agent,
        "vendored_services_present": bool(vendored),
        "vendored_services": [p.name for p in vendored],
    }
    print(json.dumps(out))
    # Block if vendored services are present AND system agent is not running
    if vendored and not sys_agent:
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
