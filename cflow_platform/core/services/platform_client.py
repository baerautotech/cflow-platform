from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from pathlib import Path
import json
import os
import time

import httpx
from .specs import (
    HEADER_ALGORITHM,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    SIGN_ALGORITHM,
    canonical_json,
    default_endpoints,
    sign_request as spec_sign,
    validate_policy_doc,
)
from ..telemetry import log_event


def _truthy(val: Optional[str]) -> bool:
    return bool(val and val.strip().lower() in {"1", "true", "yes", "on"})


def _require_host_allowlist(url: str) -> None:
    host = urlparse(url).hostname or ""
    allow_env = os.getenv("CFLOW_ALLOWED_HOSTS", "")
    allowed = [h.strip().lower() for h in allow_env.replace(";", ",").split(",") if h.strip()]
    if allowed and host.lower() not in allowed:
        raise RuntimeError(f"Host not allowed: {host}")


def _ts_nonce() -> tuple[str, str]:
    ts = str(int(time.time()))
    nonce = hashlib.sha256(f"{ts}:{os.getpid()}:{os.urandom(8).hex()}".encode()).hexdigest()[:16]
    return ts, nonce


def sign_request(secret: str, method: str, path: str, body: str, ts: str, nonce: str) -> str:
    return spec_sign(secret, method, path, body, ts, nonce)


@dataclass
class PlatformClient:
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    timeout_sec: float = 30.0

    def __post_init__(self) -> None:
        _require_host_allowlist(self.base_url)
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout_sec, http2=True)
        self._policy: Optional[Dict[str, Any]] = None
        self._enforce_policy = _truthy(os.getenv("CFLOW_ENFORCE_POLICY"))
        # Opportunistically load cached policy when enforcement enabled
        if self._enforce_policy:
            try:
                self.load_policy_from_cache()
            except Exception:
                self._policy = None

    def _headers(self, method: str, path: str, body_obj: Optional[Dict[str, Any]]) -> Dict[str, str]:
        body = canonical_json(body_obj or {})
        ts, nonce = _ts_nonce()
        sig = ""
        if self.api_secret:
            sig = sign_request(self.api_secret, method, path, body, ts, nonce)
        hdrs = {
            "Content-Type": "application/json",
            HEADER_TIMESTAMP: ts,
            HEADER_NONCE: nonce,
            HEADER_SIGNATURE: sig,
            HEADER_ALGORITHM: SIGN_ALGORITHM,
        }
        if self.api_key:
            hdrs["Authorization"] = f"Bearer {self.api_key}"
        return hdrs

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body_obj = body or {}
        headers = self._headers(method, path, body_obj)
        payload = canonical_json(body_obj)
        max_retries = int(os.getenv("CFLOW_HTTP_MAX_RETRIES", "3") or "3")
        attempt = 0
        last_exc: Exception | None = None
        while attempt <= max_retries:
            try:
                resp = self._client.request(method, path, headers=headers, content=payload)
                resp.raise_for_status()
                try:
                    return resp.json()
                except Exception:
                    return {"status": "error", "message": "invalid json"}
            except Exception as e:
                last_exc = e
                if attempt == max_retries:
                    break
                # Exponential backoff with cap
                delay = min(2 ** attempt * 0.25, 3.0)
                log_event("platform_client.retry", {"method": method, "path": path, "attempt": attempt + 1, "delay": delay})
                import time as _t
                _t.sleep(delay)
                attempt += 1
                continue
        raise last_exc if last_exc else RuntimeError("request failed")

    # Policy cache helpers
    def _policy_cache_path(self, override: Optional[str] = None) -> Path:
        if override:
            return Path(override)
        root = Path.cwd() / ".cerebraflow"
        root.mkdir(parents=True, exist_ok=True)
        return root / "policy.json"

    def load_policy_from_cache(self, cache_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        path = self._policy_cache_path(cache_path)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        ok, errs = validate_policy_doc(data if isinstance(data, dict) else {})
        if not ok:
            raise RuntimeError(f"invalid cached policy: {'; '.join(errs)}")
        self._policy = data
        return data

    def sync_policies(self, cache_path: Optional[str] = None) -> Dict[str, Any]:
        doc = self.fetch_policies()
        ok, errs = validate_policy_doc(doc if isinstance(doc, dict) else {})
        if not ok:
            raise RuntimeError(f"invalid policy doc: {'; '.join(errs)}")
        self._policy = doc
        path = self._policy_cache_path(cache_path or os.getenv("CFLOW_POLICY_CACHE"))
        path.write_text(canonical_json(doc), encoding="utf-8")
        return doc

    def has_capability(self, cap: str) -> bool:
        if not self._policy or not isinstance(self._policy.get("capabilities"), list):
            return False
        caps = self._policy.get("capabilities") or []
        for c in caps:
            try:
                if c.get("name") == cap and bool(c.get("enabled")):
                    return True
            except Exception:
                continue
        return False

    def _ensure_cap(self, cap: str) -> None:
        if not self._enforce_policy:
            return
        if not self.has_capability(cap):
            raise RuntimeError(f"policy gate: capability not enabled -> {cap}")

    # Public API
    def fetch_policies(self) -> Dict[str, Any]:
        return self._request("GET", "/api/policies")

    def submit_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_cap("task.submit")
        return self._request("POST", "/api/tasks", task)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        self._ensure_cap("task.status")
        return self._request("GET", f"/api/tasks/{task_id}")

    def stream_task_logs(self, task_id: str) -> Dict[str, Any]:
        """Stream task logs using realtime client integration."""
        self._ensure_cap("task.logs")
        return self._request("GET", f"/api/tasks/{task_id}/logs")

    def upload_artifact(self, task_id: str, artifact: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_cap("task.artifact")
        return self._request("POST", f"/api/tasks/{task_id}/artifacts", artifact)


