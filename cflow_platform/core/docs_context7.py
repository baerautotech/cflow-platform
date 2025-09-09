from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple
import os
import re
import json
from .failure_parser import parse_pytest_failures


def _unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for it in items:
        if not it:
            continue
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def extract_symbols_from_failure_report(failure_report: Dict[str, Any], max_symbols: int = 8) -> List[str]:
    """Extract likely library/API symbols from a parsed pytest failure report.

    Accepts the structure returned by `failure_parser.parse_pytest_failures`:
    {"failures": [{"error_type", "message", "top_trace": [...]}]}
    """
    candidates: List[str] = []

    def extract_from_text(text: str) -> List[str]:
        found: List[str] = []
        # Patterns for common Python failure messages
        # 1) AttributeError: module 'X' has no attribute 'Y' → X.Y
        m = re.search(r"AttributeError:\s*(?:module\s+)?'([A-Za-z_][\w\.]*)'\s+has\s+no\s+attribute\s+'([A-Za-z_][\w\.]*)'", text)
        if m:
            found.append(f"{m.group(1)}.{m.group(2)}")
        # 2) ModuleNotFoundError: No module named 'X' → X
        m = re.search(r"ModuleNotFoundError:\s*No\s+module\s+named\s+'([A-Za-z_][\w\.]*)'", text)
        if m:
            found.append(m.group(1))
        # 3) ImportError: cannot import name 'X' from 'Y' → Y.X
        m = re.search(r"ImportError:\s*cannot\s+import\s+name\s+'([A-Za-z_][\w\.]*)'\s+from\s+'([A-Za-z_][\w\.]*)'", text)
        if m:
            found.append(f"{m.group(2)}.{m.group(1)}")
        # 4) NameError: name 'X' is not defined → X
        m = re.search(r"NameError:\s*name\s+'([A-Za-z_][\w\.]*)'\s+is\s+not\s+defined", text)
        if m:
            found.append(m.group(1))
        # 5) TypeError: X(...) ... → X
        m = re.search(r"TypeError:\s*([A-Za-z_][\w\.]*)\s*\(", text)
        if m:
            found.append(m.group(1))
        # 6) module.func( → module.func
        for mm in re.finditer(r"\b([a-zA-Z_][\w\.]*)\s*\(", text):
            token = mm.group(1)
            # Filter obvious test internals
            if token.startswith("assert") or token.startswith("pytest"):
                continue
            found.append(token)
        return found

    for f in failure_report.get("failures", []) or []:
        error_type = f.get("error_type") or ""
        message = f.get("message") or ""
        if error_type:
            candidates.extend(extract_from_text(str(error_type)))
        if message:
            candidates.extend(extract_from_text(str(message)))
        for line in f.get("top_trace", []) or []:
            candidates.extend(extract_from_text(str(line)))

    # Normalize: drop obvious Python builtins and overly generic tokens
    blacklist_prefixes = {"assert", "builtins", "unittest", "pytest", "_pytest"}
    filtered = []
    for c in candidates:
        if any(c.startswith(p) for p in blacklist_prefixes):
            continue
        # Skip single-letter tokens
        if len(c) <= 1:
            continue
        filtered.append(c)

    return _unique_preserve_order(filtered)[:max_symbols]


def fetch_context7_docs_for_symbols(symbols: List[str], *, per_symbol_limit: int = 2, timeout_sec: int = 6) -> Dict[str, Any]:
    """Fetch documentation excerpts and sources for symbols using a WebMCP Context7 endpoint.

    Environment:
    - CONTEXT7_WEBMCP_URL or WEBMCP_URL: endpoint to POST tool calls
    - CFLOW_CONTEXT7_FAKE=1: return deterministic fake docs (for tests/offline)
    """
    # Test-friendly fake mode to avoid network
    if os.getenv("CFLOW_CONTEXT7_FAKE", "").strip().lower() in {"1", "true", "yes"}:
        sources = [{"title": "Example Docs", "url": "https://docs.example.com"}]
        notes = [f"Docs for {s}: Example excerpt..." for s in symbols[:max(1, per_symbol_limit)]]
        return {"notes": notes, "sources": sources}

    webmcp = os.environ.get("CONTEXT7_WEBMCP_URL") or os.environ.get("WEBMCP_URL") or "http://localhost:30080/mcp/tools/call"
    # Optional auth/header support for public WebMCP gateways
    bearer_token = os.environ.get("CONTEXT7_BEARER_TOKEN") or os.environ.get("CONTEXT7_API_TOKEN") or ""
    custom_header_name = (os.environ.get("CONTEXT7_HEADER_NAME") or "").strip()
    custom_header_value = (os.environ.get("CONTEXT7_HEADER_VALUE") or "").strip()
    base_headers: Dict[str, str] = {"Content-Type": "application/json"}
    if bearer_token:
        # Provide both Authorization and X-API-Key to cover common gateway conventions
        base_headers["Authorization"] = f"Bearer {bearer_token}"
        base_headers["X-API-Key"] = bearer_token
    if custom_header_name and custom_header_value:
        base_headers[custom_header_name] = custom_header_value
    notes: List[str] = []
    sources: List[Dict[str, str]] = []
    try:
        import urllib.request as _http
        for sym in symbols[: max(1, len(symbols))]:
            payload = json.dumps({
                "name": "context7.search",
                "arguments": {
                    "query": f"{sym} Python API usage",
                    "limit": per_symbol_limit,
                },
            }).encode("utf-8")
            req = _http.Request(webmcp, data=payload, headers=base_headers, method="POST")
            with _http.urlopen(req, timeout=timeout_sec) as resp:
                raw = resp.read().decode("utf-8", "ignore")
                data = json.loads(raw)
                for item in (data.get("result", {}).get("content", []) or []):
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        if text:
                            notes.append(text[:800])
                    if isinstance(item, dict) and item.get("type") == "link":
                        sources.append({
                            "title": item.get("title", "ref"),
                            "url": item.get("href", ""),
                        })
    except Exception:
        # Best-effort; return what we have
        pass
    return {"notes": notes, "sources": _unique_preserve_order([json.dumps(s) for s in sources]) and sources}


def summarize_docs(notes: List[str], max_chars: int = 800) -> str:
    if not notes:
        return ""
    joined = "\n\n".join(notes)
    return joined[:max_chars]


def build_failure_report_from_test_result(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Construct a failure report compatible with `extract_symbols_from_failure_report`.

    - If `stdout` or `stderr` fields are present, parse with `parse_pytest_failures`.
    - Otherwise, attempt to join any per-test `longrepr` entries to produce a text blob.
    """
    stdout = test_result.get("stdout") or ""
    stderr = test_result.get("stderr") or ""
    if stdout or stderr:
        parsed = parse_pytest_failures((stdout or "") + "\n" + (stderr or ""))
        if parsed.get("failures"):
            return parsed
    # Fallback: synthesize from structured tests
    tests = test_result.get("tests") or []
    blob_parts: List[str] = []
    for t in tests:
        if t.get("outcome") != "passed" and t.get("longrepr"):
            blob_parts.append(str(t.get("longrepr")))
    if not blob_parts:
        return {"failures": [], "summary_line": test_result.get("summary", {}).get("exit_code", "")}
    text = "\n\n".join(blob_parts)
    parsed = parse_pytest_failures(text)
    if parsed.get("failures"):
        return parsed
    # As a last resort, fabricate a single failure entry with the collected text
    return {"failures": [{"error_type": "", "message": text, "top_trace": []}], "summary_line": ""}


