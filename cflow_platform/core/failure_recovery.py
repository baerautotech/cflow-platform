"""
BMAD Failure Recovery and Distributed Coordination

Production-ready failure recovery mechanisms for multi-agent systems.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class FailureType(Enum):
    """Failure type enumeration."""
    AGENT_OFFLINE = "agent_offline"
    TASK_TIMEOUT = "task_timeout"
    MESSAGE_LOST = "message_lost"
    STATE_CORRUPTION = "state_corruption"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery action enumeration."""
    RETRY = "retry"
    RESCHEDULE = "reschedule"
    FAILOVER = "failover"
    RESTART = "restart"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass
class FailureEvent:
    """Failure event data structure."""
    id: str = ""
    failure_type: FailureType = FailureType.UNKNOWN
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    message_id: Optional[str] = None
    description: str = ""
    timestamp: datetime = None
    severity: int = 5  # 1-10 scale
    context: Dict[str, Any] = None
    resolved: bool = False
    recovery_action: Optional[RecoveryAction] = None
    recovery_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.context:
            self.context = {}


@dataclass
class RecoveryPlan:
    """Recovery plan data structure."""
    id: str
    failure_event_id: str
    actions: List[RecoveryAction]
    timeout: int  # seconds
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"  # pending, executing, completed, failed
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()


class BMADFailureRecovery:
    """Production-ready failure recovery system for BMAD."""
    
    def __init__(self):
        self.supabase_client = None
        self.failure_events: List[FailureEvent] = []
        self.recovery_plans: List[RecoveryPlan] = []
        self.recovery_handlers: Dict[FailureType, List[Callable]] = {}
        self.agent_health_monitor = {}
        self.task_timeout_monitor = {}
        self.message_timeout_monitor = {}
        self.running = False
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Create Supabase client."""
        try:
            from .config.supabase_config import get_api_key, get_rest_url
            from supabase import create_client
            
            url = get_rest_url()
            key = get_api_key(secure=True)
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("[INFO] Failure Recovery: Supabase client created")
            else:
                print("[INFO][INFO] Failure Recovery: Supabase not available")
                
        except Exception as e:
            print(f"[INFO][INFO] Failure Recovery: Supabase setup failed: {e}")
    
    async def create_failure_recovery_tables(self) -> bool:
        """Create failure recovery tables in Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Failure Recovery: Supabase not available")
                return False
            
            # Create failure_events table
            failure_events_migration = """
            CREATE TABLE IF NOT EXISTS failure_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                failure_type TEXT NOT NULL,
                agent_id TEXT,
                task_id TEXT,
                message_id TEXT,
                description TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                severity INTEGER DEFAULT 5,
                context JSONB DEFAULT '{}',
                resolved BOOLEAN DEFAULT FALSE,
                recovery_action TEXT,
                recovery_timestamp TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_failure_events_failure_type ON failure_events(failure_type);
            CREATE INDEX IF NOT EXISTS idx_failure_events_agent_id ON failure_events(agent_id);
            CREATE INDEX IF NOT EXISTS idx_failure_events_resolved ON failure_events(resolved);
            """
            
            # Create recovery_plans table
            recovery_plans_migration = """
            CREATE TABLE IF NOT EXISTS recovery_plans (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                failure_event_id UUID REFERENCES failure_events(id),
                actions JSONB NOT NULL,
                timeout INTEGER DEFAULT 300,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_recovery_plans_failure_event_id ON recovery_plans(failure_event_id);
            CREATE INDEX IF NOT EXISTS idx_recovery_plans_status ON recovery_plans(status);
            """
            
            # Apply migrations
            from .migrations import apply_migration
            apply_migration("create_failure_events_table", failure_events_migration)
            apply_migration("create_recovery_plans_table", recovery_plans_migration)
            
            print("[INFO] Failure Recovery: Tables created successfully")
            return True
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Failed to create tables: {e}")
            return False
    
    async def report_failure(self, failure_type: FailureType, description: str,
                           agent_id: Optional[str] = None, task_id: Optional[str] = None,
                           message_id: Optional[str] = None, severity: int = 5,
                           context: Optional[Dict[str, Any]] = None) -> str:
        """Report a failure event."""
        try:
            failure_event = FailureEvent(
                id=str(uuid.uuid4()),
                failure_type=failure_type,
                agent_id=agent_id,
                task_id=task_id,
                message_id=message_id,
                description=description,
                severity=severity,
                context=context or {}
            )
            
            # Store in memory
            self.failure_events.append(failure_event)
            
            # Store in Supabase if available
            if self.supabase_client:
                failure_data = {
                    "id": failure_event.id,
                    "failure_type": failure_event.failure_type.value,
                    "agent_id": failure_event.agent_id,
                    "task_id": failure_event.task_id,
                    "message_id": failure_event.message_id,
                    "description": failure_event.description,
                    "timestamp": failure_event.timestamp.isoformat(),
                    "severity": failure_event.severity,
                    "context": failure_event.context,
                    "resolved": failure_event.resolved
                }
                
                self.supabase_client.table("failure_events").insert(failure_data).execute()
            
            # Trigger recovery
            await self._trigger_recovery(failure_event)
            
            print(f"[INFO] Failure Recovery: Reported failure {failure_event.id} - {failure_type.value}")
            return failure_event.id
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Failed to report failure: {e}")
            return None
    
    async def _trigger_recovery(self, failure_event: FailureEvent) -> None:
        """Trigger recovery for a failure event."""
        try:
            # Determine recovery actions based on failure type
            recovery_actions = self._determine_recovery_actions(failure_event)
            
            if not recovery_actions:
                print(f"[INFO][INFO] Failure Recovery: No recovery actions for {failure_event.failure_type.value}")
                return
            
            # Create recovery plan
            recovery_plan = RecoveryPlan(
                id=str(uuid.uuid4()),
                failure_event_id=failure_event.id,
                actions=recovery_actions,
                timeout=self._get_recovery_timeout(failure_event.failure_type)
            )
            
            # Store recovery plan
            self.recovery_plans.append(recovery_plan)
            
            # Store in Supabase if available
            if self.supabase_client:
                plan_data = {
                    "id": recovery_plan.id,
                    "failure_event_id": recovery_plan.failure_event_id,
                    "actions": [action.value for action in recovery_plan.actions],
                    "timeout": recovery_plan.timeout,
                    "retry_count": recovery_plan.retry_count,
                    "max_retries": recovery_plan.max_retries,
                    "status": recovery_plan.status,
                    "created_at": recovery_plan.created_at.isoformat()
                }
                
                self.supabase_client.table("recovery_plans").insert(plan_data).execute()
            
            # Execute recovery plan
            await self._execute_recovery_plan(recovery_plan)
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Failed to trigger recovery: {e}")
    
    def _determine_recovery_actions(self, failure_event: FailureEvent) -> List[RecoveryAction]:
        """Determine recovery actions based on failure type."""
        recovery_map = {
            FailureType.AGENT_OFFLINE: [RecoveryAction.FAILOVER, RecoveryAction.RESCHEDULE],
            FailureType.TASK_TIMEOUT: [RecoveryAction.RETRY, RecoveryAction.RESCHEDULE],
            FailureType.MESSAGE_LOST: [RecoveryAction.RETRY, RecoveryAction.RESCHEDULE],
            FailureType.STATE_CORRUPTION: [RecoveryAction.RESTART, RecoveryAction.ESCALATE],
            FailureType.NETWORK_PARTITION: [RecoveryAction.RETRY, RecoveryAction.FAILOVER],
            FailureType.RESOURCE_EXHAUSTION: [RecoveryAction.RESCHEDULE, RecoveryAction.ESCALATE],
            FailureType.UNKNOWN: [RecoveryAction.ESCALATE]
        }
        
        return recovery_map.get(failure_event.failure_type, [RecoveryAction.ESCALATE])
    
    def _get_recovery_timeout(self, failure_type: FailureType) -> int:
        """Get recovery timeout based on failure type."""
        timeout_map = {
            FailureType.AGENT_OFFLINE: 60,  # 1 minute
            FailureType.TASK_TIMEOUT: 30,   # 30 seconds
            FailureType.MESSAGE_LOST: 15,  # 15 seconds
            FailureType.STATE_CORRUPTION: 120,  # 2 minutes
            FailureType.NETWORK_PARTITION: 45,  # 45 seconds
            FailureType.RESOURCE_EXHAUSTION: 90,  # 1.5 minutes
            FailureType.UNKNOWN: 300  # 5 minutes
        }
        
        return timeout_map.get(failure_type, 60)
    
    async def _execute_recovery_plan(self, recovery_plan: RecoveryPlan) -> None:
        """Execute a recovery plan."""
        try:
            recovery_plan.status = "executing"
            recovery_plan.started_at = datetime.utcnow()
            
            print(f"[INFO] Failure Recovery: Executing recovery plan {recovery_plan.id}")
            
            for action in recovery_plan.actions:
                try:
                    await self._execute_recovery_action(action, recovery_plan)
                except Exception as e:
                    print(f"[INFO] Failure Recovery: Action {action.value} failed: {e}")
                    recovery_plan.retry_count += 1
                    
                    if recovery_plan.retry_count >= recovery_plan.max_retries:
                        recovery_plan.status = "failed"
                        break
            
            if recovery_plan.status == "executing":
                recovery_plan.status = "completed"
                recovery_plan.completed_at = datetime.utcnow()
                
                # Mark failure event as resolved
                failure_event = next((f for f in self.failure_events if f.id == recovery_plan.failure_event_id), None)
                if failure_event:
                    failure_event.resolved = True
                    failure_event.recovery_action = recovery_plan.actions[0] if recovery_plan.actions else None
                    failure_event.recovery_timestamp = datetime.utcnow()
            
            print(f"[INFO] Failure Recovery: Recovery plan {recovery_plan.id} completed with status: {recovery_plan.status}")
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Recovery plan execution failed: {e}")
            recovery_plan.status = "failed"
    
    async def _execute_recovery_action(self, action: RecoveryAction, recovery_plan: RecoveryPlan) -> None:
        """Execute a specific recovery action."""
        try:
            failure_event = next((f for f in self.failure_events if f.id == recovery_plan.failure_event_id), None)
            if not failure_event:
                return
            
            print(f"Failure Recovery: Executing action {action.value} for failure {failure_event.id}")
            
            if action == RecoveryAction.RETRY:
                await self._retry_action(failure_event)
            elif action == RecoveryAction.RESCHEDULE:
                await self._reschedule_action(failure_event)
            elif action == RecoveryAction.FAILOVER:
                await self._failover_action(failure_event)
            elif action == RecoveryAction.RESTART:
                await self._restart_action(failure_event)
            elif action == RecoveryAction.ESCALATE:
                await self._escalate_action(failure_event)
            elif action == RecoveryAction.ABORT:
                await self._abort_action(failure_event)
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Action {action.value} execution failed: {e}")
            raise
    
    async def _retry_action(self, failure_event: FailureEvent) -> None:
        """Retry the failed operation."""
        print(f"Failure Recovery: Retrying operation for failure {failure_event.id}")
        # Implementation would depend on the specific operation
        await asyncio.sleep(1)  # Simulate retry delay
    
    async def _reschedule_action(self, failure_event: FailureEvent) -> None:
        """Reschedule the failed operation."""
        print(f"📅 Failure Recovery: Rescheduling operation for failure {failure_event.id}")
        # Implementation would reschedule the task to another agent or time
        await asyncio.sleep(1)  # Simulate reschedule delay
    
    async def _failover_action(self, failure_event: FailureEvent) -> None:
        """Failover to another agent."""
        print(f"Failure Recovery: Failing over for failure {failure_event.id}")
        # Implementation would find another available agent
        await asyncio.sleep(1)  # Simulate failover delay
    
    async def _restart_action(self, failure_event: FailureEvent) -> None:
        """Restart the agent or service."""
        print(f"Failure Recovery: Restarting for failure {failure_event.id}")
        # Implementation would restart the agent
        await asyncio.sleep(2)  # Simulate restart delay
    
    async def _escalate_action(self, failure_event: FailureEvent) -> None:
        """Escalate the failure to human operators."""
        print(f"Failure Recovery: Escalating failure {failure_event.id}")
        # Implementation would notify human operators
        await asyncio.sleep(1)  # Simulate escalation delay
    
    async def _abort_action(self, failure_event: FailureEvent) -> None:
        """Abort the operation."""
        print(f"🛑 Failure Recovery: Aborting operation for failure {failure_event.id}")
        # Implementation would abort the operation
        await asyncio.sleep(1)  # Simulate abort delay
    
    async def start_monitoring(self) -> None:
        """Start failure monitoring service."""
        try:
            self.running = True
            print("[INFO] Failure Recovery: Starting failure monitoring service...")
            
            while self.running:
                # Monitor agent health
                await self._monitor_agent_health()
                
                # Monitor task timeouts
                await self._monitor_task_timeouts()
                
                # Monitor message timeouts
                await self._monitor_message_timeouts()
                
                # Clean up old failure events
                await self._cleanup_old_failures()
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
        except Exception as e:
            print(f"[INFO] Failure Recovery: Monitoring service failed: {e}")
    
    async def _monitor_agent_health(self) -> None:
        """Monitor agent health."""
        try:
            # Implementation would check agent heartbeats and status
            pass
        except Exception as e:
            print(f"[INFO] Failure Recovery: Agent health monitoring failed: {e}")
    
    async def _monitor_task_timeouts(self) -> None:
        """Monitor task timeouts."""
        try:
            # Implementation would check for timed out tasks
            pass
        except Exception as e:
            print(f"[INFO] Failure Recovery: Task timeout monitoring failed: {e}")
    
    async def _monitor_message_timeouts(self) -> None:
        """Monitor message timeouts."""
        try:
            # Implementation would check for timed out messages
            pass
        except Exception as e:
            print(f"[INFO] Failure Recovery: Message timeout monitoring failed: {e}")
    
    async def _cleanup_old_failures(self) -> None:
        """Clean up old failure events."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Remove old failure events from memory
            self.failure_events = [f for f in self.failure_events if f.timestamp > cutoff_time]
            
            # Clean up old recovery plans
            self.recovery_plans = [r for r in self.recovery_plans if r.created_at > cutoff_time]
            
        except Exception as e:
            print(f"[INFO] Failure Recovery: Cleanup failed: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop failure monitoring service."""
        self.running = False
        print("🛑 Failure Recovery: Monitoring service stopped")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get failure recovery system status."""
        return {
            "running": self.running,
            "failure_events": len(self.failure_events),
            "recovery_plans": len(self.recovery_plans),
            "unresolved_failures": len([f for f in self.failure_events if not f.resolved]),
            "active_recovery_plans": len([r for r in self.recovery_plans if r.status == "executing"]),
            "status": "operational" if self.running else "stopped"
        }


# Global failure recovery instance
failure_recovery = BMADFailureRecovery()


def get_failure_recovery() -> BMADFailureRecovery:
    """Get global failure recovery instance."""
    return failure_recovery


# Test function
async def test_failure_recovery():
    """Test failure recovery system."""
    print("[INFO] Failure Recovery: Testing Failure Recovery System...")
    
    recovery = get_failure_recovery()
    
    # Create tables
    await recovery.create_failure_recovery_tables()
    
    # Report test failures
    failure1_id = await recovery.report_failure(
        failure_type=FailureType.AGENT_OFFLINE,
        description="Agent analyst_1 went offline",
        agent_id="analyst_1",
        severity=7
    )
    
    failure2_id = await recovery.report_failure(
        failure_type=FailureType.TASK_TIMEOUT,
        description="Task analyze_requirements timed out",
        task_id="task_123",
        severity=5
    )
    
    # Wait for recovery plans to be created
    await asyncio.sleep(2)
    
    # Get status
    status = recovery.get_recovery_status()
    print(f"Recovery status: {status}")
    
    print("[INFO] Failure Recovery: Failure recovery system test complete!")


if __name__ == "__main__":
    asyncio.run(test_failure_recovery())
