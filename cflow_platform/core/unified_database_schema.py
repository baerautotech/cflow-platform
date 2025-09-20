"""
Unified Database Schema for BMAD Platform

This module provides a single source of truth for all database schema definitions,
consolidating the various migration files and schema definitions.
"""

import asyncio
from typing import Dict, Any, List, Optional
from cflow_platform.core.config.supabase_config import get_api_key, get_rest_url
from supabase import create_client


class UnifiedDatabaseSchema:
    """Unified database schema manager for BMAD platform."""
    
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
    
    def get_core_tables_schema(self) -> Dict[str, str]:
        """Get the core BMAD tables schema."""
        return {
            "cerebral_documents": """
                CREATE TABLE IF NOT EXISTS cerebral_documents (
                    doc_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    project_id uuid NOT NULL,
                    type text NOT NULL CHECK (type IN ('PRD', 'ARCH', 'STORY', 'EPIC', 'TASK')),
                    version int NOT NULL DEFAULT 1,
                    status text NOT NULL CHECK (status IN ('draft', 'review', 'approved', 'archived')),
                    title text NOT NULL,
                    content text NOT NULL,
                    metadata jsonb DEFAULT '{}',
                    authored_by uuid,
                    artifacts jsonb DEFAULT '{}',
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    
                    CONSTRAINT unique_doc_version UNIQUE (tenant_id, project_id, type, version)
                );
                
                CREATE INDEX IF NOT EXISTS idx_cerebral_documents_tenant_project 
                    ON cerebral_documents(tenant_id, project_id);
                CREATE INDEX IF NOT EXISTS idx_cerebral_documents_type_status 
                    ON cerebral_documents(type, status);
                CREATE INDEX IF NOT EXISTS idx_cerebral_documents_created_at 
                    ON cerebral_documents(created_at);
            """,
            
            "cerebral_tasks": """
                CREATE TABLE IF NOT EXISTS cerebral_tasks (
                    task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    project_id uuid NOT NULL,
                    derived_from_story uuid REFERENCES cerebral_documents(doc_id),
                    status text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
                    priority text NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
                    title text NOT NULL,
                    description text,
                    dependencies jsonb DEFAULT '[]',
                    metadata jsonb DEFAULT '{}',
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                );
                
                CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_tenant_project 
                    ON cerebral_tasks(tenant_id, project_id);
                CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_status_priority 
                    ON cerebral_tasks(status, priority);
                CREATE INDEX IF NOT EXISTS idx_cerebral_tasks_derived_from_story 
                    ON cerebral_tasks(derived_from_story);
            """,
            
            "cerebral_activities": """
                CREATE TABLE IF NOT EXISTS cerebral_activities (
                    activity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    actor uuid NOT NULL,
                    action text NOT NULL,
                    resource_type text NOT NULL,
                    resource_id uuid NOT NULL,
                    metadata jsonb DEFAULT '{}',
                    timestamp timestamptz NOT NULL DEFAULT now()
                );
                
                CREATE INDEX IF NOT EXISTS idx_cerebral_activities_tenant_actor 
                    ON cerebral_activities(tenant_id, actor);
                CREATE INDEX IF NOT EXISTS idx_cerebral_activities_resource 
                    ON cerebral_activities(resource_type, resource_id);
                CREATE INDEX IF NOT EXISTS idx_cerebral_activities_timestamp 
                    ON cerebral_activities(timestamp);
            """
        }
    
    def get_bmad_workflow_schema(self) -> Dict[str, str]:
        """Get the BMAD workflow tables schema."""
        return {
            "bmad_commit_tracking": """
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
            """,
            
            "bmad_validation_results": """
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
            """,
            
            "bmad_git_workflow_status": """
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
        }
    
    def get_rag_integration_schema(self) -> Dict[str, str]:
        """Get the RAG integration schema extensions."""
        return {
            "knowledge_items_extension": """
                ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
                ALTER TABLE knowledge_items ADD COLUMN IF NOT EXISTS content_type text CHECK (content_type IN ('PRD', 'ARCH', 'STORY', 'TASK', 'GENERAL'));
                
                CREATE INDEX IF NOT EXISTS idx_knowledge_items_doc_id ON knowledge_items(doc_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_items_content_type ON knowledge_items(content_type);
            """,
            
            "knowledge_embeddings_extension": """
                ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS doc_id uuid REFERENCES cerebral_documents(doc_id);
                ALTER TABLE knowledge_embeddings ADD COLUMN IF NOT EXISTS chunk_type text CHECK (chunk_type IN ('section', 'requirement', 'story', 'task', 'general'));
                
                CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_doc_id ON knowledge_embeddings(doc_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_chunk_type ON knowledge_embeddings(chunk_type);
            """,
            
            "memory_items_extension": """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    collection text NOT NULL DEFAULT 'default',
                    content text NOT NULL,
                    metadata jsonb DEFAULT '{}',
                    created_at timestamptz DEFAULT now(),
                    source text DEFAULT 'bmad',
                    line_number integer DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_memory_items_collection ON memory_items(collection);
                CREATE INDEX IF NOT EXISTS idx_memory_items_created_at ON memory_items(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_items_source ON memory_items(source);
            """
        }
    
    async def create_all_tables(self) -> Dict[str, Any]:
        """Create all BMAD platform tables."""
        if not self.supabase_client:
            return {
                "success": False,
                "error": "Supabase client not available"
            }
        
        try:
            results = {}
            
            # Create core tables
            core_tables = self.get_core_tables_schema()
            for table_name, schema_sql in core_tables.items():
                try:
                    result = self.supabase_client.rpc('run_sql', {'sql': schema_sql}).execute()
                    results[table_name] = {
                        "success": True,
                        "message": f"{table_name} table created successfully"
                    }
                except Exception as e:
                    results[table_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Create BMAD workflow tables
            workflow_tables = self.get_bmad_workflow_schema()
            for table_name, schema_sql in workflow_tables.items():
                try:
                    result = self.supabase_client.rpc('run_sql', {'sql': schema_sql}).execute()
                    results[table_name] = {
                        "success": True,
                        "message": f"{table_name} table created successfully"
                    }
                except Exception as e:
                    results[table_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Create RAG integration extensions
            rag_extensions = self.get_rag_integration_schema()
            for extension_name, schema_sql in rag_extensions.items():
                try:
                    result = self.supabase_client.rpc('run_sql', {'sql': schema_sql}).execute()
                    results[extension_name] = {
                        "success": True,
                        "message": f"{extension_name} extension applied successfully"
                    }
                except Exception as e:
                    results[extension_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check overall success
            all_successful = all(result.get("success", False) for result in results.values())
            
            return {
                "success": all_successful,
                "message": "Database schema creation completed",
                "results": results,
                "total_tables": len(results),
                "successful_tables": sum(1 for r in results.values() if r.get("success", False)),
                "failed_tables": sum(1 for r in results.values() if not r.get("success", False))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create database schema: {str(e)}"
            }
    
    async def verify_schema(self) -> Dict[str, Any]:
        """Verify that all required tables exist."""
        if not self.supabase_client:
            return {
                "success": False,
                "error": "Supabase client not available"
            }
        
        try:
            # Define all required tables
            required_tables = [
                "cerebral_documents",
                "cerebral_tasks", 
                "cerebral_activities",
                "bmad_commit_tracking",
                "bmad_validation_results",
                "bmad_git_workflow_status",
                "memory_items"
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
            
            # Check for RAG extensions
            rag_extensions_status = {}
            try:
                # Check if knowledge_items has doc_id column
                result = self.supabase_client.table("knowledge_items").select("doc_id").limit(1).execute()
                rag_extensions_status["knowledge_items_doc_id"] = True
            except Exception:
                rag_extensions_status["knowledge_items_doc_id"] = False
                
            try:
                # Check if knowledge_embeddings has doc_id column
                result = self.supabase_client.table("knowledge_embeddings").select("doc_id").limit(1).execute()
                rag_extensions_status["knowledge_embeddings_doc_id"] = True
            except Exception:
                rag_extensions_status["knowledge_embeddings_doc_id"] = False
            
            return {
                "success": len(missing_tables) == 0,
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
                "rag_extensions_status": rag_extensions_status,
                "all_tables_exist": len(missing_tables) == 0,
                "total_required": len(required_tables),
                "existing_count": len(existing_tables),
                "missing_count": len(missing_tables)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to verify schema: {str(e)}"
            }
    
    def get_schema_documentation(self) -> str:
        """Get comprehensive schema documentation."""
        return """
# BMAD Unified Database Schema

## Core Tables

### cerebral_documents
Primary table for all BMAD documents (PRD, Architecture, Story, Epic, Task)
- doc_id: Unique document identifier
- tenant_id: Multi-tenant support
- project_id: Project association
- type: Document type (PRD, ARCH, STORY, EPIC, TASK)
- version: Document versioning
- status: Document status (draft, review, approved, archived)
- content: Document content
- metadata: Additional metadata
- artifacts: BMAD-specific artifacts

### cerebral_tasks
Task management derived from stories
- task_id: Unique task identifier
- derived_from_story: Reference to story document
- status: Task status (pending, in_progress, completed, blocked, cancelled)
- priority: Task priority (low, medium, high, critical)
- dependencies: Task dependencies as JSON array

### cerebral_activities
Activity tracking for audit trails
- activity_id: Unique activity identifier
- actor: User who performed the action
- action: Action type (create, update, approve, reject, etc.)
- resource_type: Type of resource affected
- resource_id: ID of the affected resource

## BMAD Workflow Tables

### bmad_commit_tracking
Git commit tracking for BMAD workflows
- workflow_id: BMAD workflow identifier
- commit_hash: Git commit hash
- branch: Git branch name
- document_ids: Array of document IDs in commit
- validation_results: Validation results as JSON

### bmad_validation_results
Workflow validation tracking
- validation_id: Unique validation identifier
- workflow_id: BMAD workflow identifier
- validation_type: Type of validation performed
- checks: Validation checks as JSON
- overall_status: Overall validation status

### bmad_git_workflow_status
Git workflow status tracking
- workflow_id: BMAD workflow identifier
- current_step: Current workflow step
- last_commit_hash: Last commit hash
- last_push_hash: Last push hash
- validation_status: Current validation status

## RAG Integration

### knowledge_items (Extended)
Extended with BMAD document references
- doc_id: Reference to cerebral_documents
- content_type: Type of content (PRD, ARCH, STORY, TASK, GENERAL)

### knowledge_embeddings (Extended)
Extended with BMAD document references
- doc_id: Reference to cerebral_documents
- chunk_type: Type of chunk (section, requirement, story, task, general)

### memory_items
Memory storage for BMAD system
- collection: Memory collection name
- content: Memory content
- metadata: Additional metadata
- source: Source of memory (bmad, migration, etc.)

## Indexes and Performance

All tables include appropriate indexes for:
- Multi-tenant queries (tenant_id, project_id)
- Document type and status filtering
- Temporal queries (created_at, updated_at)
- Workflow and task associations
- RAG integration queries

## Migration Strategy

1. Create core tables first (cerebral_documents, cerebral_tasks, cerebral_activities)
2. Create BMAD workflow tables
3. Extend existing RAG tables with new columns
4. Create memory_items table
5. Apply all indexes
6. Verify schema integrity
        """


# Global instance
_unified_schema = UnifiedDatabaseSchema()


def get_unified_schema() -> UnifiedDatabaseSchema:
    """Get global unified schema instance."""
    return _unified_schema


async def run_schema_migration() -> Dict[str, Any]:
    """Run the unified schema migration."""
    schema = get_unified_schema()
    
    # First verify what exists
    verification = await schema.verify_schema()
    print(f"Schema verification: {verification}")
    
    # Create missing tables
    if not verification.get("all_tables_exist", False):
        result = await schema.create_all_tables()
        print(f"Schema migration result: {result}")
        return result
    else:
        return {
            "success": True,
            "message": "All schema tables already exist",
            "verification": verification
        }


if __name__ == "__main__":
    asyncio.run(run_schema_migration())
