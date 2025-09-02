from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except Exception as e:
        print(f"error: {e}")
        return 1


def _spawn(cmd: list[str]) -> None:
    print("$ (bg)", " ".join(cmd))
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"error (bg): {e}")


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow one-touch installer")
    parser.add_argument("--watch", action="store_true", help="Start memory watcher after setup")
    parser.add_argument("--install-sync-agent", action="store_true", help="Install LaunchAgents to auto-start sync daemon")
    parser.add_argument("--apply-migrations", action="store_true", help="Apply Supabase memory schema migration if SUPABASE_DB_URL available")
    parser.add_argument("--initial-backfill", action="store_true", help="Backfill docs/tasks locally and run one-shot sync")
    args = parser.parse_args()

    rc = 0
    # Verify environment (non-interactive)
    rc |= _run([sys.executable, "-m", "cflow_platform.verify_env", "--mode", "migrations", "--mode", "ragkg", "--mode", "llm", "--scope", "both"])
    # Install hooks
    rc |= _run([sys.executable, "-m", "cflow_platform.install_hooks"])
    # Setup Cursor workspace
    rc |= _run([sys.executable, "-m", "cflow_platform.cli.setup_cursor"])
    # Memory connectivity check
    rc |= _run([sys.executable, "-m", "cflow_platform.cli.memory_check"])

    # Optional: Supabase migrations
    if args.apply_migrations and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.migrate_supabase", "--apply"])

    # Install auto-start sync agent
    if args.install_sync_agent and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "install-agent", "--project-root", str(Path.cwd())])

    # Initial backfill & parity sync
    if args.initial_backfill and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.docs_backfill"])
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.tasks_backfill"])
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "status"])  # parity report

    if args.watch and rc == 0:
        # Start memory watcher in background
        _spawn([sys.executable, "-m", "cflow_platform.cli.memory_watch", "--watch"])

    if rc == 0:
        print("One-touch installer completed successfully.")
    else:
        print("One-touch installer completed with issues. See logs above.")
    return rc


if __name__ == "__main__":
    raise SystemExit(cli())


