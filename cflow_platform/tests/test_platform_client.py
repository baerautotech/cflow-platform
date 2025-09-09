from __future__ import annotations

import os
import pytest

from cflow_platform.core.services.platform_client import sign_request, PlatformClient
from cflow_platform.core.services.specs import canonical_json, validate_policy_doc
from cflow_platform.core.services.realtime_client import RealtimeClient


def test_sign_request_stable() -> None:
    sig = sign_request("secret", "post", "/api/tasks", "{}", "1700000000", "abcd1234")
    # Fixed expected digest for regression protection
    assert sig == "22da9fb0c716c73cfe5d3e275a047d0ffaa0d995bd653dce3f46adff3151d19b"


def test_allowlist_blocks_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CFLOW_ALLOWED_HOSTS", "api.cerebral.ai")
    with pytest.raises(RuntimeError):
        PlatformClient(base_url="https://example.com")


def test_canonical_json_and_policy_validation() -> None:
    obj = {"b": 2, "a": 1}
    s = canonical_json(obj)
    assert s == "{\"a\":1,\"b\":2}"

    ok, errs = validate_policy_doc({"version": "1", "capabilities": [{"name": "task.submit", "enabled": True}]})
    assert ok and not errs

    ok2, errs2 = validate_policy_doc({"version": "", "capabilities": ["bad"]})
    assert not ok2 and errs2


def test_realtime_client_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CFLOW_ALLOWED_HOSTS", "realtime.supabase.co")
    with pytest.raises(RuntimeError):
        RealtimeClient(url="wss://other.example.com")
    # Allowed host
    RealtimeClient(url="wss://realtime.supabase.co")


