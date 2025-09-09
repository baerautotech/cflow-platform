from __future__ import annotations

from pathlib import Path
from typing import Optional
import json
import os
import stat


class SecretStore:
    """Minimal secret store with a safe file-mode fallback.

    - Default mode: file under .cerebraflow/secrets.json with 0o600 perms
    - Future: macOS Keychain integration (not required for tests)
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        root = base_dir or Path.cwd() / ".cerebraflow"
        root.mkdir(parents=True, exist_ok=True)
        self._path = root / "secrets.json"
        if not self._path.exists():
            self._path.write_text("{}", encoding="utf-8")
            try:
                os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass

    def set(self, key: str, value: str) -> None:
        data = self._read()
        data[str(key)] = str(value)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    def get(self, key: str) -> Optional[str]:
        data = self._read()
        val = data.get(str(key))
        return str(val) if val is not None else None

    def _read(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}


