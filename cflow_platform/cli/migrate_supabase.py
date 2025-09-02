from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def read_sql(sql_path: str) -> str:
    p = Path(sql_path)
    return p.read_text(encoding="utf-8")


def print_sql(sql: str) -> None:
    print(sql)


def apply_sql(sql: str, db_url: str) -> None:
    # Use psycopg3 if available; otherwise, print instructions
    try:
        import psycopg
    except Exception:
        raise SystemExit("psycopg is required to apply SQL. Install and re-run or use 'psql'.")
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)


def cli() -> int:
    parser = argparse.ArgumentParser(description="Apply Supabase migration for memory schema (tables, RLS, indexes, RPC)")
    default_sql = Path(__file__).resolve().parents[2] / "docs" / "agentic-plan" / "sql" / "001_memory_schema.sql"
    parser.add_argument("sql", nargs="?", default=str(default_sql))
    parser.add_argument("--apply", action="store_true", help="Apply SQL to database (requires SUPABASE_DB_URL)")
    args = parser.parse_args()

    # Load env per project memory policy
    load_dotenv(dotenv_path=Path.cwd() / ".env")  # repo-level .env
    load_dotenv(dotenv_path=Path.cwd() / ".cerebraflow" / ".env")  # optional override

    sql = read_sql(args.sql)
    if not args.apply:
        print_sql(sql)
        return 0

    db_url: Optional[str] = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise SystemExit("SUPABASE_DB_URL not set; set it or run without --apply to print SQL")
    apply_sql(sql, db_url)
    print("Migration applied successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())


