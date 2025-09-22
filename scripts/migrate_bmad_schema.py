#!/usr/bin/env python3
"""
BMAD Database Schema Migration Script

This script applies the BMAD artifacts database schema to Supabase.
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path
import httpx
from typing import Optional

# Add the parent directory to the path to import cflow_platform modules
sys.path.insert(0, str(Path(__file__).parent.parent))


async def apply_migration(
    supabase_url: str,
    supabase_key: str,
    schema_file: str = "docs/agentic-plan/sql/004_bmad_artifacts_schema.sql"
) -> bool:
    """
    Apply the BMAD schema migration to Supabase.
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        schema_file: Path to SQL schema file
        
    Returns:
        Success status
    """
    try:
        # Read the SQL schema file
        schema_path = Path(__file__).parent.parent / schema_file
        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            sql_content = f.read()
        
        print(f"📄 Loaded schema file: {schema_path}")
        print(f"📊 SQL content length: {len(sql_content)} characters")
        
        # Apply migration using Supabase REST API
        async with httpx.AsyncClient() as client:
            # Execute the SQL using Supabase's SQL execution endpoint
            response = await client.post(
                f"{supabase_url}/rest/v1/rpc/run_sql",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": sql_content
                }
            )
            
            if response.status_code == 200:
                print("✅ Migration applied successfully!")
                return True
            else:
                print(f"❌ Migration failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        return False


async def verify_migration(supabase_url: str, supabase_key: str) -> bool:
    """
    Verify that the migration was applied successfully.
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        
    Returns:
        Verification status
    """
    try:
        print("🔍 Verifying migration...")
        
        async with httpx.AsyncClient() as client:
            # Check if cerebral_documents table exists
            response = await client.get(
                f"{supabase_url}/rest/v1/cerebral_documents?limit=1",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
            )
            
            if response.status_code == 200:
                print("✅ cerebral_documents table exists")
            else:
                print(f"❌ cerebral_documents table not found: {response.status_code}")
                return False
            
            # Check if cerebral_tasks table exists
            response = await client.get(
                f"{supabase_url}/rest/v1/cerebral_tasks?limit=1",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
            )
            
            if response.status_code == 200:
                print("✅ cerebral_tasks table exists")
            else:
                print(f"❌ cerebral_tasks table not found: {response.status_code}")
                return False
            
            # Check if cerebral_activities table exists
            response = await client.get(
                f"{supabase_url}/rest/v1/cerebral_activities?limit=1",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
            )
            
            if response.status_code == 200:
                print("✅ cerebral_activities table exists")
            else:
                print(f"❌ cerebral_activities table not found: {response.status_code}")
                return False
            
            # Check if cerebral_projects table exists
            response = await client.get(
                f"{supabase_url}/rest/v1/cerebral_projects?limit=1",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
            )
            
            if response.status_code == 200:
                print("✅ cerebral_projects table exists")
            else:
                print(f"❌ cerebral_projects table not found: {response.status_code}")
                return False
            
            print("✅ All BMAD tables verified successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


async def test_bmad_functions(supabase_url: str, supabase_key: str) -> bool:
    """
    Test BMAD-specific functions.
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        
    Returns:
        Test status
    """
    try:
        print("🧪 Testing BMAD functions...")
        
        async with httpx.AsyncClient() as client:
            # Test create_bmad_document function
            test_tenant_id = "00000000-0000-0000-0000-000000000001"
            test_project_id = "00000000-0000-0000-0000-000000000002"
            
            response = await client.post(
                f"{supabase_url}/rest/v1/rpc/create_bmad_document",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "p_tenant_id": test_tenant_id,
                    "p_project_id": test_project_id,
                    "p_type": "PRD",
                    "p_title": "Test PRD Document",
                    "p_content": "This is a test PRD document content.",
                    "p_metadata": {"test": True},
                    "p_artifacts": {"template": "test"},
                    "p_bmad_template": "test-tmpl.yaml",
                    "p_bmad_workflow": "test-workflow.yaml",
                    "p_authored_by": test_tenant_id
                }
            )
            
            if response.status_code == 200:
                doc_id = response.text.strip('"')
                print(f"✅ create_bmad_document function works (created doc: {doc_id})")
                
                # Clean up test document
                await client.delete(
                    f"{supabase_url}/rest/v1/cerebral_documents?doc_id=eq.{doc_id}",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}"
                    }
                )
                print("🧹 Cleaned up test document")
                
            else:
                print(f"❌ create_bmad_document function failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            print("✅ All BMAD functions tested successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Function testing failed: {e}")
        return False


def load_env_vars() -> tuple[Optional[str], Optional[str]]:
    """Load Supabase environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL environment variable not set")
        return None, None
    
    if not supabase_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY environment variable not set")
        return None, None
    
    return supabase_url, supabase_key


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="BMAD Database Schema Migration")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing migration")
    parser.add_argument("--test-only", action="store_true", help="Only test BMAD functions")
    parser.add_argument("--schema-file", default="docs/agentic-plan/sql/004_bmad_artifacts_schema.sql",
                       help="Path to SQL schema file")
    
    args = parser.parse_args()
    
    print("🚀 BMAD Database Schema Migration")
    print("=" * 50)
    
    # Load environment variables
    supabase_url, supabase_key = load_env_vars()
    if not supabase_url or not supabase_key:
        return 1
    
    print(f"📡 Supabase URL: {supabase_url}")
    print(f"🔑 Using service role key: {'*' * 20}...")
    
    success = True
    
    if args.verify_only:
        print("\n🔍 Verification mode")
        success = await verify_migration(supabase_url, supabase_key)
    elif args.test_only:
        print("\n🧪 Testing mode")
        success = await test_bmad_functions(supabase_url, supabase_key)
    else:
        print("\n📦 Migration mode")
        
        # Apply migration
        migration_success = await apply_migration(supabase_url, supabase_key, args.schema_file)
        if not migration_success:
            success = False
        else:
            # Verify migration
            verify_success = await verify_migration(supabase_url, supabase_key)
            if not verify_success:
                success = False
            else:
                # Test functions
                test_success = await test_bmad_functions(supabase_url, supabase_key)
                if not test_success:
                    success = False
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\n📖 Next steps:")
        print("1. Update BMAD API service to use the new database integration")
        print("2. Test document creation and retrieval")
        print("3. Verify RAG indexing is working")
        print("4. Test task generation from stories")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
