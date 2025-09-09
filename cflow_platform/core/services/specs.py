from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import hashlib
import hmac
import json


# Signing/headers spec (align with server defaults)
SIGN_ALGORITHM = "HMAC-SHA256"
HEADER_TIMESTAMP = "X-Cerebral-Timestamp"
HEADER_NONCE = "X-Cerebral-Nonce"
HEADER_SIGNATURE = "X-Cerebral-Signature"
HEADER_ALGORITHM = "X-Cerebral-Alg"


def canonical_json(obj: Dict[str, Any]) -> str:
    """Canonical JSON for signing (minimal separators, stable key order)."""
    try:
        return json.dumps(obj or {}, separators=(",", ":"), sort_keys=True)
    except Exception:
        return "{}"


def sign_request(secret: str, method: str, path: str, body_json_str: str, ts: str, nonce: str) -> str:
    msg = "\n".join([method.upper(), path, ts, nonce, body_json_str])
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class Endpoint:
    method: str
    path: str


def default_endpoints() -> Dict[str, Endpoint]:
    return {
        "policies": Endpoint("GET", "/api/policies"),
        "task_submit": Endpoint("POST", "/api/tasks"),
        "task_status": Endpoint("GET", "/api/tasks/{task_id}"),
        "task_logs": Endpoint("GET", "/api/tasks/{task_id}/logs"),
        "task_artifact": Endpoint("POST", "/api/tasks/{task_id}/artifacts"),
    }


def validate_policy_doc(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(doc, dict):
        return False, ["policy must be an object"]
    version = doc.get("version")
    caps = doc.get("capabilities")
    if not isinstance(version, str) or not version.strip():
        errors.append("missing policy version")
    if not isinstance(caps, list):
        errors.append("capabilities must be a list")
    else:
        for i, c in enumerate(caps):
            if not isinstance(c, dict):
                errors.append(f"capabilities[{i}] must be an object")
                continue
            name = c.get("name")
            enabled = c.get("enabled")
            if not isinstance(name, str) or not name:
                errors.append(f"capabilities[{i}].name missing")
            if not isinstance(enabled, bool):
                errors.append(f"capabilities[{i}].enabled must be boolean")
    return (len(errors) == 0), errors


