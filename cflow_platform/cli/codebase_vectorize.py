from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from cflow_platform.core.services.enterprise_codebase_vectorization_service import (
    CoreCodebaseVectorizer,
)


async def _run(commit: str, repo: str | None, chroma_path: str | None) -> dict[str, Any]:
    svc = CoreCodebaseVectorizer(chroma_path=chroma_path)
    return await svc.process_commit(commit_hash=commit, repo_path=repo)


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow codebase vectorization (core)")
    parser.add_argument("--commit", required=True, help="Git commit hash to process")
    parser.add_argument("--repo", default=None, help="Path to git repo (defaults to CWD)")
    parser.add_argument("--chroma-path", default=None, help="Chroma persistence path")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    result = asyncio.get_event_loop().run_until_complete(
        _run(args.commit, args.repo, args.chroma_path)
    )
    if args.json:
        print(json.dumps(result))
    else:
        print(
            f"commit={result.get('commit')} files_processed={result.get('files_processed')} "
            f"vectors_written={result.get('vectors_written')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


