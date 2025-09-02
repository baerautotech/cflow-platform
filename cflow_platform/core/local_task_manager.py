from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import sqlite3
from datetime import datetime


class LocalTaskManager:
    """Minimal local-first task manager backed by SQLite.

    Schema:
      tasks(task_id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT,
            priority TEXT, created_at TEXT, updated_at TEXT, parentId TEXT)
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        # Prefer consolidated .cerebraflow dir; migrate legacy .cflow if present
        repo_root = Path.cwd()
        new_base = repo_root / ".cerebraflow"
        old_base = repo_root / ".cflow"
        new_base.mkdir(parents=True, exist_ok=True)
        candidate = new_base / "tasks.db"
        if not candidate.exists():
            legacy = old_base / "tasks.db"
            if legacy.exists():
                try:
                    legacy.rename(candidate)
                except Exception:
                    pass
        self.db_path = db_path or candidate
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    status TEXT,
                    priority TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    parentId TEXT
                )
                """
            )
            conn.commit()

    def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at ASC", (status,))
            return [dict(row) for row in cur.fetchall()]

    def list_all(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC")
            return [dict(row) for row in cur.fetchall()]

    def get_task(self, task_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else {}

    def add_task(self, title: str, description: str, priority: str = "medium") -> str:
        task_id = f"T{int(datetime.now().timestamp()*1000)}"
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks(task_id, title, description, status, priority, created_at, updated_at, parentId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, title, description, "pending", priority, now, now, None),
            )
            conn.commit()
        return task_id

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return True
        fields = []
        values: List[Any] = []
        for k, v in updates.items():
            if k == "task_id":
                continue
            fields.append(f"{k} = ?")
            values.append(v)
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(task_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE task_id = ?", tuple(values))
            conn.commit()
            return cur.rowcount > 0

    def update_status(self, task_id: str, status: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                (status, datetime.now().isoformat(), task_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_task(self, task_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            return cur.rowcount > 0


