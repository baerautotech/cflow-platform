"""
Basic BMAD Workflow Implementations

This module implements the basic BMAD workflows for Story 1.5:
- Basic PRD creation workflow
- Basic Architecture creation workflow  
- Basic Story creation workflow

These workflows provide simplified implementations that use BMAD templates
and store documents in Cerebral storage (Supabase).
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .bmad_workflow_engine import BMADWorkflowEngine, BMADWorkflow, BMADWorkflowStep
from .bmad_hil_integration import BMADHILIntegration
from .public_api import get_direct_client_executor


class BasicWorkflowImplementations:
    """
    Basic BMAD workflow implementations for Story 1.5.
    
    These provide simplified workflows that:
    1. Use BMAD templates from vendor/bmad/
    2. Store documents in Cerebral storage (Supabase)
    3. Provide basic workflow orchestration
    4. Support HIL (Human-in-the-Loop) integration
    """
    
    def __init__(self):
        self.workflow_engine = BMADWorkflowEngine()
        self.hil_integration = BMADHILIntegration()
        self.executor = get_direct_client_executor()
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
    
    # ============================================================================
    # 1.5.1: Basic PRD Creation Workflow
    # ============================================================================
    
    async def create_basic_prd_workflow(
        self,
        project_name: str,
        goals: Optional[List[str]] = None,
        background: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a basic PRD using BMAD templates and Cerebral storage.
        
        This implements the basic PRD creation workflow from Story 1.5.1.
        """
        try:
            # Initialize project context
            if not project_context:
                project_context = {
                    "project_id": str(uuid.uuid4()),
                    "project_name": project_name,
                    "project_type": "web-app",
                    "workspace_path": os.getcwd()
                }
            
            # Step 1: Create PRD document using BMAD template
            prd_result = await self._create_prd_document(project_name, goals, background, project_context)
            
            if not prd_result.get("success"):
                return {
                    "workflow_status": "error",
                    "message": f"Failed to create PRD: {prd_result.get('error')}",
                    "step_results": [{"step": "create_prd", "status": "error", "result": prd_result}]
                }
            
            doc_id = prd_result["doc_id"]
            
            # Step 2: Check if HIL interaction is needed
            hil_check = await self._check_prd_hil_needed(doc_id, prd_result["data"])
            
            if hil_check.get("hil_required", False):
                # Start HIL session for PRD completion
                hil_result = await self.hil_integration.trigger_hil_session(
                    doc_id=doc_id,
                    doc_type="PRD",
                    workflow_context={
                        "workflow_step": "prd_creation",
                        "project_context": project_context,
                        "incomplete_sections": hil_check.get("incomplete_sections", [])
                    }
                )
                
                if hil_result.get("success"):
                    return {
                        "workflow_status": "paused_for_hil",
                        "message": "PRD created and HIL session started for completion",
                        "doc_id": doc_id,
                        "hil_session_id": hil_result.get("session_id"),
                        "next_action": "Complete HIL session to finalize PRD",
                        "step_results": [
                            {"step": "create_prd", "status": "success", "result": prd_result},
                            {"step": "start_hil", "status": "success", "result": hil_result}
                        ]
                    }
            
            # Step 3: PRD completed (no HIL needed)
            return {
                "workflow_status": "completed",
                "message": f"Basic PRD created successfully for {project_name}",
                "doc_id": doc_id,
                "next_action": "Create Architecture document",
                "step_results": [
                    {"step": "create_prd", "status": "success", "result": prd_result},
                    {"step": "hil_check", "status": "completed", "result": {"hil_required": False}}
                ]
            }
            
        except Exception as e:
            return {
                "workflow_status": "error",
                "message": f"PRD creation workflow failed: {str(e)}",
                "error": str(e)
            }
    
    async def _create_prd_document(
        self,
        project_name: str,
        goals: Optional[List[str]],
        background: Optional[str],
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create PRD document using BMAD template."""
        try:
            # Use the existing BMAD handlers to create PRD
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            result = await handlers.bmad_prd_create(
                project_name=project_name,
                goals=goals,
                background=background
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create PRD document: {str(e)}"
            }
    
    async def _check_prd_hil_needed(self, doc_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if PRD needs HIL interaction for completion."""
        try:
            content = doc_data.get("content", "")
            
            # Check for template placeholders that need completion
            incomplete_sections = []
            if "*[To be filled during interactive elicitation]*" in content:
                incomplete_sections = [
                    "User Research and Personas",
                    "Functional Requirements",
                    "Non-Functional Requirements", 
                    "Success Metrics and KPIs",
                    "Risks and Assumptions",
                    "Timeline and Milestones"
                ]
            
            return {
                "hil_required": len(incomplete_sections) > 0,
                "incomplete_sections": incomplete_sections,
                "completion_percentage": 100 - (len(incomplete_sections) * 16.67)  # Rough estimate
            }
            
        except Exception as e:
            return {
                "hil_required": False,
                "error": f"Failed to check HIL requirements: {str(e)}"
            }
    
    # ============================================================================
    # 1.5.2: Basic Architecture Creation Workflow
    # ============================================================================
    
    async def create_basic_architecture_workflow(
        self,
        project_name: str,
        prd_id: str,
        tech_stack: Optional[List[str]] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a basic Architecture document using BMAD templates and Cerebral storage.
        
        This implements the basic Architecture creation workflow from Story 1.5.2.
        """
        try:
            # Initialize project context
            if not project_context:
                project_context = {
                    "project_id": str(uuid.uuid4()),
                    "project_name": project_name,
                    "project_type": "web-app",
                    "workspace_path": os.getcwd()
                }
            
            # Step 1: Validate PRD exists
            prd_validation = await self._validate_prd_exists(prd_id)
            if not prd_validation.get("valid"):
                return {
                    "workflow_status": "error",
                    "message": f"PRD validation failed: {prd_validation.get('error')}",
                    "step_results": [{"step": "validate_prd", "status": "error", "result": prd_validation}]
                }
            
            # Step 2: Create Architecture document using BMAD template
            arch_result = await self._create_architecture_document(
                project_name, prd_id, tech_stack, project_context
            )
            
            if not arch_result.get("success"):
                return {
                    "workflow_status": "error",
                    "message": f"Failed to create Architecture: {arch_result.get('error')}",
                    "step_results": [
                        {"step": "validate_prd", "status": "success", "result": prd_validation},
                        {"step": "create_architecture", "status": "error", "result": arch_result}
                    ]
                }
            
            doc_id = arch_result["doc_id"]
            
            # Step 3: Check if HIL interaction is needed
            hil_check = await self._check_architecture_hil_needed(doc_id, arch_result["data"])
            
            if hil_check.get("hil_required", False):
                # Start HIL session for Architecture completion
                hil_result = await self.hil_integration.trigger_hil_session(
                    doc_id=doc_id,
                    doc_type="ARCH",
                    workflow_context={
                        "workflow_step": "architecture_creation",
                        "project_context": project_context,
                        "prd_id": prd_id,
                        "incomplete_sections": hil_check.get("incomplete_sections", [])
                    }
                )
                
                if hil_result.get("success"):
                    return {
                        "workflow_status": "paused_for_hil",
                        "message": "Architecture created and HIL session started for completion",
                        "doc_id": doc_id,
                        "prd_id": prd_id,
                        "hil_session_id": hil_result.get("session_id"),
                        "next_action": "Complete HIL session to finalize Architecture",
                        "step_results": [
                            {"step": "validate_prd", "status": "success", "result": prd_validation},
                            {"step": "create_architecture", "status": "success", "result": arch_result},
                            {"step": "start_hil", "status": "success", "result": hil_result}
                        ]
                    }
            
            # Step 4: Architecture completed (no HIL needed)
            return {
                "workflow_status": "completed",
                "message": f"Basic Architecture created successfully for {project_name}",
                "doc_id": doc_id,
                "prd_id": prd_id,
                "next_action": "Create User Stories",
                "step_results": [
                    {"step": "validate_prd", "status": "success", "result": prd_validation},
                    {"step": "create_architecture", "status": "success", "result": arch_result},
                    {"step": "hil_check", "status": "completed", "result": {"hil_required": False}}
                ]
            }
            
        except Exception as e:
            return {
                "workflow_status": "error",
                "message": f"Architecture creation workflow failed: {str(e)}",
                "error": str(e)
            }
    
    async def _validate_prd_exists(self, prd_id: str) -> Dict[str, Any]:
        """Validate that PRD document exists and is accessible."""
        try:
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            result = await handlers.bmad_prd_get(prd_id)
            
            if result.get("success"):
                return {
                    "valid": True,
                    "prd_data": result.get("data"),
                    "message": "PRD validation successful"
                }
            else:
                return {
                    "valid": False,
                    "error": result.get("error", "PRD not found"),
                    "message": "PRD validation failed"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": f"PRD validation error: {str(e)}",
                "message": "PRD validation failed"
            }
    
    async def _create_architecture_document(
        self,
        project_name: str,
        prd_id: str,
        tech_stack: Optional[List[str]],
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Architecture document using BMAD template."""
        try:
            # Use the existing BMAD handlers to create Architecture
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            result = await handlers.bmad_arch_create(
                project_name=project_name,
                prd_id=prd_id,
                tech_stack=tech_stack
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Architecture document: {str(e)}"
            }
    
    async def _check_architecture_hil_needed(self, doc_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if Architecture needs HIL interaction for completion."""
        try:
            content = doc_data.get("content", "")
            
            # Check for template placeholders that need completion
            incomplete_sections = []
            if "*[To be filled during interactive elicitation]*" in content:
                incomplete_sections = [
                    "System Architecture",
                    "Data Architecture",
                    "Security Architecture",
                    "Deployment Architecture", 
                    "Integration Patterns",
                    "Performance Considerations"
                ]
            
            return {
                "hil_required": len(incomplete_sections) > 0,
                "incomplete_sections": incomplete_sections,
                "completion_percentage": 100 - (len(incomplete_sections) * 16.67)  # Rough estimate
            }
            
        except Exception as e:
            return {
                "hil_required": False,
                "error": f"Failed to check HIL requirements: {str(e)}"
            }
    
    # ============================================================================
    # 1.5.3: Basic Story Creation Workflow
    # ============================================================================
    
    async def create_basic_story_workflow(
        self,
        project_name: str,
        prd_id: str,
        arch_id: str,
        user_stories: Optional[List[str]] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a basic User Story document using BMAD templates and Cerebral storage.
        
        This implements the basic Story creation workflow from Story 1.5.3.
        """
        try:
            # Initialize project context
            if not project_context:
                project_context = {
                    "project_id": str(uuid.uuid4()),
                    "project_name": project_name,
                    "project_type": "web-app",
                    "workspace_path": os.getcwd()
                }
            
            # Step 1: Validate PRD and Architecture exist
            prd_validation = await self._validate_prd_exists(prd_id)
            arch_validation = await self._validate_architecture_exists(arch_id)
            
            if not prd_validation.get("valid"):
                return {
                    "workflow_status": "error",
                    "message": f"PRD validation failed: {prd_validation.get('error')}",
                    "step_results": [{"step": "validate_prd", "status": "error", "result": prd_validation}]
                }
            
            if not arch_validation.get("valid"):
                return {
                    "workflow_status": "error",
                    "message": f"Architecture validation failed: {arch_validation.get('error')}",
                    "step_results": [
                        {"step": "validate_prd", "status": "success", "result": prd_validation},
                        {"step": "validate_architecture", "status": "error", "result": arch_validation}
                    ]
                }
            
            # Step 2: Create Story document using BMAD template
            story_result = await self._create_story_document(
                project_name, prd_id, arch_id, user_stories, project_context
            )
            
            if not story_result.get("success"):
                return {
                    "workflow_status": "error",
                    "message": f"Failed to create Story: {story_result.get('error')}",
                    "step_results": [
                        {"step": "validate_prd", "status": "success", "result": prd_validation},
                        {"step": "validate_architecture", "status": "success", "result": arch_validation},
                        {"step": "create_story", "status": "error", "result": story_result}
                    ]
                }
            
            doc_id = story_result["doc_id"]
            
            # Step 3: Check if HIL interaction is needed
            hil_check = await self._check_story_hil_needed(doc_id, story_result["data"])
            
            if hil_check.get("hil_required", False):
                # Start HIL session for Story completion
                hil_result = await self.hil_integration.trigger_hil_session(
                    doc_id=doc_id,
                    doc_type="STORY",
                    workflow_context={
                        "workflow_step": "story_creation",
                        "project_context": project_context,
                        "prd_id": prd_id,
                        "arch_id": arch_id,
                        "incomplete_sections": hil_check.get("incomplete_sections", [])
                    }
                )
                
                if hil_result.get("success"):
                    return {
                        "workflow_status": "paused_for_hil",
                        "message": "Story created and HIL session started for completion",
                        "doc_id": doc_id,
                        "prd_id": prd_id,
                        "arch_id": arch_id,
                        "hil_session_id": hil_result.get("session_id"),
                        "next_action": "Complete HIL session to finalize Story",
                        "step_results": [
                            {"step": "validate_prd", "status": "success", "result": prd_validation},
                            {"step": "validate_architecture", "status": "success", "result": arch_validation},
                            {"step": "create_story", "status": "success", "result": story_result},
                            {"step": "start_hil", "status": "success", "result": hil_result}
                        ]
                    }
            
            # Step 4: Story completed (no HIL needed)
            return {
                "workflow_status": "completed",
                "message": f"Basic Story created successfully for {project_name}",
                "doc_id": doc_id,
                "prd_id": prd_id,
                "arch_id": arch_id,
                "next_action": "Begin implementation with Dev agent",
                "step_results": [
                    {"step": "validate_prd", "status": "success", "result": prd_validation},
                    {"step": "validate_architecture", "status": "success", "result": arch_validation},
                    {"step": "create_story", "status": "success", "result": story_result},
                    {"step": "hil_check", "status": "completed", "result": {"hil_required": False}}
                ]
            }
            
        except Exception as e:
            return {
                "workflow_status": "error",
                "message": f"Story creation workflow failed: {str(e)}",
                "error": str(e)
            }
    
    async def _validate_architecture_exists(self, arch_id: str) -> Dict[str, Any]:
        """Validate that Architecture document exists and is accessible."""
        try:
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            result = await handlers.bmad_arch_get(arch_id)
            
            if result.get("success"):
                return {
                    "valid": True,
                    "arch_data": result.get("data"),
                    "message": "Architecture validation successful"
                }
            else:
                return {
                    "valid": False,
                    "error": result.get("error", "Architecture not found"),
                    "message": "Architecture validation failed"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": f"Architecture validation error: {str(e)}",
                "message": "Architecture validation failed"
            }
    
    async def _create_story_document(
        self,
        project_name: str,
        prd_id: str,
        arch_id: str,
        user_stories: Optional[List[str]],
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Story document using BMAD template."""
        try:
            # Use the existing BMAD handlers to create Story
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            result = await handlers.bmad_story_create(
                project_name=project_name,
                prd_id=prd_id,
                arch_id=arch_id,
                user_stories=user_stories
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Story document: {str(e)}"
            }
    
    async def _check_story_hil_needed(self, doc_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if Story needs HIL interaction for completion."""
        try:
            content = doc_data.get("content", "")
            
            # Check for template placeholders that need completion
            incomplete_sections = []
            if "*[To be filled during interactive elicitation]*" in content:
                incomplete_sections = [
                    "Acceptance Criteria",
                    "Implementation Notes",
                    "Testing Strategy",
                    "Dependencies"
                ]
            
            return {
                "hil_required": len(incomplete_sections) > 0,
                "incomplete_sections": incomplete_sections,
                "completion_percentage": 100 - (len(incomplete_sections) * 25)  # Rough estimate
            }
            
        except Exception as e:
            return {
                "hil_required": False,
                "error": f"Failed to check HIL requirements: {str(e)}"
            }
    
    # ============================================================================
    # Workflow Orchestration and Status
    # ============================================================================
    
    async def get_workflow_status(self, project_id: str) -> Dict[str, Any]:
        """Get current status of all workflows for a project."""
        try:
            from ..handlers.bmad_handlers import BMADHandlers
            handlers = BMADHandlers()
            
            # Get all documents for the project
            docs_result = await handlers.bmad_doc_list(project_id=project_id)
            
            if not docs_result.get("success"):
                return {
                    "success": False,
                    "error": docs_result.get("error"),
                    "workflow_status": "error"
                }
            
            documents = docs_result.get("documents", [])
            
            # Analyze workflow status
            workflow_status = {
                "project_id": project_id,
                "prd_exists": any(doc["kind"] == "PRD" for doc in documents),
                "architecture_exists": any(doc["kind"] == "ARCHITECTURE" for doc in documents),
                "story_exists": any(doc["kind"] == "STORY" for doc in documents),
                "current_step": self._determine_current_step(documents),
                "next_action": self._determine_next_action(documents),
                "documents": documents,
                "completion_percentage": self._calculate_completion_percentage(documents)
            }
            
            return {
                "success": True,
                "workflow_status": workflow_status,
                "message": f"Workflow status: {workflow_status['current_step']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get workflow status: {str(e)}",
                "workflow_status": "error"
            }
    
    def _determine_current_step(self, documents: List[Dict[str, Any]]) -> str:
        """Determine current step in BMAD workflow."""
        doc_types = [doc["kind"] for doc in documents]
        
        if "STORY" in doc_types:
            return "Stories Created"
        elif "ARCHITECTURE" in doc_types:
            return "Architecture Created"
        elif "PRD" in doc_types:
            return "PRD Created"
        else:
            return "Workflow Not Started"
    
    def _determine_next_action(self, documents: List[Dict[str, Any]]) -> str:
        """Determine next action in BMAD workflow."""
        doc_types = [doc["kind"] for doc in documents]
        
        if "STORY" in doc_types:
            return "Review Stories"
        elif "ARCHITECTURE" in doc_types:
            return "Create Stories"
        elif "PRD" in doc_types:
            return "Create Architecture"
        else:
            return "Create PRD"
    
    def _calculate_completion_percentage(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate workflow completion percentage."""
        doc_types = [doc["kind"] for doc in documents]
        
        # Basic completion: PRD (33%), Architecture (33%), Story (34%)
        completion = 0.0
        if "PRD" in doc_types:
            completion += 33.33
        if "ARCHITECTURE" in doc_types:
            completion += 33.33
        if "STORY" in doc_types:
            completion += 33.34
        
        return round(completion, 2)
    
    async def run_complete_basic_workflow(
        self,
        project_name: str,
        goals: Optional[List[str]] = None,
        background: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
        user_stories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete basic workflow: PRD → Architecture → Story.
        
        This orchestrates all three basic workflows in sequence.
        """
        try:
            project_context = {
                "project_id": str(uuid.uuid4()),
                "project_name": project_name,
                "project_type": "web-app",
                "workspace_path": os.getcwd()
            }
            
            all_step_results = []
            
            # Step 1: Create PRD
            prd_workflow = await self.create_basic_prd_workflow(
                project_name, goals, background, project_context
            )
            
            all_step_results.extend(prd_workflow.get("step_results", []))
            
            if prd_workflow.get("workflow_status") == "error":
                return {
                    "workflow_status": "error",
                    "message": f"PRD workflow failed: {prd_workflow.get('message')}",
                    "step_results": all_step_results
                }
            
            if prd_workflow.get("workflow_status") == "paused_for_hil":
                return {
                    "workflow_status": "paused_for_hil",
                    "message": "Workflow paused for PRD HIL completion",
                    "current_step": "prd_creation",
                    "step_results": all_step_results,
                    "hil_session_id": prd_workflow.get("hil_session_id")
                }
            
            prd_id = prd_workflow.get("doc_id")
            project_context["prd_id"] = prd_id
            
            # Step 2: Create Architecture
            arch_workflow = await self.create_basic_architecture_workflow(
                project_name, prd_id, tech_stack, project_context
            )
            
            all_step_results.extend(arch_workflow.get("step_results", []))
            
            if arch_workflow.get("workflow_status") == "error":
                return {
                    "workflow_status": "error",
                    "message": f"Architecture workflow failed: {arch_workflow.get('message')}",
                    "step_results": all_step_results
                }
            
            if arch_workflow.get("workflow_status") == "paused_for_hil":
                return {
                    "workflow_status": "paused_for_hil",
                    "message": "Workflow paused for Architecture HIL completion",
                    "current_step": "architecture_creation",
                    "step_results": all_step_results,
                    "hil_session_id": arch_workflow.get("hil_session_id")
                }
            
            arch_id = arch_workflow.get("doc_id")
            project_context["arch_id"] = arch_id
            
            # Step 3: Create Story
            story_workflow = await self.create_basic_story_workflow(
                project_name, prd_id, arch_id, user_stories, project_context
            )
            
            all_step_results.extend(story_workflow.get("step_results", []))
            
            if story_workflow.get("workflow_status") == "error":
                return {
                    "workflow_status": "error",
                    "message": f"Story workflow failed: {story_workflow.get('message')}",
                    "step_results": all_step_results
                }
            
            if story_workflow.get("workflow_status") == "paused_for_hil":
                return {
                    "workflow_status": "paused_for_hil",
                    "message": "Workflow paused for Story HIL completion",
                    "current_step": "story_creation",
                    "step_results": all_step_results,
                    "hil_session_id": story_workflow.get("hil_session_id")
                }
            
            # All workflows completed successfully
            return {
                "workflow_status": "completed",
                "message": f"Complete basic workflow finished successfully for {project_name}",
                "project_context": project_context,
                "documents": {
                    "prd_id": prd_id,
                    "arch_id": arch_id,
                    "story_id": story_workflow.get("doc_id")
                },
                "next_action": "Begin implementation with Dev agent",
                "step_results": all_step_results,
                "completion_percentage": 100.0
            }
            
        except Exception as e:
            return {
                "workflow_status": "error",
                "message": f"Complete workflow failed: {str(e)}",
                "error": str(e)
            }


# Global instance for easy access
_basic_workflows: Optional[BasicWorkflowImplementations] = None


def get_basic_workflows() -> BasicWorkflowImplementations:
    """Get the global basic workflow implementations instance."""
    global _basic_workflows
    if _basic_workflows is None:
        _basic_workflows = BasicWorkflowImplementations()
    return _basic_workflows


# Convenience functions for direct workflow execution
async def create_basic_prd(
    project_name: str,
    goals: Optional[List[str]] = None,
    background: Optional[str] = None
) -> Dict[str, Any]:
    """Create a basic PRD using the BMAD workflow."""
    workflows = get_basic_workflows()
    return await workflows.create_basic_prd_workflow(project_name, goals, background)


async def create_basic_architecture(
    project_name: str,
    prd_id: str,
    tech_stack: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a basic Architecture document using the BMAD workflow."""
    workflows = get_basic_workflows()
    return await workflows.create_basic_architecture_workflow(project_name, prd_id, tech_stack)


async def create_basic_story(
    project_name: str,
    prd_id: str,
    arch_id: str,
    user_stories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a basic Story document using the BMAD workflow."""
    workflows = get_basic_workflows()
    return await workflows.create_basic_story_workflow(project_name, prd_id, arch_id, user_stories)


async def run_complete_basic_workflow(
    project_name: str,
    goals: Optional[List[str]] = None,
    background: Optional[str] = None,
    tech_stack: Optional[List[str]] = None,
    user_stories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Run the complete basic workflow: PRD → Architecture → Story."""
    workflows = get_basic_workflows()
    return await workflows.run_complete_basic_workflow(
        project_name, goals, background, tech_stack, user_stories
    )
