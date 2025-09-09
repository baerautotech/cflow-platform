from __future__ import annotations

import argparse
import asyncio
import json
import os

from cflow_platform.core.public_api import get_direct_client_executor


async def _run(query: str, limit: int, min_score: float) -> dict:
    dc = get_direct_client_executor()
    res = await dc(
        "memory_search",
        query=query,
        userId=os.getenv("CEREBRAL_USER_ID", "system"),
        limit=int(limit),
        min_score=float(min_score),
    )
    return res


def cli() -> int:
    p = argparse.ArgumentParser(description="Query CerebralMemory KG via memory_search")
    p.add_argument("query", help="query text")
    p.add_argument("--limit", type=int, default=5, help="max results")
    p.add_argument("--min-score", type=float, default=0.0, help="minimum similarity score (0.0-1.0)")
    args = p.parse_args()
    res = asyncio.get_event_loop().run_until_complete(_run(args.query, args.limit, args.min_score))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


