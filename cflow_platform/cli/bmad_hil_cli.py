#!/usr/bin/env python3
"""
BMAD HIL CLI - Command-line interface for BMAD Human-in-the-Loop interactions

This provides a BMAD-style interactive interface for testing and using HIL sessions.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional

from cflow_platform.core.direct_client import execute_mcp_tool


class BMADHILCLI:
    """BMAD-style CLI for Human-in-the-Loop interactions."""
    
    def __init__(self):
        self.active_session_id: Optional[str] = None
        self.active_doc_type: Optional[str] = None
    
    async def run(self):
        """Run the BMAD HIL CLI."""
        print("BMAD Human-in-the-Loop (HIL) Interactive Session")
        print("=" * 60)
        print("This CLI provides BMAD-style interactive elicitation sessions.")
        print("Type 'help' for available commands, 'exit' to quit.")
        print()
        
        while True:
            try:
                command = input("BMAD-HIL> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit']:
                    print("Exiting BMAD HIL CLI...")
                    break
                elif command.lower() == 'help':
                    self._show_help()
                elif command.lower() == 'status':
                    await self._check_workflow_status()
                elif command.startswith('start '):
                    await self._start_session(command)
                elif command.startswith('continue '):
                    await self._continue_session(command)
                elif command.lower() == 'session_status':
                    await self._check_session_status()
                elif command.lower() == 'test_workflow':
                    await self._test_workflow()
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting BMAD HIL CLI...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("\nBMAD HIL CLI Commands:")
        print("=" * 30)
        print("help              - Show this help")
        print("status            - Check BMAD workflow status")
        print("start <doc_id> <type> - Start HIL session for document")
        print("continue <response>   - Continue active session with response")
        print("session_status    - Check current session status")
        print("test_workflow     - Test complete BMAD workflow")
        print("exit/quit         - Exit CLI")
        print()
        print("Examples:")
        print("  start 6aa1f35b-9f00-4817-8feb-112c300bf74e PRD")
        print("  continue Our target users are development teams...")
        print()
    
    async def _check_workflow_status(self):
        """Check BMAD workflow status."""
        print("\nSEARCH: Checking BMAD workflow status...")
        
        result = await execute_mcp_tool('bmad_workflow_status', project_id="")
        
        if result.get('success'):
            if result.get('workflow_paused'):
                print("WARNING: BMAD workflow is PAUSED")
                print(f"   Reason: {result.get('message', 'Unknown')}")
                if result.get('hil_session_active'):
                    print(f"   Active HIL Session: {result.get('session_id')}")
                    print(f"   Document Type: {result.get('doc_type')}")
                    print(f"   Current Step: {result.get('current_step', 0)}")
            else:
                print("SUCCESS: BMAD workflow is READY to proceed")
                print(f"   Status: {result.get('message', 'Unknown')}")
        else:
            print(f"ERROR: Error checking workflow status: {result.get('error')}")
    
    async def _start_session(self, command: str):
        """Start a HIL session."""
        parts = command.split()
        if len(parts) < 3:
            print("Usage: start <doc_id> <doc_type>")
            return
        
        doc_id = parts[1]
        doc_type = parts[2].upper()
        
        if doc_type not in ['PRD', 'ARCH', 'STORY']:
            print("Document type must be PRD, ARCH, or STORY")
            return
        
        print(f"\nSTARTING: Starting BMAD HIL session for {doc_type} document...")
        
        result = await execute_mcp_tool('bmad_hil_start_session', 
            doc_id=doc_id, 
            doc_type=doc_type, 
            session_type='elicitation'
        )
        
        if result.get('success'):
            self.active_session_id = result.get('session_id')
            self.active_doc_type = doc_type
            
            print("SUCCESS: BMAD HIL session started successfully!")
            print(f"   Session ID: {self.active_session_id}")
            print(f"   Document Type: {doc_type}")
            
            if result.get('bmad_elicitation'):
                elicitation = result['bmad_elicitation']
                print(f"\nWRITE: BMAD Elicitation Question:")
                print(f"   {elicitation.get('question', 'No question provided')}")
                
                if elicitation.get('options'):
                    print(f"\nOPTIONS: BMAD Options:")
                    for i, option in enumerate(elicitation['options']):
                        print(f"   {i}: {option}")
                
                print(f"\nRESPONSE: Please provide your response using: continue <your response>")
        else:
            print(f"ERROR: Failed to start HIL session: {result.get('error')}")
    
    async def _continue_session(self, command: str):
        """Continue active HIL session."""
        if not self.active_session_id:
            print("ERROR: No active HIL session. Start a session first.")
            return
        
        # Extract response from command
        response = command[9:].strip()  # Remove 'continue ' prefix
        
        if not response:
            print("Please provide a response: continue <your response>")
            return
        
        print(f"\nSEND: Sending response to BMAD HIL session...")
        print(f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        result = await execute_mcp_tool('bmad_hil_continue_session',
            session_id=self.active_session_id,
            user_response=response
        )
        
        if result.get('success'):
            if result.get('workflow_resumed'):
                print("COMPLETED: BMAD HIL session completed!")
                print("SUCCESS: BMAD workflow has been RESUMED")
                print(f"   {result.get('message', '')}")
                self.active_session_id = None
                self.active_doc_type = None
            elif result.get('workflow_paused'):
                print("PAUSED:  BMAD workflow remains PAUSED")
                
                if result.get('bmad_elicitation'):
                    elicitation = result['bmad_elicitation']
                    print(f"\nWRITE: Next BMAD Elicitation Question:")
                    print(f"   {elicitation.get('question', 'No question provided')}")
                    
                    if elicitation.get('options'):
                        print(f"\nOPTIONS: BMAD Options:")
                        for i, option in enumerate(elicitation['options']):
                            print(f"   {i}: {option}")
                    
                    print(f"\nRESPONSE: Please provide your next response using: continue <your response>")
            else:
                print(f"SUCCESS: Response processed: {result.get('message', '')}")
        else:
            print(f"ERROR: Failed to continue HIL session: {result.get('error')}")
    
    async def _check_session_status(self):
        """Check current session status."""
        if not self.active_session_id:
            print("ERROR: No active HIL session.")
            return
        
        print(f"\nSEARCH: Checking HIL session status...")
        
        result = await execute_mcp_tool('bmad_hil_session_status',
            session_id=self.active_session_id
        )
        
        if result.get('success'):
            print("SUCCESS: Session Status:")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Document Type: {result.get('doc_type')}")
            print(f"   Current Step: {result.get('current_step', 0)}")
            print(f"   Questions Asked: {result.get('questions_asked', 0)}")
            print(f"   Responses Received: {result.get('responses_received', 0)}")
            print(f"   Created: {result.get('created_at')}")
        else:
            print(f"ERROR: Error checking session status: {result.get('error')}")
    
    async def _test_workflow(self):
        """Test complete BMAD workflow."""
        print("\nTEST: Testing Complete BMAD Workflow...")
        print("=" * 40)
        
        # Step 1: Check workflow status
        print("1. Checking workflow status...")
        await self._check_workflow_status()
        
        # Step 2: Run Master Checklist (this should trigger HIL if needed)
        print("\n2. Running Master Checklist...")
        result = await execute_mcp_tool('bmad_master_checklist',
            prd_id='6aa1f35b-9f00-4817-8feb-112c300bf74e',
            arch_id='79556ce4-c68f-437f-8fdd-b639f35e4da4'
        )
        
        if result.get('success'):
            if result.get('checklist_passed'):
                print("SUCCESS: Master Checklist PASSED - workflow ready to proceed")
            else:
                print("WARNING:  Master Checklist FAILED")
                print(f"   Results: {result.get('results', {})}")
                
                if result.get('bmad_hil_triggered'):
                    print("BMAD HIL sessions have been TRIGGERED!")
                    print("   Workflow is PAUSED until HIL sessions complete")
                    
                    hil_sessions = result.get('hil_sessions', [])
                    for session in hil_sessions:
                        print(f"   - Session: {session.get('session_id')}")
                        print(f"     Document: {session.get('doc_type')}")
                        print(f"     Question: {session.get('bmad_elicitation', {}).get('question', 'N/A')}")
                else:
                    print("ERROR: No HIL sessions triggered - manual intervention needed")
        else:
            print(f"ERROR: Master Checklist failed: {result.get('error')}")
        
        print("\nSUCCESS: BMAD workflow test completed!")


async def main():
    """Main entry point."""
    cli = BMADHILCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
