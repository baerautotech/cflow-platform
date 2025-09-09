from __future__ import annotations

import json
import runpy
import sys
from io import StringIO


def test_kg_query_cli_smoke(monkeypatch):
    # Simulate arguments and capture stdout
    monkeypatch.setenv("PYTHONUNBUFFERED", "1")
    argv_backup = sys.argv[:]
    try:
        sys.argv = ["kg_query.py", "PLAN SUMMARY", "--limit", "1", "--min-score", "0.0"]
        buf = StringIO()
        stdout_backup = sys.stdout
        sys.stdout = buf
        try:
            runpy.run_module("cflow_platform.cli.kg_query", run_name="__main__")
        finally:
            sys.stdout = stdout_backup
        out = buf.getvalue().strip()
        # Expect JSON output
        data = json.loads(out)
        assert isinstance(data, dict)
        assert "success" in data or "count" in data
    finally:
        sys.argv = argv_backup


