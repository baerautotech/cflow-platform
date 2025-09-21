"""
Scenario-based Testing Engine for BMAD Workflows

This module provides scenario-based testing capabilities for real-world use cases,
including scenario definition, execution, validation, and reporting.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ScenarioPriority(Enum):
    """Scenario priority levels based on BMAD test priorities matrix"""
    P0_CRITICAL = "P0"  # Revenue-impacting, security-critical, compliance
    P1_HIGH = "P1"     # Core user journeys, frequently used
    P2_MEDIUM = "P2"   # Secondary features, admin functions
    P3_LOW = "P3"      # Nice-to-have, rarely used


class ScenarioStatus(Enum):
    """Scenario execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ScenarioStep:
    """Individual step within a scenario"""
    step_id: str
    name: str
    description: str
    action: str  # Tool or action to execute
    parameters: Dict[str, Any]
    expected_result: Dict[str, Any]
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ScenarioResult:
    """Result of scenario execution"""
    scenario_id: str
    execution_id: str
    status: ScenarioStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    error_summary: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestScenario:
    """Test scenario definition"""
    scenario_id: str
    name: str
    description: str
    priority: ScenarioPriority
    category: str  # e.g., "user_registration", "payment_flow", "data_migration"
    steps: List[ScenarioStep]
    prerequisites: List[str] = field(default_factory=list)
    cleanup_steps: List[ScenarioStep] = field(default_factory=list)
    expected_duration_seconds: float = 60.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScenarioTestingEngine:
    """Engine for executing scenario-based tests"""
    
    def __init__(self):
        self.scenarios: Dict[str, TestScenario] = {}
        self.execution_history: List[ScenarioResult] = []
        self.active_executions: Dict[str, ScenarioResult] = {}
        
    def register_scenario(self, scenario: TestScenario) -> None:
        """Register a new test scenario"""
        self.scenarios[scenario.scenario_id] = scenario
        logger.info(f"Registered scenario: {scenario.name} ({scenario.scenario_id})")
    
    def create_scenario(
        self,
        name: str,
        description: str,
        priority: ScenarioPriority,
        category: str,
        steps: List[Dict[str, Any]],
        prerequisites: List[str] = None,
        cleanup_steps: List[Dict[str, Any]] = None,
        expected_duration_seconds: float = 60.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> TestScenario:
        """Create a new test scenario"""
        
        scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
        
        # Convert step dictionaries to ScenarioStep objects
        scenario_steps = []
        for i, step_data in enumerate(steps):
            step = ScenarioStep(
                step_id=f"{scenario_id}_step_{i+1}",
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", ""),
                action=step_data.get("action", ""),
                parameters=step_data.get("parameters", {}),
                expected_result=step_data.get("expected_result", {}),
                timeout_seconds=step_data.get("timeout_seconds", 30.0),
                max_retries=step_data.get("max_retries", 3)
            )
            scenario_steps.append(step)
        
        # Convert cleanup step dictionaries to ScenarioStep objects
        cleanup_scenario_steps = []
        if cleanup_steps:
            for i, cleanup_data in enumerate(cleanup_steps):
                cleanup_step = ScenarioStep(
                    step_id=f"{scenario_id}_cleanup_{i+1}",
                    name=cleanup_data.get("name", f"Cleanup {i+1}"),
                    description=cleanup_data.get("description", ""),
                    action=cleanup_data.get("action", ""),
                    parameters=cleanup_data.get("parameters", {}),
                    expected_result=cleanup_data.get("expected_result", {}),
                    timeout_seconds=cleanup_data.get("timeout_seconds", 30.0),
                    max_retries=cleanup_data.get("max_retries", 3)
                )
                cleanup_scenario_steps.append(cleanup_step)
        
        scenario = TestScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            priority=priority,
            category=category,
            steps=scenario_steps,
            prerequisites=prerequisites or [],
            cleanup_steps=cleanup_scenario_steps,
            expected_duration_seconds=expected_duration_seconds,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.register_scenario(scenario)
        return scenario
    
    async def execute_scenario(
        self,
        scenario_id: str,
        context: Dict[str, Any] = None
    ) -> ScenarioResult:
        """Execute a test scenario"""
        
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.scenarios[scenario_id]
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        result = ScenarioResult(
            scenario_id=scenario_id,
            execution_id=execution_id,
            status=ScenarioStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.active_executions[execution_id] = result
        
        try:
            logger.info(f"Executing scenario: {scenario.name} ({scenario_id})")
            
            # Execute scenario steps
            step_results = []
            total_score = 0.0
            passed_steps = 0
            
            for step in scenario.steps:
                step_result = await self._execute_step(step, context or {})
                step_results.append(step_result)
                
                if step_result.get("status") == "PASSED":
                    passed_steps += 1
                    total_score += step_result.get("score", 100.0)
                elif step_result.get("status") == "FAILED":
                    result.status = ScenarioStatus.FAILED
                    result.error_summary = f"Step failed: {step.name}"
                    break
            
            # Calculate overall score
            if scenario.steps:
                result.overall_score = total_score / len(scenario.steps)
            
            # Determine final status
            if result.status == ScenarioStatus.RUNNING:
                if passed_steps == len(scenario.steps):
                    result.status = ScenarioStatus.PASSED
                else:
                    result.status = ScenarioStatus.FAILED
            
            result.step_results = step_results
            
        except Exception as e:
            logger.error(f"Scenario execution failed: {e}")
            result.status = ScenarioStatus.ERROR
            result.error_summary = str(e)
        
        finally:
            # Execute cleanup steps
            if scenario.cleanup_steps:
                await self._execute_cleanup_steps(scenario.cleanup_steps, context or {})
            
            # Finalize result
            result.end_time = datetime.now()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # Move to history
            self.execution_history.append(result)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return result
    
    async def _execute_step(
        self,
        step: ScenarioStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single scenario step"""
        
        step_start_time = time.time()
        
        try:
            # Merge context with step parameters
            parameters = {**context, **step.parameters}
            
            # Execute the step action (simplified - in real implementation, this would call actual tools)
            result = await self._execute_action(step.action, parameters)
            
            # Validate result
            validation_result = self._validate_step_result(result, step.expected_result)
            
            step_duration = time.time() - step_start_time
            
            return {
                "step_id": step.step_id,
                "name": step.name,
                "status": "PASSED" if validation_result["valid"] else "FAILED",
                "start_time": datetime.fromtimestamp(step_start_time).isoformat(),
                "end_time": datetime.fromtimestamp(step_start_time + step_duration).isoformat(),
                "duration_seconds": step_duration,
                "score": validation_result.get("score", 100.0 if validation_result["valid"] else 0.0),
                "validation_results": validation_result,
                "result": result
            }
            
        except Exception as e:
            step_duration = time.time() - step_start_time
            logger.error(f"Step execution failed: {e}")
            
            return {
                "step_id": step.step_id,
                "name": step.name,
                "status": "ERROR",
                "start_time": datetime.fromtimestamp(step_start_time).isoformat(),
                "end_time": datetime.fromtimestamp(step_start_time + step_duration).isoformat(),
                "duration_seconds": step_duration,
                "score": 0.0,
                "error_message": str(e),
                "validation_results": {"valid": False, "score": 0.0, "issues": [str(e)]}
            }
    
    async def _execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a scenario step action"""
        
        # This is a simplified implementation
        # In a real implementation, this would call actual MCP tools or workflows
        
        if action == "create_user":
            return {
                "status": "success",
                "user_id": f"user_{uuid.uuid4().hex[:8]}",
                "email": parameters.get("email", "test@example.com"),
                "created_at": datetime.now().isoformat()
            }
        elif action == "authenticate_user":
            return {
                "status": "success",
                "token": f"token_{uuid.uuid4().hex[:8]}",
                "expires_at": datetime.now().isoformat()
            }
        elif action == "create_project":
            return {
                "status": "success",
                "project_id": f"project_{uuid.uuid4().hex[:8]}",
                "name": parameters.get("name", "Test Project"),
                "created_at": datetime.now().isoformat()
            }
        elif action == "bmad_workflow_execute":
            return {
                "status": "success",
                "workflow_id": parameters.get("workflow_id", "test_workflow"),
                "execution_id": f"workflow_exec_{uuid.uuid4().hex[:8]}",
                "result": "Workflow completed successfully"
            }
        else:
            # Generic action
            return {
                "status": "success",
                "action": action,
                "parameters": parameters,
                "result": f"Action {action} executed successfully"
            }
    
    def _validate_step_result(
        self,
        actual_result: Dict[str, Any],
        expected_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate step result against expected outcome"""
        
        issues = []
        score = 100.0
        
        # Check required fields
        for field, expected_value in expected_result.items():
            if field not in actual_result:
                issues.append(f"Missing field: {field}")
                score -= 20.0
            elif actual_result[field] != expected_value:
                issues.append(f"Field {field} mismatch: expected {expected_value}, got {actual_result[field]}")
                score -= 10.0
        
        # Check status
        if actual_result.get("status") != "success":
            issues.append(f"Action failed with status: {actual_result.get('status')}")
            score = 0.0
        
        return {
            "valid": len(issues) == 0,
            "score": max(0.0, score),
            "issues": issues,
            "recommendations": []
        }
    
    async def _execute_cleanup_steps(
        self,
        cleanup_steps: List[ScenarioStep],
        context: Dict[str, Any]
    ) -> None:
        """Execute cleanup steps"""
        
        for cleanup_step in cleanup_steps:
            try:
                await self._execute_action(cleanup_step.action, {**context, **cleanup_step.parameters})
                logger.info(f"Cleanup step executed: {cleanup_step.name}")
            except Exception as e:
                logger.warning(f"Cleanup step failed: {cleanup_step.name} - {e}")
    
    def list_scenarios(
        self,
        category: Optional[str] = None,
        priority: Optional[ScenarioPriority] = None,
        tags: Optional[List[str]] = None
    ) -> List[TestScenario]:
        """List scenarios with optional filtering"""
        
        scenarios = list(self.scenarios.values())
        
        if category:
            scenarios = [s for s in scenarios if s.category == category]
        
        if priority:
            scenarios = [s for s in scenarios if s.priority == priority]
        
        if tags:
            scenarios = [s for s in scenarios if any(tag in s.tags for tag in tags)]
        
        return scenarios
    
    def get_execution_history(
        self,
        scenario_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ScenarioResult]:
        """Get execution history with optional filtering"""
        
        history = self.execution_history.copy()
        
        if scenario_id:
            history = [r for r in history if r.scenario_id == scenario_id]
        
        # Sort by start time (newest first)
        history.sort(key=lambda x: x.start_time, reverse=True)
        
        return history[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scenario testing statistics"""
        
        total_executions = len(self.execution_history)
        if total_executions == 0:
            return {
                "total_scenarios": len(self.scenarios),
                "total_executions": 0,
                "success_rate": 0.0,
                "average_score": 0.0,
                "average_duration": 0.0
            }
        
        successful_executions = len([r for r in self.execution_history if r.status == ScenarioStatus.PASSED])
        total_score = sum(r.overall_score for r in self.execution_history)
        total_duration = sum(r.duration_seconds for r in self.execution_history)
        
        return {
            "total_scenarios": len(self.scenarios),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": (successful_executions / total_executions) * 100.0,
            "average_score": total_score / total_executions,
            "average_duration": total_duration / total_executions,
            "scenarios_by_priority": {
                priority.value: len([s for s in self.scenarios.values() if s.priority == priority])
                for priority in ScenarioPriority
            }
        }


# Global instance
_scenario_engine: Optional[ScenarioTestingEngine] = None


def get_scenario_engine() -> ScenarioTestingEngine:
    """Get the global scenario testing engine instance"""
    global _scenario_engine
    if _scenario_engine is None:
        _scenario_engine = ScenarioTestingEngine()
    return _scenario_engine
