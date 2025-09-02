from __future__ import annotations

from typing import Any, Dict, List
import re


def parse_pytest_failures(pytest_output: str, max_trace_lines: int = 20) -> Dict[str, Any]:
    """
    Parse pytest textual output into a structured failure report.

    Returns a dictionary containing a list of failures and a best-effort summary line.
    Each failure includes: test_id, file_path, node_id, error_type, message, and top_trace.
    """
    failures: List[Dict[str, Any]] = []
    summary_line = ""

    # 1) Short summary parsing (robust across pytest versions)
    short_summary_start = re.compile(r"^=+\s*short test summary info\s*=+", re.IGNORECASE)
    failed_line = re.compile(r"^FAILED\s+(.+?)\s*(?:-\s+([^:]+)\s*:?\s*(.*))?$")

    in_short = False
    for line in pytest_output.splitlines():
        if short_summary_start.search(line.strip()):
            in_short = True
            continue
        if in_short and line.strip().startswith("===="):  # next section delimiter
            in_short = False
            continue
        if in_short:
            m = failed_line.match(line.strip())
            if m:
                location = m.group(1) or ""
                error_type = (m.group(2) or "").strip()
                message = (m.group(3) or "").strip()
                file_path, node_id = _split_location(location)
                failures.append({
                    "test_id": location,
                    "file_path": file_path,
                    "node_id": node_id,
                    "error_type": error_type,
                    "message": message,
                    "top_trace": [],  # filled below via FAILURES section if available
                })

        # capture a best-effort overall summary line
        if re.search(r"\b(no tests ran|passed|failed|errors?|skipped|xfailed|xpassed)\b", line, re.IGNORECASE):
            summary_line = line.strip()

    # 2) FAILURES section parsing for top traces
    failures_section_start = re.compile(r"^=+\s*FAILURES\s*=+", re.IGNORECASE)
    underline_re = re.compile(r"^_+")
    in_failures = False
    current_block: List[str] = []
    collected_blocks: List[List[str]] = []
    for raw in pytest_output.splitlines():
        line = raw.rstrip("\n")
        if failures_section_start.search(line.strip()):
            in_failures = True
            current_block = []
            collected_blocks = []
            continue
        if in_failures:
            if underline_re.match(line.strip()):
                # boundary between failure entries
                if current_block:
                    collected_blocks.append(current_block)
                    current_block = []
                continue
            # end of FAILURES section when next header starts
            if line.strip().startswith("=") and "short test summary" in line.lower():
                if current_block:
                    collected_blocks.append(current_block)
                in_failures = False
                continue
            current_block.append(line)

    if in_failures and current_block:
        collected_blocks.append(current_block)

    # Map blocks to failures by matching the first non-empty line containing path::node
    for block in collected_blocks:
        header_line = _find_header_line(block)
        if not header_line:
            continue
        file_path, node_id = _split_location(header_line)
        # find matching failure by file/node
        for f in failures:
            if f.get("file_path") == file_path and f.get("node_id") == node_id:
                f["top_trace"] = _extract_top_trace(block, max_trace_lines)
                # try to refine error_type/message from block tail if previously empty
                if not f.get("error_type") or not f.get("message"):
                    etype, msg = _extract_error_from_block(block)
                    if etype:
                        f["error_type"] = etype
                    if msg:
                        f["message"] = msg
                break

    # De-duplicate by (file_path, node_id)
    unique: Dict[str, Dict[str, Any]] = {}
    for f in failures:
        key = f"{f.get('file_path')}::{f.get('node_id')}"
        if key not in unique:
            unique[key] = f

    return {"failures": list(unique.values()), "summary_line": summary_line}


def _split_location(location: str) -> tuple[str, str]:
    # Handles cases like path/to/test_file.py::TestClass::test_name[param]
    if "::" in location:
        parts = location.split("::", 1)
        return parts[0], parts[1]
    return location, ""


def _find_header_line(block: List[str]) -> str | None:
    # First non-empty line that looks like a location header
    for line in block:
        s = line.strip()
        if s and "::" in s and s.endswith(""):
            return s
    return None


def _extract_top_trace(block: List[str], max_lines: int) -> List[str]:
    # Take the last max_lines of the block, filtering header-like lines
    trace = [ln for ln in block if not ln.strip().startswith("_")]
    return trace[-max_lines:]


def _extract_error_from_block(block: List[str]) -> tuple[str, str]:
    # Look for "ErrorType: message" at the tail of the block
    tail = "\n".join(block[-30:])
    m = re.search(r"\n([A-Za-z_][A-Za-z0-9_\.]*):\s*(.+)$", tail)
    if m:
        return m.group(1), m.group(2)
    return "", ""


