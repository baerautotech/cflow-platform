"""
BMAD Vendor Wrapper - Exposes vendor/bmad/ functionality via MCP tools

This module creates MCP wrappers for the existing vendor BMAD functionality,
allowing the cflow-platform to use vendor BMAD workflows, agents, templates,
and tasks without rebuilding them.
"""

import asyncio
import json
import yaml
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from dotenv import load_dotenv
from .config.supabase_config import get_api_key, get_rest_url
from supabase import create_client

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class ProjectType(Enum):
    """Project type enumeration."""
    BROWNFIELD = "brownfield"
    GREENFIELD = "greenfield"
    UNKNOWN = "unknown"


class WorkflowType(Enum):
    """Workflow type enumeration."""
    BROWNFIELD_SERVICE = "brownfield-service"
    BROWNFIELD_FULLSTACK = "brownfield-fullstack"
    GREENFIELD_FULLSTACK = "greenfield-fullstack"
    GREENFIELD_PROTOTYPE = "greenfield-prototype"


class VendorBMADWrapper:
    """
    Wrapper for vendor BMAD functionality.
    
    This class provides MCP-compatible access to vendor BMAD workflows,
    agents, templates, and tasks without rebuilding the functionality.
    """
    
    def __init__(self):
        self.supabase_client = None
        self._ensure_supabase()
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
        self.workflows_dir = self.bmad_root / "bmad-core" / "workflows"
        self.agents_dir = self.bmad_root / "bmad-core" / "agents"
        self.templates_dir = self.bmad_root / "bmad-core" / "templates"
        self.tasks_dir = self.bmad_root / "bmad-core" / "tasks"
        self.expansion_packs_dir = self.bmad_root / "expansion-packs"
    
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
    
    async def detect_project_type(self, project_path: str, project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect project type (brownfield vs greenfield) using vendor BMAD patterns.
        
        Args:
            project_path: Path to the project directory
            project_context: Optional context about the project
            
        Returns:
            Dict with project type detection results
        """
        try:
            project_path_obj = Path(project_path)
            
            # Check for existing codebase indicators
            has_existing_code = False
            has_documentation = False
            has_tests = False
            has_config_files = False
            
            # Look for common project indicators
            if project_path_obj.exists():
                # Check for existing source code
                for pattern in ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go", "**/*.rs"]:
                    if list(project_path_obj.glob(pattern)):
                        has_existing_code = True
                        break
                
                # Check for documentation
                for pattern in ["**/*.md", "**/README*", "**/docs/**"]:
                    if list(project_path_obj.glob(pattern)):
                        has_documentation = True
                        break
                
                # Check for tests
                for pattern in ["**/test*", "**/*test*", "**/spec*", "**/*spec*"]:
                    if list(project_path_obj.glob(pattern)):
                        has_tests = True
                        break
                
                # Check for config files
                config_files = ["package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]
                for config_file in config_files:
                    if (project_path_obj / config_file).exists():
                        has_config_files = True
                        break
            
            # Determine project type based on indicators
            if has_existing_code or has_documentation or has_tests or has_config_files:
                project_type = ProjectType.BROWNFIELD
                confidence = 0.9 if has_existing_code else 0.7
            else:
                project_type = ProjectType.GREENFIELD
                confidence = 0.8
            
            # Get recommended workflow
            recommended_workflow = self._get_recommended_workflow(project_type, project_context)
            
            return {
                "success": True,
                "project_type": project_type.value,
                "confidence": confidence,
                "indicators": {
                    "has_existing_code": has_existing_code,
                    "has_documentation": has_documentation,
                    "has_tests": has_tests,
                    "has_config_files": has_config_files
                },
                "recommended_workflow": recommended_workflow,
                "message": f"Project detected as {project_type.value} with {confidence:.1%} confidence"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to detect project type: {str(e)}"
            }
    
    def _get_recommended_workflow(self, project_type: ProjectType, project_context: Optional[Dict[str, Any]]) -> str:
        """Get recommended workflow based on project type and context."""
        if project_type == ProjectType.BROWNFIELD:
            # Check if it's a service/API project
            if project_context and project_context.get("project_category") in ["service", "api", "microservice"]:
                return WorkflowType.BROWNFIELD_SERVICE.value
            else:
                return WorkflowType.BROWNFIELD_FULLSTACK.value
        else:
            # Check if it's a prototype or full application
            if project_context and project_context.get("project_scope") == "prototype":
                return WorkflowType.GREENFIELD_PROTOTYPE.value
            else:
                return WorkflowType.GREENFIELD_FULLSTACK.value
    
    async def start_brownfield_workflow(self, project_path: str, workflow_type: str = "brownfield-service", 
                                      enhancement_description: str = "", project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a brownfield workflow using vendor BMAD patterns.
        
        Args:
            project_path: Path to the project directory
            workflow_type: Type of brownfield workflow to use
            enhancement_description: Description of the enhancement to add
            project_context: Optional context about the project
            
        Returns:
            Dict with workflow start results
        """
        try:
            # Load vendor BMAD workflow
            workflow_file = self.workflows_dir / f"{workflow_type}.yaml"
            if not workflow_file.exists():
                return {
                    "success": False,
                    "error": f"Workflow {workflow_type} not found in vendor BMAD"
                }
            
            with open(workflow_file, 'r') as f:
                workflow_config = yaml.safe_load(f)
            
            # Create workflow session
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "project_path": project_path,
                "workflow_type": workflow_type,
                "workflow_config": workflow_config,
                "enhancement_description": enhancement_description,
                "project_context": project_context or {},
                "status": "started",
                "current_step": 0,
                "created_at": datetime.utcnow().isoformat(),
                "vendor_bmad_version": self._get_vendor_bmad_version()
            }
            
            # Store session in database
            if self.supabase_client:
                result = self.supabase_client.table("bmad_workflow_sessions").insert(session_data).execute()
                if not result.data:
                    return {
                        "success": False,
                        "error": "Failed to store workflow session"
                    }
            
            # Get first step from workflow
            first_step = self._get_workflow_step(workflow_config, 0)
            
            return {
                "success": True,
                "session_id": session_id,
                "workflow_type": workflow_type,
                "workflow_name": workflow_config.get("workflow", {}).get("name", "Unknown"),
                "first_step": first_step,
                "total_steps": len(workflow_config.get("workflow", {}).get("sequence", [])),
                "message": f"Brownfield workflow '{workflow_type}' started successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start brownfield workflow: {str(e)}"
            }
    
    async def start_greenfield_workflow(self, project_path: str, workflow_type: str = "greenfield-fullstack",
                                      project_description: str = "", project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a greenfield workflow using vendor BMAD patterns.
        
        Args:
            project_path: Path to the project directory
            workflow_type: Type of greenfield workflow to use
            project_description: Description of the project to build
            project_context: Optional context about the project
            
        Returns:
            Dict with workflow start results
        """
        try:
            # Load vendor BMAD workflow
            workflow_file = self.workflows_dir / f"{workflow_type}.yaml"
            if not workflow_file.exists():
                return {
                    "success": False,
                    "error": f"Workflow {workflow_type} not found in vendor BMAD"
                }
            
            with open(workflow_file, 'r') as f:
                workflow_config = yaml.safe_load(f)
            
            # Create workflow session
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "project_path": project_path,
                "workflow_type": workflow_type,
                "workflow_config": workflow_config,
                "project_description": project_description,
                "project_context": project_context or {},
                "status": "started",
                "current_step": 0,
                "created_at": datetime.utcnow().isoformat(),
                "vendor_bmad_version": self._get_vendor_bmad_version()
            }
            
            # Store session in database
            if self.supabase_client:
                result = self.supabase_client.table("bmad_workflow_sessions").insert(session_data).execute()
                if not result.data:
                    return {
                        "success": False,
                        "error": "Failed to store workflow session"
                    }
            
            # Get first step from workflow
            first_step = self._get_workflow_step(workflow_config, 0)
            
            return {
                "success": True,
                "session_id": session_id,
                "workflow_type": workflow_type,
                "workflow_name": workflow_config.get("workflow", {}).get("name", "Unknown"),
                "first_step": first_step,
                "total_steps": len(workflow_config.get("workflow", {}).get("sequence", [])),
                "message": f"Greenfield workflow '{workflow_type}' started successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start greenfield workflow: {str(e)}"
            }
    
    async def execute_workflow_step(self, session_id: str, step_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the next step in a vendor BMAD workflow.
        
        Args:
            session_id: ID of the workflow session
            step_result: Result from the previous step (if any)
            
        Returns:
            Dict with step execution results
        """
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }
            
            # Get session
            session_result = self.supabase_client.table("bmad_workflow_sessions").select("*").eq("id", session_id).execute()
            
            if not session_result.data:
                return {
                    "success": False,
                    "error": f"Workflow session {session_id} not found"
                }
            
            session = session_result.data[0]
            workflow_config = session["workflow_config"]
            current_step = session.get("current_step", 0)
            
            # Store step result if provided
            if step_result:
                step_results = session.get("step_results", [])
                step_results.append({
                    "step": current_step,
                    "result": step_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Update session with step result
                self.supabase_client.table("bmad_workflow_sessions").update({
                    "step_results": step_results,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", session_id).execute()
            
            # Get next step
            next_step = self._get_workflow_step(workflow_config, current_step + 1)
            
            if next_step:
                # Update session to next step
                self.supabase_client.table("bmad_workflow_sessions").update({
                    "current_step": current_step + 1,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", session_id).execute()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "current_step": current_step + 1,
                    "next_step": next_step,
                    "workflow_continuing": True,
                    "message": f"Executed step {current_step + 1}, ready for next step"
                }
            else:
                # Workflow complete
                self.supabase_client.table("bmad_workflow_sessions").update({
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", session_id).execute()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "current_step": current_step + 1,
                    "workflow_complete": True,
                    "message": "Workflow completed successfully"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute workflow step: {str(e)}"
            }
    
    def _get_workflow_step(self, workflow_config: Dict[str, Any], step_index: int) -> Optional[Dict[str, Any]]:
        """Get a specific step from workflow configuration."""
        sequence = workflow_config.get("workflow", {}).get("sequence", [])
        if step_index < len(sequence):
            return sequence[step_index]
        return None
    
    def _get_vendor_bmad_version(self) -> str:
        """Get vendor BMAD version."""
        try:
            version_file = self.bmad_root / "docs" / "versions.md"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    content = f.read()
                    # Extract version from content (simple parsing)
                    for line in content.split('\n'):
                        if 'version' in line.lower() and 'v' in line:
                            return line.strip()
            return "unknown"
        except Exception:
            return "unknown"
    
    async def get_available_workflows(self) -> Dict[str, Any]:
        """Get list of available vendor BMAD workflows."""
        try:
            workflows = []
            
            if self.workflows_dir.exists():
                for workflow_file in self.workflows_dir.glob("*.yaml"):
                    try:
                        with open(workflow_file, 'r') as f:
                            workflow_config = yaml.safe_load(f)
                        
                        workflow_info = workflow_config.get("workflow", {})
                        workflows.append({
                            "id": workflow_info.get("id", workflow_file.stem),
                            "name": workflow_info.get("name", "Unknown"),
                            "description": workflow_info.get("description", ""),
                            "type": workflow_info.get("type", "unknown"),
                            "project_types": workflow_info.get("project_types", []),
                            "file": workflow_file.name
                        })
                    except Exception as e:
                        print(f"Error loading workflow {workflow_file}: {e}")
            
            return {
                "success": True,
                "workflows": workflows,
                "total_count": len(workflows),
                "vendor_bmad_version": self._get_vendor_bmad_version()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get available workflows: {str(e)}"
            }
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a workflow session."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }
            
            session_result = self.supabase_client.table("bmad_workflow_sessions").select("*").eq("id", session_id).execute()
            
            if not session_result.data:
                return {
                    "success": False,
                    "error": f"Workflow session {session_id} not found"
                }
            
            session = session_result.data[0]
            
            return {
                "success": True,
                "session_id": session_id,
                "workflow_type": session["workflow_type"],
                "status": session["status"],
                "current_step": session.get("current_step", 0),
                "total_steps": len(session.get("workflow_config", {}).get("workflow", {}).get("sequence", [])),
                "created_at": session["created_at"],
                "updated_at": session.get("updated_at"),
                "completed_at": session.get("completed_at")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get workflow status: {str(e)}"
            }
