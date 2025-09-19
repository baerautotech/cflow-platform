from __future__ import annotations

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


def _normalize_rest_url(url: Optional[str], dsn: Optional[str], override: Optional[str]) -> Optional[str]:
    """Normalize Supabase REST base URL.

    - Accepts REST host, REST URL, or Postgres DSN
    - Strips db.<proj>.supabase.co → <proj>.supabase.co
    - Ensures https scheme
    """
    # Highest precedence: explicit override
    if override:
        url = override
    if url:
        u = url.strip()
        # Handle cases where a Postgres DSN was wrapped in http(s) (e.g., "https://postgresql://...")
        if "://postgres" in u:
            try:
                # Strip leading scheme so we can parse DSN
                u2 = u.split("://", 1)[1]
                if not u2.startswith("postgres"):
                    u2 = "postgresql://" + u2
                from urllib.parse import urlparse
                p = urlparse(u2)
                host = p.hostname or ""
                if host.startswith("db.") and host.endswith(".supabase.co"):
                    host = host[len("db."):]
                if host.endswith(".supabase.co"):
                    return f"https://{host}"
            except Exception:
                pass
        if not u.startswith("http://") and not u.startswith("https://"):
            u = f"https://{u}"
        try:
            from urllib.parse import urlparse, urlunparse
            p = urlparse(u)
            host = p.netloc
            if host.startswith("db.") and host.endswith(".supabase.co"):
                host = host[len("db."):]
            return urlunparse(p._replace(netloc=host, path="", params="", query="", fragment=""))
        except Exception:
            return u
    # Derive from DSN
    if dsn:
        try:
            from urllib.parse import urlparse
            p = urlparse(dsn)
            host = p.hostname or ""
            if host.startswith("db.") and host.endswith(".supabase.co"):
                host = host[len("db."):]
            if host.endswith(".supabase.co"):
                return f"https://{host}"
        except Exception:
            pass
    return None


def get_rest_url() -> Optional[str]:
    return _normalize_rest_url(
        url=(
            os.getenv("CEREBRAL_SUPABASE_URL")
            or os.getenv("SUPABASE_URL")
            or os.getenv("CEREBRAL_SUPABASE_REST_URL")
            or os.getenv("SUPABASE_REST_URL")
        ),
        dsn=(os.getenv("CEREBRAL_SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")),
        override=(os.getenv("SUPABASE_REST_URL") or os.getenv("CEREBRAL_SUPABASE_REST_URL")),
    )


def is_secure_mode() -> bool:
    val = os.getenv("CFLOW_SECURE_MODE", "").strip().lower()
    return val in {"1", "true", "yes", "on"}


def get_api_key(secure: Optional[bool] = None) -> Optional[str]:
    if secure is None:
        secure = is_secure_mode()
    if secure:
        return (
            os.getenv("CEREBRAL_SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("CEREBRAL_SUPABASE_KEY")
            or os.getenv("SUPABASE_KEY")
        )
    return (
        os.getenv("CEREBRAL_SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("CEREBRAL_SUPABASE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("CEREBRAL_SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )


def get_tenant_id() -> Optional[str]:
    return os.getenv("CEREBRAL_TENANT_ID") or os.getenv("CFLOW_TENANT_ID")


def get_edge_url() -> Optional[str]:
    """Return fully qualified Edge Function URL if configured.

    Accepts CEREBRAL_EDGE_URL or SUPABASE_EDGE_URL; caller should POST to it directly.
    """
    u = (
        os.getenv("CEREBRAL_EDGE_URL")
        or os.getenv("SUPABASE_EDGE_URL")
        or os.getenv("CEREBRAL_SUPABASE_EDGE_URL")
        or os.getenv("EDGE_FUNCTION_URL")
    )
    return u.strip() if u else None


def get_edge_key() -> Optional[str]:
    """Return auth key for Edge Function if configured.

    Falls back to API key to avoid breakage, but prefer a dedicated edge key.
    """
    return (
        os.getenv("CEREBRAL_EDGE_KEY")
        or os.getenv("SUPABASE_EDGE_KEY")
        or os.getenv("EDGE_FUNCTION_KEY")
        or get_api_key()
    )


