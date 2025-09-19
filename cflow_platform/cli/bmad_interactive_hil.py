#!/usr/bin/env python3
"""
BMAD Interactive HIL - Real interactive interface for BMAD Human-in-the-Loop sessions

This provides a REAL interactive interface that pauses and waits for user input.
"""

import asyncio
import sys
from typing import Dict, Any, Optional

from cflow_platform.core.direct_client import execute_mcp_tool


class BMADInteractiveHIL:
    """Real interactive BMAD HIL interface that pauses workflow."""
    
    def __init__(self):
        self.active_session_id: Optional[str] = None
        self.active_doc_type: Optional[str] = None
    
    async def start_interactive_session(self):
        """Start a real interactive BMAD HIL session."""
        print("BMAD Human-in-the-Loop Interactive Session")
        print("=" * 60)
        
        # Check for active HIL session
        workflow_status = await execute_mcp_tool('bmad_workflow_status', project_id='')
        
        if not workflow_status.get('hil_session_active'):
            print("ERROR: No active HIL session found.")
            print("Please run Master Checklist first to trigger HIL session.")
            return
        
        self.active_session_id = workflow_status.get('session_id')
        self.active_doc_type = workflow_status.get('doc_type')
        
        print(f"SUCCESS: Active HIL Session Found!")
        print(f"DOCUMENT: Document Type: {self.active_doc_type}")
        print(f"ID: Session ID: {self.active_session_id}")
        print()
        
        # Start the interactive loop
        await self._interactive_loop()
    
    async def _interactive_loop(self):
        """Main interactive loop that pauses and waits for user input."""
        while True:
            try:
                # Get current session status
                session_status = await execute_mcp_tool('bmad_hil_session_status', 
                    session_id=self.active_session_id)
                
                if session_status.get('status') != 'waiting_for_user':
                    print(f"SUCCESS: HIL Session completed! Status: {session_status.get('status')}")
                    break
                
                # Get current question
                current_step = session_status.get('current_step', 0)
                document_sections = session_status.get('document_sections', [])
                
                if current_step < len(document_sections):
                    current_section = document_sections[current_step]
                    
                    # Display BMAD-style question
                    print(f"OPTIONS: BMAD ELICITATION QUESTION (Step {current_step + 1}/{len(document_sections)}):")
                    print("-" * 60)
                    print(f"I need to gather more details for your {self.active_doc_type}.")
                    print(f"Let's work on **{current_section}**.")
                    print()
                    
                    # Generate specific question based on section
                    question = self._generate_section_question(current_section, self.active_doc_type)
                    print(f"QUESTION: {question}")
                    print()
                    
                    # Display BMAD options
                    print("OPTIONS: BMAD OPTIONS:")
                    print("-" * 30)
                    options = self._get_bmad_options(self.active_doc_type)
                    for i, option in enumerate(options):
                        print(f"{i}: {option}")
                    print()
                    
                    # REAL INTERACTIVE INPUT - This actually pauses and waits
                    print("RESPONSE: YOUR RESPONSE:")
                    print("-" * 20)
                    user_response = input("> ").strip()
                    
                    if not user_response:
                        print("ERROR: Empty response. Please provide an answer.")
                        continue
                    
                    # Submit response to BMAD HIL system
                    print(f"\nSEND: Submitting response to BMAD HIL system...")
                    result = await execute_mcp_tool('bmad_hil_continue_session',
                        session_id=self.active_session_id,
                        user_response=user_response
                    )
                    
                    if result.get('success'):
                        if result.get('workflow_resumed'):
                            print("COMPLETED: BMAD HIL Session COMPLETED!")
                            print("SUCCESS: BMAD workflow has been RESUMED!")
                            print(f"WRITE: {result.get('message', '')}")
                            break
                        elif result.get('workflow_paused'):
                            print("SUCCESS: Response processed successfully!")
                            print("PAUSED:  BMAD workflow remains paused for next question...")
                            
                            if result.get('bmad_elicitation'):
                                elicitation = result['bmad_elicitation']
                                print(f"\nWRITE: Next Question Preview: {elicitation.get('question', 'N/A')[:100]}...")
                        else:
                            print(f"SUCCESS: Response processed: {result.get('message', '')}")
                    else:
                        print(f"ERROR: Failed to process response: {result.get('error')}")
                        break
                    
                    print("\n" + "="*60 + "\n")
                    
                else:
                    print("SUCCESS: All sections completed!")
                    break
                    
            except KeyboardInterrupt:
                print("\n\nWARNING:  Session interrupted by user.")
                print("WAITING: BMAD workflow remains paused.")
                break
            except Exception as e:
                print(f"\nERROR: Error: {e}")
                break
    
    def _generate_section_question(self, section: str, doc_type: str) -> str:
        """Generate specific question for each section."""
        if doc_type == "PRD":
            questions = {
                "User Research and Personas": "Who are your target users and what are their key pain points?",
                "Functional Requirements": "What specific features and capabilities should the system have?",
                "Non-Functional Requirements": "What are the performance, security, and scalability requirements?",
                "Success Metrics and KPIs": "How will you measure success? What KPIs are important?",
                "Risks and Assumptions": "What are the main risks and assumptions to consider?",
                "Timeline and Milestones": "What's the timeline? What are the key milestones?"
            }
        elif doc_type == "ARCH":
            questions = {
                "System Architecture": "How should the overall system be designed? How will components interact?",
                "Data Architecture": "How will data flow through the system?",
                "Security Architecture": "How will the system be secured?",
                "Deployment Architecture": "How will the system be deployed?",
                "Integration Patterns": "What integration patterns will be used?",
                "Performance Considerations": "What performance considerations are important?"
            }
        elif doc_type == "STORY":
            questions = {
                "Acceptance Criteria": "What specific criteria should be met for these stories?",
                "Implementation Notes": "What implementation notes should developers consider?",
                "Testing Strategy": "What testing strategy should be used?",
                "Dependencies": "What dependencies exist between stories?"
            }
        else:
            questions = {}
        
        return questions.get(section, f"Please provide details for {section}.")
    
    def _get_bmad_options(self, doc_type: str) -> list:
        """Get BMAD-style options for user selection."""
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


async def main():
    """Main entry point for interactive BMAD HIL."""
    hil = BMADInteractiveHIL()
    await hil.start_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
