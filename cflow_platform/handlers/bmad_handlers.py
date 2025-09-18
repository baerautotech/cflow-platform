"""
BMAD Planning Tools Handlers

This module provides handlers for BMAD planning tools that will eventually
call the BMAD HTTP API facade on the cerebral cluster. For now, it provides
local implementations using the vendored BMAD templates.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from cflow_platform.core.config.supabase_config import get_api_key, get_rest_url
from supabase import create_client

# Load environment variables
load_dotenv()


class BMADHandlers:
    """Handlers for BMAD planning tools."""

    def __init__(self):
        self.supabase_client = None
        self._ensure_supabase()

    def _ensure_supabase(self) -> None:
        """Create and cache a Supabase client."""
        if self.supabase_client is not None:
            return
        
        url = get_rest_url()
        # Use service role key for Knowledge Graph operations
        key = get_api_key(secure=True)  # This will get the service role key
        if url and key:
            try:
                self.supabase_client = create_client(url, key)
            except Exception as e:
                print(f"Supabase client creation failed: {e}")
                self.supabase_client = None

    async def bmad_prd_create(self, project_name: str, goals: Optional[List[str]] = None, background: Optional[str] = None) -> Dict[str, Any]:
        """Create a new PRD document using BMAD templates."""
        try:
            # Load BMAD PRD template
            template_path = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "bmad-core" / "templates" / "prd-tmpl.yaml"
            
            if not template_path.exists():
                return {
                    "success": False,
                    "error": "BMAD PRD template not found",
                    "doc_id": None
                }

            # Create document record (using existing schema)
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "tenant_id": "00000000-0000-0000-0000-000000000100",  # Default tenant UUID
                "project_id": str(uuid.uuid4()),  # Generate project ID
                "kind": "PRD",  # Document type
                "version": 1,  # Document version
                "status": "draft",  # Document status
                "content": self._generate_prd_content(project_name, goals, background),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in Supabase if available
            if self.supabase_client:
                try:
                    result = self.supabase_client.table("cerebral_documents").insert(doc_data).execute()
                    if result.data:
                        # Automatically index into Knowledge Graph
                        kg_result = await self._index_to_knowledge_graph(
                            doc_id=doc_id,
                            title=f"{project_name} Product Requirements Document",
                            content=self._generate_prd_content(project_name, goals, background),
                            content_type="PRD",
                            metadata={"project_name": project_name, "goals": goals or [], "background": background or ""}
                        )
                        
                        kg_status = " and indexed to Knowledge Graph" if kg_result.get("success") else " (KG indexing failed)"
                        
                        return {
                            "success": True,
                            "doc_id": doc_id,
                            "message": f"PRD document created successfully for {project_name} and stored in Supabase{kg_status}",
                            "data": result.data[0],
                            "kg_indexed": kg_result.get("success", False)
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to store in Supabase: {str(e)}",
                        "doc_id": doc_id
                    }

            # Fallback: return document data without storage
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"PRD document created locally for {project_name} (not stored)",
                "data": doc_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create PRD: {str(e)}",
                "doc_id": None
            }

    async def bmad_arch_create(self, project_name: str, prd_id: str, tech_stack: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new Architecture document using BMAD templates."""
        try:
            # Load BMAD Architecture template
            template_path = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "bmad-core" / "templates" / "architecture-tmpl.yaml"
            
            if not template_path.exists():
                return {
                    "success": False,
                    "error": "BMAD Architecture template not found",
                    "doc_id": None
                }

            # Create document record (using existing schema)
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "tenant_id": "00000000-0000-0000-0000-000000000100",  # Default tenant UUID
                "project_id": str(uuid.uuid4()),  # Generate project ID
                "kind": "ARCHITECTURE",  # Document type
                "version": 1,  # Document version
                "status": "draft",  # Document status
                "content": self._generate_arch_content(project_name, tech_stack),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in Supabase if available
            if self.supabase_client:
                try:
                    result = self.supabase_client.table("cerebral_documents").insert(doc_data).execute()
                    if result.data:
                        # Automatically index into Knowledge Graph
                        kg_result = await self._index_to_knowledge_graph(
                            doc_id=doc_id,
                            title=f"{project_name} Architecture Document",
                            content=self._generate_arch_content(project_name, tech_stack),
                            content_type="ARCH",
                            metadata={"project_name": project_name, "prd_id": prd_id, "tech_stack": tech_stack or []}
                        )
                        
                        kg_status = " and indexed to Knowledge Graph" if kg_result.get("success") else " (KG indexing failed)"
                        
                        return {
                            "success": True,
                            "doc_id": doc_id,
                            "message": f"Architecture document created successfully for {project_name} and stored in Supabase{kg_status}",
                            "data": result.data[0],
                            "kg_indexed": kg_result.get("success", False)
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to store in Supabase: {str(e)}",
                        "doc_id": doc_id
                    }

            # Fallback: return document data without storage
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"Architecture document created locally for {project_name} (not stored)",
                "data": doc_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Architecture document: {str(e)}",
                "doc_id": None
            }

    async def bmad_story_create(self, project_name: str, prd_id: str, arch_id: str, user_stories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new User Story document using BMAD templates."""
        try:
            # Load BMAD Story template
            template_path = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "bmad-core" / "templates" / "story-tmpl.yaml"
            
            if not template_path.exists():
                return {
                    "success": False,
                    "error": "BMAD Story template not found",
                    "doc_id": None
                }

            # Create document record (using existing schema)
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "tenant_id": "00000000-0000-0000-0000-000000000100",  # Default tenant UUID
                "project_id": str(uuid.uuid4()),  # Generate project ID
                "kind": "STORY",  # Document type
                "version": 1,  # Document version
                "status": "draft",  # Document status
                "content": self._generate_story_content(project_name, user_stories),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in Supabase if available
            if self.supabase_client:
                try:
                    result = self.supabase_client.table("cerebral_documents").insert(doc_data).execute()
                    if result.data:
                        # Automatically index into Knowledge Graph
                        kg_result = await self._index_to_knowledge_graph(
                            doc_id=doc_id,
                            title=f"{project_name} User Story Document",
                            content=self._generate_story_content(project_name, user_stories),
                            content_type="STORY",
                            metadata={"project_name": project_name, "prd_id": prd_id, "arch_id": arch_id, "user_stories": user_stories or []}
                        )
                        
                        kg_status = " and indexed to Knowledge Graph" if kg_result.get("success") else " (KG indexing failed)"
                        
                        return {
                            "success": True,
                            "doc_id": doc_id,
                            "message": f"Story document created successfully for {project_name} and stored in Supabase{kg_status}",
                            "data": result.data[0],
                            "kg_indexed": kg_result.get("success", False)
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to store in Supabase: {str(e)}",
                        "doc_id": doc_id
                    }

            # Fallback: return document data without storage
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"Story document created locally for {project_name} (not stored)",
                "data": doc_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Story document: {str(e)}",
                "doc_id": None
            }

    async def bmad_doc_list(self, project_id: Optional[str] = None, doc_type: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """List BMAD documents with optional filtering."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "documents": []
                }

            # Build query
            query = self.supabase_client.table("cerebral_documents").select("*")
            
            if project_id:
                query = query.eq("project_id", project_id)
            if doc_type:
                query = query.eq("type", doc_type)
            if status:
                query = query.eq("status", status)

            result = query.execute()
            
            return {
                "success": True,
                "documents": result.data or [],
                "count": len(result.data or [])
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list documents: {str(e)}",
                "documents": []
            }

    async def bmad_doc_approve(self, doc_id: str, approver: str) -> Dict[str, Any]:
        """Approve a BMAD document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Update document status
            result = self.supabase_client.table("cerebral_documents").update({
                "status": "approved",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("doc_id", doc_id).execute()

            if result.data:
                # Log approval activity
                activity_data = {
                    "activity_id": str(uuid.uuid4()),
                    "tenant_id": "default",
                    "actor": approver,
                    "action": "approve",
                    "resource_type": "document",
                    "resource_id": doc_id,
                    "metadata": {"approved_by": approver},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                self.supabase_client.table("cerebral_activities").insert(activity_data).execute()
                
                return {
                    "success": True,
                    "message": f"Document {doc_id} approved by {approver}",
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Document not found or update failed"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to approve document: {str(e)}"
            }

    def _generate_prd_content(self, project_name: str, goals: Optional[List[str]], background: Optional[str]) -> str:
        """Generate PRD content from template and parameters."""
        content = f"""# {project_name} Product Requirements Document (PRD)

## Goals and Background Context

### Goals
{chr(10).join(f"- {goal}" for goal in (goals or ["Define product requirements"]))}

### Background Context
{background or "This document outlines the product requirements for " + project_name + "."}

## User Research and Personas

*[To be filled during interactive elicitation]*

## Functional Requirements

*[To be filled during interactive elicitation]*

## Non-Functional Requirements

*[To be filled during interactive elicitation]*

## Success Metrics and KPIs

*[To be filled during interactive elicitation]*

## Risks and Assumptions

*[To be filled during interactive elicitation]*

## Timeline and Milestones

*[To be filled during interactive elicitation]*

## Appendices and References

*[To be filled during interactive elicitation]*
"""
        return content

    async def _index_to_knowledge_graph(self, doc_id: str, title: str, content: str, content_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Index BMAD document into Knowledge Graph for RAG search."""
        if not self.supabase_client:
            return {"success": False, "error": "Supabase client not available"}
        
        try:
            # Create knowledge graph entry for BMAD document
            kg_data = {
                "id": str(uuid.uuid4()),
                "tenant_id": "00000000-0000-0000-0000-000000000100",  # Default tenant UUID
                "doc_id": doc_id,
                "title": title,
                "content": content,
                "content_type": content_type,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in knowledge graph table
            result = self.supabase_client.table("agentic_knowledge_chunks").insert(kg_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "kg_id": kg_data["id"],
                    "message": f"Document indexed to Knowledge Graph successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to insert into knowledge graph table"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Knowledge Graph indexing failed: {str(e)}"}

    def _generate_arch_content(self, project_name: str, tech_stack: Optional[List[str]]) -> str:
        """Generate Architecture content from template and parameters."""
        tech_list = ", ".join(tech_stack or ["Python", "React", "PostgreSQL"])
        
        content = f"""# {project_name} Architecture Document

## Introduction

This document outlines the overall project architecture for {project_name}, including backend systems, shared services, and non-UI specific concerns.

## Technology Stack

**Core Technologies:**
{chr(10).join(f"- {tech}" for tech in (tech_stack or ["Python", "React", "PostgreSQL"]))}

## System Architecture

*[To be filled during interactive elicitation]*

## Data Architecture

*[To be filled during interactive elicitation]*

## Security Architecture

*[To be filled during interactive elicitation]*

## Deployment Architecture

*[To be filled during interactive elicitation]*

## Integration Patterns

*[To be filled during interactive elicitation]*

## Performance Considerations

*[To be filled during interactive elicitation]*
"""
        return content

    def _generate_story_content(self, project_name: str, user_stories: Optional[List[str]]) -> str:
        """Generate Story content from template and parameters."""
        stories_list = chr(10).join(f"- {story}" for story in (user_stories or ["As a user, I want to..."]))
        
        content = f"""# {project_name} User Story Document

## Story Overview

This document outlines the user stories and implementation approach for {project_name}.

## User Stories

{stories_list}

## Acceptance Criteria

*[To be filled during interactive elicitation]*

## Implementation Notes

*[To be filled during interactive elicitation]*

## Testing Strategy

*[To be filled during interactive elicitation]*

## Dependencies

*[To be filled during interactive elicitation]*
"""
        return content

    # BMAD Orchestration & Workflow Gates

    async def bmad_master_checklist(self, prd_id: str, arch_id: str) -> Dict[str, Any]:
        """Run PO master checklist to validate PRD/Architecture alignment."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Get PRD and Architecture documents
            prd_result = self.supabase_client.table("cerebral_documents").select("*").eq("id", prd_id).execute()
            arch_result = self.supabase_client.table("cerebral_documents").select("*").eq("id", arch_id).execute()

            if not prd_result.data or not arch_result.data:
                return {
                    "success": False,
                    "error": "PRD or Architecture document not found"
                }

            prd_doc = prd_result.data[0]
            arch_doc = arch_result.data[0]

            # Master checklist validation
            checklist_results = {
                "prd_complete": prd_doc.get("status") == "approved",
                "arch_complete": arch_doc.get("status") == "approved",
                "prd_arch_aligned": self._validate_prd_arch_alignment(prd_doc, arch_doc),
                "tech_stack_defined": bool(arch_doc.get("content", "").strip()),
                "goals_defined": bool(prd_doc.get("content", "").strip())
            }

            all_passed = all(checklist_results.values())
            
            return {
                "success": True,
                "checklist_passed": all_passed,
                "results": checklist_results,
                "message": "Master checklist completed successfully" if all_passed else "Master checklist failed - documents need revision",
                "next_action": "Create epics" if all_passed else "Revise PRD or Architecture"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Master checklist failed: {str(e)}"
            }

    async def bmad_epic_create(self, project_name: str, prd_id: str, arch_id: str) -> Dict[str, Any]:
        """Create epics from PRD and Architecture."""
        try:
            # First run master checklist
            checklist_result = await self.bmad_master_checklist(prd_id, arch_id)
            if not checklist_result.get("checklist_passed", False):
                return {
                    "success": False,
                    "error": "Master checklist failed - cannot create epics",
                    "checklist_results": checklist_result.get("results", {})
                }

            # Create epic document record
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "tenant_id": "00000000-0000-0000-0000-000000000100",
                "project_id": str(uuid.uuid4()),
                "kind": "EPIC",
                "version": 1,
                "status": "draft",
                "content": self._generate_epic_content(project_name, prd_id, arch_id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in Supabase if available
            if self.supabase_client:
                try:
                    result = self.supabase_client.table("cerebral_documents").insert(doc_data).execute()
                    if result.data:
                        # Index into Knowledge Graph
                        kg_result = await self._index_to_knowledge_graph(
                            doc_id=doc_id,
                            title=f"{project_name} Epic Document",
                            content=self._generate_epic_content(project_name, prd_id, arch_id),
                            content_type="EPIC",
                            metadata={"project_name": project_name, "prd_id": prd_id, "arch_id": arch_id}
                        )
                        
                        kg_status = " and indexed to Knowledge Graph" if kg_result.get("success") else " (KG indexing failed)"
                        
                        return {
                            "success": True,
                            "doc_id": doc_id,
                            "message": f"Epic document created successfully for {project_name} and stored in Supabase{kg_status}",
                            "data": result.data[0],
                            "kg_indexed": kg_result.get("success", False)
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to store in Supabase: {str(e)}",
                        "doc_id": doc_id
                    }
            else:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "message": f"Epic document created successfully for {project_name} (local only)",
                    "data": doc_data
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create epic: {str(e)}",
                "doc_id": None
            }

    async def bmad_orchestrator_status(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Check current BMAD workflow status."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Get all documents for project
            query = self.supabase_client.table("cerebral_documents")
            if project_id:
                query = query.eq("project_id", project_id)
            
            result = query.select("*").execute()
            documents = result.data

            # Analyze workflow status
            workflow_status = {
                "prd_exists": any(doc["kind"] == "PRD" for doc in documents),
                "arch_exists": any(doc["kind"] == "ARCHITECTURE" for doc in documents),
                "epic_exists": any(doc["kind"] == "EPIC" for doc in documents),
                "story_exists": any(doc["kind"] == "STORY" for doc in documents),
                "current_step": self._determine_current_step(documents),
                "next_action": self._determine_next_action(documents),
                "documents": documents
            }

            return {
                "success": True,
                "workflow_status": workflow_status,
                "message": f"Workflow status: {workflow_status['current_step']}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get orchestrator status: {str(e)}"
            }

    async def bmad_workflow_next(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get next recommended action in workflow."""
        try:
            # Get current workflow status
            status_result = await self.bmad_orchestrator_status(project_id)
            if not status_result.get("success"):
                return status_result

            workflow_status = status_result["workflow_status"]
            current_step = workflow_status["current_step"]
            next_action = workflow_status["next_action"]

            return {
                "success": True,
                "current_step": current_step,
                "next_action": next_action,
                "workflow_status": workflow_status,
                "message": f"Next action: {next_action}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get next workflow action: {str(e)}"
            }

    # Helper methods

    def _validate_prd_arch_alignment(self, prd_doc: Dict[str, Any], arch_doc: Dict[str, Any]) -> bool:
        """Validate that PRD and Architecture are aligned."""
        # Basic validation - both documents should have content
        prd_content = prd_doc.get("content", "")
        arch_content = arch_doc.get("content", "")
        
        # Check if both documents have substantial content
        return len(prd_content.strip()) > 100 and len(arch_content.strip()) > 100

    def _generate_epic_content(self, project_name: str, prd_id: str, arch_id: str) -> str:
        """Generate epic content from PRD and Architecture."""
        return f"""# {project_name} Epic Document

## Epic Overview

This document outlines the epics for {project_name} based on the PRD and Architecture documents.

## Epics

### Epic 1: Core Functionality
- **Description**: Implement core functionality as defined in PRD
- **Dependencies**: PRD ({prd_id}), Architecture ({arch_id})
- **Status**: Draft

### Epic 2: User Interface
- **Description**: Implement user interface components
- **Dependencies**: Core functionality epic
- **Status**: Draft

### Epic 3: Integration
- **Description**: Integrate with external systems
- **Dependencies**: Core functionality epic
- **Status**: Draft

## Acceptance Criteria

*[To be filled during interactive elicitation]*

## Implementation Notes

*[To be filled during interactive elicitation]*

## Testing Strategy

*[To be filled during interactive elicitation]*

## Dependencies

*[To be filled during interactive elicitation]*
"""

    def _determine_current_step(self, documents: List[Dict[str, Any]]) -> str:
        """Determine current step in BMAD workflow."""
        doc_types = [doc["kind"] for doc in documents]
        
        if "STORY" in doc_types:
            return "Stories Created"
        elif "EPIC" in doc_types:
            return "Epics Created"
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
        elif "EPIC" in doc_types:
            return "Create Stories"
        elif "ARCHITECTURE" in doc_types:
            return "Run Master Checklist"
        elif "PRD" in doc_types:
            return "Create Architecture"
        else:
            return "Create PRD"
