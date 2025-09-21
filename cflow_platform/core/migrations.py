"""
BMAD Database Migrations

DEPRECATED: This module is deprecated. Use cflow_platform.core.unified_database_schema instead.

Database migration utilities for BMAD.
"""

from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def apply_migration(name: str, query: str) -> bool:
    """Apply a database migration."""
    try:
        from .config.supabase_config import get_api_key, get_rest_url
        from supabase import create_client
        
        url = get_rest_url()
        key = get_api_key(secure=True)
        
        if not url or not key:
            print(f"[INFO][INFO] Migration: Supabase not available for migration {name}")
            return False
        
        client = create_client(url, key)
        
        # Execute the migration query
        result = client.rpc('run_sql', {'sql': query}).execute()
        
        print(f"[INFO] Migration: Applied migration {name}")
        return True
        
    except Exception as e:
        print(f"[INFO] Migration: Failed to apply migration {name}: {e}")
        return False


def list_migrations() -> list:
    """List applied migrations."""
    try:
        from .config.supabase_config import get_api_key, get_rest_url
        from supabase import create_client
        
        url = get_rest_url()
        key = get_api_key(secure=True)
        
        if not url or not key:
            return []
        
        client = create_client(url, key)
        
        # Query migrations table
        result = client.table("migrations").select("*").execute()
        return result.data
        
    except Exception as e:
        print(f"[INFO] Migration: Failed to list migrations: {e}")
        return []

