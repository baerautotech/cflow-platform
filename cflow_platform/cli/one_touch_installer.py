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
    parser = argparse.ArgumentParser(description="CFlow one-touch installer with BMAD integration")
    parser.add_argument("--watch", action="store_true", help="Start memory watcher after setup")
    parser.add_argument("--install-sync-agent", action="store_true", help="Install LaunchAgents to auto-start sync daemon")
    parser.add_argument("--apply-migrations", action="store_true", help="Apply Supabase memory schema migration if SUPABASE_DB_URL available")
    parser.add_argument("--initial-backfill", action="store_true", help="Backfill docs/tasks locally and run one-shot sync")
    parser.add_argument("--setup-bmad", action="store_true", help="Setup BMAD integration components")
    parser.add_argument("--verify-bmad", action="store_true", help="Verify BMAD templates and handlers are available")
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

    # BMAD integration setup
    if args.setup_bmad and rc == 0:
        print("Setting up BMAD integration components...")
        # Verify BMAD vendor directory exists
        bmad_path = Path.cwd() / "vendor" / "bmad"
        if not bmad_path.exists():
            print("Warning: BMAD vendor directory not found. BMAD integration may not work properly.")
        else:
            print(f"BMAD vendor directory found at: {bmad_path}")
            # Verify BMAD templates are available
            templates_path = bmad_path / "bmad-core" / "templates"
            if templates_path.exists():
                print(f"BMAD templates found at: {templates_path}")
            else:
                print("Warning: BMAD templates directory not found.")

    # Verify BMAD components
    if args.verify_bmad and rc == 0:
        print("Verifying BMAD integration components...")
        # Check if BMAD handlers are available
        try:
            from cflow_platform.handlers.bmad_handlers import BMADHandlers
            print("✓ BMAD handlers available")
        except ImportError as e:
            print(f"✗ BMAD handlers not available: {e}")
            rc |= 1

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
        if args.setup_bmad or args.verify_bmad:
            print("BMAD integration components verified and ready.")
    else:
        print("One-touch installer completed with issues. See logs above.")
    return rc


if __name__ == "__main__":
    raise SystemExit(cli())


