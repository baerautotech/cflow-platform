from __future__ import annotations

import argparse
import subprocess
import sys


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


