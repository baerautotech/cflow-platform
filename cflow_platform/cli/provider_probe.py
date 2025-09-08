from __future__ import annotations

import argparse
import asyncio
import json

from cflow_platform.core.public_api import get_direct_client_executor


def cli() -> int:
    parser = argparse.ArgumentParser(description="Probe LLM provider (Gate P)")
    parser.add_argument("--model", default=None, help="Model ID (default env CFLOW_LLM_MODEL)")
    parser.add_argument("--prompt", default=None, help="Custom probe prompt (expects 'ok')")
    args = parser.parse_args()

    exec_fn = get_direct_client_executor()
    result = asyncio.get_event_loop().run_until_complete(
        exec_fn("llm_provider.probe", model=args.model, prompt=args.prompt)
    )
    print(json.dumps(result))
    return 0 if str(result.get("status")) == "success" else 2

