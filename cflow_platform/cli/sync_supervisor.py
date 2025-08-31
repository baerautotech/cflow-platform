from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _python_executable() -> str:
    return sys.executable


def _service_paths() -> dict[str, str]:
    base = Path(__file__).resolve().parents[2] / "vendor" / "cerebral" / "services"
    return {
        "unified": str(base / "unified_realtime_sync_service.py"),
        "core": str(base / "chromadb_supabase_sync_service.py"),
    }


def run_command(args: list[str], cwd: str | None = None, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def start(project_root: str | None) -> int:
    paths = _service_paths()
    if not Path(paths["unified"]).exists():
        print(json.dumps({"success": False, "error": "unified_realtime_sync_service.py not found"}))
        return 1
    code, out, err = run_command([_python_executable(), paths["unified"], "daemon", "--project-root", project_root or str(Path.cwd())])
    print(out or err)
    return 0 if code == 0 else 1


def _report_databases(project_root: str | None) -> dict:
    root = Path(project_root or Path.cwd())
    report: dict[str, object] = {"project_root": str(root)}
    # SQLite
    try:
        sqlite_path = root / ".cflow" / "tasks.db"
        sqlite_ok = sqlite_path.exists()
        count = None
        if sqlite_ok:
            import sqlite3
            with sqlite3.connect(sqlite_path) as conn:
                cur = conn.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='tasks'")
                has_table = cur.fetchone()[0] == 1
                if has_table:
                    cur2 = conn.execute("SELECT COUNT(1) FROM tasks")
                    count = cur2.fetchone()[0]
        report["sqlite"] = {"path": str(sqlite_path), "exists": sqlite_ok, "tasks": count}
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
        supabase_url = os.environ.get("SUPABASE_URL")
        reachable = False
        code = None
        if supabase_url:
            try:
                r = httpx.get(supabase_url, timeout=5.0)
                reachable = True
                code = r.status_code
            except Exception:
                reachable = False
        report["supabase"] = {"url": supabase_url, "reachable": reachable, "status_code": code}
    except Exception as e:
        report["supabase"] = {"error": str(e)}
    # MinIO
    try:
        import httpx  # type: ignore
        minio_endpoint = os.environ.get("MINIO_ENDPOINT") or os.environ.get("S3_ENDPOINT")
        minio_health = None
        code = None
        if minio_endpoint:
            url = minio_endpoint.rstrip("/") + "/minio/health/live"
            try:
                r = httpx.get(url, timeout=5.0)
                minio_health = r.text
                code = r.status_code
            except Exception:
                pass
        report["minio"] = {"endpoint": minio_endpoint, "health": minio_health, "status_code": code}
    except Exception as e:
        report["minio"] = {"error": str(e)}
    return report


def status(project_root: str | None) -> int:
    paths = _service_paths()
    code, out, err = run_command([_python_executable(), paths["unified"], "status", "--project-root", project_root or str(Path.cwd())])
    try:
        status_payload = json.loads(out) if out.strip().startswith("{") else {"raw": out or err}
    except Exception:
        status_payload = {"raw": out or err}
    status_payload["databases"] = _report_databases(project_root)
    print(json.dumps(status_payload))
    return 0 if code == 0 else 1


def stop(project_root: str | None) -> int:
    paths = _service_paths()
    code, out, err = run_command([_python_executable(), paths["unified"], "stop", "--project-root", project_root or str(Path.cwd())])
    print(out or err)
    return 0 if code == 0 else 1


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow sync supervisor (vendored Cerebral sync service)")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Supervisor command")
    parser.add_argument("--project-root", dest="project_root", help="Project root for underlying service")
    args = parser.parse_args()
    if args.command == "start":
        return start(args.project_root)
    if args.command == "stop":
        return stop(args.project_root)
    return status(args.project_root)


if __name__ == "__main__":
    raise SystemExit(cli())


