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
    # Services are vendored under cflow_platform/vendor/cerebral/services
    base = Path(__file__).resolve().parents[1] / "vendor" / "cerebral" / "services"
    return {
        "unified": str(base / "unified_realtime_sync_service.py"),
        "core": str(base / "chromadb_supabase_sync_service.py"),
    }


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
    # Run the vendored unified service in foreground "start" mode so this PID represents the daemon
    log_handle = open(log_file, "a", buffering=1)
    proc = subprocess.Popen([
        _python_executable(),
        paths["unified"],
        "start",
        "--project-root",
        project_root or str(Path.cwd()),
    ], stdout=log_handle, stderr=log_handle, env=child_env)
    # Write PID file
    pid_path = _pid_file(project_root)
    pid_path.write_text(str(proc.pid))
    print(json.dumps({"success": True, "pid": proc.pid, "pid_file": str(pid_path), "log_file": str(log_file)}))
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
        minio_endpoint = env.get("MINIO_ENDPOINT") or env.get("S3_ENDPOINT")
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


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow sync supervisor (vendored Cerebral sync service)")
    parser.add_argument("command", choices=["start", "stop", "status", "import-hooks", "import-memories", "import-env", "import-mcp"], help="Supervisor command")
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
    return status(args.project_root)


if __name__ == "__main__":
    raise SystemExit(cli())


