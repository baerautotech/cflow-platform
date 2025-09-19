"""
BMAD Agent State Persistence

Production-ready agent state persistence using Supabase.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class AgentState(Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentStateData:
    """Agent state data structure."""
    agent_id: str = ""
    agent_type: str = ""
    state: AgentState = AgentState.IDLE
    current_task_id: Optional[str] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    last_heartbeat: datetime = None
    capabilities: List[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskStateData:
    """Task state data structure."""
    task_id: str = ""
    agent_id: str = ""
    agent_type: str = ""
    task_name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    parameters: Dict[str, Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class BMADAgentStatePersistence:
    """Production-ready agent state persistence."""
    
    def __init__(self):
        self.supabase_client = None
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Create Supabase client."""
        try:
            from .config.supabase_config import get_api_key, get_rest_url
            
            url = get_rest_url()
            key = get_api_key(secure=True)
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("[INFO] Agent State Persistence: Supabase client created")
            else:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                
        except Exception as e:
            print(f"[INFO][INFO] Agent State Persistence: Supabase setup failed: {e}")
    
    async def create_agent_state_tables(self) -> bool:
        """Create agent state tables in Supabase using migrations."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return False
            
            # Use Supabase migrations to create tables
            from .migrations import apply_migration
            
            # Create agent_states table migration
            agent_states_migration = """
            CREATE TABLE IF NOT EXISTS agent_states (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id TEXT UNIQUE NOT NULL,
                agent_type TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('idle', 'busy', 'overloaded', 'error', 'offline')),
                current_task_id TEXT,
                cpu_usage FLOAT DEFAULT 0.0,
                memory_usage FLOAT DEFAULT 0.0,
                active_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                average_response_time FLOAT DEFAULT 0.0,
                last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                capabilities JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id ON agent_states(agent_id);
            CREATE INDEX IF NOT EXISTS idx_agent_states_agent_type ON agent_states(agent_type);
            CREATE INDEX IF NOT EXISTS idx_agent_states_state ON agent_states(state);
            """
            
            # Create task_states table migration
            task_states_migration = """
            CREATE TABLE IF NOT EXISTS task_states (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                parameters JSONB DEFAULT '{}',
                result JSONB,
                error TEXT,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_task_states_task_id ON task_states(task_id);
            CREATE INDEX IF NOT EXISTS idx_task_states_agent_id ON task_states(agent_id);
            CREATE INDEX IF NOT EXISTS idx_task_states_status ON task_states(status);
            """
            
            # Apply migrations
            apply_migration("create_agent_states_table", agent_states_migration)
            apply_migration("create_task_states_table", task_states_migration)
            
            print("[INFO] Agent State Persistence: Tables created successfully")
            return True
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to create tables: {e}")
            return False
    
    async def save_agent_state(self, agent_state: AgentStateData) -> bool:
        """Save agent state to Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return False
            
            # Convert to dict for Supabase
            state_data = {
                "agent_id": agent_state.agent_id,
                "agent_type": agent_state.agent_type,
                "state": agent_state.state.value,
                "current_task_id": agent_state.current_task_id,
                "cpu_usage": agent_state.cpu_usage,
                "memory_usage": agent_state.memory_usage,
                "active_tasks": agent_state.active_tasks,
                "completed_tasks": agent_state.completed_tasks,
                "failed_tasks": agent_state.failed_tasks,
                "average_response_time": agent_state.average_response_time,
                "last_heartbeat": agent_state.last_heartbeat.isoformat(),
                "capabilities": agent_state.capabilities,
                "metadata": agent_state.metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert agent state
            result = self.supabase_client.table("agent_states").upsert(
                state_data,
                on_conflict="agent_id"
            ).execute()
            
            print(f"[INFO] Agent State Persistence: Saved state for agent {agent_state.agent_id}")
            return True
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to save agent state: {e}")
            return False
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateData]:
        """Get agent state from Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return None
            
            result = self.supabase_client.table("agent_states").select("*").eq("agent_id", agent_id).execute()
            
            if result.data:
                data = result.data[0]
                return AgentStateData(
                    agent_id=data["agent_id"],
                    agent_type=data["agent_type"],
                    state=AgentState(data["state"]),
                    current_task_id=data.get("current_task_id"),
                    cpu_usage=data.get("cpu_usage", 0.0),
                    memory_usage=data.get("memory_usage", 0.0),
                    active_tasks=data.get("active_tasks", 0),
                    completed_tasks=data.get("completed_tasks", 0),
                    failed_tasks=data.get("failed_tasks", 0),
                    average_response_time=data.get("average_response_time", 0.0),
                    last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
                    capabilities=data.get("capabilities", []),
                    metadata=data.get("metadata", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )
            
            return None
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to get agent state: {e}")
            return None
    
    async def get_all_agent_states(self, agent_type: Optional[str] = None) -> List[AgentStateData]:
        """Get all agent states from Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return []
            
            query = self.supabase_client.table("agent_states").select("*")
            
            if agent_type:
                query = query.eq("agent_type", agent_type)
            
            result = query.execute()
            
            agent_states = []
            for data in result.data:
                agent_state = AgentStateData(
                    agent_id=data["agent_id"],
                    agent_type=data["agent_type"],
                    state=AgentState(data["state"]),
                    current_task_id=data.get("current_task_id"),
                    cpu_usage=data.get("cpu_usage", 0.0),
                    memory_usage=data.get("memory_usage", 0.0),
                    active_tasks=data.get("active_tasks", 0),
                    completed_tasks=data.get("completed_tasks", 0),
                    failed_tasks=data.get("failed_tasks", 0),
                    average_response_time=data.get("average_response_time", 0.0),
                    last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
                    capabilities=data.get("capabilities", []),
                    metadata=data.get("metadata", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )
                agent_states.append(agent_state)
            
            return agent_states
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to get agent states: {e}")
            return []
    
    async def save_task_state(self, task_state: TaskStateData) -> bool:
        """Save task state to Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return False
            
            # Convert to dict for Supabase
            state_data = {
                "task_id": task_state.task_id,
                "agent_id": task_state.agent_id,
                "agent_type": task_state.agent_type,
                "task_name": task_state.task_name,
                "status": task_state.status.value,
                "parameters": task_state.parameters,
                "result": task_state.result,
                "error": task_state.error,
                "started_at": task_state.started_at.isoformat() if task_state.started_at else None,
                "completed_at": task_state.completed_at.isoformat() if task_state.completed_at else None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert task state
            result = self.supabase_client.table("task_states").upsert(
                state_data,
                on_conflict="task_id"
            ).execute()
            
            print(f"[INFO] Agent State Persistence: Saved state for task {task_state.task_id}")
            return True
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to save task state: {e}")
            return False
    
    async def get_task_state(self, task_id: str) -> Optional[TaskStateData]:
        """Get task state from Supabase."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return None
            
            result = self.supabase_client.table("task_states").select("*").eq("task_id", task_id).execute()
            
            if result.data:
                data = result.data[0]
                return TaskStateData(
                    task_id=data["task_id"],
                    agent_id=data["agent_id"],
                    agent_type=data["agent_type"],
                    task_name=data["task_name"],
                    status=TaskStatus(data["status"]),
                    parameters=data.get("parameters", {}),
                    result=data.get("result"),
                    error=data.get("error"),
                    started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )
            
            return None
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to get task state: {e}")
            return None
    
    async def get_agent_tasks(self, agent_id: str, status: Optional[TaskStatus] = None) -> List[TaskStateData]:
        """Get tasks for a specific agent."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return []
            
            query = self.supabase_client.table("task_states").select("*").eq("agent_id", agent_id)
            
            if status:
                query = query.eq("status", status.value)
            
            result = query.execute()
            
            tasks = []
            for data in result.data:
                task_state = TaskStateData(
                    task_id=data["task_id"],
                    agent_id=data["agent_id"],
                    agent_type=data["agent_type"],
                    task_name=data["task_name"],
                    status=TaskStatus(data["status"]),
                    parameters=data.get("parameters", {}),
                    result=data.get("result"),
                    error=data.get("error"),
                    started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )
                tasks.append(task_state)
            
            return tasks
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to get agent tasks: {e}")
            return []
    
    async def cleanup_old_states(self, days_old: int = 7) -> bool:
        """Clean up old agent and task states."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] Agent State Persistence: Supabase not available")
                return False
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            
            # Clean up old agent states
            self.supabase_client.table("agent_states").delete().lt("updated_at", cutoff_date).execute()
            
            # Clean up old task states
            self.supabase_client.table("task_states").delete().lt("updated_at", cutoff_date).execute()
            
            print(f"[INFO] Agent State Persistence: Cleaned up states older than {days_old} days")
            return True
            
        except Exception as e:
            print(f"[INFO] Agent State Persistence: Failed to cleanup old states: {e}")
            return False
    
    def get_persistence_status(self) -> Dict[str, Any]:
        """Get persistence system status."""
        return {
            "supabase_connected": self.supabase_client is not None,
            "status": "operational" if self.supabase_client else "offline"
        }


# Global persistence instance
agent_state_persistence = BMADAgentStatePersistence()


def get_agent_state_persistence() -> BMADAgentStatePersistence:
    """Get global agent state persistence instance."""
    return agent_state_persistence


# Test function
async def test_agent_state_persistence():
    """Test agent state persistence."""
    print("[INFO] Agent State Persistence: Testing Agent State Persistence...")
    
    persistence = get_agent_state_persistence()
    
    # Create tables
    await persistence.create_agent_state_tables()
    
    # Create test agent state
    agent_state = AgentStateData(
        agent_id="test_agent_1",
        agent_type="analyst",
        state=AgentState.IDLE,
        current_task_id=None,
        cpu_usage=25.0,
        memory_usage=40.0,
        active_tasks=0,
        completed_tasks=10,
        failed_tasks=1,
        average_response_time=2.5,
        last_heartbeat=datetime.utcnow(),
        capabilities=["analysis", "research"],
        metadata={"version": "1.0", "region": "us-west"}
    )
    
    # Save agent state
    await persistence.save_agent_state(agent_state)
    
    # Retrieve agent state
    retrieved_state = await persistence.get_agent_state("test_agent_1")
    if retrieved_state:
        print(f"Retrieved agent state: {retrieved_state.agent_id} - {retrieved_state.state.value}")
    
    # Create test task state
    task_state = TaskStateData(
        task_id="test_task_1",
        agent_id="test_agent_1",
        agent_type="analyst",
        task_name="analyze_requirements",
        status=TaskStatus.COMPLETED,
        parameters={"project": "test_project"},
        result={"analysis": "complete"},
        error=None,
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow()
    )
    
    # Save task state
    await persistence.save_task_state(task_state)
    
    # Get agent tasks
    tasks = await persistence.get_agent_tasks("test_agent_1")
    print(f"Agent has {len(tasks)} tasks")
    
    # Get status
    status = persistence.get_persistence_status()
    print(f"Persistence status: {status}")
    
    print("[INFO] Agent State Persistence: Agent state persistence test complete!")


if __name__ == "__main__":
    asyncio.run(test_agent_state_persistence())
