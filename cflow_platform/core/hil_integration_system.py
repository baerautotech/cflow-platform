# BMAD-Method HIL (Human-in-the-Loop) Integration System

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class HILSessionStatus(Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class HILSession:
    """Represents a Human-in-the-Loop session"""
    session_id: str
    user_id: str
    task_type: str
    status: HILSessionStatus
    created_at: datetime
    updated_at: datetime
    context: Dict[str, Any]
    approvals: List[Dict[str, Any]]
    elicitations: List[Dict[str, Any]]
    cerebral_extensions: Dict[str, Any] = None

class BMADHILIntegrationSystem:
    """HIL Integration System for BMAD-Method with Cerebral extensions"""
    
    def __init__(self, bmad_root: Path = None):
        self.bmad_root = bmad_root or Path('vendor/bmad')
        self.active_sessions: Dict[str, HILSession] = {}
        self.session_history: List[HILSession] = []
        self.cerebral_extensions: Dict[str, Any] = {}
        
        # HIL task types from vendor/bmad
        self.hil_task_types = {
            'elicitation': 'Requirements elicitation sessions',
            'approval': 'Approval workflow sessions',
            'review': 'Code review sessions',
            'validation': 'Validation sessions',
            'brainstorming': 'Brainstorming sessions',
            'decision': 'Decision making sessions'
        }
    
    async def create_hil_session(self, user_id: str, task_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new HIL session"""
        try:
            session_id = f"hil_{user_id}_{int(datetime.now().timestamp())}"
            
            session = HILSession(
                session_id=session_id,
                user_id=user_id,
                task_type=task_type,
                status=HILSessionStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                context=context or {},
                approvals=[],
                elicitations=[],
                cerebral_extensions={
                    'mcp_integration': True,
                    'context_preservation': True,
                    'session_management': True,
                    'webmcp_routing': True,
                    'real_time_updates': True
                }
            )
            
            self.active_sessions[session_id] = session
            
            return {
                'success': True,
                'session_id': session_id,
                'task_type': task_type,
                'status': session.status.value,
                'message': f'Successfully created HIL session: {task_type}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_hil_session(self, session_id: str) -> Optional[HILSession]:
        """Get a specific HIL session by ID"""
        return self.active_sessions.get(session_id)
    
    async def update_hil_session(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a HIL session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {
                    'success': False,
                    'error': f'HIL session {session_id} not found'
                }
            
            # Update session fields
            if 'status' in updates:
                session.status = HILSessionStatus(updates['status'])
            if 'context' in updates:
                session.context.update(updates['context'])
            if 'approvals' in updates:
                session.approvals.extend(updates['approvals'])
            if 'elicitations' in updates:
                session.elicitations.extend(updates['elicitations'])
            
            session.updated_at = datetime.now()
            
            return {
                'success': True,
                'session_id': session_id,
                'status': session.status.value,
                'message': f'Successfully updated HIL session: {session_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def complete_hil_session(self, session_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a HIL session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {
                    'success': False,
                    'error': f'HIL session {session_id} not found'
                }
            
            # Update session with result
            session.status = HILSessionStatus.COMPLETED
            session.context['result'] = result
            session.updated_at = datetime.now()
            
            # Move to history
            self.session_history.append(session)
            del self.active_sessions[session_id]
            
            return {
                'success': True,
                'session_id': session_id,
                'result': result,
                'message': f'Successfully completed HIL session: {session_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_hil_session(self, session_id: str, reason: str = None) -> Dict[str, Any]:
        """Cancel a HIL session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {
                    'success': False,
                    'error': f'HIL session {session_id} not found'
                }
            
            # Update session status
            session.status = HILSessionStatus.CANCELLED
            if reason:
                session.context['cancellation_reason'] = reason
            session.updated_at = datetime.now()
            
            # Move to history
            self.session_history.append(session)
            del self.active_sessions[session_id]
            
            return {
                'success': True,
                'session_id': session_id,
                'reason': reason,
                'message': f'Successfully cancelled HIL session: {session_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_active_sessions(self) -> List[HILSession]:
        """List all active HIL sessions"""
        return list(self.active_sessions.values())
    
    async def list_session_history(self) -> List[HILSession]:
        """List HIL session history"""
        return self.session_history
    
    async def get_hil_task_types(self) -> Dict[str, str]:
        """Get available HIL task types"""
        return self.hil_task_types
    
    async def get_hil_status(self) -> Dict[str, Any]:
        """Get HIL integration system status"""
        return {
            'active_sessions': len(self.active_sessions),
            'total_history': len(self.session_history),
            'task_types': len(self.hil_task_types),
            'cerebral_extensions': {
                'mcp_integration': True,
                'context_preservation': True,
                'session_management': True,
                'webmcp_routing': True,
                'real_time_updates': True
            },
            'system_version': '1.0',
            'last_update': datetime.now().isoformat()
        }

# Global HIL integration system instance
bmad_hil_integration_system = BMADHILIntegrationSystem()
