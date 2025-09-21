"""
BMAD Workflow Testing Engine
Phase 4.1.1: Implement complete workflow testing

This module provides comprehensive workflow testing capabilities that test
workflows from PRD to deployment, ensuring end-to-end functionality.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Test execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

class WorkflowPhase(Enum):
    """Workflow phases for testing"""
    PRD_CREATION = "PRD_CREATION"
    ARCHITECTURE_DESIGN = "ARCHITECTURE_DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    MONITORING = "MONITORING"

@dataclass
class WorkflowTestStep:
    """Individual test step in a workflow test"""
    step_id: str
    step_name: str
    phase: WorkflowPhase
    description: str
    expected_output: Dict[str, Any]
    validation_criteria: Dict[str, Any]
    dependencies: List[str]
    timeout_seconds: int = 300
    retry_count: int = 3
    critical: bool = True

@dataclass
class WorkflowTestResult:
    """Result of a workflow test execution"""
    test_id: str
    step_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    validation_results: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowTestSuite:
    """Complete workflow test suite"""
    suite_id: str
    suite_name: str
    description: str
    workflow_phases: List[WorkflowPhase]
    test_steps: List[WorkflowTestStep]
    created_at: datetime
    updated_at: datetime

@dataclass
class WorkflowTestExecution:
    """Complete workflow test execution"""
    execution_id: str
    suite_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    step_results: List[WorkflowTestResult] = None
    overall_score: Optional[float] = None
    error_summary: Optional[str] = None

class WorkflowTestValidator:
    """Validates workflow test outputs against expected criteria"""
    
    def __init__(self):
        self.validation_rules = {
            "prd_creation": self._validate_prd_creation,
            "architecture_design": self._validate_architecture_design,
            "development": self._validate_development,
            "testing": self._validate_testing,
            "deployment": self._validate_deployment,
            "monitoring": self._validate_monitoring
        }
    
    async def validate_step_output(self, step: WorkflowTestStep, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step output against criteria"""
        validation_results = {
            "valid": True,
            "score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Get validation function for this phase
            validator_func = self.validation_rules.get(step.phase.value.lower())
            if validator_func:
                validation_results = await validator_func(output, step.validation_criteria)
            else:
                validation_results["valid"] = False
                validation_results["issues"].append(f"No validator found for phase: {step.phase.value}")
                
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            logger.error(f"Validation error for step {step.step_id}: {e}")
        
        return validation_results
    
    async def _validate_prd_creation(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PRD creation phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check required PRD sections
        required_sections = criteria.get("required_sections", [
            "problem_definition", "solution_overview", "user_stories", "acceptance_criteria"
        ])
        
        prd_content = output.get("prd_content", {})
        for section in required_sections:
            if section not in prd_content:
                results["issues"].append(f"Missing required section: {section}")
                results["valid"] = False
            else:
                results["score"] += 1.0
        
        # Check PRD quality metrics
        if prd_content.get("word_count", 0) < criteria.get("min_word_count", 500):
            results["issues"].append("PRD too short - insufficient detail")
            results["valid"] = False
        
        results["score"] = results["score"] / len(required_sections) * 100
        return results
    
    async def _validate_architecture_design(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate architecture design phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check architecture components
        architecture = output.get("architecture", {})
        required_components = criteria.get("required_components", [
            "database_schema", "api_endpoints", "security_model", "deployment_plan"
        ])
        
        for component in required_components:
            if component not in architecture:
                results["issues"].append(f"Missing architecture component: {component}")
                results["valid"] = False
            else:
                results["score"] += 1.0
        
        # Check architecture quality
        if architecture.get("complexity_score", 0) > criteria.get("max_complexity", 8):
            results["issues"].append("Architecture too complex")
            results["recommendations"].append("Consider simplifying architecture")
        
        results["score"] = results["score"] / len(required_components) * 100
        return results
    
    async def _validate_development(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate development phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check code quality metrics
        code_metrics = output.get("code_metrics", {})
        min_coverage = criteria.get("min_test_coverage", 80)
        max_complexity = criteria.get("max_cyclomatic_complexity", 10)
        
        if code_metrics.get("test_coverage", 0) < min_coverage:
            results["issues"].append(f"Test coverage below {min_coverage}%")
            results["valid"] = False
        
        if code_metrics.get("cyclomatic_complexity", 0) > max_complexity:
            results["issues"].append(f"Cyclomatic complexity above {max_complexity}")
            results["recommendations"].append("Refactor complex functions")
        
        # Check for linting errors
        linting_errors = output.get("linting_errors", [])
        if linting_errors:
            results["issues"].append(f"Found {len(linting_errors)} linting errors")
            results["valid"] = False
        
        results["score"] = 100 - len(results["issues"]) * 10
        return results
    
    async def _validate_testing(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate testing phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check test results
        test_results = output.get("test_results", {})
        required_tests = criteria.get("required_tests", [
            "unit_tests", "integration_tests", "e2e_tests"
        ])
        
        for test_type in required_tests:
            if test_type not in test_results:
                results["issues"].append(f"Missing {test_type}")
                results["valid"] = False
            elif test_results[test_type].get("pass_rate", 0) < criteria.get("min_pass_rate", 95):
                results["issues"].append(f"{test_type} pass rate below threshold")
                results["valid"] = False
            else:
                results["score"] += 1.0
        
        results["score"] = results["score"] / len(required_tests) * 100
        return results
    
    async def _validate_deployment(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check deployment status
        deployment_status = output.get("deployment_status", {})
        if deployment_status.get("status") != "SUCCESS":
            results["issues"].append(f"Deployment failed: {deployment_status.get('error', 'Unknown error')}")
            results["valid"] = False
        
        # Check health endpoints
        health_checks = output.get("health_checks", [])
        failed_checks = [check for check in health_checks if not check.get("healthy", False)]
        if failed_checks:
            results["issues"].append(f"{len(failed_checks)} health checks failed")
            results["valid"] = False
        
        # Check performance metrics
        performance = output.get("performance_metrics", {})
        if performance.get("response_time", 0) > criteria.get("max_response_time", 2000):
            results["issues"].append("Response time exceeds threshold")
            results["recommendations"].append("Optimize performance")
        
        results["score"] = 100 if results["valid"] else 0
        return results
    
    async def _validate_monitoring(self, output: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate monitoring phase"""
        results = {"valid": True, "score": 0.0, "issues": [], "recommendations": []}
        
        # Check monitoring setup
        monitoring_config = output.get("monitoring_config", {})
        required_monitors = criteria.get("required_monitors", [
            "system_metrics", "application_metrics", "error_tracking", "alerting"
        ])
        
        for monitor in required_monitors:
            if monitor not in monitoring_config:
                results["issues"].append(f"Missing monitoring: {monitor}")
                results["valid"] = False
            else:
                results["score"] += 1.0
        
        # Check alerting configuration
        alerting_config = monitoring_config.get("alerting", {})
        if not alerting_config.get("enabled", False):
            results["issues"].append("Alerting not enabled")
            results["recommendations"].append("Enable alerting for production")
        
        results["score"] = results["score"] / len(required_monitors) * 100
        return results

class WorkflowTestExecutor:
    """Executes workflow tests with proper sequencing and validation"""
    
    def __init__(self):
        self.validator = WorkflowTestValidator()
        self.active_executions: Dict[str, WorkflowTestExecution] = {}
    
    async def execute_test_suite(self, suite: WorkflowTestSuite) -> WorkflowTestExecution:
        """Execute a complete workflow test suite"""
        execution_id = str(uuid.uuid4())
        execution = WorkflowTestExecution(
            execution_id=execution_id,
            suite_id=suite.suite_id,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            step_results=[]
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            logger.info(f"Starting workflow test execution: {execution_id}")
            
            # Execute test steps in dependency order
            executed_steps = set()
            step_results = []
            
            while len(executed_steps) < len(suite.test_steps):
                # Find steps that can be executed (dependencies satisfied)
                ready_steps = self._get_ready_steps(suite.test_steps, executed_steps)
                
                if not ready_steps:
                    # Circular dependency or missing step
                    execution.status = TestStatus.ERROR
                    execution.error_summary = "Circular dependency or missing step detected"
                    break
                
                # Execute ready steps in parallel
                step_tasks = [self._execute_test_step(step, execution_id) for step in ready_steps]
                batch_results = await asyncio.gather(*step_tasks, return_exceptions=True)
                
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Step execution error: {result}")
                        step_results.append(WorkflowTestResult(
                            test_id=execution_id,
                            step_id=ready_steps[i].step_id,
                            status=TestStatus.ERROR,
                            start_time=datetime.utcnow(),
                            error_message=str(result)
                        ))
                    else:
                        step_results.append(result)
                        executed_steps.add(ready_steps[i].step_id)
                
                # Check if any critical step failed
                failed_critical = any(
                    result.status == TestStatus.FAILED and 
                    any(step.step_id == result.step_id and step.critical for step in suite.test_steps)
                    for result in step_results
                )
                
                if failed_critical:
                    execution.status = TestStatus.FAILED
                    execution.error_summary = "Critical step failed"
                    break
            
            execution.step_results = step_results
            execution.end_time = datetime.utcnow()
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            
            # Calculate overall score
            if execution.status == TestStatus.RUNNING:
                execution.status = TestStatus.PASSED
                execution.overall_score = self._calculate_overall_score(step_results)
            
            # Ensure overall_score is not None
            if execution.overall_score is None:
                execution.overall_score = 0.0
            
            logger.info(f"Workflow test execution completed: {execution_id}, Status: {execution.status}")
            
        except Exception as e:
            logger.error(f"Workflow test execution error: {e}")
            execution.status = TestStatus.ERROR
            execution.error_summary = str(e)
            execution.end_time = datetime.utcnow()
        
        finally:
            self.active_executions.pop(execution_id, None)
        
        return execution
    
    def _get_ready_steps(self, steps: List[WorkflowTestStep], executed_steps: set) -> List[WorkflowTestStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []
        
        for step in steps:
            if step.step_id in executed_steps:
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(dep in executed_steps for dep in step.dependencies)
            
            if dependencies_satisfied:
                ready_steps.append(step)
        
        return ready_steps
    
    async def _execute_test_step(self, step: WorkflowTestStep, execution_id: str) -> WorkflowTestResult:
        """Execute a single test step"""
        result = WorkflowTestResult(
            test_id=execution_id,
            step_id=step.step_id,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            logger.info(f"Executing test step: {step.step_name}")
            
            # Execute the step (this would integrate with actual workflow execution)
            output = await self._run_workflow_step(step)
            
            # Validate the output
            validation_results = await self.validator.validate_step_output(step, output)
            
            result.validation_results = validation_results
            result.output = output
            
            if validation_results["valid"]:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                result.error_message = "; ".join(validation_results["issues"])
            
        except asyncio.TimeoutError:
            result.status = TestStatus.FAILED
            result.error_message = f"Step timed out after {step.timeout_seconds} seconds"
            logger.error(f"Test step timeout: {step.step_name}")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            logger.error(f"Test step error: {step.step_name}, Error: {e}")
        
        finally:
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _run_workflow_step(self, step: WorkflowTestStep) -> Dict[str, Any]:
        """Run the actual workflow step (placeholder for integration)"""
        # This would integrate with the actual BMAD workflow execution
        # For now, return mock data based on the step phase
        
        mock_outputs = {
            WorkflowPhase.PRD_CREATION: {
                "prd_content": {
                    "problem_definition": "Mock problem definition",
                    "solution_overview": "Mock solution overview",
                    "user_stories": ["Mock user story 1", "Mock user story 2"],
                    "acceptance_criteria": ["Mock criteria 1", "Mock criteria 2"],
                    "word_count": 750
                }
            },
            WorkflowPhase.ARCHITECTURE_DESIGN: {
                "architecture": {
                    "database_schema": "Mock schema",
                    "api_endpoints": "Mock endpoints",
                    "security_model": "Mock security",
                    "deployment_plan": "Mock deployment",
                    "complexity_score": 6
                }
            },
            WorkflowPhase.DEVELOPMENT: {
                "code_metrics": {
                    "test_coverage": 85,
                    "cyclomatic_complexity": 8,
                    "lines_of_code": 1500
                },
                "linting_errors": []
            },
            WorkflowPhase.TESTING: {
                "test_results": {
                    "unit_tests": {"pass_rate": 98, "total_tests": 150},
                    "integration_tests": {"pass_rate": 95, "total_tests": 50},
                    "e2e_tests": {"pass_rate": 92, "total_tests": 25}
                }
            },
            WorkflowPhase.DEPLOYMENT: {
                "deployment_status": {"status": "SUCCESS"},
                "health_checks": [
                    {"name": "API Health", "healthy": True},
                    {"name": "Database Health", "healthy": True}
                ],
                "performance_metrics": {"response_time": 1500}
            },
            WorkflowPhase.MONITORING: {
                "monitoring_config": {
                    "system_metrics": {"enabled": True},
                    "application_metrics": {"enabled": True},
                    "error_tracking": {"enabled": True},
                    "alerting": {"enabled": True}
                }
            }
        }
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        return mock_outputs.get(step.phase, {})
    
    def _calculate_overall_score(self, step_results: List[WorkflowTestResult]) -> float:
        """Calculate overall test score"""
        if not step_results:
            return 0.0
        
        total_score = 0.0
        valid_results = 0
        
        for result in step_results:
            if result.validation_results and "score" in result.validation_results:
                total_score += result.validation_results["score"]
                valid_results += 1
        
        return total_score / valid_results if valid_results > 0 else 0.0

class WorkflowTestSuiteBuilder:
    """Builder for creating workflow test suites"""
    
    def __init__(self):
        self.test_suites: Dict[str, WorkflowTestSuite] = {}
    
    def create_default_suite(self) -> WorkflowTestSuite:
        """Create a default workflow test suite covering all phases"""
        suite_id = str(uuid.uuid4())
        
        test_steps = [
            WorkflowTestStep(
                step_id="prd_creation",
                step_name="PRD Creation",
                phase=WorkflowPhase.PRD_CREATION,
                description="Create Product Requirements Document",
                expected_output={"prd_content": "object"},
                validation_criteria={
                    "required_sections": ["problem_definition", "solution_overview", "user_stories", "acceptance_criteria"],
                    "min_word_count": 500
                },
                dependencies=[],
                timeout_seconds=600
            ),
            WorkflowTestStep(
                step_id="architecture_design",
                step_name="Architecture Design",
                phase=WorkflowPhase.ARCHITECTURE_DESIGN,
                description="Design system architecture",
                expected_output={"architecture": "object"},
                validation_criteria={
                    "required_components": ["database_schema", "api_endpoints", "security_model", "deployment_plan"],
                    "max_complexity": 8
                },
                dependencies=["prd_creation"],
                timeout_seconds=900
            ),
            WorkflowTestStep(
                step_id="development",
                step_name="Development",
                phase=WorkflowPhase.DEVELOPMENT,
                description="Implement the solution",
                expected_output={"code_metrics": "object"},
                validation_criteria={
                    "min_test_coverage": 80,
                    "max_cyclomatic_complexity": 10
                },
                dependencies=["architecture_design"],
                timeout_seconds=1800
            ),
            WorkflowTestStep(
                step_id="testing",
                step_name="Testing",
                phase=WorkflowPhase.TESTING,
                description="Execute comprehensive testing",
                expected_output={"test_results": "object"},
                validation_criteria={
                    "required_tests": ["unit_tests", "integration_tests", "e2e_tests"],
                    "min_pass_rate": 95
                },
                dependencies=["development"],
                timeout_seconds=1200
            ),
            WorkflowTestStep(
                step_id="deployment",
                step_name="Deployment",
                phase=WorkflowPhase.DEPLOYMENT,
                description="Deploy to production",
                expected_output={"deployment_status": "object"},
                validation_criteria={
                    "max_response_time": 2000
                },
                dependencies=["testing"],
                timeout_seconds=600
            ),
            WorkflowTestStep(
                step_id="monitoring",
                step_name="Monitoring",
                phase=WorkflowPhase.MONITORING,
                description="Set up monitoring and alerting",
                expected_output={"monitoring_config": "object"},
                validation_criteria={
                    "required_monitors": ["system_metrics", "application_metrics", "error_tracking", "alerting"]
                },
                dependencies=["deployment"],
                timeout_seconds=300
            )
        ]
        
        suite = WorkflowTestSuite(
            suite_id=suite_id,
            suite_name="Complete Workflow Test Suite",
            description="Comprehensive workflow testing from PRD to deployment",
            workflow_phases=list(WorkflowPhase),
            test_steps=test_steps,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.test_suites[suite_id] = suite
        return suite
    
    def create_custom_suite(self, name: str, description: str, phases: List[WorkflowPhase], 
                          custom_steps: List[WorkflowTestStep]) -> WorkflowTestSuite:
        """Create a custom workflow test suite"""
        suite_id = str(uuid.uuid4())
        
        suite = WorkflowTestSuite(
            suite_id=suite_id,
            suite_name=name,
            description=description,
            workflow_phases=phases,
            test_steps=custom_steps,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.test_suites[suite_id] = suite
        return suite
    
    def get_suite(self, suite_id: str) -> Optional[WorkflowTestSuite]:
        """Get a test suite by ID"""
        return self.test_suites.get(suite_id)
    
    def list_suites(self) -> List[WorkflowTestSuite]:
        """List all test suites"""
        return list(self.test_suites.values())

class WorkflowTestingEngine:
    """Main workflow testing engine that orchestrates all testing activities"""
    
    def __init__(self):
        self.suite_builder = WorkflowTestSuiteBuilder()
        self.test_executor = WorkflowTestExecutor()
        self.test_history: List[WorkflowTestExecution] = []
    
    async def run_complete_workflow_test(self) -> WorkflowTestExecution:
        """Run a complete workflow test from PRD to deployment"""
        logger.info("Starting complete workflow test")
        
        # Create default test suite
        suite = self.suite_builder.create_default_suite()
        
        # Execute the test suite
        execution = await self.test_executor.execute_test_suite(suite)
        
        # Store in history
        self.test_history.append(execution)
        
        logger.info(f"Complete workflow test completed with status: {execution.status}")
        return execution
    
    async def run_custom_workflow_test(self, suite_id: str) -> WorkflowTestExecution:
        """Run a custom workflow test suite"""
        suite = self.suite_builder.get_suite(suite_id)
        if not suite:
            raise ValueError(f"Test suite not found: {suite_id}")
        
        execution = await self.test_executor.execute_test_suite(suite)
        self.test_history.append(execution)
        
        return execution
    
    def get_test_history(self, limit: int = 50) -> List[WorkflowTestExecution]:
        """Get test execution history"""
        return self.test_history[-limit:]
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get test execution statistics"""
        if not self.test_history:
            return {"total_tests": 0, "pass_rate": 0, "average_score": 0}
        
        total_tests = len(self.test_history)
        passed_tests = len([t for t in self.test_history if t.status == TestStatus.PASSED])
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        scores = [t.overall_score for t in self.test_history if t.overall_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": len([t for t in self.test_history if t.status == TestStatus.FAILED]),
            "error_tests": len([t for t in self.test_history if t.status == TestStatus.ERROR]),
            "pass_rate": pass_rate,
            "average_score": average_score
        }

# Global instance for easy access
workflow_testing_engine = WorkflowTestingEngine()
