from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import ast
import subprocess

from cflow_platform.core.code_intel.function_extractor import extract_functions, FunctionInfo


@dataclass
class CallEdge:
    caller_id: str
    callee_name: str
    caller: FunctionInfo


def _python_call_edges(file_path: Path, content: str, functions: List[FunctionInfo]) -> List[CallEdge]:
    results: List[CallEdge] = []
    try:
        tree = ast.parse(content)
    except Exception:
        return results

    # Build quick lookup of function spans to map calls to caller function
    spans: List[Tuple[FunctionInfo, int, int]] = []
    for f in functions:
        if f.language != "python":
            continue
        spans.append((f, f.start_line, f.end_line))

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            super().__init__()
            self.current_line = 1

        def visit(self, node: ast.AST) -> None:  # type: ignore[override]
            self.current_line = getattr(node, "lineno", self.current_line)
            super().visit(node)

        def visit_Call(self, node: ast.Call) -> None:  # type: ignore[override]
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name:
                # find enclosing function by line
                for f, start, end in spans:
                    if start <= self.current_line <= end:
                        results.append(CallEdge(caller_id=f"{f.file_path}:{f.name}:{f.start_line}-{f.end_line}", callee_name=name, caller=f))
                        break
            self.generic_visit(node)

    try:
        Visitor().visit(tree)
    except RecursionError:
        return results
    return results


def build_call_edges(file_path: Path, content: str) -> List[CallEdge]:
    fns = extract_functions(file_path, content)
    if not fns:
        return []
    if file_path.suffix.lower() == ".py":
        return _python_call_edges(file_path, content, fns)
    if file_path.suffix.lower() in {".ts", ".tsx"}:
        # Use ts-morph via a small Node helper if available (optional)
        try:
            helper = Path.cwd() / "vendor" / "cerebral" / "ts_callgraph.js"
            if helper.exists():
                out = subprocess.check_output(["node", str(helper), str(file_path)], text=True)
                # Helper should emit JSON lines: { caller_id, caller_name, caller_path, callee_name }
                edges: List[CallEdge] = []
                for line in out.splitlines():
                    try:
                        import json
                        obj = json.loads(line)
                        # Minimal mapping back to FunctionInfo for compatibility
                        fi = FunctionInfo(
                            name=obj.get("caller_name", ""),
                            file_path=obj.get("caller_path", str(file_path)),
                            language="typescript",
                            start_line=1,
                            end_line=1,
                            signature=obj.get("caller_name", "") + "(...)",
                            docstring=None,
                        )
                        edges.append(CallEdge(caller_id=obj.get("caller_id", ""), callee_name=obj.get("callee_name", ""), caller=fi))
                    except Exception:
                        continue
                return edges
        except Exception:
            return []
    return []


