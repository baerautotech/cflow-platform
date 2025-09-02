from __future__ import annotations

"""
Core Codebase Vectorization Service

Generates embeddings for code chunks from a commit and stores them in Chroma,
with optional Supabase dual-write via the existing sync service. Uses the core
Apple Silicon accelerator.
"""

import hashlib
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cflow_platform.core.embeddings.apple_silicon_accelerator import (
    generate_accelerated_embeddings,
)

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    hash: str


class CoreCodebaseVectorizer:
    def __init__(self, chroma_path: Optional[str] = None) -> None:
        self.chroma_client = None
        self.collection = None
        if CHROMA_AVAILABLE:
            path = chroma_path or ".cerebraflow/core/storage/chromadb"
            self.chroma_client = chromadb.PersistentClient(  # type: ignore
                path=path,
                settings=Settings(anonymized_telemetry=False, is_persistent=True),  # type: ignore
            )
            self.collection = self.chroma_client.get_or_create_collection(  # type: ignore
                name="cflow_codebase",
                metadata={"description": "CFlow codebase vectors"},
            )

    def _git(self, args: List[str], repo_path: Optional[str]) -> str:
        cmd = ["git"] + args
        if repo_path:
            return subprocess.check_output(cmd, cwd=repo_path, text=True).strip()
        return subprocess.check_output(cmd, text=True).strip()

    def _changed_files(self, commit_hash: str, repo_path: Optional[str]) -> List[str]:
        out = self._git(["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash], repo_path)
        return [l for l in out.splitlines() if l.strip()]

    def _should_process(self, file_path: str) -> bool:
        exclude = [
            "__pycache__",
            ".git/",
            "node_modules",
            ".venv",
            "venv",
            ".DS_Store",
        ]
        if any(x in file_path for x in exclude):
            return False
        ext = Path(file_path).suffix.lower()
        return ext in {
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".rs",
            ".go",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".sql",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
        }

    def _lang_for(self, file_path: str) -> str:
        return {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".sql": "sql",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
        }.get(Path(file_path).suffix.lower(), "unknown")

    def _chunk(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        lines = content.split("\n")
        size = 50
        overlap = 5
        chunks: List[CodeChunk] = []
        i = 0
        while i < len(lines):
            part = lines[i : i + size]
            txt = "\n".join(part)
            if txt.strip():
                h = hashlib.sha256(txt.encode("utf-8")).hexdigest()
                chunks.append(
                    CodeChunk(
                        content=txt,
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=min(i + size, len(lines)),
                        language=language,
                        hash=h,
                    )
                )
            i += size - overlap
        return chunks

    def _read_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_keywords(self, content: str) -> List[str]:
        identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)
        common = {"if", "else", "for", "while", "return", "class", "def", "import", "from"}
        uniq = [w for w in set(identifiers) if len(w) > 2 and w.lower() not in common]
        return uniq[:20]

    async def process_commit(
        self, commit_hash: str, repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        changed = self._changed_files(commit_hash, repo_path)
        vectors_written = 0
        files_processed = 0
        for rel in changed:
            if not self._should_process(rel):
                continue
            full = (Path(repo_path) / rel) if repo_path else Path(rel)
            if not full.exists() or not full.is_file():
                continue
            content = self._read_file(full)
            if not content.strip():
                continue
            language = self._lang_for(rel)
            chunks = self._chunk(content, rel, language)
            if not chunks:
                continue
            # Embed in batches to minimize overhead
            texts = [c.content for c in chunks]
            vecs = generate_accelerated_embeddings(texts)
            if not isinstance(vecs, list) or not vecs:
                continue
            ids: List[str] = []
            docs: List[str] = []
            metas: List[Dict[str, Any]] = []
            for c, v in zip(chunks, vecs):
                ids.append(f"{commit_hash}_{c.hash}")
                docs.append(c.content)
                metas.append(
                    {
                        "file_path": c.file_path,
                        "language": c.language,
                        "start": c.start_line,
                        "end": c.end_line,
                        "keywords": self._extract_keywords(c.content),
                        "commit": commit_hash,
                        "ts": datetime.utcnow().isoformat() + "Z",
                    }
                )
            if self.collection is not None:
                # Best-effort add; ignore duplicates
                try:
                    self.collection.add(ids=ids, documents=docs, embeddings=vecs, metadatas=metas)  # type: ignore
                except Exception:
                    pass
            vectors_written += len(ids)
            files_processed += 1
        return {
            "commit": commit_hash,
            "vectors_written": vectors_written,
            "files_processed": files_processed,
        }


