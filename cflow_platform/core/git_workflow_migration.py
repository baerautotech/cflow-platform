"""
BMAD Git Workflow Database Migration

⚠️  DEPRECATED: This module is deprecated. Use cflow_platform.core.unified_database_schema instead.

This module creates the necessary database tables for BMAD git workflow tracking.
"""

import asyncio
from typing import Dict, Any
from cflow_platform.core.config.supabase_config import get_api_key, get_rest_url
from supabase import create_client


class GitWorkflowMigration:
    """Migration for BMAD git workflow tables."""
    
    def __init__(self):
        self.supabase_client = None
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Create and cache a Supabase client."""
        if self.supabase_client is not None:
            return
        
        try:
            api_key = get_api_key()
            rest_url = get_rest_url()
            self.supabase_client = create_client(rest_url, api_key)
        except Exception as e:
            print(f"Warning: Supabase client not available: {e}")
            self.supabase_client = None
    
    async def create_git_workflow_tables(self) -> Dict[str, Any]:
        """Create tables for BMAD git workflow tracking."""
        if not self.supabase_client:
            return {
                "success": False,
                "error": "Supabase client not available"
            }
        
        try:
            results = {}
            
            # Create bmad_commit_tracking table
            commit_tracking_sql = """
            CREATE TABLE IF NOT EXISTS bmad_commit_tracking (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                commit_hash TEXT NOT NULL,
                branch TEXT NOT NULL,
                commit_message TEXT NOT NULL,
                document_ids TEXT[] DEFAULT '{}',
                validation_results JSONB DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'committed',
                pushed BOOLEAN DEFAULT FALSE,
                push_output TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_bmad_commit_tracking_workflow_id 
                ON bmad_commit_tracking(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_commit_tracking_project_id 
                ON bmad_commit_tracking(project_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_commit_tracking_created_at 
                ON bmad_commit_tracking(created_at DESC);
            """
            
            commit_result = self.supabase_client.rpc('run_sql', {'sql': commit_tracking_sql}).execute()
            results["bmad_commit_tracking"] = {
                "success": True,
                "message": "bmad_commit_tracking table created successfully"
            }
            
            # Create bmad_validation_results table
            validation_results_sql = """
            CREATE TABLE IF NOT EXISTS bmad_validation_results (
                validation_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                validation_type TEXT NOT NULL DEFAULT 'comprehensive',
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                checks JSONB DEFAULT '{}',
                overall_status TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_bmad_validation_results_workflow_id 
                ON bmad_validation_results(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_validation_results_project_id 
                ON bmad_validation_results(project_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_validation_results_timestamp 
                ON bmad_validation_results(timestamp DESC);
            """
            
            validation_result = self.supabase_client.rpc('run_sql', {'sql': validation_results_sql}).execute()
            results["bmad_validation_results"] = {
                "success": True,
                "message": "bmad_validation_results table created successfully"
            }
            
            # Create bmad_git_workflow_status table for tracking workflow states
            workflow_status_sql = """
            CREATE TABLE IF NOT EXISTS bmad_git_workflow_status (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                current_step TEXT,
                last_commit_hash TEXT,
                last_push_hash TEXT,
                validation_status TEXT,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_bmad_git_workflow_status_workflow_id 
                ON bmad_git_workflow_status(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_git_workflow_status_project_id 
                ON bmad_git_workflow_status(project_id);
            CREATE INDEX IF NOT EXISTS idx_bmad_git_workflow_status_status 
                ON bmad_git_workflow_status(status);
            """
            
            status_result = self.supabase_client.rpc('run_sql', {'sql': workflow_status_sql}).execute()
            results["bmad_git_workflow_status"] = {
                "success": True,
                "message": "bmad_git_workflow_status table created successfully"
            }
            
            return {
                "success": True,
                "message": "All git workflow tables created successfully",
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create git workflow tables: {str(e)}"
            }
    
    async def verify_tables_exist(self) -> Dict[str, Any]:
        """Verify that all required tables exist."""
        if not self.supabase_client:
            return {
                "success": False,
                "error": "Supabase client not available"
            }
        
        try:
            required_tables = [
                "bmad_commit_tracking",
                "bmad_validation_results", 
                "bmad_git_workflow_status"
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                try:
                    # Try to query the table to see if it exists
                    result = self.supabase_client.table(table).select("id").limit(1).execute()
                    existing_tables.append(table)
                except Exception:
                    missing_tables.append(table)
            
            return {
                "success": True,
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
                "all_tables_exist": len(missing_tables) == 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to verify tables: {str(e)}"
            }


async def run_git_workflow_migration() -> Dict[str, Any]:
    """Run the git workflow migration."""
    migration = GitWorkflowMigration()
    
    # First verify what tables exist
    verification = await migration.verify_tables_exist()
    print(f"Table verification: {verification}")
    
    # Create missing tables
    if not verification.get("all_tables_exist", False):
        result = await migration.create_git_workflow_tables()
        print(f"Migration result: {result}")
        return result
    else:
        return {
            "success": True,
            "message": "All git workflow tables already exist",
            "verification": verification
        }


if __name__ == "__main__":
    asyncio.run(run_git_workflow_migration())
