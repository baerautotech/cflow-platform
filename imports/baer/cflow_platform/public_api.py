"""Thin wrapper re-exporting the CFlow public API from the monorepo path.

This allows early adoption of the import path `cflow_platform.public_api` while
the code still lives under `.cerebraflow/` during Phase 1.
"""

from typing import Any, Callable, Dict
from .core.public_api import get_direct_client_executor as _get_exec


def get_direct_client_executor() -> Callable[..., Any]:
    return _get_exec()


