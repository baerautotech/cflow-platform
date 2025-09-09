from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import json


@dataclass
class StoredEdge:
    caller_id: str
    caller_name: str
    caller_path: str
    callee_name: str


class InMemoryCallGraph:
    def __init__(self) -> None:
        self.adj: Dict[str, List[StoredEdge]] = {}

    def add_edge(self, edge: StoredEdge) -> None:
        self.adj.setdefault(edge.caller_id, []).append(edge)

    def reverse_index(self) -> Dict[str, List[StoredEdge]]:
        rev: Dict[str, List[StoredEdge]] = {}
        for edges in self.adj.values():
            for e in edges:
                rev.setdefault(e.callee_name, []).append(e)
        return rev

    def call_paths_to(self, target_name: str, max_depth: int = 6) -> List[List[StoredEdge]]:
        rev = self.reverse_index()
        starts = rev.get(target_name, [])
        # DFS backwards along caller chains based on name match only (best-effort)
        paths: List[List[StoredEdge]] = []
        visited: Set[Tuple[str, str]] = set()

        def dfs(edge: StoredEdge, path: List[StoredEdge], depth: int) -> None:
            if depth > max_depth:
                paths.append(list(path))
                return
            key = (edge.caller_id, edge.callee_name)
            if key in visited:
                paths.append(list(path))
                return
            visited.add(key)
            # find callers of this caller by matching callee_name == caller name
            callers = rev.get(edge.caller_name, [])
            if not callers:
                paths.append(list(path))
                return
            for up in callers:
                path.append(up)
                dfs(up, path, depth + 1)
                path.pop()

        for s in starts:
            dfs(s, [s], 1)
        return paths


class FileCallGraphStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        base = path or Path.cwd() / ".cerebraflow" / "core" / "storage" / "callgraph.jsonl"
        self.path = base
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_edges(self, edges: List[StoredEdge]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for e in edges:
                f.write(json.dumps({
                    "caller_id": e.caller_id,
                    "caller_name": e.caller_name,
                    "caller_path": e.caller_path,
                    "callee_name": e.callee_name,
                }) + "\n")

    def load_graph(self) -> InMemoryCallGraph:
        g = InMemoryCallGraph()
        if not self.path.exists():
            return g
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    g.add_edge(StoredEdge(
                        caller_id=obj.get("caller_id", ""),
                        caller_name=obj.get("caller_name", ""),
                        caller_path=obj.get("caller_path", ""),
                        callee_name=obj.get("callee_name", ""),
                    ))
                except Exception:
                    continue
        return g


