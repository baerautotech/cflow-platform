from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


GATES_FILE = Path(".cerebraflow/validation/gates.json")


def _load() -> Dict[str, Any]:
    try:
        if GATES_FILE.exists():
            return json.loads(GATES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "gates": {
            # Default unknown → not enforced; keep permissive until explicitly set
        }
    }


def _save(data: Dict[str, Any]) -> None:
    try:
        GATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        GATES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _bool(val: str) -> bool:
    v = (val or "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def cmd_set(args: argparse.Namespace) -> int:
    data = _load()
    gates = data.setdefault("gates", {})
    name = args.name.strip()
    val = _bool(args.value)
    gates[name] = bool(val)
    _save(data)
    print(json.dumps({"status": "success", "updated": {name: gates[name]}}))
    return 0


def cmd_check_latest(_: argparse.Namespace) -> int:
    data = _load()
    gates = data.get("gates", {})
    # If no gates recorded, do not fail commits; treat as informational
    if not gates:
        print(json.dumps({"status": "success", "message": "no gates recorded", "gates": {}}))
        return 0
    failed = [k for k, v in gates.items() if not bool(v)]
    print(json.dumps({"status": "success" if not failed else "error", "failed": failed, "gates": gates}))
    return 0 if not failed else 2


def cmd_summary(_: argparse.Namespace) -> int:
    data = _load()
    print(json.dumps(data, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate registry manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="Set a gate value")
    s.add_argument("name", help="Gate name, e.g., GateA, GateB, GateP, GateRDB")
    s.add_argument("value", help="Boolean value: true/false/1/0/yes/no")
    s.set_defaults(func=cmd_set)

    c = sub.add_parser("check-latest", help="Check latest gate statuses; non-zero exit if any are false")
    c.set_defaults(func=cmd_check_latest)

    g = sub.add_parser("summary", help="Print current gates JSON")
    g.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


