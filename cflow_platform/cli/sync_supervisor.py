from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
import signal
from dotenv import dotenv_values


def _python_executable() -> str:
    return sys.executable


def _service_paths() -> dict[str, str]:
    # No longer used; kept for compatibility
    return {}


def _pid_file(project_root: str | None) -> Path:
    root = Path(project_root or Path.cwd())
    p = root / ".cerebraflow"
    p.mkdir(parents=True, exist_ok=True)
    return p / "cflow-sync.pid"


def _load_env(project_root: str | None) -> dict[str, str]:
    root = Path(project_root or Path.cwd())
    env_path = root / ".cerebraflow" / ".env"
    merged: dict[str, str] = {}
    if env_path.exists():
        for k, v in dotenv_values(str(env_path)).items():  # type: ignore[arg-type]
            if isinstance(k, str) and isinstance(v, str):
                merged[k] = v
    # Ensure Chroma path default
    chroma_default = str(root / ".cerebraflow" / "core" / "storage" / "chromadb")
    merged.setdefault("CFLOW_CHROMADB_PATH", chroma_default)
    return merged


def run_command(args: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _notify_status(status_path: Path) -> None:
    try:
        import json as _json
        data = _json.loads(status_path.read_text(encoding="utf-8"))
        daemon = (data or {}).get("daemon", {})
        running = bool(daemon.get("running"))
        msg = "Realtime daemon running" if running else "Realtime daemon stopped"
        # Optional desktop notification
        if str(os.environ.get("CFLOW_DESKTOP_NOTIFICATIONS", "")).lower() in {"1", "true", "yes", "on"}:
            try:
                import subprocess as _sp
                _sp.run([
                    sys.executable,
                    "-m",
                    "cflow_platform.cli.desktop_commander",
                    msg,
                    "--title",
                    "CFlow Sync",
                    "--subtitle",
                    "Status",
                ], check=False)
            except Exception:
                pass
    except Exception:
        pass


def start(project_root: str | None) -> int:
    paths = _service_paths()
    # Load env for child
    child_env = os.environ.copy()
    child_env.update(_load_env(project_root))
    # Enable Apple MPS and vector sync by default for this run
    child_env.setdefault("CFLOW_APPLE_MPS", "1")
    child_env.setdefault("CFLOW_VECTOR_SYNC_ENABLED", "1")
    # Match current Supabase schema which uses jsonb column 'embeddings'
    child_env.setdefault("CFLOW_VECTOR_COLUMN", "embeddings")
    # Default vector tables to discovered base tables
    child_env.setdefault("CFLOW_SUPABASE_TASKS_VECTOR_TABLE", child_env.get("CFLOW_SUPABASE_TASKS_TABLE", "cerebraflow_tasks"))
    child_env.setdefault("CFLOW_SUPABASE_DOCS_VECTOR_TABLE", child_env.get("CFLOW_SUPABASE_DOCS_TABLE", "documentation_files"))
    # Configure verbose debug logging to file
    root = Path(project_root or Path.cwd())
    log_dir = root / ".cerebraflow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "sync-service.log"
    child_env.setdefault("CFLOW_SYNC_LOG_LEVEL", "DEBUG")
    child_env.setdefault("CFLOW_SYNC_LOG_FILE", str(log_file))
    # Optional Supabase Realtime sidecar (env-gated)
    if child_env.get("CFLOW_SUPABASE_REALTIME", "").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            from cflow_platform.core.services.realtime_client import RealtimeClient  # type: ignore
            from cflow_platform.core.services.sync_handlers import handle_pg_event  # type: ignore
            supabase_url = child_env.get("SUPABASE_URL", "").strip()
            supabase_key = (child_env.get("SUPABASE_SERVICE_ROLE_KEY") or child_env.get("SUPABASE_ANON_KEY") or "").strip()
            if supabase_url and supabase_key:
                # Build WS URL
                ws = supabase_url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://") + "/realtime/v1/websocket?vsn=1.0.0"
                # Optional SSE URL (for environments without websockets)
                sse = supabase_url.rstrip("/") + "/realtime/v1/sse?vsn=1.0.0"
                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
                # Allowlist gate
                child_env.setdefault("CFLOW_ALLOWED_HOSTS", (Path(supabase_url).name if "://" not in supabase_url else supabase_url.split("//",1)[1].split("/",1)[0]))
                # Start client (daemon thread)
                rc = RealtimeClient(url=ws, headers=headers, on_event=handle_pg_event, sse_url=sse)
                # Subscribe to common tables
                schema = child_env.get("CFLOW_SUPABASE_SCHEMA", "public")
                rc.subscribe_postgres(schema, child_env.get("CFLOW_SUPABASE_TASKS_TABLE", "cerebraflow_tasks"))
                rc.subscribe_postgres(schema, child_env.get("CFLOW_SUPABASE_DOCS_TABLE", "documentation_files"))
                rc.start()
        except Exception:
            pass

    # Replace vendored daemon with a thin local supervisor that persists a PID and stays resident
    # This keeps compatibility with start/stop/status while using the new realtime path
    import threading, time as _time
    stop_flag = {"stop": False}

    def _supervisor_loop() -> None:
        while not stop_flag["stop"]:
            _time.sleep(1.0)

    th = threading.Thread(target=_supervisor_loop, name="cflow-sync-supervisor", daemon=True)
    th.start()
    # Write a synthetic PID file for this process
    pid_path = _pid_file(project_root)
    pid_path.write_text(str(os.getpid()))
    # Write initial status snapshot
    try:
        status_path = Path(project_root or Path.cwd()) / ".cerebraflow" / "sync-status.json"
        payload = {
            "daemon": {"running": True, "pid": os.getpid(), "pid_file": str(pid_path), "log_file": str(log_file)},
            "databases": _report_databases(project_root),
        }
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _notify_status(status_path)
    except Exception:
        pass
    print(json.dumps({"success": True, "pid": os.getpid(), "pid_file": str(pid_path), "log_file": str(log_file), "realtime": True}))
    return 0


def _report_databases(project_root: str | None) -> dict:
    root = Path(project_root or Path.cwd())
    env = _load_env(project_root)
    report: dict[str, object] = {"project_root": str(root)}
    # SQLite
    try:
        sqlite_paths = [root / ".cerebraflow" / "tasks.db"]
        sqlite_info: list[dict[str, object]] = []
        for sqlite_path in sqlite_paths:
            sqlite_ok = sqlite_path.exists()
            count = None
            import sqlite3
            if sqlite_ok:
                try:
                    with sqlite3.connect(sqlite_path) as conn:
                        cur = conn.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='tasks'")
                        has_table = cur.fetchone()[0] == 1
                        if has_table:
                            cur2 = conn.execute("SELECT COUNT(1) FROM tasks")
                            count = cur2.fetchone()[0]
                except Exception:
                    pass
            sqlite_info.append({"path": str(sqlite_path), "exists": sqlite_ok, "tasks": count})
        report["sqlite"] = sqlite_info
    except Exception as e:
        report["sqlite"] = {"error": str(e)}
    # ChromaDB
    try:
        chroma_info: dict[str, object] = {}
        chroma_path = root / ".cerebraflow" / "core" / "storage" / "chromadb"
        chroma_info["path"] = str(chroma_path)
        try:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore
            if chroma_path.exists():
                client = chromadb.PersistentClient(path=str(chroma_path), settings=Settings(anonymized_telemetry=False, allow_reset=False))
                try:
                    col = client.get_or_create_collection(name="cerebral_tasks")
                    chroma_info["cerebral_tasks_count"] = col.count()  # type: ignore
                except Exception:
                    pass
                try:
                    col2 = client.get_or_create_collection(name="cerebral_docs")
                    chroma_info["cerebral_docs_count"] = col2.count()  # type: ignore
                except Exception:
                    pass
                chroma_info["reachable"] = True
            else:
                chroma_info["reachable"] = False
        except Exception as e:
            chroma_info["error"] = str(e)
        report["chromadb"] = chroma_info
    except Exception as e:
        report["chromadb"] = {"error": str(e)}
    # Supabase
    try:
        import httpx  # type: ignore
        supabase_url = env.get("SUPABASE_URL")
        supabase_key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_ANON_KEY")
        reachable = False
        code = None
        if supabase_url and supabase_key:
            try:
                r = httpx.get(supabase_url.rstrip("/") + "/rest/v1/", headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}, timeout=6.0)
                reachable = True
                code = r.status_code
            except Exception:
                reachable = False
        # Counts per table (best-effort)
        tasks_table = env.get("CFLOW_SUPABASE_TASKS_TABLE") or "cerebraflow_tasks"
        docs_table = env.get("CFLOW_SUPABASE_DOCS_TABLE") or "documentation_files"
        def _table_count(table: str) -> int | None:
            if not (supabase_url and supabase_key and table):
                return None
            headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Prefer": "count=exact"}
            try:
                resp = httpx.get(supabase_url.rstrip("/") + f"/rest/v1/{table}", params={"select": "id", "limit": 1}, headers=headers, timeout=8.0)
                cr = resp.headers.get("Content-Range") or resp.headers.get("content-range")
                if cr and "/" in cr:
                    total = cr.split("/")[-1]
                    return int(total) if total.isdigit() else None
            except Exception:
                return None
            return None
        sup_counts = {
            "tasks_table": tasks_table,
            "docs_table": docs_table,
            "tasks_count": _table_count(tasks_table),
            "docs_count": _table_count(docs_table),
        }
        report["supabase"] = {"url": supabase_url, "reachable": reachable, "status_code": code, "counts": sup_counts}
    except Exception as e:
        report["supabase"] = {"error": str(e)}
    # MinIO
    try:
        import httpx  # type: ignore
        minio_endpoint = env.get("MINIO_ENDPOINT") or env.get("S3_ENDPOINT") or "minio.cerebral.baerautotech.com"
        minio_access = env.get("MINIO_ACCESS_KEY")
        minio_secret = env.get("MINIO_SECRET_KEY")
        minio_health = None
        code = None
        skipped = False
        if minio_endpoint and minio_access and minio_secret:
            url = minio_endpoint.rstrip("/") + "/minio/health/live"
            try:
                r = httpx.get(url, timeout=5.0)
                minio_health = r.text
                code = r.status_code
            except Exception:
                pass
        else:
            skipped = True
        report["minio"] = {"endpoint": minio_endpoint, "health": minio_health, "status_code": code, "skipped": skipped}
        # Consistency check: compare Chroma vs Supabase counts when available
        try:
            chroma = report.get("chromadb", {})  # type: ignore[assignment]
            sup = report.get("supabase", {})  # type: ignore[assignment]
            sup_counts = (sup or {}).get("counts", {}) if isinstance(sup, dict) else {}
            t_local = chroma.get("cerebral_tasks_count") if isinstance(chroma, dict) else None
            d_local = chroma.get("cerebral_docs_count") if isinstance(chroma, dict) else None
            t_remote = sup_counts.get("tasks_count") if isinstance(sup_counts, dict) else None
            d_remote = sup_counts.get("docs_count") if isinstance(sup_counts, dict) else None
            report["consistency"] = {
                "tasks_equal": (t_local is not None and t_remote is not None and t_local == t_remote),
                "docs_equal": (d_local is not None and d_remote is not None and d_local == d_remote),
                "local": {"tasks": t_local, "docs": d_local},
                "remote": {"tasks": t_remote, "docs": d_remote},
            }
        except Exception:
            pass
    except Exception as e:
        report["minio"] = {"error": str(e)}
    # Always attempt to write a status file snapshot for external watchers
    try:
        status_path = root / ".cerebraflow" / "sync-status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass
    return report


def status(project_root: str | None) -> int:
    # Process status from PID file
    pid_path = _pid_file(project_root)
    running = False
    pid = None
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            running = True
        except Exception:
            running = False
    payload = {
        "daemon": {
            "running": running,
            "pid": pid,
            "pid_file": str(pid_path),
            "log_file": str((Path(project_root or Path.cwd()) / ".cerebraflow" / "logs" / "sync-service.log")),
        },
        "databases": _report_databases(project_root),
    }
    # Persist status for reliable inspection
    try:
        root = Path(project_root or Path.cwd())
        status_path = root / ".cerebraflow" / "sync-status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass
    # Print to stdout in the simplest form
    print(json.dumps(payload))
    return 0


def stop(project_root: str | None) -> int:
    pid_path = _pid_file(project_root)
    if not pid_path.exists():
        print(json.dumps({"success": True, "message": "no pid file"}))
        return 0
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        pid_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        # Write status snapshot on stop
        try:
            status_path = Path(project_root or Path.cwd()) / ".cerebraflow" / "sync-status.json"
            payload = {
                "daemon": {"running": False, "pid": None, "pid_file": str(pid_path), "log_file": str((Path(project_root or Path.cwd()) / ".cerebraflow" / "logs" / "sync-service.log"))},
                "databases": _report_databases(project_root),
            }
            status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            _notify_status(status_path)
        except Exception:
            pass
        print(json.dumps({"success": True, "stopped_pid": pid}))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return 1


def _install_hooks(project_root: str | None) -> int:
    root = Path(project_root or Path.cwd())
    src = Path(__file__).resolve().parents[2] / "vendor" / "cerebral" / "git-hooks"
    hooks_dir = root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "enhanced-pre-commit": hooks_dir / "pre-commit",
        "enhanced-post-commit": hooks_dir / "post-commit",
    }
    for s, dest in mapping.items():
        content = (src / s).read_bytes()
        dest.write_bytes(content)
        os.chmod(dest, 0o755)
    print(json.dumps({"success": True, "installed": [str(p) for p in mapping.values()]}))
    return 0


def _agent_plist_content(project_root: Path) -> str:
    logs_dir = project_root / ".cerebraflow" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_log = logs_dir / "sync-agent.out.log"
    err_log = logs_dir / "sync-agent.err.log"
    cmd = f"cd {project_root} && uv run python -m cflow_platform.cli.sync_supervisor start --project-root {project_root}"
    return f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.cerebraflow.sync</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/zsh</string>
      <string>-lc</string>
      <string>{cmd}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{out_log}</string>
    <key>StandardErrorPath</key>
    <string>{err_log}</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>CEREBRAL_PROJECT_ROOT</key>
      <string>{project_root}</string>
    </dict>
  </dict>
  </plist>
""".strip()


def _watch_plist_content(project_root: Path) -> str:
    script_path = project_root / ".cerebraflow" / "scripts" / "sync_watch.sh"
    return f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.cerebraflow.sync.watch</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/zsh</string>
      <string>{script_path}</string>
    </array>
    <key>StartInterval</key>
    <integer>120</integer>
    <key>RunAtLoad</key>
    <true/>
  </dict>
  </plist>
""".strip()


def _install_launch_agents(project_root: str | None) -> int:
    root = Path(project_root or Path.cwd())
    launch_dir = Path.home() / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True, exist_ok=True)
    agent_plist = launch_dir / "com.cerebraflow.sync.plist"
    watch_plist = launch_dir / "com.cerebraflow.sync.watch.plist"
    # Write agent plist
    agent_plist.write_text(_agent_plist_content(root), encoding="utf-8")
    # Write watch script and plist
    script_dir = root / ".cerebraflow" / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / "sync_watch.sh"
    script_path.write_text(
        """
#!/bin/zsh
set -euo pipefail
LABEL="com.cerebraflow.sync"
if ! launchctl list | grep -q "$LABEL"; then
  /usr/bin/osascript -e 'display notification "Sync agent not found" with title "CerebraFlow" subtitle "Attempting start"'
  launchctl load -w ~/Library/LaunchAgents/com.cerebraflow.sync.plist || true
fi
if ! launchctl list | grep "$LABEL" | awk '{print $1}' | grep -qE '^[0-9]+$'; then
  /usr/bin/osascript -e 'display notification "Sync agent restarting" with title "CerebraFlow"'
  launchctl kickstart -k gui/$UID/$LABEL || launchctl load -w ~/Library/LaunchAgents/com.cerebraflow.sync.plist || true
fi
""".lstrip(),
        encoding="utf-8",
    )
    os.chmod(script_path, 0o755)
    watch_plist.write_text(_watch_plist_content(root), encoding="utf-8")
    # Load plists
    subprocess.run(["launchctl", "load", "-w", str(agent_plist)], check=False)
    subprocess.run(["launchctl", "load", "-w", str(watch_plist)], check=False)
    print(json.dumps({"success": True, "agent": str(agent_plist), "watch": str(watch_plist)}))
    return 0


def _uninstall_launch_agents() -> int:
    launch_dir = Path.home() / "Library" / "LaunchAgents"
    agent_plist = launch_dir / "com.cerebraflow.sync.plist"
    watch_plist = launch_dir / "com.cerebraflow.sync.watch.plist"
    subprocess.run(["launchctl", "unload", str(agent_plist)], check=False)
    subprocess.run(["launchctl", "unload", str(watch_plist)], check=False)
    removed = []
    for p in [agent_plist, watch_plist]:
        try:
            if p.exists():
                p.unlink()
                removed.append(str(p))
        except Exception:
            pass
    print(json.dumps({"success": True, "removed": removed}))
    return 0

def _import_memories(project_root: str | None) -> int:
    report: dict[str, object] = {"imported": 0, "errors": []}
    try:
        from chromadb import PersistentClient  # type: ignore
        from chromadb.config import Settings  # type: ignore
    except Exception as e:
        print(json.dumps({"success": False, "error": f"chromadb missing: {e}"}))
        return 1
    root = Path(project_root or Path.cwd())
    sqlite_path = root / ".cerebraflow" / "tasks.db"
    chroma_path = root / ".cerebraflow" / "core" / "storage" / "chromadb"
    try:
        import sqlite3
        tasks: list[dict[str, object]] = []
        if sqlite_path.exists():
            with sqlite3.connect(sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                try:
                    cur = conn.execute("SELECT * FROM tasks")
                    tasks = [dict(r) for r in cur.fetchall()]
                except Exception:
                    pass
        client = PersistentClient(path=str(chroma_path), settings=Settings(anonymized_telemetry=False, allow_reset=False))
        collection = client.get_or_create_collection(name="cerebral_tasks")
        imported = 0
        for t in tasks:
            try:
                tid = str(t.get("task_id") or f"T{t.get('created_at','')}")
                title = str(t.get("title") or "")
                desc = str(t.get("description") or "")
                doc = f"{title}\n{desc}"
                metadata = {k: ("" if v is None else v) for k, v in t.items() if k != "description"}
                collection.add(ids=[tid], documents=[doc], metadatas=[metadata])
                imported += 1
            except Exception as e:
                report["errors"].append(str(e))  # type: ignore[index]
        report["imported"] = imported
        print(json.dumps({"success": True, "report": report}))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "report": report}))
        return 1


def _import_env(project_root: str | None, source_env: str | None) -> int:
    src = Path(source_env or "/Users/bbaer/Development/Cerebral/.env")
    if not src.exists():
        print(json.dumps({"success": False, "error": f"source env not found: {src}"}))
        return 1
    root = Path(project_root or Path.cwd())
    dest_dir = root / ".cerebraflow"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ".env"
    allowed = {
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "MINIO_ENDPOINT",
        "S3_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "CEREBRAFLOW_TENANT_ID",
        "CEREBRAFLOW_PROJECT_ID",
        "CEREBRAFLOW_USER_ID",
        "CEREBRAL_TENANT_ID",
        "CEREBRAL_PROJECT_ID",
        "CEREBRAL_USER_ID",
    }
    lines: list[str] = []
    for line in src.read_text().splitlines():
        if not line or line.strip().startswith("#"):
            continue
        k = line.split("=", 1)[0].strip()
        if k in allowed:
            lines.append(line)
    dest.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(json.dumps({"success": True, "written": str(dest), "keys": [l.split("=",1)[0] for l in lines]}))
    return 0


def _import_mcp(project_root: str | None, source_mcp: str | None) -> int:
    src = Path(source_mcp or "/Users/bbaer/Development/Cerebral/.cursor/mcp.json")
    if not src.exists():
        print(json.dumps({"success": False, "error": f"source mcp.json not found: {src}"}))
        return 1
    root = Path(project_root or Path.cwd())
    dest_dir = root / ".cursor"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "mcp.json"
    dest.write_bytes(src.read_bytes())
    print(json.dumps({"success": True, "written": str(dest)}))
    return 0


def _install_systemd(project_root: str | None) -> int:
    root = Path(project_root or Path.cwd())
    unit_name = "cerebraflow-sync"
    service = f"""
[Unit]
Description=CerebraFlow Sync Service
After=network.target

[Service]
Type=simple
WorkingDirectory={root}
EnvironmentFile={root}/.cerebraflow/.env
ExecStart={_python_executable()} -m cflow_platform.cli.sync_supervisor start --project-root {root}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""".strip()
    timer = f"""
[Unit]
Description=CerebraFlow Sync Watchdog

[Timer]
OnBootSec=30
OnUnitActiveSec=120
Unit={unit_name}.service

[Install]
WantedBy=timers.target
""".strip()
    etc = Path("/etc/systemd/system")
    try:
        (etc / f"{unit_name}.service").write_text(service)
        (etc / f"{unit_name}.timer").write_text(timer)
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "enable", f"{unit_name}.service"], check=False)
        subprocess.run(["systemctl", "enable", f"{unit_name}.timer"], check=False)
        print(json.dumps({"success": True, "unit": unit_name}))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return 1


def _install_windows(project_root: str | None) -> int:
    root = Path(project_root or Path.cwd())
    # Create a scheduled task that runs at logon and on a 2-minute interval retry
    cmd = f"{_python_executable()} -m cflow_platform.cli.sync_supervisor start --project-root {root}"
    try:
        # Register task
        subprocess.run(["schtasks", "/Create", "/TN", "CerebraFlowSync", "/TR", cmd, "/SC", "ONLOGON", "/RL", "LIMITED", "/F"], check=False)
        # Add repeat
        subprocess.run(["schtasks", "/Change", "/TN", "CerebraFlowSync", "/RI", "2"], check=False)
        print(json.dumps({"success": True, "task": "CerebraFlowSync"}))
        return 0
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return 1


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow sync supervisor (vendored Cerebral sync service)")
    parser.add_argument("command", choices=["start", "stop", "status", "import-hooks", "import-memories", "import-env", "import-mcp", "install-agent", "uninstall-agent", "install-systemd", "install-windows"], help="Supervisor command")
    parser.add_argument("--project-root", dest="project_root", help="Project root for underlying service")
    parser.add_argument("--source-env", dest="source_env", help="Source .env path (defaults to Cerebral .env)")
    parser.add_argument("--source-mcp", dest="source_mcp", help="Source mcp.json path (defaults to Cerebral .cursor/mcp.json)")
    args = parser.parse_args()
    if args.command == "start":
        return start(args.project_root)
    if args.command == "stop":
        return stop(args.project_root)
    if args.command == "import-hooks":
        return _install_hooks(args.project_root)
    if args.command == "import-memories":
        return _import_memories(args.project_root)
    if args.command == "import-env":
        return _import_env(args.project_root, args.source_env)
    if args.command == "import-mcp":
        return _import_mcp(args.project_root, args.source_mcp)
    if args.command == "install-agent":
        return _install_launch_agents(args.project_root)
    if args.command == "uninstall-agent":
        return _uninstall_launch_agents()
    if args.command == "install-systemd":
        return _install_systemd(args.project_root)
    if args.command == "install-windows":
        return _install_windows(args.project_root)
    return status(args.project_root)


if __name__ == "__main__":
    raise SystemExit(cli())


