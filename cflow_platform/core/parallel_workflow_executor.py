"""
BMAD Parallel Workflow Execution

Phase 3.3: Concurrent workflow processing system.
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowPriority(Enum):
    """Workflow priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkflowStep:
    """Individual workflow step definition."""
    id: str
    name: str
    agent_type: str
    task_name: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    timeout: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    id: str = None
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = None
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    created_at: datetime = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.steps is None:
            self.steps = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BMADParallelWorkflowExecutor:
    """Parallel workflow execution engine for BMAD."""
    
    def __init__(self):
        self.supabase_client = None
        self.active_workflows: Dict[str, WorkflowDefinition] = {}
        self.workflow_queue: List[WorkflowDefinition] = []
        self.completed_workflows: Dict[str, WorkflowDefinition] = {}
        self.max_concurrent_workflows = 3
        self.max_concurrent_steps = 10
        self.orchestrator = None
        self.communication = None
        self._ensure_supabase()
        self._initialize_components()
    
    def _ensure_supabase(self) -> None:
        """Create Supabase client."""
        try:
            from supabase import create_client
            from .config.supabase_config import get_api_key, get_rest_url
            
            url = get_rest_url()
            key = get_api_key(secure=True)
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("[INFO] Parallel Workflow: Supabase client created")
            else:
                print("[INFO][INFO] Parallel Workflow: Supabase not available")
                
        except Exception as e:
            print(f"[INFO][INFO] Parallel Workflow: Supabase setup failed: {e}")
    
    def _initialize_components(self) -> None:
        """Initialize orchestrator and communication components."""
        try:
            from .multi_agent_orchestrator import get_multi_agent_orchestrator
            from .agent_communication import get_agent_communication
            
            self.orchestrator = get_multi_agent_orchestrator()
            self.communication = get_agent_communication()
            
            print("[INFO] Parallel Workflow: Components initialized")
            
        except Exception as e:
            print(f"[INFO][INFO] Parallel Workflow: Component initialization failed: {e}")
    
    def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]], 
                       priority: WorkflowPriority = WorkflowPriority.NORMAL) -> str:
        """Create a new workflow definition."""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Convert step definitions to WorkflowStep objects
            workflow_steps = []
            for step_def in steps:
                step = WorkflowStep(
                    id=str(uuid.uuid4()),
                    name=step_def["name"],
                    agent_type=step_def["agent_type"],
                    task_name=step_def["task_name"],
                    parameters=step_def.get("parameters", {}),
                    dependencies=step_def.get("dependencies", []),
                    timeout=step_def.get("timeout")
                )
                workflow_steps.append(step)
            
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=name,
                description=description,
                steps=workflow_steps,
                priority=priority
            )
            
            # Add to queue
            self.workflow_queue.append(workflow)
            
            # Sort by priority
            self.workflow_queue.sort(key=lambda w: w.priority.value, reverse=True)
            
            print(f"[INFO] Parallel Workflow: Created workflow '{name}' with {len(workflow_steps)} steps")
            return workflow_id
            
        except Exception as e:
            print(f"[INFO] Parallel Workflow: Failed to create workflow: {e}")
            return None
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a complete workflow."""
        try:
            if workflow_id not in [w.id for w in self.workflow_queue]:
                print(f"[INFO] Parallel Workflow: Workflow {workflow_id} not found in queue")
                return {"status": "error", "error": "Workflow not found"}
            
            # Find workflow
            workflow = next(w for w in self.workflow_queue if w.id == workflow_id)
            
            print(f"[INFO] Parallel Workflow: Starting workflow '{workflow.name}'")
            
            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.utcnow()
            self.active_workflows[workflow_id] = workflow
            self.workflow_queue.remove(workflow)
            
            # Create coordination channel
            channel_id = self.communication.create_channel(
                name=f"workflow_{workflow.name}_{workflow_id[:8]}",
                participants=[f"workflow_{workflow_id}"] + [step.agent_type for step in workflow.steps]
            )
            
            # Execute workflow steps
            execution_result = await self._execute_workflow_steps(workflow, channel_id)
            
            # Update workflow completion
            if execution_result["status"] == "completed":
                workflow.status = WorkflowStatus.COMPLETED
                workflow.result = execution_result["result"]
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.error = execution_result.get("error", "Unknown error")
            
            workflow.completed_at = datetime.utcnow()
            self.completed_workflows[workflow_id] = workflow
            
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            result = {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "execution_time": (workflow.completed_at - workflow.started_at).total_seconds(),
                "steps_completed": execution_result["steps_completed"],
                "steps_failed": execution_result["steps_failed"],
                "result": workflow.result,
                "error": workflow.error
            }
            
            print(f"[INFO] Parallel Workflow: Workflow '{workflow.name}' completed with status: {workflow.status.value}")
            return result
            
        except Exception as e:
            print(f"[INFO] Parallel Workflow: Workflow execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_workflow_steps(self, workflow: WorkflowDefinition, channel_id: str) -> Dict[str, Any]:
        """Execute all steps in a workflow."""
        try:
            completed_steps = 0
            failed_steps = 0
            step_results = {}
            
            # Continue until all steps are processed
            while completed_steps + failed_steps < len(workflow.steps):
                # Get ready steps (dependencies satisfied)
                ready_steps = self._get_ready_steps(workflow.steps)
                
                if not ready_steps:
                    print("[INFO][INFO] Parallel Workflow: No ready steps, checking for circular dependencies")
                    # Check if we have unprocessed steps
                    unprocessed = [s for s in workflow.steps if s.status == WorkflowStatus.PENDING]
                    if unprocessed:
                        print(f"[INFO] Parallel Workflow: Circular dependencies detected in {len(unprocessed)} steps")
                        failed_steps += len(unprocessed)
                        for step in unprocessed:
                            step.status = WorkflowStatus.FAILED
                            step.error = "Circular dependency detected"
                    break
                
                # Limit concurrent step execution
                concurrent_steps = ready_steps[:self.max_concurrent_steps]
                
                # Execute steps in parallel
                step_tasks = [self._execute_workflow_step(step, channel_id) for step in concurrent_steps]
                step_results_batch = await asyncio.gather(*step_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(step_results_batch):
                    step = concurrent_steps[i]
                    if isinstance(result, Exception):
                        step.status = WorkflowStatus.FAILED
                        step.error = str(result)
                        failed_steps += 1
                        print(f"[INFO] Parallel Workflow: Step '{step.name}' failed: {result}")
                    else:
                        step.status = WorkflowStatus.COMPLETED
                        step.result = result
                        completed_steps += 1
                        step_results[step.id] = result
                        print(f"[INFO] Parallel Workflow: Step '{step.name}' completed")
            
            # Determine overall result
            if failed_steps == 0:
                status = "completed"
                result = step_results
            else:
                status = "failed"
                result = None
            
            return {
                "status": status,
                "steps_completed": completed_steps,
                "steps_failed": failed_steps,
                "result": result
            }
            
        except Exception as e:
            print(f"[INFO] Parallel Workflow: Step execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_workflow_step(self, step: WorkflowStep, channel_id: str) -> Any:
        """Execute a single workflow step."""
        try:
            print(f"[INFO] Parallel Workflow: Executing step '{step.name}' with {step.agent_type} agent")
            
            # Update step status
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.utcnow()
            
            # Send coordination message
            from .agent_communication import MessageType
            self.communication.broadcast_message(
                sender_id=f"workflow_{step.id}",
                channel_id=channel_id,
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": "running",
                    "agent_type": step.agent_type
                }
            )
            
            # Create task for orchestrator
            from .multi_agent_orchestrator import TaskPriority
            task_id = self.orchestrator.create_task(
                agent_type=step.agent_type,
                task_name=step.task_name,
                parameters=step.parameters,
                priority=TaskPriority.HIGH
            )
            
            if not task_id:
                raise ValueError(f"Failed to create task for step '{step.name}'")
            
            # Execute task
            result = await self.orchestrator.execute_task(
                next(t for t in self.orchestrator.task_queue if t.id == task_id)
            )
            
            # Update step completion
            step.status = WorkflowStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            step.result = result
            
            # Send completion message
            self.communication.broadcast_message(
                sender_id=f"workflow_{step.id}",
                channel_id=channel_id,
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": "completed",
                    "result": result
                }
            )
            
            print(f"[INFO] Parallel Workflow: Step '{step.name}' completed successfully")
            return result
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            
            print(f"[INFO] Parallel Workflow: Step '{step.name}' failed: {e}")
            raise
    
    def _get_ready_steps(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready_steps = []
        
        for step in steps:
            if step.status != WorkflowStatus.PENDING:
                continue
            
            # Check dependencies
            dependencies_satisfied = True
            for dep_name in step.dependencies:
                # Find dependency by name (not ID)
                dep_step = next((s for s in steps if s.name == dep_name), None)
                if not dep_step or dep_step.status != WorkflowStatus.COMPLETED:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                ready_steps.append(step)
        
        return ready_steps
    
    async def run_parallel_workflows(self) -> Dict[str, Any]:
        """Run multiple workflows in parallel."""
        try:
            print(f"[INFO] Parallel Workflow: Starting parallel workflow execution")
            
            # Get ready workflows
            ready_workflows = self.workflow_queue[:self.max_concurrent_workflows]
            
            if not ready_workflows:
                print("[INFO][INFO] Parallel Workflow: No workflows ready for execution")
                return {"status": "no_workflows", "workflows": 0}
            
            # Execute workflows in parallel
            start_time = time.time()
            workflow_tasks = [self.execute_workflow(w.id) for w in ready_workflows]
            results = await asyncio.gather(*workflow_tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results
            successful_workflows = 0
            failed_workflows = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_workflows += 1
                    print(f"[INFO] Parallel Workflow: Workflow {ready_workflows[i].name} failed: {result}")
                else:
                    successful_workflows += 1
            
            execution_time = end_time - start_time
            
            result = {
                "status": "completed",
                "total_workflows": len(ready_workflows),
                "successful_workflows": successful_workflows,
                "failed_workflows": failed_workflows,
                "execution_time": execution_time,
                "active_workflows": len(self.active_workflows),
                "remaining_workflows": len(self.workflow_queue)
            }
            
            print(f"[INFO] Parallel Workflow: Parallel execution complete: {successful_workflows}/{len(ready_workflows)} successful in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"[INFO] Parallel Workflow: Parallel execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_executor_status(self) -> Dict[str, Any]:
        """Get workflow executor status."""
        return {
            "active_workflows": len(self.active_workflows),
            "queued_workflows": len(self.workflow_queue),
            "completed_workflows": len(self.completed_workflows),
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "max_concurrent_steps": self.max_concurrent_steps,
            "status": "operational"
        }


# Global executor instance
parallel_workflow_executor = BMADParallelWorkflowExecutor()


def get_parallel_workflow_executor() -> BMADParallelWorkflowExecutor:
    """Get global parallel workflow executor instance."""
    return parallel_workflow_executor


# Test function
async def test_parallel_workflow_executor():
    """Test parallel workflow executor."""
    print("[INFO] Parallel Workflow: Testing Parallel Workflow Executor...")
    
    executor = get_parallel_workflow_executor()
    
    # Create test workflow
    workflow_steps = [
        {
            "name": "analyze_requirements",
            "agent_type": "analyst",
            "task_name": "analyze_requirements",
            "parameters": {"project": "test_project"},
            "dependencies": []
        },
        {
            "name": "create_prd",
            "agent_type": "pm",
            "task_name": "create_prd",
            "parameters": {"project": "test_project"},
            "dependencies": ["analyze_requirements"]
        },
        {
            "name": "design_architecture",
            "agent_type": "architect",
            "task_name": "design_architecture",
            "parameters": {"project": "test_project"},
            "dependencies": ["create_prd"]
        }
    ]
    
    workflow_id = executor.create_workflow(
        name="test_workflow",
        description="Test workflow for parallel execution",
        steps=workflow_steps,
        priority=WorkflowPriority.HIGH
    )
    
    print(f"Created workflow: {workflow_id}")
    
    # Execute workflow
    result = await executor.execute_workflow(workflow_id)
    print(f"Workflow execution result: {result}")
    
    # Get status
    status = executor.get_executor_status()
    print(f"Executor status: {status}")
    
    print("[INFO] Parallel Workflow: Parallel workflow executor test complete!")


if __name__ == "__main__":
    asyncio.run(test_parallel_workflow_executor())
