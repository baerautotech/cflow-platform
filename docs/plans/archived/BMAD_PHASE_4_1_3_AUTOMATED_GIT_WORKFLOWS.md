# BMAD Phase 4.1.3.1: Automated Git Workflow Integration

## Story Overview

**Story ID**: `4.1.3` (Updated)  
**Title**: Implement Regression Testing with Automated Git Workflows  
**Epic**: Phase 4.1.3 - Regression Testing  
**Priority**: P0 (Critical)  
**Story Points**: 8 (5 original + 3 for git workflows)  

## Acceptance Criteria

### AC1: Automated Commit Functionality
- **Given** a testing framework execution completes successfully
- **When** the system detects changes in the repository
- **Then** it should automatically commit changes with descriptive messages
- **And** the commit should include all modified and new files
- **And** the commit message should follow conventional commit format

### AC2: Automated Push Functionality  
- **Given** a successful automated commit has been created
- **When** the system is configured for automated push
- **Then** it should automatically push changes to the remote repository
- **And** it should handle push failures gracefully with retry logic
- **And** it should provide status feedback on push operations

### AC3: Testing Integration
- **Given** the automated git workflow is integrated
- **When** workflow testing, scenario testing, or regression testing completes
- **Then** it should automatically commit and push all changes
- **And** it should include test results in commit messages
- **And** it should maintain proper git history

### AC4: Configuration Management
- **Given** the automated git workflow system
- **When** users need to configure git behavior
- **Then** it should support configurable commit message templates
- **And** it should support enabling/disabling auto-push
- **And** it should support branch management and conflict resolution

### AC5: Error Handling & Recovery
- **Given** the automated git workflow encounters errors
- **When** commit or push operations fail
- **Then** it should provide detailed error messages
- **And** it should support manual intervention when needed
- **And** it should maintain system stability

### AC6: Regression Testing Functionality
- **Given** a regression testing framework
- **When** regression tests are executed
- **Then** it should detect workflow changes that break existing functionality
- **And** it should compare current behavior against baseline
- **And** it should identify specific regressions with detailed reports
- **And** it should automatically commit and push regression test results

### AC7: Baseline Management
- **Given** regression testing capabilities
- **When** establishing test baselines
- **Then** it should capture current system behavior as baseline
- **And** it should store baseline data for comparison
- **And** it should support baseline updates when intentional changes occur

## Technical Implementation

### Core Components

#### 1. Regression Testing Engine
```python
# File: cflow_platform/core/regression_testing_engine.py
class RegressionTestingEngine:
    """Engine for detecting regressions in workflow changes"""
    
    def __init__(self):
        self.baseline_manager = BaselineManager()
        self.comparison_engine = ComparisonEngine()
        self.regression_detector = RegressionDetector()
        self.report_generator = RegressionReportGenerator()
        self.git_workflow_manager = GitWorkflowManager()
    
    async def run_regression_tests(
        self,
        test_suite_id: Optional[str] = None,
        baseline_id: Optional[str] = None
    ) -> RegressionTestResult:
        """Run comprehensive regression tests"""
        
        # Get baseline for comparison
        baseline = await self.baseline_manager.get_baseline(baseline_id)
        
        # Execute current tests
        current_results = await self._execute_current_tests(test_suite_id)
        
        # Compare with baseline
        comparison_result = await self.comparison_engine.compare_results(
            baseline=baseline,
            current=current_results
        )
        
        # Detect regressions
        regressions = await self.regression_detector.detect_regressions(
            comparison_result
        )
        
        # Generate report
        report = await self.report_generator.generate_report(
            regressions=regressions,
            comparison_result=comparison_result
        )
        
        # Create result
        result = RegressionTestResult(
            test_suite_id=test_suite_id,
            baseline_id=baseline_id,
            regressions_found=len(regressions),
            regressions=regressions,
            comparison_result=comparison_result,
            report=report,
            status="PASSED" if len(regressions) == 0 else "REGRESSIONS_DETECTED"
        )
        
        # Auto-commit and push results
        git_result = await self.git_workflow_manager.auto_commit_and_push(
            test_type="regression_testing",
            test_results=result.to_dict()
        )
        
        result.git_workflow_result = git_result
        return result
    
    async def establish_baseline(
        self,
        test_suite_id: str,
        description: str
    ) -> BaselineResult:
        """Establish a new baseline for regression testing"""
        
        # Execute tests to capture baseline
        test_results = await self._execute_current_tests(test_suite_id)
        
        # Create baseline
        baseline = await self.baseline_manager.create_baseline(
            test_suite_id=test_suite_id,
            description=description,
            test_results=test_results
        )
        
        # Auto-commit baseline
        git_result = await self.git_workflow_manager.auto_commit_and_push(
            test_type="baseline_establishment",
            test_results={"baseline_id": baseline.baseline_id, "description": description}
        )
        
        return BaselineResult(
            baseline_id=baseline.baseline_id,
            test_suite_id=test_suite_id,
            description=description,
            test_count=len(test_results),
            git_workflow_result=git_result
        )
```

#### 2. Git Workflow Manager
```python
# File: cflow_platform/core/git_workflow_manager.py
class GitWorkflowManager:
    """Manages automated git operations for testing framework"""
    
    def __init__(self):
        self.git_ops = GitOperations()
        self.config_manager = GitConfigManager()
        self.commit_templates = CommitTemplateManager()
        self.push_handler = PushHandler()
    
    async def auto_commit_and_push(
        self,
        test_type: str,
        test_results: Dict[str, Any],
        include_untracked: bool = True
    ) -> GitWorkflowResult:
        """Automatically commit and push changes after testing"""
        
        # Check for changes
        if not self.git_ops.has_changes():
            return GitWorkflowResult(status="skipped", reason="no_changes")
        
        # Generate commit message
        commit_message = self.commit_templates.generate_message(
            test_type=test_type,
            test_results=test_results
        )
        
        # Commit changes
        commit_result = await self.git_ops.commit_changes(
            message=commit_message,
            include_untracked=include_untracked
        )
        
        if not commit_result.success:
            return GitWorkflowResult(status="error", error=commit_result.error)
        
        # Push changes (if enabled)
        if self.config_manager.auto_push_enabled():
            push_result = await self.push_handler.push_changes()
            return GitWorkflowResult(
                status="success" if push_result.success else "partial",
                commit_hash=commit_result.commit_hash,
                push_result=push_result
            )
        
        return GitWorkflowResult(
            status="success",
            commit_hash=commit_result.commit_hash,
            push_result=None
        )
```

#### 2. Commit Template Manager
```python
# File: cflow_platform/core/commit_template_manager.py
class CommitTemplateManager:
    """Manages commit message templates for different test types"""
    
    def __init__(self):
        self.templates = {
            "workflow_testing": self._workflow_testing_template,
            "scenario_testing": self._scenario_testing_template,
            "regression_testing": self._regression_testing_template,
            "integration_testing": self._integration_testing_template
        }
    
    def generate_message(self, test_type: str, test_results: Dict[str, Any]) -> str:
        """Generate commit message based on test type and results"""
        
        template = self.templates.get(test_type, self._default_template)
        return template(test_results)
    
    def _workflow_testing_template(self, results: Dict[str, Any]) -> str:
        """Template for workflow testing commits"""
        success_count = results.get("successful_tests", 0)
        total_count = results.get("total_tests", 0)
        score = results.get("overall_score", 0.0)
        
        return f"""test(workflow): Complete workflow testing execution

✅ Tests: {success_count}/{total_count} passed
📊 Score: {score:.1f}%
🎯 Status: {'PASSED' if success_count == total_count else 'PARTIAL'}

Automated commit from workflow testing framework."""
    
    def _scenario_testing_template(self, results: Dict[str, Any]) -> str:
        """Template for scenario testing commits"""
        scenarios_executed = results.get("scenarios_executed", 0)
        success_rate = results.get("success_rate", 0.0)
        
        return f"""test(scenario): Execute scenario-based testing

🎭 Scenarios: {scenarios_executed} executed
📈 Success Rate: {success_rate:.1f}%
🏷️ Priority: {results.get('priority_level', 'Mixed')}

Automated commit from scenario testing framework."""
    
    def _regression_testing_template(self, results: Dict[str, Any]) -> str:
        """Template for regression testing commits"""
        regressions_found = results.get("regressions_found", 0)
        tests_run = results.get("tests_run", 0)
        
        return f"""test(regression): Regression testing execution

🔍 Tests Run: {tests_run}
⚠️ Regressions Found: {regressions_found}
✅ Status: {'CLEAN' if regressions_found == 0 else 'REGRESSIONS DETECTED'}

Automated commit from regression testing framework."""
```

#### 3. Push Handler
```python
# File: cflow_platform/core/push_handler.py
class PushHandler:
    """Handles automated git push operations with retry logic"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5.0
        self.conflict_resolver = ConflictResolver()
    
    async def push_changes(self) -> PushResult:
        """Push changes to remote repository with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                result = await self._attempt_push()
                
                if result.success:
                    return result
                
                if result.conflict:
                    # Try to resolve conflicts
                    resolution_result = await self.conflict_resolver.resolve_conflicts()
                    if resolution_result.success:
                        continue
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                return PushResult(
                    success=False,
                    error=f"Push failed after {self.max_retries} attempts: {result.error}"
                )
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                return PushResult(
                    success=False,
                    error=f"Push failed with exception: {str(e)}"
                )
        
        return PushResult(success=False, error="Max retries exceeded")
```

### MCP Tools Integration

#### New MCP Tools for Regression Testing & Git Workflow Management

**Regression Testing Tools:**
1. **`bmad_regression_test_run`** - Run comprehensive regression tests
2. **`bmad_regression_baseline_establish`** - Establish new baseline for regression testing
3. **`bmad_regression_baseline_list`** - List available baselines
4. **`bmad_regression_report_generate`** - Generate detailed regression reports
5. **`bmad_regression_history_get`** - Get regression testing history

**Git Workflow Management Tools:**
6. **`bmad_git_auto_commit`** - Automatically commit changes after testing
7. **`bmad_git_auto_push`** - Automatically push committed changes
8. **`bmad_git_workflow_status`** - Get status of automated git workflows
9. **`bmad_git_workflow_configure`** - Configure automated git workflow settings

### Integration Points

#### 1. Workflow Testing Integration
```python
# Integration with WorkflowTestingEngine
class WorkflowTestingEngine:
    async def run_complete_test_suite(self) -> WorkflowTestResult:
        # ... existing test execution logic ...
        
        # Auto-commit and push results
        git_manager = GitWorkflowManager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="workflow_testing",
            test_results=result.to_dict()
        )
        
        result.git_workflow_result = git_result
        return result
```

#### 2. Scenario Testing Integration
```python
# Integration with ScenarioTestingEngine
class ScenarioTestingEngine:
    async def execute_scenario(self, scenario_id: str) -> ScenarioResult:
        # ... existing scenario execution logic ...
        
        # Auto-commit and push results
        git_manager = GitWorkflowManager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="scenario_testing",
            test_results=result.to_dict()
        )
        
        result.git_workflow_result = git_result
        return result
```

#### 3. Regression Testing Integration
```python
# Integration with RegressionTestingEngine (to be implemented)
class RegressionTestingEngine:
    async def run_regression_tests(self) -> RegressionTestResult:
        # ... regression testing logic ...
        
        # Auto-commit and push results
        git_manager = GitWorkflowManager()
        git_result = await git_manager.auto_commit_and_push(
            test_type="regression_testing",
            test_results=result.to_dict()
        )
        
        result.git_workflow_result = git_result
        return result
```

## Dependencies

- **Phase 4.1.1**: Complete Workflow Testing ✅ COMPLETE
- **Phase 4.1.2**: Scenario-based Testing ✅ COMPLETE
- **Existing**: `cflow_platform/core/git_ops.py` (has `attempt_auto_commit`)

## Implementation Tasks

### Task 4.1.3.1: Implement Regression Testing Engine
- **Duration**: 2 days
- **Description**: Create RegressionTestingEngine with baseline management and comparison
- **Outputs**: Complete regression testing framework

### Task 4.1.3.2: Implement Git Workflow Manager
- **Duration**: 1 day
- **Description**: Create core GitWorkflowManager class
- **Outputs**: GitWorkflowManager with auto-commit and push functionality

### Task 4.1.3.3: Implement Commit Template Manager
- **Duration**: 0.5 days
- **Description**: Create CommitTemplateManager for test-specific commit messages
- **Outputs**: Template system for different test types

### Task 4.1.3.4: Implement Push Handler
- **Duration**: 0.5 days
- **Description**: Create PushHandler with retry logic and conflict resolution
- **Outputs**: Robust push handling with error recovery

### Task 4.1.3.5: Integrate with Testing Frameworks
- **Duration**: 1 day
- **Description**: Integrate git workflows with workflow, scenario, and regression testing
- **Outputs**: Automated git operations in all testing frameworks

### Task 4.1.3.6: Add MCP Tools
- **Duration**: 1 day
- **Description**: Add MCP tools for regression testing and git workflow management
- **Outputs**: 9 new MCP tools (5 regression + 4 git workflow)

### Task 4.1.3.7: Testing and Validation
- **Duration**: 1 day
- **Description**: Test regression testing and automated git workflows end-to-end
- **Outputs**: Validated regression testing and automated git workflow system

## Definition of Done

- [ ] All acceptance criteria met
- [ ] GitWorkflowManager implemented and tested
- [ ] CommitTemplateManager implemented with all test type templates
- [ ] PushHandler implemented with retry logic
- [ ] Integration with workflow and scenario testing complete
- [ ] 4 new MCP tools implemented and registered
- [ ] End-to-end testing validates automated git workflows
- [ ] Documentation updated
- [ ] No linting errors
- [ ] All tests passing

## Risk Assessment

**Low Risk**: Building on existing `git_ops.py` infrastructure
**Mitigation**: Comprehensive testing and error handling
**Rollback**: Can disable auto-push if issues arise

## Success Metrics

- Automated commits created for all testing activities
- Zero manual git operations required during testing
- Proper commit message formatting and test result inclusion
- Successful push operations with conflict resolution
- Integration with all testing frameworks
