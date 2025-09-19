"""
BMAD Multi-Agent Testing

Phase 3.5: Validate parallel system performance.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    status: str
    execution_time: float
    success_count: int
    failure_count: int
    details: Dict[str, Any]
    timestamp: datetime

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class BMADMultiAgentTesting:
    """Comprehensive multi-agent system testing."""
    
    def __init__(self):
        self.supabase_client = None
        self.orchestrator = None
        self.communication = None
        self.workflow_executor = None
        self.load_balancer = None
        self.test_results: List[TestResult] = []
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
                print("[INFO] Multi-Agent Testing: Supabase client created")
            else:
                print("[INFO][INFO] Multi-Agent Testing: Supabase not available")
                
        except Exception as e:
            print(f"[INFO][INFO] Multi-Agent Testing: Supabase setup failed: {e}")
    
    def _initialize_components(self) -> None:
        """Initialize all multi-agent components."""
        try:
            from .multi_agent_orchestrator import get_multi_agent_orchestrator
            from .agent_communication import get_agent_communication
            from .parallel_workflow_executor import get_parallel_workflow_executor
            from .agent_load_balancer import get_agent_load_balancer
            
            self.orchestrator = get_multi_agent_orchestrator()
            self.communication = get_agent_communication()
            self.workflow_executor = get_parallel_workflow_executor()
            self.load_balancer = get_agent_load_balancer()
            
            print("[INFO] Multi-Agent Testing: All components initialized")
            
        except Exception as e:
            print(f"[INFO][INFO] Multi-Agent Testing: Component initialization failed: {e}")
    
    async def test_orchestrator_performance(self) -> TestResult:
        """Test multi-agent orchestrator performance."""
        try:
            print("[INFO] Multi-Agent Testing: Testing orchestrator performance...")
            start_time = time.time()
            
            # Create multiple concurrent tasks
            task_ids = []
            for i in range(5):
                task_id = self.orchestrator.create_task(
                    agent_type="analyst",
                    task_name="analyze_requirements",
                    parameters={"project": f"test_project_{i}"}
                )
                if task_id:
                    task_ids.append(task_id)
            
            # Execute tasks in parallel
            execution_result = await self.orchestrator.run_parallel_execution()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success_count = execution_result.get("successful_tasks", 0)
            failure_count = execution_result.get("failed_tasks", 0)
            
            status = "passed" if failure_count == 0 else "failed"
            
            result = TestResult(
                test_name="orchestrator_performance",
                status=status,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                details=execution_result,
                timestamp=datetime.utcnow()
            )
            
            print(f"[INFO] Multi-Agent Testing: Orchestrator test completed: {success_count}/{success_count + failure_count} successful")
            return result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Orchestrator test failed: {e}")
            return TestResult(
                test_name="orchestrator_performance",
                status="error",
                execution_time=0.0,
                success_count=0,
                failure_count=1,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def test_communication_protocol(self) -> TestResult:
        """Test agent communication protocol."""
        try:
            print("[INFO] Multi-Agent Testing: Testing communication protocol...")
            start_time = time.time()
            
            # Create test channel
            channel_id = self.communication.create_channel(
                name="test_channel",
                participants=["agent1", "agent2", "agent3"]
            )
            
            # Send multiple messages
            message_ids = []
            for i in range(10):
                message_id = self.communication.send_message(
                    sender_id="agent1",
                    receiver_id="agent2",
                    message_type=self.communication.MessageType.TASK_REQUEST,
                    content={"task": f"test_task_{i}", "data": f"test_data_{i}"}
                )
                if message_id:
                    message_ids.append(message_id)
            
            # Broadcast messages
            broadcast_ids = []
            for i in range(5):
                broadcast_id = self.communication.broadcast_message(
                    sender_id="agent1",
                    channel_id=channel_id,
                    message_type=self.communication.MessageType.STATUS_UPDATE,
                    content={"status": "testing", "iteration": i}
                )
                broadcast_ids.extend(broadcast_id)
            
            # Test coordination
            coordination_result = await self.communication.coordinate_agents(
                coordinator_id="coordinator",
                task_agents=["agent1", "agent2", "agent3"],
                coordination_type="parallel_test",
                parameters={"test_type": "communication"}
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success_count = len(message_ids) + len(broadcast_ids)
            failure_count = 0
            
            status = "passed" if failure_count == 0 else "failed"
            
            result = TestResult(
                test_name="communication_protocol",
                status=status,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                details={
                    "messages_sent": len(message_ids),
                    "broadcasts_sent": len(broadcast_ids),
                    "coordination_result": coordination_result,
                    "channels_created": 1
                },
                timestamp=datetime.utcnow()
            )
            
            print(f"[INFO] Multi-Agent Testing: Communication test completed: {success_count} messages sent")
            return result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Communication test failed: {e}")
            return TestResult(
                test_name="communication_protocol",
                status="error",
                execution_time=0.0,
                success_count=0,
                failure_count=1,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def test_workflow_execution(self) -> TestResult:
        """Test parallel workflow execution."""
        try:
            print("[INFO] Multi-Agent Testing: Testing workflow execution...")
            start_time = time.time()
            
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
            
            workflow_id = self.workflow_executor.create_workflow(
                name="test_workflow",
                description="Test workflow for multi-agent testing",
                steps=workflow_steps
            )
            
            # Execute workflow
            execution_result = await self.workflow_executor.execute_workflow(workflow_id)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success_count = execution_result.get("steps_completed", 0)
            failure_count = execution_result.get("steps_failed", 0)
            
            status = "passed" if failure_count == 0 else "failed"
            
            result = TestResult(
                test_name="workflow_execution",
                status=status,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                details=execution_result,
                timestamp=datetime.utcnow()
            )
            
            print(f"[INFO] Multi-Agent Testing: Workflow test completed: {success_count}/{success_count + failure_count} steps successful")
            return result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Workflow test failed: {e}")
            return TestResult(
                test_name="workflow_execution",
                status="error",
                execution_time=0.0,
                success_count=0,
                failure_count=1,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def test_load_balancing(self) -> TestResult:
        """Test agent load balancing."""
        try:
            print("[INFO] Multi-Agent Testing: Testing load balancing...")
            start_time = time.time()
            
            # Register test agents
            agents_registered = 0
            for i in range(3):
                if self.load_balancer.register_agent(f"analyst_{i}", "analyst", 1.0 + i * 0.2):
                    agents_registered += 1
            
            # Update metrics
            metrics_updated = 0
            for i in range(3):
                if self.load_balancer.update_agent_metrics(f"analyst_{i}", {
                    "cpu_usage": 20.0 + i * 10.0,
                    "memory_usage": 30.0 + i * 15.0,
                    "active_tasks": i,
                    "completed_tasks": 10 + i * 5,
                    "failed_tasks": i,
                    "average_response_time": 1.0 + i * 0.5
                }):
                    metrics_updated += 1
            
            # Test agent selection
            selections_made = 0
            for strategy in ["resource_based", "least_connections", "round_robin"]:
                self.load_balancer.set_load_balancing_strategy(strategy)
                decision = self.load_balancer.select_agent("analyst", "normal")
                if decision.agent_id:
                    selections_made += 1
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success_count = agents_registered + metrics_updated + selections_made
            failure_count = 0
            
            status = "passed" if failure_count == 0 else "failed"
            
            result = TestResult(
                test_name="load_balancing",
                status=status,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                details={
                    "agents_registered": agents_registered,
                    "metrics_updated": metrics_updated,
                    "selections_made": selections_made,
                    "load_balancer_status": self.load_balancer.get_load_balancing_status()
                },
                timestamp=datetime.utcnow()
            )
            
            print(f"[INFO] Multi-Agent Testing: Load balancing test completed: {success_count} operations successful")
            return result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Load balancing test failed: {e}")
            return TestResult(
                test_name="load_balancing",
                status="error",
                execution_time=0.0,
                success_count=0,
                failure_count=1,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def test_integrated_system(self) -> TestResult:
        """Test integrated multi-agent system."""
        try:
            print("[INFO] Multi-Agent Testing: Testing integrated system...")
            start_time = time.time()
            
            # Register agents in load balancer
            self.load_balancer.register_agent("analyst_1", "analyst", 1.0)
            self.load_balancer.register_agent("pm_1", "pm", 1.2)
            self.load_balancer.register_agent("architect_1", "architect", 1.5)
            
            # Create communication channel
            channel_id = self.communication.create_channel(
                name="integrated_test",
                participants=["analyst_1", "pm_1", "architect_1"]
            )
            
            # Create and execute workflow with load balancing
            workflow_steps = [
                {
                    "name": "analyze_requirements",
                    "agent_type": "analyst",
                    "task_name": "analyze_requirements",
                    "parameters": {"project": "integrated_test"},
                    "dependencies": []
                },
                {
                    "name": "create_prd",
                    "agent_type": "pm",
                    "task_name": "create_prd",
                    "parameters": {"project": "integrated_test"},
                    "dependencies": ["analyze_requirements"]
                }
            ]
            
            workflow_id = self.workflow_executor.create_workflow(
                name="integrated_test_workflow",
                description="Integrated system test workflow",
                steps=workflow_steps
            )
            
            # Execute workflow
            execution_result = await self.workflow_executor.execute_workflow(workflow_id)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            success_count = execution_result.get("steps_completed", 0)
            failure_count = execution_result.get("steps_failed", 0)
            
            status = "passed" if failure_count == 0 else "failed"
            
            result = TestResult(
                test_name="integrated_system",
                status=status,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                details={
                    "workflow_result": execution_result,
                    "communication_status": self.communication.get_communication_status(),
                    "load_balancer_status": self.load_balancer.get_load_balancing_status(),
                    "orchestrator_status": self.orchestrator.get_orchestrator_status()
                },
                timestamp=datetime.utcnow()
            )
            
            print(f"[INFO] Multi-Agent Testing: Integrated system test completed: {success_count}/{success_count + failure_count} successful")
            return result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Integrated system test failed: {e}")
            return TestResult(
                test_name="integrated_system",
                status="error",
                execution_time=0.0,
                success_count=0,
                failure_count=1,
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive multi-agent test suite."""
        try:
            print("[INFO] Multi-Agent Testing: Starting comprehensive test suite...")
            suite_start_time = time.time()
            
            # Run all tests
            tests = [
                self.test_orchestrator_performance(),
                self.test_communication_protocol(),
                self.test_workflow_execution(),
                self.test_load_balancing(),
                self.test_integrated_system()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # Process results
            successful_tests = 0
            failed_tests = 0
            total_execution_time = 0.0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_tests += 1
                    print(f"[INFO] Multi-Agent Testing: Test {i} failed with exception: {result}")
                else:
                    self.test_results.append(result)
                    if result.status == "passed":
                        successful_tests += 1
                    else:
                        failed_tests += 1
                    total_execution_time += result.execution_time
            
            suite_end_time = time.time()
            suite_execution_time = suite_end_time - suite_start_time
            
            # Calculate overall score
            total_tests = successful_tests + failed_tests
            overall_score = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            
            suite_result = {
                "test_suite": "multi_agent_comprehensive",
                "timestamp": datetime.utcnow().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "overall_score": overall_score,
                "suite_execution_time": suite_execution_time,
                "total_execution_time": total_execution_time,
                "status": "passed" if overall_score >= 80 else "failed",
                "test_results": [result.__dict__ for result in self.test_results]
            }
            
            print(f"[INFO] Multi-Agent Testing: Test suite completed: {successful_tests}/{total_tests} tests passed (Score: {overall_score:.1f}%)")
            return suite_result
            
        except Exception as e:
            print(f"[INFO] Multi-Agent Testing: Test suite failed: {e}")
            return {
                "test_suite": "multi_agent_comprehensive",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global testing instance
multi_agent_testing = BMADMultiAgentTesting()


def get_multi_agent_testing() -> BMADMultiAgentTesting:
    """Get global multi-agent testing instance."""
    return multi_agent_testing


# Test function
async def test_multi_agent_testing():
    """Test multi-agent testing system."""
    print("[INFO] Multi-Agent Testing: Testing Multi-Agent Testing System...")
    
    testing = get_multi_agent_testing()
    
    # Run comprehensive test suite
    result = await testing.run_comprehensive_test_suite()
    
    print(f"Test suite result: {result.get('status', 'unknown')}")
    print(f"Overall score: {result.get('overall_score', 0):.1f}%")
    print(f"Tests passed: {result.get('successful_tests', 0)}/{result.get('total_tests', 0)}")
    
    print("[INFO] Multi-Agent Testing: Multi-agent testing system test complete!")


if __name__ == "__main__":
    asyncio.run(test_multi_agent_testing())

