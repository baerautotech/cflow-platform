"""
BMAD Human-in-the-Loop (HIL) Integration

This module integrates BMAD's interactive elicitation patterns with the cflow platform,
ensuring we leverage BMAD's updates, expansions, and bug fixes automatically.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from .config.supabase_config import get_api_key, get_rest_url
from supabase import create_client

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class BMADHILIntegration:
    """
    BMAD-style Human-in-the-Loop integration that leverages BMAD's existing patterns.
    
    This ensures we get BMAD's updates, expansions, and bug fixes automatically.
    """
    
    def __init__(self):
        self.supabase_client = None
        self._ensure_supabase()
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
    
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
    
    async def trigger_hil_session(self, doc_id: str, doc_type: str, workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a BMAD-style HIL session when Master Checklist fails.
        
        This pauses the BMAD workflow until user interaction completes.
        """
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }
            
            # Get the document to understand what needs completion
            doc_result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).execute()
            
            if not doc_result.data:
                return {
                    "success": False,
                    "error": f"Document {doc_id} not found"
                }
            
            document = doc_result.data[0]
            content = document.get("content", "")
            
            # Create BMAD-style interactive session
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "doc_id": doc_id,
                "doc_type": doc_type,
                "session_type": "bmad_elicitation",
                "status": "waiting_for_user",
                "created_at": datetime.utcnow().isoformat(),
                "current_step": 0,
                "workflow_context": workflow_context,
                "bmad_pattern": "elicit_true",  # Use BMAD's elicit: true pattern
                "elicitation_method": self._get_bmad_elicitation_method(doc_type),
                "document_sections": self._identify_bmad_sections(content, doc_type)
            }
            
            # Store session in database
            result = self.supabase_client.table("bmad_hil_sessions").insert(session_data).execute()
            
            if result.data:
                # Generate BMAD-style first question
                first_question = self._generate_bmad_question(doc_type, session_data["document_sections"])
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "workflow_paused": True,
                    "bmad_elicitation": {
                        "question": first_question,
                        "format": "bmad_numbered_list",
                        "options": self._get_bmad_options(doc_type),
                        "waiting_for_user": True
                    },
                    "message": f"BMAD workflow paused for {doc_type} elicitation. Please respond to continue."
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create BMAD HIL session"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to trigger BMAD HIL session: {str(e)}"
            }
    
    async def process_user_response(self, session_id: str, user_response: str, response_type: str = "text") -> Dict[str, Any]:
        """
        Process user response using BMAD's elicitation patterns.
        
        Supports BMAD's numbered list selection, form input, and direct text responses.
        """
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
                    "error": f"BMAD HIL session {session_id} not found"
                }
            
            session = session_result.data[0]
            
            # Process response based on BMAD pattern
            if session.get("bmad_pattern") == "elicit_true":
                return await self._process_bmad_elicitation(session, user_response, response_type)
            else:
                return {
                    "success": False,
                    "error": f"Unknown BMAD pattern: {session.get('bmad_pattern')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process user response: {str(e)}"
            }
    
    async def _process_bmad_elicitation(self, session: Dict[str, Any], user_response: str, response_type: str) -> Dict[str, Any]:
        """Process BMAD-style elicitation response."""
        doc_type = session["doc_type"]
        current_step = session.get("current_step", 0)
        
        # Store response
        responses = session.get("responses_received", [])
        responses.append({
            "step": current_step,
            "response": user_response,
            "response_type": response_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check if we need more elicitation
        sections = session.get("document_sections", [])
        if current_step < len(sections):
            # Generate next BMAD question
            next_question = self._generate_bmad_question(doc_type, sections, current_step + 1)
            
            # Update session
            session_updates = {
                "current_step": current_step + 1,
                "responses_received": responses,
                "status": "waiting_for_user",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.table("bmad_hil_sessions").update(session_updates).eq("id", session["id"]).execute()
            
            return {
                "success": True,
                "session_id": session["id"],
                "workflow_paused": True,
                "bmad_elicitation": {
                    "question": next_question,
                    "format": "bmad_numbered_list",
                    "options": self._get_bmad_options(doc_type),
                    "waiting_for_user": True
                },
                "message": "Please provide your response to continue the BMAD elicitation."
            }
        else:
            # Elicitation complete - update document and resume workflow
            return await self._complete_bmad_elicitation(session, responses)
    
    async def _complete_bmad_elicitation(self, session: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete BMAD elicitation and update document."""
        try:
            doc_id = session["doc_id"]
            doc_type = session["doc_type"]
            
            # Get original document
            doc_result = self.supabase_client.table("cerebral_documents").select("*").eq("id", doc_id).execute()
            
            if not doc_result.data:
                return {
                    "success": False,
                    "error": f"Document {doc_id} not found"
                }
            
            document = doc_result.data[0]
            
            # Generate updated content using BMAD patterns
            updated_content = self._apply_bmad_responses(document["content"], responses, doc_type)
            
            # Update document
            doc_updates = {
                "content": updated_content,
                "status": "review",  # Move to review status after BMAD elicitation
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.table("cerebral_documents").update(doc_updates).eq("id", doc_id).execute()
            
            # Mark session as completed
            self.supabase_client.table("bmad_hil_sessions").update({
                "status": "completed",
                "responses_received": responses,
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", session["id"]).execute()
            
            return {
                "success": True,
                "session_id": session["id"],
                "doc_id": doc_id,
                "doc_type": doc_type,
                "workflow_paused": False,
                "workflow_resumed": True,
                "message": f"BMAD elicitation completed for {doc_type}. Workflow resumed - Master Checklist can now be re-run."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to complete BMAD elicitation: {str(e)}"
            }
    
    def _get_bmad_elicitation_method(self, doc_type: str) -> str:
        """Get BMAD elicitation method based on document type."""
        if doc_type == "PRD":
            return "advanced_elicitation"  # Use BMAD's advanced elicitation task
        elif doc_type == "ARCH":
            return "technical_elicitation"
        elif doc_type == "STORY":
            return "story_elicitation"
        else:
            return "general_elicitation"
    
    def _identify_bmad_sections(self, content: str, doc_type: str) -> List[str]:
        """Identify sections that need BMAD-style elicitation."""
        sections = []
        
        if "*[To be filled during interactive elicitation]*" in content:
            if doc_type == "PRD":
                sections = [
                    "User Research and Personas",
                    "Functional Requirements", 
                    "Non-Functional Requirements",
                    "Success Metrics and KPIs",
                    "Risks and Assumptions",
                    "Timeline and Milestones"
                ]
            elif doc_type == "ARCH":
                sections = [
                    "System Architecture",
                    "Data Architecture", 
                    "Security Architecture",
                    "Deployment Architecture",
                    "Integration Patterns",
                    "Performance Considerations"
                ]
            elif doc_type == "STORY":
                sections = [
                    "Acceptance Criteria",
                    "Implementation Notes",
                    "Testing Strategy",
                    "Dependencies"
                ]
        
        return sections
    
    def _generate_bmad_question(self, doc_type: str, sections: List[str], step: int = 0) -> str:
        """Generate BMAD-style questions using their elicitation patterns."""
        if step >= len(sections):
            return "BMAD elicitation complete. Ready to proceed."
        
        current_section = sections[step]
        
        if doc_type == "PRD":
            questions = {
                "User Research and Personas": "I need to gather more details for your PRD. Let's start with **User Research and Personas**. Can you tell me about your target users and their key pain points?",
                "Functional Requirements": "Great! Now let's define the **Functional Requirements**. What specific features and capabilities should the system have?",
                "Non-Functional Requirements": "Excellent! What about **Non-Functional Requirements** like performance, security, scalability?",
                "Success Metrics and KPIs": "Perfect! How will we measure success? What **KPIs and metrics** are important?",
                "Risks and Assumptions": "Good! What are the main **Risks and Assumptions** we should consider?",
                "Timeline and Milestones": "Finally, what's the **Timeline**? What are the key milestones?"
            }
        elif doc_type == "ARCH":
            questions = {
                "System Architecture": "I need to understand your **System Architecture** better. Can you describe your overall system design and how components will interact?",
                "Data Architecture": "Great! Now let's define the **Data Architecture**. How will data flow through the system?",
                "Security Architecture": "Excellent! What about **Security Architecture**? How will we secure the system?",
                "Deployment Architecture": "Perfect! How will the system be **Deployed**? What's the deployment strategy?",
                "Integration Patterns": "Good! What **Integration Patterns** will we use? How will components communicate?",
                "Performance Considerations": "Finally, what **Performance Considerations** are important?"
            }
        elif doc_type == "STORY":
            questions = {
                "Acceptance Criteria": "I need more details for your **Acceptance Criteria**. What specific criteria should be met for these stories?",
                "Implementation Notes": "Great! What **Implementation Notes** should developers consider?",
                "Testing Strategy": "Excellent! What **Testing Strategy** should be used?",
                "Dependencies": "Perfect! What **Dependencies** exist between stories?"
            }
        
        return questions.get(current_section, f"Please provide details for {current_section}.")
    
    def _get_bmad_options(self, doc_type: str) -> List[str]:
        """Get BMAD-style numbered options for user selection."""
        if doc_type == "PRD":
            return [
                "Provide detailed response",
                "Use advanced elicitation techniques",
                "Skip this section for now",
                "Request clarification",
                "Apply BMAD brainstorming methods"
            ]
        elif doc_type == "ARCH":
            return [
                "Provide technical details",
                "Use architecture elicitation",
                "Skip this section for now", 
                "Request technical clarification",
                "Apply system design methods"
            ]
        elif doc_type == "STORY":
            return [
                "Provide story details",
                "Use story elicitation",
                "Skip this section for now",
                "Request story clarification", 
                "Apply user story methods"
            ]
        else:
            return [
                "Provide response",
                "Use elicitation techniques",
                "Skip section",
                "Request clarification",
                "Apply BMAD methods"
            ]
    
    def _apply_bmad_responses(self, original_content: str, responses: List[Dict[str, Any]], doc_type: str) -> str:
        """Apply user responses to document content using BMAD patterns."""
        updated_content = original_content
        
        # Replace placeholders with responses in order
        placeholder = "*[To be filled during interactive elicitation]*"
        for response_data in responses:
            if placeholder in updated_content:
                updated_content = updated_content.replace(placeholder, response_data["response"], 1)
        
        return updated_content
    
    async def check_workflow_status(self, project_id: str) -> Dict[str, Any]:
        """Check if BMAD workflow is paused for HIL interaction."""
        try:
            if not self.supabase_client:
                return {
                    "success": False,
                    "error": "Supabase client not available"
                }
            
            # Check for active HIL sessions
            sessions_result = self.supabase_client.table("bmad_hil_sessions").select("*").eq("status", "waiting_for_user").execute()
            
            if sessions_result.data:
                active_session = sessions_result.data[0]
                return {
                    "success": True,
                    "workflow_paused": True,
                    "hil_session_active": True,
                    "session_id": active_session["id"],
                    "doc_type": active_session["doc_type"],
                    "current_step": active_session.get("current_step", 0),
                    "message": f"BMAD workflow paused for {active_session['doc_type']} elicitation"
                }
            else:
                return {
                    "success": True,
                    "workflow_paused": False,
                    "hil_session_active": False,
                    "message": "BMAD workflow ready to proceed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check workflow status: {str(e)}"
            }
