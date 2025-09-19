"""
BMAD Git Workflow Integration

This module provides automated git commit and push workflows specifically designed
for BMAD workflow engine integration, including change tracking and validation.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .git_ops import attempt_auto_commit, _run_git, _repo_root, _current_branch, _head_hash
from .config.supabase_config import get_api_key, get_rest_url
from supabase import create_client


class BMADGitWorkflow:
    """BMAD-specific git workflow manager with change tracking and validation."""
    
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
    
    async def commit_bmad_changes(
        self,
        workflow_id: str,
        project_id: str,
        changes_summary: str,
        document_ids: Optional[List[str]] = None,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Commit BMAD workflow changes with comprehensive tracking.
        
        Args:
            workflow_id: BMAD workflow identifier
            project_id: Project identifier
            changes_summary: Human-readable summary of changes
            document_ids: List of document IDs that were modified
            validation_results: Results from BMAD validation steps
        
        Returns:
            Dict with commit status and metadata
        """
        try:
            # Generate commit message with BMAD context
            commit_message = self._generate_bmad_commit_message(
                workflow_id, changes_summary, document_ids
            )
            
            # Perform the commit
            commit_result = attempt_auto_commit(message=commit_message)
            
            if commit_result.get("status") != "success":
                return {
                    "success": False,
                    "error": f"Git commit failed: {commit_result.get('error')}",
                    "commit_result": commit_result
                }
            
            # Track the commit in database
            tracking_result = await self._track_bmad_commit(
                workflow_id=workflow_id,
                project_id=project_id,
                commit_hash=commit_result.get("commit"),
                branch=commit_result.get("branch"),
                message=commit_message,
                document_ids=document_ids,
                validation_results=validation_results
            )
            
            return {
                "success": True,
                "commit_hash": commit_result.get("commit"),
                "branch": commit_result.get("branch"),
                "message": commit_message,
                "tracking_id": tracking_result.get("tracking_id"),
                "workflow_id": workflow_id,
                "project_id": project_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"BMAD commit workflow failed: {str(e)}"
            }
    
    async def push_bmad_changes(
        self,
        tracking_id: str,
        remote: str = "origin",
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Push BMAD workflow changes to remote repository.
        
        Args:
            tracking_id: BMAD commit tracking ID
            remote: Remote repository name
            branch: Branch to push (defaults to current branch)
        
        Returns:
            Dict with push status and metadata
        """
        try:
            # Get tracking information
            tracking_info = await self._get_commit_tracking(tracking_id)
            if not tracking_info:
                return {
                    "success": False,
                    "error": f"Tracking ID {tracking_id} not found"
                }
            
            repo_root = _repo_root()
            if not repo_root:
                return {
                    "success": False,
                    "error": "Not in a git repository"
                }
            
            # Determine branch to push
            push_branch = branch or tracking_info.get("branch") or _current_branch(repo_root)
            
            # Push to remote
            push_result = _run_git(["push", remote, push_branch], cwd=repo_root)
            
            if not push_result.success:
                return {
                    "success": False,
                    "error": f"Git push failed: {push_result.stderr}",
                    "push_result": {
                        "success": push_result.success,
                        "stdout": push_result.stdout,
                        "stderr": push_result.stderr,
                        "exit_code": push_result.exit_code
                    }
                }
            
            # Update tracking record
            await self._update_push_status(tracking_id, True, push_result.stdout)
            
            return {
                "success": True,
                "tracking_id": tracking_id,
                "remote": remote,
                "branch": push_branch,
                "push_output": push_result.stdout,
                "workflow_id": tracking_info.get("workflow_id"),
                "project_id": tracking_info.get("project_id")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"BMAD push workflow failed: {str(e)}"
            }
    
    async def validate_bmad_changes(
        self,
        workflow_id: str,
        project_id: str,
        validation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Validate BMAD workflow changes before commit.
        
        Args:
            workflow_id: BMAD workflow identifier
            project_id: Project identifier
            validation_type: Type of validation to perform
        
        Returns:
            Dict with validation results
        """
        try:
            validation_results = {
                "validation_id": str(uuid.uuid4()),
                "workflow_id": workflow_id,
                "project_id": project_id,
                "validation_type": validation_type,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {}
            }
            
            # Check 1: Git repository status
            repo_root = _repo_root()
            if not repo_root:
                validation_results["checks"]["git_repo"] = {
                    "status": "failed",
                    "error": "Not in a git repository"
                }
            else:
                validation_results["checks"]["git_repo"] = {
                    "status": "passed",
                    "repo_root": str(repo_root)
                }
            
            # Check 2: Uncommitted changes
            if repo_root:
                has_changes = _run_git(["status", "--porcelain"], cwd=repo_root)
                validation_results["checks"]["uncommitted_changes"] = {
                    "status": "passed" if has_changes.stdout.strip() else "warning",
                    "has_changes": bool(has_changes.stdout.strip()),
                    "changes": has_changes.stdout.strip().split('\n') if has_changes.stdout.strip() else []
                }
            
            # Check 3: BMAD document consistency
            if self.supabase_client:
                doc_consistency = await self._validate_bmad_documents(project_id)
                validation_results["checks"]["bmad_documents"] = doc_consistency
            
            # Check 4: Workflow state consistency
            workflow_consistency = await self._validate_workflow_state(workflow_id, project_id)
            validation_results["checks"]["workflow_state"] = workflow_consistency
            
            # Overall validation status
            all_passed = all(
                check.get("status") in ["passed", "warning"]
                for check in validation_results["checks"].values()
            )
            validation_results["overall_status"] = "passed" if all_passed else "failed"
            
            # Store validation results
            if self.supabase_client:
                await self._store_validation_results(validation_results)
            
            return {
                "success": True,
                "validation_results": validation_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"BMAD validation failed: {str(e)}"
            }
    
    def _generate_bmad_commit_message(
        self,
        workflow_id: str,
        changes_summary: str,
        document_ids: Optional[List[str]]
    ) -> str:
        """Generate a structured commit message for BMAD workflows."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        message_parts = [
            f"bmad: {workflow_id}",
            f"Changes: {changes_summary}",
            f"Timestamp: {timestamp}"
        ]
        
        if document_ids:
            message_parts.append(f"Documents: {', '.join(document_ids[:3])}")
            if len(document_ids) > 3:
                message_parts.append(f"... and {len(document_ids) - 3} more")
        
        return " | ".join(message_parts)
    
    async def _track_bmad_commit(
        self,
        workflow_id: str,
        project_id: str,
        commit_hash: str,
        branch: str,
        message: str,
        document_ids: Optional[List[str]],
        validation_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Track BMAD commit in database."""
        if not self.supabase_client:
            return {"tracking_id": None, "error": "Supabase not available"}
        
        try:
            tracking_id = str(uuid.uuid4())
            tracking_data = {
                "id": tracking_id,
                "workflow_id": workflow_id,
                "project_id": project_id,
                "commit_hash": commit_hash,
                "branch": branch,
                "commit_message": message,
                "document_ids": document_ids or [],
                "validation_results": validation_results or {},
                "status": "committed",
                "pushed": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase_client.table("bmad_commit_tracking").insert(tracking_data).execute()
            
            if result.data:
                return {
                    "tracking_id": tracking_id,
                    "success": True
                }
            else:
                return {
                    "tracking_id": None,
                    "error": "Failed to insert tracking record"
                }
                
        except Exception as e:
            return {
                "tracking_id": None,
                "error": f"Tracking failed: {str(e)}"
            }
    
    async def _get_commit_tracking(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """Get commit tracking information."""
        if not self.supabase_client:
            return None
        
        try:
            result = self.supabase_client.table("bmad_commit_tracking").select("*").eq("id", tracking_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    async def _update_push_status(self, tracking_id: str, pushed: bool, push_output: str) -> bool:
        """Update push status in tracking record."""
        if not self.supabase_client:
            return False
        
        try:
            updates = {
                "pushed": pushed,
                "push_output": push_output,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase_client.table("bmad_commit_tracking").update(updates).eq("id", tracking_id).execute()
            return bool(result.data)
        except Exception:
            return False
    
    async def _validate_bmad_documents(self, project_id: str) -> Dict[str, Any]:
        """Validate BMAD document consistency."""
        try:
            if not self.supabase_client:
                return {"status": "skipped", "reason": "Supabase not available"}
            
            # Get all documents for project
            result = self.supabase_client.table("cerebral_documents").select("*").eq("project_id", project_id).execute()
            documents = result.data or []
            
            # Check for required document types
            doc_types = [doc.get("kind") for doc in documents]
            required_types = ["PRD", "ARCHITECTURE", "STORY"]
            missing_types = [t for t in required_types if t not in doc_types]
            
            return {
                "status": "passed" if not missing_types else "warning",
                "total_documents": len(documents),
                "document_types": doc_types,
                "missing_types": missing_types,
                "documents": documents
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _validate_workflow_state(self, workflow_id: str, project_id: str) -> Dict[str, Any]:
        """Validate BMAD workflow state consistency."""
        try:
            # Check for active HIL sessions
            if self.supabase_client:
                hil_result = self.supabase_client.table("bmad_hil_sessions").select("*").eq("status", "waiting_for_user").execute()
                active_sessions = hil_result.data or []
                
                return {
                    "status": "passed" if not active_sessions else "warning",
                    "active_hil_sessions": len(active_sessions),
                    "sessions": active_sessions
                }
            else:
                return {
                    "status": "skipped",
                    "reason": "Supabase not available"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _store_validation_results(self, validation_results: Dict[str, Any]) -> bool:
        """Store validation results in database."""
        if not self.supabase_client:
            return False
        
        try:
            result = self.supabase_client.table("bmad_validation_results").insert(validation_results).execute()
            return bool(result.data)
        except Exception:
            return False
    
    async def get_bmad_commit_history(
        self,
        project_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get BMAD commit history for a project."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase not available",
                    "commits": []
                }
            
            result = self.supabase_client.table("bmad_commit_tracking").select("*").eq("project_id", project_id).order("created_at", desc=True).limit(limit).execute()
            
            return {
                "success": True,
                "commits": result.data or [],
                "count": len(result.data or [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get commit history: {str(e)}",
                "commits": []
            }


# Convenience functions for direct use
async def commit_bmad_workflow_changes(
    workflow_id: str,
    project_id: str,
    changes_summary: str,
    document_ids: Optional[List[str]] = None,
    validation_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Convenience function to commit BMAD workflow changes."""
    workflow = BMADGitWorkflow()
    return await workflow.commit_bmad_changes(
        workflow_id, project_id, changes_summary, document_ids, validation_results
    )


async def push_bmad_workflow_changes(
    tracking_id: str,
    remote: str = "origin",
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to push BMAD workflow changes."""
    workflow = BMADGitWorkflow()
    return await workflow.push_bmad_changes(tracking_id, remote, branch)


async def validate_bmad_workflow_changes(
    workflow_id: str,
    project_id: str,
    validation_type: str = "comprehensive"
) -> Dict[str, Any]:
    """Convenience function to validate BMAD workflow changes."""
    workflow = BMADGitWorkflow()
    return await workflow.validate_bmad_changes(workflow_id, project_id, validation_type)

