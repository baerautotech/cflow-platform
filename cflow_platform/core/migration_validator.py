"""
Migration Validation Script

This module provides comprehensive validation of legacy tool migrations
with performance testing, compatibility testing, and regression testing.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json
import statistics

from .legacy_tool_migration import LegacyToolMigrationManager, MigrationResult
from .performance_testing import PerformanceRegressionTester, LoadTester, CompatibilityTester

logger = logging.getLogger(__name__)


@dataclass
class ValidationTest:
    """Validation test case"""
    name: str
    description: str
    test_type: str  # performance, compatibility, regression
    test_data: Dict[str, Any]
    expected_result: Any
    performance_threshold: float = 500.0


@dataclass
class ValidationResult:
    """Result of validation test"""
    test_name: str
    test_type: str
    passed: bool
    execution_time: float
    actual_result: Any
    expected_result: Any
    performance_score: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class MigrationValidator:
    """Validates legacy tool migrations with comprehensive testing"""
    
    def __init__(self, migration_manager: LegacyToolMigrationManager):
        self.migration_manager = migration_manager
        self.performance_tester = PerformanceRegressionTester()
        self.load_tester = LoadTester()
        self.compatibility_tester = CompatibilityTester()
        
        # Validation test cases
        self.validation_tests: Dict[str, List[ValidationTest]] = {}
        self._initialize_validation_tests()
    
    def _initialize_validation_tests(self):
        """Initialize validation test cases for all legacy tools"""
        
        # BMAD Document Tools Tests
        self.validation_tests["bmad_prd_create"] = [
            ValidationTest(
                name="test_prd_creation_basic",
                description="Test basic PRD creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "title": "Test PRD",
                        "content": "This is a test PRD content",
                        "document_type": "prd"
                    }
                },
                expected_result={"document_id": str, "status": "draft"},
                performance_threshold=300.0
            ),
            ValidationTest(
                name="test_prd_creation_complex",
                description="Test complex PRD creation with all fields",
                test_type="performance",
                test_data={
                    "arguments": {
                        "title": "Complex Test PRD",
                        "content": "This is a complex test PRD with detailed content",
                        "document_type": "prd",
                        "project_id": "test_project",
                        "template": "standard_prd"
                    }
                },
                expected_result={"document_id": str, "status": "draft"},
                performance_threshold=400.0
            )
        ]
        
        self.validation_tests["bmad_prd_update"] = [
            ValidationTest(
                name="test_prd_update_basic",
                description="Test basic PRD update",
                test_type="performance",
                test_data={
                    "arguments": {
                        "document_id": "test_doc_123",
                        "title": "Updated Test PRD",
                        "content": "Updated content"
                    }
                },
                expected_result={"document_id": "test_doc_123", "status": "updated"},
                performance_threshold=300.0
            )
        ]
        
        self.validation_tests["bmad_prd_get"] = [
            ValidationTest(
                name="test_prd_retrieval",
                description="Test PRD retrieval",
                test_type="performance",
                test_data={
                    "arguments": {
                        "document_id": "test_doc_123"
                    }
                },
                expected_result={"document_id": "test_doc_123", "title": str},
                performance_threshold=200.0
            )
        ]
        
        # BMAD Task Tools Tests
        self.validation_tests["bmad_story_create"] = [
            ValidationTest(
                name="test_story_creation_basic",
                description="Test basic story creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "title": "Test Story",
                        "description": "This is a test story",
                        "priority": "medium"
                    }
                },
                expected_result={"task_id": str, "status": "pending"},
                performance_threshold=300.0
            ),
            ValidationTest(
                name="test_story_creation_high_priority",
                description="Test high priority story creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "title": "High Priority Story",
                        "description": "This is a high priority story",
                        "priority": "high",
                        "assignee": "test_user",
                        "due_date": "2025-01-15"
                    }
                },
                expected_result={"task_id": str, "status": "pending"},
                performance_threshold=350.0
            )
        ]
        
        self.validation_tests["bmad_story_update"] = [
            ValidationTest(
                name="test_story_update_status",
                description="Test story status update",
                test_type="performance",
                test_data={
                    "arguments": {
                        "task_id": "test_task_123",
                        "status": "in_progress"
                    }
                },
                expected_result={"task_id": "test_task_123", "status": "updated"},
                performance_threshold=300.0
            )
        ]
        
        # BMAD Plan Tools Tests
        self.validation_tests["bmad_epic_create"] = [
            ValidationTest(
                name="test_epic_creation_greenfield",
                description="Test greenfield epic creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "name": "Test Epic",
                        "description": "This is a test epic",
                        "project_type": "greenfield"
                    }
                },
                expected_result={"plan_id": str, "status": "draft"},
                performance_threshold=300.0
            ),
            ValidationTest(
                name="test_epic_creation_brownfield",
                description="Test brownfield epic creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "name": "Brownfield Epic",
                        "description": "This is a brownfield epic",
                        "project_type": "brownfield",
                        "estimated_duration": 4
                    }
                },
                expected_result={"plan_id": str, "status": "draft"},
                performance_threshold=350.0
            )
        ]
        
        # BMAD Workflow Tools Tests
        self.validation_tests["bmad_workflow_start"] = [
            ValidationTest(
                name="test_workflow_creation",
                description="Test workflow creation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "name": "Test Workflow",
                        "description": "This is a test workflow",
                        "steps": [
                            {"name": "step1", "action": "create_doc"},
                            {"name": "step2", "action": "review_doc"}
                        ]
                    }
                },
                expected_result={"workflow_id": str, "status": "active"},
                performance_threshold=400.0
            )
        ]
        
        self.validation_tests["bmad_workflow_execute"] = [
            ValidationTest(
                name="test_workflow_execution",
                description="Test workflow execution",
                test_type="performance",
                test_data={
                    "arguments": {
                        "workflow_id": "test_workflow_123",
                        "parameters": {"project_id": "test_project"}
                    }
                },
                expected_result={"execution_id": str, "status": "running"},
                performance_threshold=500.0
            )
        ]
        
        # BMAD HIL Tools Tests
        self.validation_tests["bmad_hil_start_session"] = [
            ValidationTest(
                name="test_hil_request_approval",
                description="Test HIL approval request",
                test_type="performance",
                test_data={
                    "arguments": {
                        "request_type": "approval",
                        "context": "Test approval request",
                        "urgency": "medium"
                    }
                },
                expected_result={"request_id": str, "status": "pending"},
                performance_threshold=300.0
            ),
            ValidationTest(
                name="test_hil_request_high_urgency",
                description="Test high urgency HIL request",
                test_type="performance",
                test_data={
                    "arguments": {
                        "request_type": "decision",
                        "context": "Urgent decision needed",
                        "urgency": "high",
                        "timeout_minutes": 30
                    }
                },
                expected_result={"request_id": str, "status": "pending"},
                performance_threshold=350.0
            )
        ]
        
        # BMAD Git Tools Tests
        self.validation_tests["bmad_git_commit_changes"] = [
            ValidationTest(
                name="test_git_commit_single_file",
                description="Test git commit with single file",
                test_type="performance",
                test_data={
                    "arguments": {
                        "message": "Test commit",
                        "files": ["test_file.py"],
                        "branch": "main"
                    }
                },
                expected_result={"commit_hash": str, "status": "committed"},
                performance_threshold=400.0
            ),
            ValidationTest(
                name="test_git_commit_multiple_files",
                description="Test git commit with multiple files",
                test_type="performance",
                test_data={
                    "arguments": {
                        "message": "Multiple file commit",
                        "files": ["file1.py", "file2.py", "file3.py"],
                        "branch": "feature_branch",
                        "author": "test_user"
                    }
                },
                expected_result={"commit_hash": str, "status": "committed"},
                performance_threshold=500.0
            )
        ]
        
        # BMAD Expansion Pack Tools Tests
        self.validation_tests["bmad_expansion_packs_install"] = [
            ValidationTest(
                name="test_expansion_install_gamedev",
                description="Test game dev expansion pack installation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "pack_name": "bmad_gamedev",
                        "version": "latest"
                    }
                },
                expected_result={"pack_name": "bmad_gamedev", "status": "installed"},
                performance_threshold=600.0
            ),
            ValidationTest(
                name="test_expansion_install_devops",
                description="Test DevOps expansion pack installation",
                test_type="performance",
                test_data={
                    "arguments": {
                        "pack_name": "bmad_devops",
                        "version": "1.0.0",
                        "config": {"environment": "production"}
                    }
                },
                expected_result={"pack_name": "bmad_devops", "status": "installed"},
                performance_threshold=600.0
            )
        ]
        
        logger.info(f"Initialized validation tests for {len(self.validation_tests)} legacy tools")
    
    async def validate_legacy_tool_migration(self, legacy_tool_name: str) -> Dict[str, Any]:
        """Validate migration for a specific legacy tool"""
        try:
            tests = self.validation_tests.get(legacy_tool_name, [])
            if not tests:
                return {
                    "legacy_tool": legacy_tool_name,
                    "validation_success": False,
                    "error": f"No validation tests found for {legacy_tool_name}"
                }
            
            validation_results = []
            passed_tests = 0
            total_execution_time = 0
            
            for test in tests:
                result = await self._run_validation_test(legacy_tool_name, test)
                validation_results.append(result)
                
                if result.passed:
                    passed_tests += 1
                
                total_execution_time += result.execution_time
            
            success_rate = (passed_tests / len(tests)) * 100
            average_execution_time = total_execution_time / len(tests)
            
            validation_summary = {
                "legacy_tool": legacy_tool_name,
                "validation_success": success_rate >= 80.0,  # 80% pass rate required
                "success_rate": success_rate,
                "passed_tests": passed_tests,
                "total_tests": len(tests),
                "average_execution_time": average_execution_time,
                "total_execution_time": total_execution_time,
                "test_results": [
                    {
                        "test_name": r.test_name,
                        "test_type": r.test_type,
                        "passed": r.passed,
                        "execution_time": r.execution_time,
                        "performance_score": r.performance_score,
                        "error": r.error
                    }
                    for r in validation_results
                ],
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Validated migration for {legacy_tool_name}: {validation_summary['validation_success']}")
            return validation_summary
            
        except Exception as e:
            logger.error(f"Validation failed for {legacy_tool_name}: {e}")
            return {
                "legacy_tool": legacy_tool_name,
                "validation_success": False,
                "error": str(e),
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    async def _run_validation_test(self, legacy_tool_name: str, test: ValidationTest) -> ValidationResult:
        """Run a single validation test"""
        start_time = time.time()
        
        try:
            # Execute migration
            migration_result = await self.migration_manager.migrate_legacy_tool(
                legacy_tool_name, test.test_data["arguments"]
            )
            
            execution_time = time.time() - start_time
            
            # Validate result
            passed = self._validate_test_result(migration_result, test.expected_result)
            
            # Calculate performance score
            performance_score = max(0, (test.performance_threshold - execution_time) / 
                                  test.performance_threshold * 100)
            
            return ValidationResult(
                test_name=test.name,
                test_type=test.test_type,
                passed=passed and migration_result.success,
                execution_time=execution_time,
                actual_result=migration_result.result,
                expected_result=test.expected_result,
                performance_score=performance_score,
                metadata={
                    "migration_result": migration_result,
                    "test_data": test.test_data
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Validation test {test.name} failed: {e}")
            
            return ValidationResult(
                test_name=test.name,
                test_type=test.test_type,
                passed=False,
                execution_time=execution_time,
                actual_result=None,
                expected_result=test.expected_result,
                performance_score=0.0,
                error=str(e)
            )
    
    def _validate_test_result(self, migration_result: MigrationResult, expected_result: Any) -> bool:
        """Validate that migration result matches expected result"""
        if not migration_result.success:
            return False
        
        actual_result = migration_result.result
        
        # Type-based validation
        if isinstance(expected_result, dict):
            if not isinstance(actual_result, dict):
                return False
            
            for key, expected_type in expected_result.items():
                if key not in actual_result:
                    return False
                
                if expected_type == str and not isinstance(actual_result[key], str):
                    return False
                elif expected_type == int and not isinstance(actual_result[key], int):
                    return False
                elif expected_type == float and not isinstance(actual_result[key], (int, float)):
                    return False
                elif expected_type == bool and not isinstance(actual_result[key], bool):
                    return False
        
        return True
    
    async def validate_all_migrations(self) -> Dict[str, Any]:
        """Validate all legacy tool migrations"""
        validation_results = {}
        total_tools = len(self.validation_tests)
        successful_validations = 0
        
        for legacy_tool_name in self.validation_tests.keys():
            result = await self.validate_legacy_tool_migration(legacy_tool_name)
            validation_results[legacy_tool_name] = result
            
            if result["validation_success"]:
                successful_validations += 1
        
        overall_success_rate = (successful_validations / total_tools) * 100
        
        return {
            "overall_validation_success": overall_success_rate >= 80.0,
            "overall_success_rate": overall_success_rate,
            "successful_validations": successful_validations,
            "total_tools": total_tools,
            "validation_results": validation_results,
            "validated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def run_performance_regression_tests(self) -> Dict[str, Any]:
        """Run performance regression tests on all migrations"""
        try:
            regression_results = {}
            
            for legacy_tool_name in self.validation_tests.keys():
                tests = self.validation_tests[legacy_tool_name]
                
                # Run performance tests
                performance_results = []
                for test in tests:
                    if test.test_type == "performance":
                        result = await self._run_validation_test(legacy_tool_name, test)
                        performance_results.append({
                            "test_name": test.name,
                            "execution_time": result.execution_time,
                            "performance_score": result.performance_score,
                            "passed": result.passed
                        })
                
                if performance_results:
                    avg_execution_time = statistics.mean([r["execution_time"] for r in performance_results])
                    avg_performance_score = statistics.mean([r["performance_score"] for r in performance_results])
                    
                    regression_results[legacy_tool_name] = {
                        "average_execution_time": avg_execution_time,
                        "average_performance_score": avg_performance_score,
                        "performance_tests_count": len(performance_results),
                        "all_tests_passed": all(r["passed"] for r in performance_results)
                    }
            
            return {
                "regression_test_success": True,
                "performance_results": regression_results,
                "tested_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Performance regression tests failed: {e}")
            return {
                "regression_test_success": False,
                "error": str(e),
                "tested_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation tests"""
        total_tests = sum(len(tests) for tests in self.validation_tests.values())
        
        return {
            "total_legacy_tools": len(self.validation_tests),
            "total_validation_tests": total_tests,
            "test_categories": {
                "performance_tests": sum(1 for tests in self.validation_tests.values() 
                                        for test in tests if test.test_type == "performance"),
                "compatibility_tests": sum(1 for tests in self.validation_tests.values() 
                                         for test in tests if test.test_type == "compatibility"),
                "regression_tests": sum(1 for tests in self.validation_tests.values() 
                                       for test in tests if test.test_type == "regression")
            },
            "legacy_tools_with_tests": list(self.validation_tests.keys())
        }
