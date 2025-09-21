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
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from cflow_platform.core.config.supabase_config import get_api_key, get_rest_url
from cflow_platform.core.bmad_hil_integration import BMADHILIntegration
from cflow_platform.core.bmad_git_workflow import BMADGitWorkflow
from cflow_platform.core.vault_integration import get_vault_integration
from cflow_platform.core.bmad_template_loader import get_bmad_template_loader
from supabase import create_client

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class BMADHandlers:
    """Handlers for BMAD planning tools."""

    def __init__(self):
        self.supabase_client = None
        self.bmad_hil = BMADHILIntegration()
        self.bmad_git = BMADGitWorkflow()
        self.vault = get_vault_integration()
        self.template_loader = get_bmad_template_loader()
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
        """Create a new PRD document using BMAD templates from S3 storage."""
        try:
            # Load BMAD PRD template from S3 (with local fallback)
            template = await self.template_loader.load_template("prd", "core")
            
            if not template:
                return {
                    "success": False,
                    "error": "BMAD PRD template not found in S3 or local fallback",
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
                "content": self._generate_prd_content_from_template(project_name, goals, background, template.content),
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
                            content=self._generate_prd_content_from_template(project_name, goals, background, template.content),
                            content_type="PRD",
                            metadata={
                                "project_name": project_name, 
                                "goals": goals or [], 
                                "background": background or "",
                                "template_source": template.loaded_from,
                                "template_pack": template.pack_name or "core"
                            }
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
        """Create a new Architecture document using BMAD templates from S3 storage."""
        try:
            # Load BMAD Architecture template from S3 (with local fallback)
            template = await self.template_loader.load_template("architecture", "core")
            
            if not template:
                return {
                    "success": False,
                    "error": "BMAD Architecture template not found in S3 or local fallback",
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
                "content": self._generate_arch_content_from_template(project_name, tech_stack, template.content),
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
        """Create a new User Story document using BMAD templates from S3 storage."""
        try:
            # Load BMAD Story template from S3 (with local fallback)
            template = await self.template_loader.load_template("story", "core")
            
            if not template:
                return {
                    "success": False,
                    "error": "BMAD Story template not found in S3 or local fallback",
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
                "content": self._generate_story_content_from_template(project_name, user_stories, template.content),
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
                query = query.eq("kind", doc_type)
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

    def _generate_prd_content_from_template(self, project_name: str, goals: Optional[List[str]], background: Optional[str], template_content: str) -> str:
        """Generate PRD content from S3-loaded template and parameters."""
        try:
            # Parse template content (assuming it's YAML with placeholders)
            import yaml
            template_data = yaml.safe_load(template_content)
            
            if isinstance(template_data, dict):
                # Replace placeholders with actual values
                content = template_content
                
                # Replace common placeholders
                replacements = {
                    "{{project_name}}": project_name,
                    "{{goals}}": "\n".join(f"- {goal}" for goal in (goals or ["Define product requirements"])),
                    "{{background}}": background or f"This document outlines the product requirements for {project_name}.",
                    "{{date}}": datetime.now().strftime("%Y-%m-%d"),
                    "{{goals_list}}": ", ".join(goals or ["Define product requirements"]),
                }
                
                for placeholder, value in replacements.items():
                    content = content.replace(placeholder, str(value))
                
                return content
            else:
                # Fallback to simple template processing
                return self._process_simple_template(template_content, {
                    "project_name": project_name,
                    "goals": goals or ["Define product requirements"],
                    "background": background or f"This document outlines the product requirements for {project_name}."
                })
                
        except Exception as e:
            print(f"[WARN] BMAD Handlers: Failed to process PRD template: {e}")
            # Fallback to original method
            return self._generate_prd_content_legacy(project_name, goals, background)
    
    def _generate_prd_content_legacy(self, project_name: str, goals: Optional[List[str]], background: Optional[str]) -> str:
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

    def _generate_arch_content_from_template(self, project_name: str, tech_stack: Optional[List[str]], template_content: str) -> str:
        """Generate Architecture content from S3-loaded template and parameters."""
        try:
            # Parse template content (assuming it's YAML with placeholders)
            import yaml
            template_data = yaml.safe_load(template_content)
            
            if isinstance(template_data, dict):
                # Replace placeholders with actual values
                content = template_content
                
                # Replace common placeholders
                replacements = {
                    "{{project_name}}": project_name,
                    "{{tech_stack}}": "\n".join(f"- {tech}" for tech in (tech_stack or ["Technology stack to be defined"])),
                    "{{tech_stack_list}}": ", ".join(tech_stack or ["Technology stack to be defined"]),
                    "{{date}}": datetime.now().strftime("%Y-%m-%d"),
                }
                
                for placeholder, value in replacements.items():
                    content = content.replace(placeholder, str(value))
                
                return content
            else:
                # Fallback to simple template processing
                return self._process_simple_template(template_content, {
                    "project_name": project_name,
                    "tech_stack": tech_stack or ["Technology stack to be defined"]
                })
                
        except Exception as e:
            print(f"[WARN] BMAD Handlers: Failed to process Architecture template: {e}")
            # Fallback to original method
            return self._generate_arch_content_legacy(project_name, tech_stack)
    
    def _generate_arch_content(self, project_name: str, tech_stack: Optional[List[str]]) -> str:
        """Generate Architecture content from parameters."""
        return self._generate_arch_content_legacy(project_name, tech_stack)

    def _generate_arch_content_legacy(self, project_name: str, tech_stack: Optional[List[str]]) -> str:
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

    def _generate_story_content_from_template(self, project_name: str, user_stories: Optional[List[str]], template_content: str) -> str:
        """Generate Story content from S3-loaded template and parameters."""
        try:
            # Parse template content (assuming it's YAML with placeholders)
            import yaml
            template_data = yaml.safe_load(template_content)
            
            if isinstance(template_data, dict):
                # Replace placeholders with actual values
                content = template_content
                
                # Replace common placeholders
                replacements = {
                    "{{project_name}}": project_name,
                    "{{user_stories}}": "\n".join(f"- {story}" for story in (user_stories or ["User stories to be defined"])),
                    "{{user_stories_list}}": ", ".join(user_stories or ["User stories to be defined"]),
                    "{{date}}": datetime.now().strftime("%Y-%m-%d"),
                }
                
                for placeholder, value in replacements.items():
                    content = content.replace(placeholder, str(value))
                
                return content
            else:
                # Fallback to simple template processing
                return self._process_simple_template(template_content, {
                    "project_name": project_name,
                    "user_stories": user_stories or ["User stories to be defined"]
                })
                
        except Exception as e:
            print(f"[WARN] BMAD Handlers: Failed to process Story template: {e}")
            # Fallback to original method
            return self._generate_story_content_legacy(project_name, user_stories)
    
    def _generate_story_content(self, project_name: str, user_stories: Optional[List[str]]) -> str:
        """Generate Story content from parameters."""
        return self._generate_story_content_legacy(project_name, user_stories)

    def _generate_story_content_legacy(self, project_name: str, user_stories: Optional[List[str]]) -> str:
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
    
    def _process_simple_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Process a simple template with variable substitution."""
        content = template_content
        
        # Replace common placeholders
        for key, value in variables.items():
            if isinstance(value, list):
                # Handle list values
                list_content = "\n".join(f"- {item}" for item in value)
                content = content.replace(f"{{{{{key}}}}}", list_content)
                content = content.replace(f"{{{{{key}_list}}}}", ", ".join(str(item) for item in value))
            else:
                content = content.replace(f"{{{{{key}}}}}", str(value))
        
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
                "prd_complete": prd_doc.get("status") in ["approved", "review"] and not self._has_template_placeholders(prd_doc.get("content", "")),
                "arch_complete": arch_doc.get("status") in ["approved", "review"] and not self._has_template_placeholders(arch_doc.get("content", "")),
                "prd_arch_aligned": self._validate_prd_arch_alignment(prd_doc, arch_doc),
                "tech_stack_defined": bool(arch_doc.get("content", "").strip()),
                "goals_defined": bool(prd_doc.get("content", "").strip())
            }

            all_passed = all(checklist_results.values())
            
            # If checklist fails, trigger BMAD HIL sessions
            if not all_passed:
                # Determine which documents need HIL completion
                hil_triggered = False
                hil_sessions = []
                
                if not checklist_results["prd_complete"]:
                    hil_result = await self.bmad_hil.trigger_hil_session(
                        prd_id, "PRD", {"workflow_step": "master_checklist", "checklist_results": checklist_results}
                    )
                    if hil_result["success"]:
                        hil_triggered = True
                        hil_sessions.append(hil_result)
                
                if not checklist_results["arch_complete"]:
                    hil_result = await self.bmad_hil.trigger_hil_session(
                        arch_id, "ARCH", {"workflow_step": "master_checklist", "checklist_results": checklist_results}
                    )
                    if hil_result["success"]:
                        hil_triggered = True
                        hil_sessions.append(hil_result)
                
                return {
                    "success": True,
                    "checklist_passed": False,
                    "results": checklist_results,
                    "bmad_hil_triggered": hil_triggered,
                    "hil_sessions": hil_sessions,
                    "workflow_paused": True,
                    "message": "Master checklist failed - BMAD HIL sessions triggered for document completion",
                    "next_action": "Complete HIL sessions to continue workflow"
                }
            
            return {
                "success": True,
                "checklist_passed": all_passed,
                "results": checklist_results,
                "message": "Master checklist completed successfully",
                "next_action": "Create epics"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Master checklist failed: {str(e)}"
            }

    async def bmad_epic_create(self, project_name: str, prd_id: str, arch_id: str) -> Dict[str, Any]:
        """Create epics in cluster database with proper multi-user support."""
        try:
            # First run master checklist
            checklist_result = await self.bmad_master_checklist(prd_id, arch_id)
            if not checklist_result.get("checklist_passed", False):
                return {
                    "success": False,
                    "error": "Master checklist failed - cannot create epics",
                    "checklist_results": checklist_result.get("results", {})
                }

            # Get PRD document to extract epics
            prd_doc = await self._get_document(prd_id)
            if not prd_doc:
                return {"success": False, "error": "PRD document not found"}

            # Parse PRD content to extract epic sections
            epics = await self._extract_epics_from_prd(prd_doc['content'])
            
            if not epics:
                return {
                    "success": False,
                    "error": "No epics found in PRD content. PRD must contain epic sections."
                }
            
            # Create epic documents in database
            created_epics = []
            for epic_data in epics:
                epic_doc = await self._create_epic_document(
                    project_id=prd_doc['project_id'],
                    epic_data=epic_data,
                    prd_id=prd_id,
                    arch_id=arch_id
                )
                if epic_doc:
                    created_epics.append(epic_doc)

            if not created_epics:
                return {
                    "success": False,
                    "error": "Failed to create any epic documents"
                }

            return {
                "success": True,
                "epics_created": len(created_epics),
                "epic_ids": [epic['id'] for epic in created_epics],
                "message": f"Created {len(created_epics)} epics for {project_name} in cluster database",
                "next_action": "create_stories_from_epics",
                "note": "Epics stored in cluster database for multi-user access"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create epics: {str(e)}"
            }


    async def bmad_workflow_next(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get next recommended action in workflow."""
        try:
            # Use basic workflow status instead of orchestrator status
            from ..core.basic_workflow_implementations import get_basic_workflows
            workflows = get_basic_workflows()
            
            if not project_id:
                return {
                    "success": False,
                    "error": "project_id is required"
                }
            
            status_result = await workflows.get_workflow_status(project_id)
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

    async def _get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID from Supabase."""
        try:
            if not self.supabase_client:
                return None
            
            result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting document {doc_id}: {e}")
            return None

    async def _extract_epics_from_prd(self, prd_content: str) -> List[Dict[str, Any]]:
        """Extract epic data from PRD content."""
        epics = []
        
        # Parse PRD content to find epic sections
        # Look for patterns like "Epic 1:", "Epic 2:", etc.
        import re
        
        epic_pattern = r'Epic (\d+):\s*([^\n]+)\s*\n(.*?)(?=Epic \d+:|$)'
        matches = re.findall(epic_pattern, prd_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            epic_number = int(match[0])
            epic_title = match[1].strip()
            epic_content = match[2].strip()
            
            # Extract epic goal from content
            goal_match = re.search(r'goal[:\s]+([^\n]+)', epic_content, re.IGNORECASE)
            epic_goal = goal_match.group(1).strip() if goal_match else f"Complete {epic_title}"
            
            epics.append({
                'number': epic_number,
                'title': epic_title,
                'goal': epic_goal,
                'content': f"# Epic {epic_number}: {epic_title}\n\n## Epic Goal\n\n{epic_goal}\n\n## Epic Content\n\n{epic_content}"
            })
        
        return epics

    async def _create_epic_document(self, project_id: str, epic_data: Dict[str, Any], prd_id: str, arch_id: str) -> Optional[Dict[str, Any]]:
        """Create epic document in database with metadata."""
        try:
            # Create epic document record
            epic_doc_id = str(uuid.uuid4())
            epic_doc = {
                "id": epic_doc_id,
                "tenant_id": "00000000-0000-0000-0000-000000000100",
                "project_id": project_id,
                "kind": "EPIC",  # Now supported in database
                "version": 1,
                "status": "draft",
                "content": epic_data['content'],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in database
            result = await self.supabase_client.table("cerebral_documents").insert(epic_doc).execute()
            
            if result.data:
                # Create epic metadata
                epic_metadata = {
                    "epic_doc_id": epic_doc_id,
                    "epic_number": epic_data['number'],
                    "epic_title": epic_data['title'],
                    "epic_goal": epic_data['goal'],
                    "epic_status": "draft",
                    "parent_prd_id": prd_id
                }
                
                await self.supabase_client.table("epic_metadata").insert(epic_metadata).execute()
                
                # Store epic content in object storage if large
                if len(epic_data['content']) > 10000:  # 10KB threshold
                    await self._store_epic_content_in_s3(epic_doc_id, epic_data['content'])
                
                # Index in Knowledge Graph
                try:
                    await self._index_document_in_kg(epic_doc_id, epic_data['content'], 'EPIC')
                except Exception as e:
                    print(f"KG indexing failed for epic {epic_doc_id}: {e}")
                
                return epic_doc
            
            return None
            
        except Exception as e:
            print(f"Error creating epic document: {e}")
            return None

    async def _store_epic_content_in_s3(self, epic_doc_id: str, content: str) -> bool:
        """Store large epic content in S3 bucket."""
        try:
            # This would integrate with MinIO S3
            # For now, just create a reference record
            storage_ref = {
                "document_id": epic_doc_id,
                "storage_type": "epic_content",
                "bucket_name": "bmad-epics",
                "object_key": f"epics/{epic_doc_id}/content.md",
                "object_size": len(content),
                "content_type": "text/markdown",
                "storage_metadata": {"epic_doc_id": epic_doc_id}
            }
            
            await self.supabase_client.table("object_storage_refs").insert(storage_ref).execute()
            return True
            
        except Exception as e:
            print(f"Error storing epic content in S3: {e}")
            return False

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

    # BMAD Expansion Packs

    async def bmad_expansion_packs_list(self) -> Dict[str, Any]:
        """List available BMAD expansion packs."""
        try:
            # List available expansion packs from vendor directory
            expansion_packs_dir = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "expansion-packs"
            
            if not expansion_packs_dir.exists():
                return {
                    "success": False,
                    "error": "BMAD expansion packs directory not found"
                }

            packs = []
            for pack_dir in expansion_packs_dir.iterdir():
                if pack_dir.is_dir() and pack_dir.name.startswith("bmad-"):
                    config_path = pack_dir / "config.yaml"
                    if config_path.exists():
                        try:
                            import yaml
                            with open(config_path, 'r') as f:
                                config = yaml.safe_load(f)
                            packs.append({
                                "id": pack_dir.name,
                                "name": config.get("name", pack_dir.name),
                                "description": config.get("description", ""),
                                "version": config.get("version", "1.0.0"),
                                "category": config.get("category", "General"),
                                "commercial": config.get("commercial", False),
                                "price": config.get("price", "Free"),
                                "features": config.get("features", []),
                                "agents": config.get("agents", []),
                                "path": str(pack_dir)
                            })
                        except ImportError:
                            # YAML module not available, parse manually
                            with open(config_path, 'r') as f:
                                content = f.read()
                            # Simple parsing for key fields
                            name = pack_dir.name.replace('bmad-', '').replace('-', ' ').title()
                            commercial = 'commercial: true' in content.lower()
                            price = 'Free'
                            if commercial:
                                if '$299' in content:
                                    price = '$299/year'
                                elif '$349' in content:
                                    price = '$349/year'
                                elif '$399' in content:
                                    price = '$399/year'
                                elif '$449' in content:
                                    price = '$449/year'
                            
                            packs.append({
                                "id": pack_dir.name,
                                "name": name,
                                "description": f"BMAD {name} Expansion Pack",
                                "version": "1.0.0",
                                "category": "Commercial" if commercial else "Free",
                                "commercial": commercial,
                                "price": price,
                                "features": [],
                                "agents": [],
                                "path": str(pack_dir)
                            })
                        except Exception as e:
                            packs.append({
                                "id": pack_dir.name,
                                "name": pack_dir.name,
                                "description": "Expansion pack",
                                "version": "1.0.0",
                                "category": "General",
                                "commercial": False,
                                "price": "Free",
                                "features": [],
                                "agents": [],
                                "path": str(pack_dir)
                            })

            return {
                "success": True,
                "expansion_packs": packs,
                "count": len(packs)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list expansion packs: {str(e)}"
            }

    async def bmad_expansion_packs_install(self, pack_id: str) -> Dict[str, Any]:
        """Install BMAD expansion pack."""
        try:
            # For now, expansion packs are already in vendor directory
            # This would typically download and install from a registry
            expansion_packs_dir = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "expansion-packs"
            pack_path = expansion_packs_dir / pack_id
            
            if not pack_path.exists():
                return {
                    "success": False,
                    "error": f"Expansion pack {pack_id} not found"
                }

            return {
                "success": True,
                "pack_id": pack_id,
                "message": f"Expansion pack {pack_id} is already available",
                "path": str(pack_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to install expansion pack: {str(e)}"
            }

    async def bmad_expansion_packs_enable(self, project_id: str, pack_id: str) -> Dict[str, Any]:
        """Enable expansion pack for project."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Store expansion pack enablement in database
            enablement_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "pack_id": pack_id,
                "enabled_at": datetime.utcnow().isoformat(),
                "status": "enabled"
            }

            result = self.supabase_client.table("project_expansion_packs").insert(enablement_data).execute()

            if result.data:
                return {
                    "success": True,
                    "project_id": project_id,
                    "pack_id": pack_id,
                    "message": f"Expansion pack {pack_id} enabled for project {project_id}",
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to enable expansion pack"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to enable expansion pack: {str(e)}"
            }

    # Missing Update Methods

    async def bmad_prd_update(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update PRD document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "doc_id": doc_id
                }

            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()

            result = self.supabase_client.table("cerebral_documents").update(updates).eq("id", doc_id).execute()

            if result.data:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "message": f"PRD document {doc_id} updated successfully",
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": f"PRD document {doc_id} not found",
                    "doc_id": doc_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update PRD: {str(e)}",
                "doc_id": doc_id
            }

    async def bmad_prd_get(self, doc_id: str) -> Dict[str, Any]:
        """Get PRD document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "doc_id": doc_id
                }

            result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).eq("kind", "PRD").execute()

            if result.data:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": f"PRD document {doc_id} not found",
                    "doc_id": doc_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get PRD: {str(e)}",
                "doc_id": doc_id
            }

    async def bmad_arch_update(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update Architecture document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "doc_id": doc_id
                }

            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()

            result = self.supabase_client.table("cerebral_documents").update(updates).eq("id", doc_id).execute()

            if result.data:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "message": f"Architecture document {doc_id} updated successfully",
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": f"Architecture document {doc_id} not found",
                    "doc_id": doc_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update Architecture: {str(e)}",
                "doc_id": doc_id
            }

    async def bmad_arch_get(self, doc_id: str) -> Dict[str, Any]:
        """Get Architecture document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "doc_id": doc_id
                }

            result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).eq("kind", "ARCHITECTURE").execute()

            if result.data:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": f"Architecture document {doc_id} not found",
                    "doc_id": doc_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get Architecture: {str(e)}",
                "doc_id": doc_id
            }

    # Human-in-the-Loop (HIL) Interactive Sessions

    async def bmad_hil_start_session(self, doc_id: str, doc_type: str, session_type: str) -> Dict[str, Any]:
        """Start BMAD-style HIL interactive session for document completion."""
        try:
            # Use the real BMAD HIL integration
            workflow_context = {
                "workflow_step": "manual_hil_start",
                "session_type": session_type
            }
            
            return await self.bmad_hil.trigger_hil_session(doc_id, doc_type, workflow_context)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start BMAD HIL session: {str(e)}"
            }

    async def bmad_hil_continue_session(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """Continue BMAD-style HIL interactive session with user response."""
        try:
            # Use the real BMAD HIL integration
            return await self.bmad_hil.process_user_response(session_id, user_response)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to continue BMAD HIL session: {str(e)}"
            }

    async def bmad_hil_end_session(self, session_id: str, finalize: bool = True) -> Dict[str, Any]:
        """End HIL interactive session and update document."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Get session
            session_result = self.supabase_client.table("bmad_hil_sessions").select("*").eq("id", session_id).execute()
            
            if not session_result.data:
                return {
                    "success": False,
                    "error": f"HIL session {session_id} not found"
                }

            session = session_result.data[0]
            doc_id = session["doc_id"]
            doc_type = session["doc_type"]

            if finalize:
                # Get original document
                doc_result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).execute()
                
                if not doc_result.data:
                    return {
                        "success": False,
                        "error": f"Document {doc_id} not found"
                    }

                document = doc_result.data[0]
                
                # Generate updated content based on session responses
                updated_content = self._generate_updated_content(document["content"], session)
                
                # Update document
                doc_updates = {
                    "content": updated_content,
                    "status": "review",  # Move to review status after HIL completion
                    "updated_at": datetime.utcnow().isoformat()
                }

                self.supabase_client.table("cerebral_documents").update(doc_updates).eq("id", doc_id).execute()

            # Mark session as finalized
            self.supabase_client.table("bmad_hil_sessions").update({
                "status": "finalized",
                "finalized_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()

            return {
                "success": True,
                "session_id": session_id,
                "doc_id": doc_id,
                "doc_type": doc_type,
                "finalized": finalize,
                "message": f"HIL session completed and document updated to 'review' status"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to end HIL session: {str(e)}"
            }

    async def bmad_hil_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of HIL interactive session."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }

            # Get session
            session_result = self.supabase_client.table("bmad_hil_sessions").select("*").eq("id", session_id).execute()
            
            if not session_result.data:
                return {
                    "success": False,
                    "error": f"HIL session {session_id} not found"
                }

            session = session_result.data[0]

            return {
                "success": True,
                "session_id": session_id,
                "status": session["status"],
                "doc_id": session["doc_id"],
                "doc_type": session["doc_type"],
                "session_type": session["session_type"],
                "current_step": session.get("current_step", 0),
                "questions_asked": session.get("questions_asked", []),
                "responses_received": session.get("responses_received", []),
                "document_sections": session.get("document_sections", []),
                "bmad_pattern": session.get("bmad_pattern", ""),
                "elicitation_method": session.get("elicitation_method", ""),
                "created_at": session["created_at"],
                "updated_at": session.get("updated_at"),
                "message": f"HIL session is {session['status']}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get HIL session status: {str(e)}"
            }

    def _identify_incomplete_sections(self, content: str, doc_type: str) -> List[str]:
        """Identify sections that need completion based on template placeholders."""
        incomplete_sections = []
        
        if "*[To be filled during interactive elicitation]*" in content:
            if doc_type == "PRD":
                incomplete_sections = [
                    "User Research and Personas",
                    "Functional Requirements", 
                    "Non-Functional Requirements",
                    "Success Metrics and KPIs",
                    "Risks and Assumptions",
                    "Timeline and Milestones"
                ]
            elif doc_type == "ARCH":
                incomplete_sections = [
                    "System Architecture",
                    "Data Architecture", 
                    "Security Architecture",
                    "Deployment Architecture",
                    "Integration Patterns",
                    "Performance Considerations"
                ]
            elif doc_type == "STORY":
                incomplete_sections = [
                    "Acceptance Criteria",
                    "Implementation Notes",
                    "Testing Strategy",
                    "Dependencies"
                ]
        
        return incomplete_sections

    def _generate_first_question(self, doc_type: str, incomplete_sections: List[str]) -> str:
        """Generate the first question for HIL session."""
        if doc_type == "PRD":
            return f"I need to gather more details for your PRD. Let's start with the most critical section: {incomplete_sections[0] if incomplete_sections else 'User Research and Personas'}. Can you tell me about your target users and their key pain points?"
        elif doc_type == "ARCH":
            return f"I need to understand your system architecture better. Let's start with: {incomplete_sections[0] if incomplete_sections else 'System Architecture'}. Can you describe your overall system design and how components will interact?"
        elif doc_type == "STORY":
            return f"I need more details for your user stories. Let's start with: {incomplete_sections[0] if incomplete_sections else 'Acceptance Criteria'}. What specific acceptance criteria should be met for these stories?"
        else:
            return "I need more information to complete this document. Can you provide additional details?"

    def _generate_next_question(self, session: Dict[str, Any], user_response: str) -> Tuple[str, bool]:
        """Generate next question based on session progress and user response."""
        doc_type = session["doc_type"]
        current_step = session.get("current_step", 0)
        incomplete_sections = session.get("document_sections", [])
        
        # Check if we've covered all sections
        if current_step >= len(incomplete_sections):
            return "", True  # Session complete
        
        # Generate next question based on current step
        next_section = incomplete_sections[current_step] if current_step < len(incomplete_sections) else ""
        
        if doc_type == "PRD":
            questions = {
                "User Research and Personas": "Great! Now let's define the functional requirements. What specific features and capabilities should the system have?",
                "Functional Requirements": "Excellent! What about non-functional requirements like performance, security, scalability?",
                "Non-Functional Requirements": "Perfect! How will we measure success? What KPIs and metrics are important?",
                "Success Metrics and KPIs": "Good! What are the main risks and assumptions we should consider?",
                "Risks and Assumptions": "Finally, what's the timeline? What are the key milestones?"
            }
        elif doc_type == "ARCH":
            questions = {
                "System Architecture": "Great! Now let's define the data architecture. How will data flow through the system?",
                "Data Architecture": "Excellent! What about security architecture? How will we secure the system?",
                "Security Architecture": "Perfect! How will the system be deployed? What's the deployment strategy?",
                "Deployment Architecture": "Good! What integration patterns will we use? How will components communicate?",
                "Integration Patterns": "Finally, what performance considerations are important?"
            }
        elif doc_type == "STORY":
            questions = {
                "Acceptance Criteria": "Great! What implementation notes should developers consider?",
                "Implementation Notes": "Excellent! What testing strategy should be used?",
                "Testing Strategy": "Perfect! What dependencies exist between stories?"
            }
        
        next_question = questions.get(next_section, "Is there anything else you'd like to add to complete this document?")
        
        return next_question, False

    def _generate_updated_content(self, original_content: str, session: Dict[str, Any]) -> str:
        """Generate updated document content based on HIL session responses."""
        responses = session.get("responses_received", [])
        doc_type = session["doc_type"]
        
        # Replace template placeholders with actual content
        updated_content = original_content
        
        # Replace all placeholders with responses in order
        placeholder = "*[To be filled during interactive elicitation]*"
        for i, response_data in enumerate(responses):
            if placeholder in updated_content:
                updated_content = updated_content.replace(placeholder, response_data["response"], 1)
        
        return updated_content

    def _has_template_placeholders(self, content: str) -> bool:
        """Check if document still has template placeholders."""
        return "*[To be filled during interactive elicitation]*" in content

    async def bmad_workflow_status(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Check BMAD workflow status and HIL session state."""
        try:
            # Use the real BMAD HIL integration to check workflow status
            return await self.bmad_hil.check_workflow_status(project_id or "")
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check BMAD workflow status: {str(e)}"
            }

    # BMAD Git Workflow Integration

    async def bmad_git_commit_changes(
        self,
        workflow_id: str,
        project_id: str,
        changes_summary: str,
        document_ids: Optional[List[str]] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """Commit BMAD workflow changes with validation and tracking."""
        try:
            validation_results = None
            if validate:
                validation = await self.bmad_git.validate_bmad_changes(
                    workflow_id, project_id, "comprehensive"
                )
                if not validation.get("success"):
                    return {
                        "status": "error",
                        "message": f"Validation failed: {validation.get('error')}",
                        "validation_results": validation
                    }
                validation_results = validation.get("validation_results")
            
            commit_result = await self.bmad_git.commit_bmad_changes(
                workflow_id=workflow_id,
                project_id=project_id,
                changes_summary=changes_summary,
                document_ids=document_ids,
                validation_results=validation_results
            )
            
            return {
                "status": "success" if commit_result.get("success") else "error",
                "message": "BMAD changes committed successfully" if commit_result.get("success") else f"Commit failed: {commit_result.get('error')}",
                "commit_result": commit_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"BMAD git commit failed: {str(e)}"
            }

    async def bmad_git_push_changes(
        self,
        tracking_id: str,
        remote: str = "origin",
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Push BMAD workflow changes to remote repository."""
        try:
            push_result = await self.bmad_git.push_bmad_changes(
                tracking_id=tracking_id,
                remote=remote,
                branch=branch
            )
            
            return {
                "status": "success" if push_result.get("success") else "error",
                "message": "BMAD changes pushed successfully" if push_result.get("success") else f"Push failed: {push_result.get('error')}",
                "push_result": push_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"BMAD git push failed: {str(e)}"
            }

    async def bmad_git_validate_changes(
        self,
        workflow_id: str,
        project_id: str,
        validation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Validate BMAD workflow changes before commit."""
        try:
            validation_result = await self.bmad_git.validate_bmad_changes(
                workflow_id, project_id, validation_type
            )
            
            return {
                "status": "success" if validation_result.get("success") else "error",
                "message": "BMAD changes validated successfully" if validation_result.get("success") else f"Validation failed: {validation_result.get('error')}",
                "validation_result": validation_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"BMAD validation failed: {str(e)}"
            }

    async def bmad_git_get_history(
        self,
        project_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get BMAD commit history for a project."""
        try:
            history_result = await self.bmad_git.get_bmad_commit_history(
                project_id, limit
            )
            
            return {
                "status": "success" if history_result.get("success") else "error",
                "message": "BMAD commit history retrieved successfully" if history_result.get("success") else f"History retrieval failed: {history_result.get('error')}",
                "history_result": history_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"BMAD history retrieval failed: {str(e)}"
            }

    # BMAD Vault Integration (Phase 2.1)

    async def bmad_vault_store_secret(
        self,
        path: str,
        secret_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store secret in HashiCorp Vault."""
        try:
            result = await self.vault.store_secret(path, secret_data, metadata)
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": "Secret stored successfully" if result.get("success") else f"Secret storage failed: {result.get('error')}",
                "vault_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault secret storage failed: {str(e)}"
            }

    async def bmad_vault_retrieve_secret(
        self,
        path: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve secret from HashiCorp Vault."""
        try:
            result = await self.vault.retrieve_secret(path, version)
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": "Secret retrieved successfully" if result.get("success") else f"Secret retrieval failed: {result.get('error')}",
                "vault_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault secret retrieval failed: {str(e)}"
            }

    async def bmad_vault_list_secrets(
        self,
        path: str = ""
    ) -> Dict[str, Any]:
        """List secrets in HashiCorp Vault."""
        try:
            result = await self.vault.list_secrets(path)
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": "Secrets listed successfully" if result.get("success") else f"Secret listing failed: {result.get('error')}",
                "vault_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault secret listing failed: {str(e)}"
            }

    async def bmad_vault_delete_secret(
        self,
        path: str,
        versions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Delete secret from HashiCorp Vault."""
        try:
            result = await self.vault.delete_secret(path, versions)
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": "Secret deleted successfully" if result.get("success") else f"Secret deletion failed: {result.get('error')}",
                "vault_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault secret deletion failed: {str(e)}"
            }

    async def bmad_vault_migrate_secrets(self) -> Dict[str, Any]:
        """Migrate all local secrets to HashiCorp Vault."""
        try:
            result = await self.vault.migrate_all_secrets()
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": f"Secret migration completed: {result.get('migrated_secrets', 0)}/{result.get('total_secrets', 0)} secrets migrated" if result.get("success") else f"Secret migration failed: {result.get('error')}",
                "migration_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault secret migration failed: {str(e)}"
            }

    async def bmad_vault_health_check(self) -> Dict[str, Any]:
        """Check HashiCorp Vault health status."""
        try:
            result = await self.vault.health_check()
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": f"Vault health check: {result.get('status', 'unknown')}" if result.get("success") else f"Health check failed: {result.get('error')}",
                "health_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault health check failed: {str(e)}"
            }

    async def bmad_vault_get_config(
        self,
        category: str
    ) -> Dict[str, Any]:
        """Get configuration from HashiCorp Vault."""
        try:
            if category == "supabase":
                result = await self.vault.get_supabase_config()
            else:
                result = await self.vault.get_secret_category(category)
            
            return {
                "status": "success" if result.get("success") else "error",
                "message": f"Configuration retrieved successfully from {result.get('source', 'vault')}" if result.get("success") else f"Configuration retrieval failed: {result.get('error')}",
                "config_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vault configuration retrieval failed: {str(e)}"
            }
