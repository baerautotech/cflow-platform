from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import os
import time
import threading
import json

try:  # Optional dependency to keep tests light
    import websockets  # type: ignore
except Exception:  # pragma: no cover - soft dependency
    websockets = None  # type: ignore
try:  # Optional SSE fallback
    import httpx  # type: ignore
except Exception:  # pragma: no cover - soft dependency
    httpx = None  # type: ignore


def _truthy(val: Optional[str]) -> bool:
    return bool(val and val.strip().lower() in {"1", "true", "yes", "on"})


def _require_host_allowlist(url: str) -> None:
    host = urlparse(url).hostname or ""
    allow_env = os.getenv("CFLOW_ALLOWED_HOSTS", "")
    allowed = [h.strip().lower() for h in allow_env.replace(";", ",").split(",") if h.strip()]
    if allowed and host.lower() not in allowed:
        raise RuntimeError(f"Host not allowed: {host}")


@dataclass
class RealtimeClient:
    url: str
    on_event: Optional[Callable[[dict], None]] = None
    max_retries: int = 5
    base_backoff_ms: int = 200
    headers: Optional[Dict[str, str]] = None
    sse_url: Optional[str] = None  # Optional explicit SSE endpoint

    # Internal state
    _subs: List[Tuple[str, Dict[str, object], Optional[Callable[[dict], None]]]] = field(default_factory=list)
    _thread: Optional[threading.Thread] = None
    _stop_flag: bool = False
    _failures: int = 0
    _notify_threshold: int = 3
    _last_notify_s: float = 0.0

    def __post_init__(self) -> None:
        _require_host_allowlist(self.url)

    def connect(self) -> None:
        # Validates URL and host policy; if websockets lib is missing, remains a no-op.
        _ = self.url
        if websockets is None:
            return None
        return None

    def subscribe(self, channel: str) -> None:
        # Placeholder for channel subscription
        _ = channel

    def subscribe_postgres(self, schema: str, table: str, callback: Optional[Callable[[dict], None]] = None) -> None:
        topic = f"realtime:{schema}:{table}"
        payload = {"events": ["INSERT", "UPDATE", "DELETE"], "schema": schema, "table": table}
        self._subs.append((topic, payload, callback))

    # Best-effort Supabase Phoenix join loop (only if websockets present)
    def _run_loop(self) -> None:  # pragma: no cover (network loop not executed in tests)
        if websockets is None:
            # Attempt SSE fallback if available
            if self.sse_url and httpx is not None:
                self._run_sse_loop()
            return
        attempt = 0
        while not self._stop_flag and (attempt <= self.max_retries):
            try:
                # Supabase Realtime expects query params apikey & vsn
                url = self.url
                if "?" not in url:
                    url = url + "?vsn=1.0.0"
                headers = self.headers or {}
                # Connect
                attempt += 1
                # Note: simple connect; no SSL tweaks here
                with websockets.sync.client.connect(url, additional_headers=headers) as ws:  # type: ignore[attr-defined]
                    # Join all topics
                    ref = 1
                    for topic, payload, _cb in self._subs:
                        msg = {
                            "topic": topic,
                            "event": "phx_join",
                            "payload": payload,
                            "ref": str(ref),
                        }
                        ref += 1
                        ws.send(json.dumps(msg))
                    # Receive loop
                    while not self._stop_flag:
                        raw = ws.recv()
                        if not raw:
                            break
                        try:
                            data = json.loads(raw)
                        except Exception:
                            continue
                        # Dispatch to topic callback or global handler
                        topic = str(data.get("topic", ""))
                        delivered = False
                        for t, _p, cb in self._subs:
                            if t == topic and cb is not None:
                                try:
                                    cb(data)
                                    delivered = True
                                except Exception:
                                    pass
                                break
                        if not delivered and self.on_event is not None:
                            try:
                                self.on_event(data)
                            except Exception:
                                pass
                attempt = 0  # reset after a clean session
            except Exception:
                self._backoff(attempt)
                self._record_failure("websocket error")
                continue

    def _run_sse_loop(self) -> None:
        if httpx is None or not self.sse_url:
            return
        attempt = 0
        while not self._stop_flag and (attempt <= self.max_retries):
            try:
                attempt += 1
                with httpx.Client(timeout=30.0) as client:
                    headers = {"Accept": "text/event-stream"}
                    if self.headers:
                        headers.update(self.headers)
                    with client.stream("GET", self.sse_url, headers=headers) as resp:
                        resp.raise_for_status()
                        for line in resp.iter_lines():
                            if self._stop_flag:
                                break
                            if not line:
                                continue
                            if line.startswith(b"data:"):
                                payload = line[len(b"data:"):].strip()
                                try:
                                    data = json.loads(payload.decode("utf-8"))
                                except Exception:
                                    continue
                                delivered = False
                                topic = str(data.get("topic", ""))
                                for t, _p, cb in self._subs:
                                    if t == topic and cb is not None:
                                        try:
                                            cb(data)
                                            delivered = True
                                        except Exception:
                                            pass
                                        break
                                if not delivered and self.on_event is not None:
                                    try:
                                        self.on_event(data)
                                    except Exception:
                                        pass
                attempt = 0
            except Exception:
                self._backoff(attempt)
                self._record_failure("sse error")
                continue

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run_loop, name="RealtimeClient", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_flag = True
        try:
            if self._thread is not None:
                self._thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            self._thread = None

    def _record_failure(self, reason: str) -> None:
        try:
            self._failures += 1
            if self._failures % max(1, self._notify_threshold) == 0:
                # Throttle to once per 60s
                now = time.time()
                if now - self._last_notify_s > 60:
                    self._last_notify_s = now
                    self._notify_desktop(f"Realtime backoff: {reason} (failures={self._failures})")
        except Exception:
            pass

    def _notify_desktop(self, message: str) -> None:
        try:
            enabled = os.getenv("CFLOW_DESKTOP_NOTIFICATIONS", "").strip().lower() in {"1", "true", "yes", "on"}
            if not enabled:
                return
            # Lazy import to avoid cycles
            from cflow_platform.core.direct_client import execute_mcp_tool  # type: ignore
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                execute_mcp_tool("desktop.notify", title="CerebraFlow", subtitle="Realtime", message=message)
            )
        except Exception:
            return

    def _backoff(self, attempt: int) -> None:
        delay = (2 ** attempt) * self.base_backoff_ms / 1000.0
        time.sleep(min(delay, 5.0))


