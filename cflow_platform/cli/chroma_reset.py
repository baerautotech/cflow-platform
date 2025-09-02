from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")


def reset_collections(chroma_path: Path, collections: List[str]) -> dict:
    from chromadb import PersistentClient  # type: ignore
    from chromadb.config import Settings  # type: ignore

    chroma_path.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(path=str(chroma_path), settings=Settings(anonymized_telemetry=False, allow_reset=False))
    report = {"dropped": [], "errors": []}
    for name in collections:
        try:
            try:
                col = client.get_collection(name)
                col.delete()
            except Exception:
                pass
            # ensure empty collection exists
            client.get_or_create_collection(name=name)
            report["dropped"].append(name)
        except Exception as e:
            report["errors"].append({"collection": name, "error": str(e)})
    return report


def cli() -> int:
    parser = argparse.ArgumentParser(description="Reset specified Chroma collections under .cerebraflow")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--collections", nargs="*", default=["cerebral_docs", "cerebral_tasks"])
    args = parser.parse_args()

    load_env()
    project_root = Path(args.project_root)
    chroma_path = project_root / ".cerebraflow" / "core" / "storage" / "chromadb"
    report = reset_collections(chroma_path, args.collections)
    print(json.dumps({"success": True, "report": report}))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


