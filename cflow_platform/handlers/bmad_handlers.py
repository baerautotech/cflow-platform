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
