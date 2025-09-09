from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import ast
import re


@dataclass
class FunctionInfo:
    name: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str]


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_python_functions(file_path: Path, content: str) -> List[FunctionInfo]:
    results: List[FunctionInfo] = []
    try:
        tree = ast.parse(content)
    except Exception:
        return results

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # type: ignore[override]
            doc = ast.get_docstring(node)
            # Build a simple signature string
            try:
                args = []
                for a in node.args.args:
                    args.append(a.arg)
                if node.args.vararg is not None:
                    args.append("*" + node.args.vararg.arg)
                for a in node.args.kwonlyargs:
                    args.append(a.arg)
                if node.args.kwarg is not None:
                    args.append("**" + node.args.kwarg.arg)
                signature = f"{node.name}({', '.join(args)})"
            except Exception:
                signature = node.name + "(...)"

            # end_lineno is available in py3.8+ when ast.parse is given full content
            start_line = getattr(node, "lineno", 1)
            end_line = getattr(node, "end_lineno", start_line)
            results.append(
                FunctionInfo(
                    name=node.name,
                    file_path=str(file_path),
                    language="python",
                    start_line=start_line,
                    end_line=end_line,
                    signature=signature,
                    docstring=doc,
                )
            )
            self.generic_visit(node)

    try:
        Visitor().visit(tree)
    except RecursionError:
        return results
    return results


_TS_FUNC_RE = re.compile(
    r"(?P<prefix>export\s+)?function\s+(?P<name>[A-Za-z_\$][A-Za-z0-9_\$]*)\s*\((?P<args>[^)]*)\)",
    re.MULTILINE,
)


def _line_spans(content: str, name: str, start_index: int) -> Tuple[int, int]:
    # Best-effort: determine start/end lines by finding the next closing brace at same nesting level
    # If we cannot reliably find it, return a small span
    lines = content.splitlines()
    line_no = content.count("\n", 0, start_index) + 1
    # naive brace matching from first '{' after start_index
    brace_pos = content.find("{", start_index)
    if brace_pos == -1:
        return line_no, max(line_no, line_no + 1)
    nesting = 0
    i = brace_pos
    end_char_index = len(content) - 1
    while i < len(content):
        ch = content[i]
        if ch == '{':
            nesting += 1
        elif ch == '}':
            nesting -= 1
            if nesting == 0:
                end_char_index = i
                break
        i += 1
    end_line = content.count("\n", 0, end_char_index) + 1
    return line_no, max(line_no, end_line)


def _extract_ts_js_functions(file_path: Path, content: str, language: str) -> List[FunctionInfo]:
    results: List[FunctionInfo] = []
    for m in _TS_FUNC_RE.finditer(content):
        name = m.group("name")
        args = m.group("args")
        start, end = _line_spans(content, name, m.start())
        signature = f"{name}({args.strip()})"
        results.append(
            FunctionInfo(
                name=name,
                file_path=str(file_path),
                language=language,
                start_line=start,
                end_line=end,
                signature=signature,
                docstring=None,
            )
        )
    return results


def extract_functions(file_path: Path, content: Optional[str] = None) -> List[FunctionInfo]:
    if content is None:
        content = _read_file(file_path)
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return _extract_python_functions(file_path, content)
    if suffix in {".ts", ".tsx"}:
        return _extract_ts_js_functions(file_path, content, "typescript")
    if suffix in {".js", ".jsx"}:
        return _extract_ts_js_functions(file_path, content, "javascript")
    return []


