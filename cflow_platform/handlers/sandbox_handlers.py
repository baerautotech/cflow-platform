from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SandboxHandlers:
    async def handle_run_python(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        code: str = str(arguments.get("code", ""))
        if not code.strip():
            return {"status": "error", "error": "Missing required field: code"}

        # Limits and policy
        time_limit_sec: int = int(arguments.get("time_limit_sec", 3))
        cpu_limit_sec: int = int(arguments.get("cpu_limit_sec", max(1, min(time_limit_sec, 3))))
        mem_limit_mb: int = int(arguments.get("mem_limit_mb", 256))
        filesystem_allowlist: List[str] = list(
            map(str, arguments.get("fs_allowlist", [str(Path.cwd())]))
        )

        # Create temp working directory
        with tempfile.TemporaryDirectory(prefix="cflow_sandbox_") as tmpdir:
            tmp_path = Path(tmpdir)

            user_code_path = tmp_path / "user_code.py"
            wrapper_path = tmp_path / "wrapper.py"

            user_code_path.write_text(code, encoding="utf-8")

            wrapper_src = _build_wrapper_script(
                user_code_path=user_code_path,
                time_limit_sec=time_limit_sec,
                cpu_limit_sec=cpu_limit_sec,
                mem_limit_mb=mem_limit_mb,
                fs_allowlist=filesystem_allowlist + [str(tmp_path)],
            )
            wrapper_path.write_text(wrapper_src, encoding="utf-8")

            env = os.environ.copy()
            # Harden environment for sandboxed run
            env.update(
                {
                    "PYTHONWARNINGS": "ignore",
                    "PYTHONUNBUFFERED": "1",
                    # Try to avoid accidentally loading site/user customizations
                    "PYTHONSAFEPATH": "1",
                    "NO_PROXY": "*",
                    "no_proxy": "*",
                    # Inform wrapper of allowlist
                    "CFLOW_SANDBOX_ALLOWLIST": json.dumps(filesystem_allowlist + [str(tmp_path)]),
                }
            )

            # Prefer running via uv when available, fallback to python
            runner: List[str]
            if _has_uv():
                runner = [sys.executable, "-m", "uv", "run", sys.executable, str(wrapper_path)]
            else:
                runner = [sys.executable, str(wrapper_path)]

            start = time.time()
            try:
                proc = subprocess.run(
                    runner,
                    cwd=str(tmp_path),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=time_limit_sec + 1,
                )
                elapsed_ms = int((time.time() - start) * 1000)
                status = "success" if proc.returncode == 0 else "error"
                return {
                    "status": status,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "time_ms": elapsed_ms,
                    "policy": {
                        "network": "denied",
                        "fs_allowlist": filesystem_allowlist + [str(tmp_path)],
                        "limits": {
                            "cpu_sec": cpu_limit_sec,
                            "time_sec": time_limit_sec,
                            "mem_mb": mem_limit_mb,
                        },
                    },
                }
            except subprocess.TimeoutExpired as e:
                elapsed_ms = int((time.time() - start) * 1000)
                stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
                stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
                return {
                    "status": "error",
                    "error": "timeout",
                    "stdout": stdout,
                    "stderr": stderr,
                    "time_ms": elapsed_ms,
                    "policy": {
                        "network": "denied",
                        "fs_allowlist": filesystem_allowlist + [str(tmp_path)],
                        "limits": {
                            "cpu_sec": cpu_limit_sec,
                            "time_sec": time_limit_sec,
                            "mem_mb": mem_limit_mb,
                        },
                    },
                }


def _has_uv() -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec("uv") is not None
    except Exception:
        return False


def _build_wrapper_script(
    user_code_path: Path,
    time_limit_sec: int,
    cpu_limit_sec: int,
    mem_limit_mb: int,
    fs_allowlist: List[str],
) -> str:
    # Wrapper script executed in a fresh Python process to enforce limits and policy.
    # Uses resource limits, signal alarm, and monkeypatches for network and file access.
    allowlist_json = json.dumps(fs_allowlist)
    return textwrap.dedent(
        f"""
        import builtins
        import errno
        import json
        import os
        import pathlib
        import resource
        import signal
        import socket
        import sys
        import time

        TIME_LIMIT_SEC = int({time_limit_sec})
        CPU_LIMIT_SEC = int({cpu_limit_sec})
        MEM_LIMIT_MB = int({mem_limit_mb})
        FS_ALLOWLIST = json.loads({json.dumps(allowlist_json)})

        def _is_path_allowed(path: str) -> bool:
            try:
                real = os.path.realpath(path)
            except Exception:
                return False
            for allowed in FS_ALLOWLIST:
                if real.startswith(os.path.realpath(allowed) + os.sep) or real == os.path.realpath(allowed):
                    return True
            return False

        # Enforce CPU and memory limits (best-effort; platform dependent)
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_SEC, CPU_LIMIT_SEC))
        except Exception:
            pass
        try:
            # Address space / data segment as best-effort memory cap
            limit_bytes = max(MEM_LIMIT_MB, 16) * 1024 * 1024
            if hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            elif hasattr(resource, 'RLIMIT_DATA'):
                resource.setrlimit(resource.RLIMIT_DATA, (limit_bytes, limit_bytes))
        except Exception:
            pass

        # Wall-clock timeout via alarm
        def _alarm_handler(signum, frame):
            raise TimeoutError('sandbox time limit exceeded')
        try:
            signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(max(1, TIME_LIMIT_SEC))
        except Exception:
            pass

        # Deny network by replacing socket constructor
        class _NetworkDisabledSocket:
            def __init__(self, *args, **kwargs):
                raise OSError(errno.EPERM, 'Network access is disabled in sandbox')
        try:
            socket.socket = _NetworkDisabledSocket  # type: ignore
        except Exception:
            pass

        # Wrap file open to enforce allowlist
        _real_open = builtins.open
        def _guarded_open(file, *args, **kwargs):
            path = str(file)
            if not _is_path_allowed(path):
                raise PermissionError(errno.EPERM, f'File access denied by sandbox: {{path}}')
            return _real_open(file, *args, **kwargs)
        builtins.open = _guarded_open  # type: ignore

        # Also guard os.open calls
        _os_open = os.open
        def _guarded_os_open(file, flags, mode=0o777):
            path = str(file)
            if not _is_path_allowed(path):
                raise PermissionError(errno.EPERM, f'File access denied by sandbox: {{path}}')
            return _os_open(file, flags, mode)
        os.open = _guarded_os_open  # type: ignore

        # Set CWD to a temporary working directory path (already set by caller)
        # Execute the user code
        start = time.time()
        exit_code = 0
        try:
            with open({json.dumps(str(user_code_path))}, 'r', encoding='utf-8') as f:
                source = f.read()
            code = compile(source, filename='user_code.py', mode='exec')
            globals_dict = {{'__name__': '__main__'}}
            exec(code, globals_dict, None)
        except TimeoutError as te:
            print(str(te), file=sys.stderr)
            exit_code = 124
        except Exception as e:
            print(str(e), file=sys.stderr)
            exit_code = 1
        finally:
            try:
                signal.alarm(0)
            except Exception:
                pass
        end = time.time()
        # Exit with code that the parent will interpret
        sys.exit(exit_code)
        """
    ).lstrip()


