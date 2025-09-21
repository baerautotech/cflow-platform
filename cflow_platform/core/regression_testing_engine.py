"""
Regression Testing Engine for BMAD Workflows

This module provides regression testing capabilities to detect workflow changes
that break existing functionality, with baseline management and automated git workflows.
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


class RegressionStatus(Enum):
    """Regression test status"""
    PASSED = "passed"
    REGRESSIONS_DETECTED = "regressions_detected"
    ERROR = "error"
    BASELINE_MISSING = "baseline_missing"


class BaselineStatus(Enum):
    """Baseline status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


@dataclass
class RegressionIssue:
    """Individual regression issue"""
    issue_id: str
    test_name: str
    baseline_value: Any
    current_value: Any
    severity: str  # "critical", "high", "medium", "low"
    description: str
    impact_assessment: str
    recommended_action: str


@dataclass
class RegressionTestResult:
    """Result of regression test execution"""
    test_suite_id: str
    baseline_id: str
    execution_id: str
    status: RegressionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    regressions_found: int = 0
    regressions: List[RegressionIssue] = field(default_factory=list)
    comparison_result: Dict[str, Any] = field(default_factory=dict)
    report: Dict[str, Any] = field(default_factory=dict)
    git_workflow_result: Optional[Dict[str, Any]] = None


@dataclass
class Baseline:
    """Test baseline for regression comparison"""
    baseline_id: str
    test_suite_id: str
    description: str
    created_at: datetime
    status: BaselineStatus
    test_results: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineResult:
    """Result of baseline establishment"""
    baseline_id: str
    test_suite_id: str
    description: str
    test_count: int
    created_at: datetime
    git_workflow_result: Optional[Dict[str, Any]] = None


class BaselineManager:
    """Manages test baselines for regression testing"""
    
    def __init__(self):
        self.baselines: Dict[str, Baseline] = {}
        self.active_baselines: Dict[str, str] = {}  # test_suite_id -> baseline_id
    
    async def create_baseline(
        self,
        test_suite_id: str,
        description: str,
        test_results: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> Baseline:
        """Create a new baseline from test results"""
        
        baseline_id = f"baseline_{uuid.uuid4().hex[:8]}"
        
        # Archive previous baseline for this test suite
        if test_suite_id in self.active_baselines:
            old_baseline_id = self.active_baselines[test_suite_id]
            if old_baseline_id in self.baselines:
                self.baselines[old_baseline_id].status = BaselineStatus.SUPERSEDED
        
        baseline = Baseline(
            baseline_id=baseline_id,
            test_suite_id=test_suite_id,
            description=description,
            created_at=datetime.now(),
            status=BaselineStatus.ACTIVE,
            test_results=test_results,
            metadata=metadata or {}
        )
        
        self.baselines[baseline_id] = baseline
        self.active_baselines[test_suite_id] = baseline_id
        
        logger.info(f"Created baseline {baseline_id} for test suite {test_suite_id}")
        return baseline
    
    async def get_baseline(self, baseline_id: Optional[str] = None) -> Optional[Baseline]:
        """Get baseline by ID or active baseline"""
        
        if baseline_id:
            return self.baselines.get(baseline_id)
        
        # Return most recent active baseline
        active_baselines = [
            b for b in self.baselines.values() 
            if b.status == BaselineStatus.ACTIVE
        ]
        
        if not active_baselines:
            return None
        
        # Return most recent
        return max(active_baselines, key=lambda b: b.created_at)
    
    async def get_active_baseline(self, test_suite_id: str) -> Optional[Baseline]:
        """Get active baseline for specific test suite"""
        
        if test_suite_id not in self.active_baselines:
            return None
        
        baseline_id = self.active_baselines[test_suite_id]
        return self.baselines.get(baseline_id)
    
    def list_baselines(
        self,
        test_suite_id: Optional[str] = None,
        status: Optional[BaselineStatus] = None
    ) -> List[Baseline]:
        """List baselines with optional filtering"""
        
        baselines = list(self.baselines.values())
        
        if test_suite_id:
            baselines = [b for b in baselines if b.test_suite_id == test_suite_id]
        
        if status:
            baselines = [b for b in baselines if b.status == status]
        
        # Sort by creation time (newest first)
        baselines.sort(key=lambda b: b.created_at, reverse=True)
        
        return baselines


class ComparisonEngine:
    """Engine for comparing test results with baselines"""
    
    def __init__(self):
        self.comparators = {
            "workflow_testing": self._compare_workflow_results,
            "scenario_testing": self._compare_scenario_results,
            "integration_testing": self._compare_integration_results
        }
    
    async def compare_results(
        self,
        baseline: Baseline,
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare current test results with baseline"""
        
        if not baseline:
            return {
                "status": "error",
                "error": "No baseline available for comparison"
            }
        
        comparison_result = {
            "baseline_id": baseline.baseline_id,
            "baseline_created_at": baseline.created_at.isoformat(),
            "comparison_timestamp": datetime.now().isoformat(),
            "test_suite_id": baseline.test_suite_id,
            "comparisons": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "new_tests": 0,
                "removed_tests": 0,
                "changed_tests": 0
            }
        }
        
        # Perform comparison based on test suite type
        test_suite_id = baseline.test_suite_id
        comparator = self.comparators.get(test_suite_id, self._compare_generic_results)
        
        comparison_data = await comparator(baseline.test_results, current)
        comparison_result["comparisons"] = comparison_data
        
        # Calculate summary
        comparison_result["summary"] = self._calculate_summary(comparison_data)
        
        return comparison_result
    
    async def _compare_workflow_results(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare workflow testing results"""
        
        comparisons = {}
        
        # Compare test suites
        baseline_suites = baseline.get("test_suites", {})
        current_suites = current.get("test_suites", {})
        
        all_suite_names = set(baseline_suites.keys()) | set(current_suites.keys())
        
        for suite_name in all_suite_names:
            baseline_suite = baseline_suites.get(suite_name, {})
            current_suite = current_suites.get(suite_name, {})
            
            suite_comparison = {
                "status": "unchanged",
                "baseline_score": baseline_suite.get("overall_score", 0.0),
                "current_score": current_suite.get("overall_score", 0.0),
                "score_difference": 0.0,
                "test_count_change": 0,
                "issues": []
            }
            
            # Compare scores
            score_diff = current_suite.get("overall_score", 0.0) - baseline_suite.get("overall_score", 0.0)
            suite_comparison["score_difference"] = score_diff
            
            if abs(score_diff) > 5.0:  # Significant score change
                suite_comparison["status"] = "changed"
                suite_comparison["issues"].append({
                    "type": "score_change",
                    "severity": "high" if abs(score_diff) > 20.0 else "medium",
                    "description": f"Score changed by {score_diff:.1f} points"
                })
            
            # Compare test counts
            baseline_count = baseline_suite.get("test_count", 0)
            current_count = current_suite.get("test_count", 0)
            count_diff = current_count - baseline_count
            suite_comparison["test_count_change"] = count_diff
            
            if count_diff != 0:
                suite_comparison["status"] = "changed"
                suite_comparison["issues"].append({
                    "type": "test_count_change",
                    "severity": "medium",
                    "description": f"Test count changed by {count_diff}"
                })
            
            comparisons[suite_name] = suite_comparison
        
        return comparisons
    
    async def _compare_scenario_results(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare scenario testing results"""
        
        comparisons = {}
        
        # Compare scenarios
        baseline_scenarios = baseline.get("scenarios", {})
        current_scenarios = current.get("scenarios", {})
        
        all_scenario_names = set(baseline_scenarios.keys()) | set(current_scenarios.keys())
        
        for scenario_name in all_scenario_names:
            baseline_scenario = baseline_scenarios.get(scenario_name, {})
            current_scenario = current_scenarios.get(scenario_name, {})
            
            scenario_comparison = {
                "status": "unchanged",
                "baseline_success_rate": baseline_scenario.get("success_rate", 0.0),
                "current_success_rate": current_scenario.get("success_rate", 0.0),
                "success_rate_difference": 0.0,
                "execution_count_change": 0,
                "issues": []
            }
            
            # Compare success rates
            success_rate_diff = (
                current_scenario.get("success_rate", 0.0) - 
                baseline_scenario.get("success_rate", 0.0)
            )
            scenario_comparison["success_rate_difference"] = success_rate_diff
            
            if abs(success_rate_diff) > 10.0:  # Significant success rate change
                scenario_comparison["status"] = "changed"
                scenario_comparison["issues"].append({
                    "type": "success_rate_change",
                    "severity": "high" if abs(success_rate_diff) > 30.0 else "medium",
                    "description": f"Success rate changed by {success_rate_diff:.1f}%"
                })
            
            comparisons[scenario_name] = scenario_comparison
        
        return comparisons
    
    async def _compare_integration_results(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare integration testing results"""
        
        comparisons = {}
        
        # Compare integration points
        baseline_integrations = baseline.get("integrations", {})
        current_integrations = current.get("integrations", {})
        
        all_integration_names = set(baseline_integrations.keys()) | set(current_integrations.keys())
        
        for integration_name in all_integration_names:
            baseline_integration = baseline_integrations.get(integration_name, {})
            current_integration = current_integrations.get(integration_name, {})
            
            integration_comparison = {
                "status": "unchanged",
                "baseline_status": baseline_integration.get("status", "unknown"),
                "current_status": current_integration.get("status", "unknown"),
                "response_time_change": 0.0,
                "issues": []
            }
            
            # Compare status
            if baseline_integration.get("status") != current_integration.get("status"):
                integration_comparison["status"] = "changed"
                integration_comparison["issues"].append({
                    "type": "status_change",
                    "severity": "critical",
                    "description": f"Status changed from {baseline_integration.get('status')} to {current_integration.get('status')}"
                })
            
            # Compare response times
            baseline_time = baseline_integration.get("response_time", 0.0)
            current_time = current_integration.get("response_time", 0.0)
            time_diff = current_time - baseline_time
            integration_comparison["response_time_change"] = time_diff
            
            if abs(time_diff) > 100.0:  # Significant response time change
                integration_comparison["status"] = "changed"
                integration_comparison["issues"].append({
                    "type": "performance_change",
                    "severity": "high" if abs(time_diff) > 500.0 else "medium",
                    "description": f"Response time changed by {time_diff:.1f}ms"
                })
            
            comparisons[integration_name] = integration_comparison
        
        return comparisons
    
    async def _compare_generic_results(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic comparison for unknown test types"""
        
        comparisons = {}
        
        # Simple key-value comparison
        all_keys = set(baseline.keys()) | set(current.keys())
        
        for key in all_keys:
            baseline_value = baseline.get(key)
            current_value = current.get(key)
            
            comparison = {
                "status": "unchanged",
                "baseline_value": baseline_value,
                "current_value": current_value,
                "issues": []
            }
            
            if baseline_value != current_value:
                comparison["status"] = "changed"
                comparison["issues"].append({
                    "type": "value_change",
                    "severity": "medium",
                    "description": f"Value changed from {baseline_value} to {current_value}"
                })
            
            comparisons[key] = comparison
        
        return comparisons
    
    def _calculate_summary(self, comparisons: Dict[str, Any]) -> Dict[str, int]:
        """Calculate summary statistics from comparisons"""
        
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "new_tests": 0,
            "removed_tests": 0,
            "changed_tests": 0
        }
        
        for comparison in comparisons.values():
            summary["total_tests"] += 1
            
            if comparison.get("status") == "unchanged":
                summary["passed"] += 1
            elif comparison.get("status") == "changed":
                summary["changed_tests"] += 1
                summary["failed"] += 1
        
        return summary


class RegressionDetector:
    """Detects regressions from comparison results"""
    
    def __init__(self):
        self.severity_thresholds = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    async def detect_regressions(
        self,
        comparison_result: Dict[str, Any]
    ) -> List[RegressionIssue]:
        """Detect regressions from comparison results"""
        
        regressions = []
        comparisons = comparison_result.get("comparisons", {})
        
        for test_name, comparison in comparisons.items():
            if comparison.get("status") != "changed":
                continue
            
            issues = comparison.get("issues", [])
            
            for issue in issues:
                regression = RegressionIssue(
                    issue_id=f"regression_{uuid.uuid4().hex[:8]}",
                    test_name=test_name,
                    baseline_value=comparison.get("baseline_value"),
                    current_value=comparison.get("current_value"),
                    severity=issue.get("severity", "medium"),
                    description=issue.get("description", "Unknown regression"),
                    impact_assessment=self._assess_impact(issue),
                    recommended_action=self._recommend_action(issue)
                )
                
                regressions.append(regression)
        
        return regressions
    
    def _assess_impact(self, issue: Dict[str, Any]) -> str:
        """Assess the impact of a regression issue"""
        
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "medium")
        
        impact_map = {
            "score_change": {
                "critical": "Significant degradation in test performance",
                "high": "Notable decrease in test quality",
                "medium": "Moderate impact on test results",
                "low": "Minor change in test performance"
            },
            "status_change": {
                "critical": "Critical functionality broken",
                "high": "Major functionality affected",
                "medium": "Some functionality impacted",
                "low": "Minor functionality change"
            },
            "performance_change": {
                "critical": "Severe performance degradation",
                "high": "Significant performance impact",
                "medium": "Moderate performance change",
                "low": "Minor performance variation"
            }
        }
        
        return impact_map.get(issue_type, {}).get(severity, "Unknown impact")
    
    def _recommend_action(self, issue: Dict[str, Any]) -> str:
        """Recommend action for regression issue"""
        
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "medium")
        
        action_map = {
            "score_change": {
                "critical": "Immediate investigation and fix required",
                "high": "Priority fix needed",
                "medium": "Schedule fix in next iteration",
                "low": "Monitor and address when convenient"
            },
            "status_change": {
                "critical": "Rollback or hotfix immediately",
                "high": "Fix in next deployment",
                "medium": "Address in next sprint",
                "low": "Document and plan fix"
            },
            "performance_change": {
                "critical": "Performance optimization required immediately",
                "high": "Performance tuning needed",
                "medium": "Investigate performance impact",
                "low": "Monitor performance trends"
            }
        }
        
        return action_map.get(issue_type, {}).get(severity, "Review and address as needed")


class RegressionReportGenerator:
    """Generates detailed regression reports"""
    
    def __init__(self):
        self.template_engine = ReportTemplateEngine()
    
    async def generate_report(
        self,
        regressions: List[RegressionIssue],
        comparison_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive regression report"""
        
        report = {
            "report_id": f"regression_report_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.now().isoformat(),
            "baseline_id": comparison_result.get("baseline_id"),
            "test_suite_id": comparison_result.get("test_suite_id"),
            "summary": {
                "total_regressions": len(regressions),
                "critical_regressions": len([r for r in regressions if r.severity == "critical"]),
                "high_regressions": len([r for r in regressions if r.severity == "high"]),
                "medium_regressions": len([r for r in regressions if r.severity == "medium"]),
                "low_regressions": len([r for r in regressions if r.severity == "low"])
            },
            "regressions": [
                {
                    "issue_id": r.issue_id,
                    "test_name": r.test_name,
                    "severity": r.severity,
                    "description": r.description,
                    "impact_assessment": r.impact_assessment,
                    "recommended_action": r.recommended_action,
                    "baseline_value": r.baseline_value,
                    "current_value": r.current_value
                }
                for r in regressions
            ],
            "comparison_summary": comparison_result.get("summary", {}),
            "recommendations": self._generate_recommendations(regressions),
            "next_steps": self._generate_next_steps(regressions)
        }
        
        return report
    
    def _generate_recommendations(self, regressions: List[RegressionIssue]) -> List[str]:
        """Generate recommendations based on regressions"""
        
        recommendations = []
        
        critical_count = len([r for r in regressions if r.severity == "critical"])
        high_count = len([r for r in regressions if r.severity == "high"])
        
        if critical_count > 0:
            recommendations.append(f"🚨 {critical_count} critical regression(s) require immediate attention")
        
        if high_count > 0:
            recommendations.append(f"⚠️ {high_count} high-priority regression(s) should be addressed soon")
        
        if len(regressions) == 0:
            recommendations.append("✅ No regressions detected - system is stable")
        else:
            recommendations.append("📋 Review all regressions and prioritize fixes based on severity")
            recommendations.append("🔄 Consider establishing new baseline after fixes are applied")
        
        return recommendations
    
    def _generate_next_steps(self, regressions: List[RegressionIssue]) -> List[str]:
        """Generate next steps based on regressions"""
        
        next_steps = []
        
        if len(regressions) == 0:
            next_steps.append("Continue with normal development workflow")
            next_steps.append("Schedule next regression test cycle")
        else:
            next_steps.append("Address critical and high-priority regressions first")
            next_steps.append("Test fixes in isolated environment before deployment")
            next_steps.append("Re-run regression tests after fixes")
            next_steps.append("Update baseline if fixes are successful")
        
        return next_steps


class ReportTemplateEngine:
    """Engine for generating report templates"""
    
    def generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate markdown format regression report"""
        
        summary = report_data.get("summary", {})
        regressions = report_data.get("regressions", [])
        
        markdown = f"""# Regression Test Report

**Report ID**: {report_data.get("report_id")}  
**Generated**: {report_data.get("generated_at")}  
**Baseline ID**: {report_data.get("baseline_id")}  
**Test Suite**: {report_data.get("test_suite_id")}

## Summary

- **Total Regressions**: {summary.get("total_regressions", 0)}
- **Critical**: {summary.get("critical_regressions", 0)}
- **High**: {summary.get("high_regressions", 0)}
- **Medium**: {summary.get("medium_regressions", 0)}
- **Low**: {summary.get("low_regressions", 0)}

## Regressions Found

"""
        
        for regression in regressions:
            markdown += f"""### {regression.get("test_name")} - {regression.get("severity").upper()}

**Description**: {regression.get("description")}  
**Impact**: {regression.get("impact_assessment")}  
**Action**: {regression.get("recommended_action")}

"""
        
        return markdown


class RegressionTestingEngine:
    """Main engine for regression testing with automated git workflows"""
    
    def __init__(self):
        self.baseline_manager = BaselineManager()
        self.comparison_engine = ComparisonEngine()
        self.regression_detector = RegressionDetector()
        self.report_generator = RegressionReportGenerator()
        self.execution_history: List[RegressionTestResult] = []
    
    async def run_regression_tests(
        self,
        test_suite_id: Optional[str] = None,
        baseline_id: Optional[str] = None
    ) -> RegressionTestResult:
        """Run comprehensive regression tests"""
        
        execution_id = f"regression_exec_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            # Get baseline for comparison
            baseline = await self.baseline_manager.get_baseline(baseline_id)
            
            if not baseline:
                return RegressionTestResult(
                    test_suite_id=test_suite_id or "unknown",
                    baseline_id=baseline_id or "none",
                    execution_id=execution_id,
                    status=RegressionStatus.BASELINE_MISSING,
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration_seconds=0.0,
                    regressions_found=0,
                    regressions=[],
                    comparison_result={"error": "No baseline available"},
                    report={"error": "Cannot run regression tests without baseline"}
                )
            
            # Execute current tests (simplified - would integrate with actual test frameworks)
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
            
            # Determine status
            status = RegressionStatus.PASSED if len(regressions) == 0 else RegressionStatus.REGRESSIONS_DETECTED
            
            # Create result
            end_time = datetime.now()
            result = RegressionTestResult(
                test_suite_id=test_suite_id or baseline.test_suite_id,
                baseline_id=baseline.baseline_id,
                execution_id=execution_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                regressions_found=len(regressions),
                regressions=regressions,
                comparison_result=comparison_result,
                report=report
            )
            
            # Store in history
            self.execution_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Regression test execution failed: {e}")
            end_time = datetime.now()
            
            return RegressionTestResult(
                test_suite_id=test_suite_id or "unknown",
                baseline_id=baseline_id or "none",
                execution_id=execution_id,
                status=RegressionStatus.ERROR,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                regressions_found=0,
                regressions=[],
                comparison_result={"error": str(e)},
                report={"error": f"Regression test failed: {str(e)}"}
            )
    
    async def establish_baseline(
        self,
        test_suite_id: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> BaselineResult:
        """Establish a new baseline for regression testing"""
        
        try:
            # Execute tests to capture baseline
            test_results = await self._execute_current_tests(test_suite_id)
            
            # Create baseline
            baseline = await self.baseline_manager.create_baseline(
                test_suite_id=test_suite_id,
                description=description,
                test_results=test_results,
                metadata=metadata
            )
            
            return BaselineResult(
                baseline_id=baseline.baseline_id,
                test_suite_id=test_suite_id,
                description=description,
                test_count=len(test_results.get("tests", [])),
                created_at=baseline.created_at
            )
            
        except Exception as e:
            logger.error(f"Baseline establishment failed: {e}")
            raise
    
    async def _execute_current_tests(self, test_suite_id: Optional[str]) -> Dict[str, Any]:
        """Execute current tests (simplified implementation)"""
        
        # This is a simplified implementation
        # In a real implementation, this would integrate with actual test frameworks
        
        if test_suite_id == "workflow_testing":
            return {
                "test_suites": {
                    "basic_workflow": {
                        "overall_score": 95.0,
                        "test_count": 5,
                        "passed": 5,
                        "failed": 0
                    },
                    "advanced_workflow": {
                        "overall_score": 87.5,
                        "test_count": 8,
                        "passed": 7,
                        "failed": 1
                    }
                },
                "total_tests": 13,
                "overall_score": 91.25
            }
        elif test_suite_id == "scenario_testing":
            return {
                "scenarios": {
                    "user_registration": {
                        "success_rate": 100.0,
                        "execution_count": 10,
                        "average_duration": 2.5
                    },
                    "payment_flow": {
                        "success_rate": 85.0,
                        "execution_count": 8,
                        "average_duration": 5.2
                    }
                },
                "total_scenarios": 2,
                "overall_success_rate": 92.5
            }
        else:
            # Generic test results
            return {
                "tests": [
                    {"name": "test_1", "status": "passed", "score": 100.0},
                    {"name": "test_2", "status": "passed", "score": 95.0},
                    {"name": "test_3", "status": "failed", "score": 0.0}
                ],
                "total_tests": 3,
                "passed": 2,
                "failed": 1,
                "overall_score": 65.0
            }
    
    def get_execution_history(
        self,
        test_suite_id: Optional[str] = None,
        limit: int = 50
    ) -> List[RegressionTestResult]:
        """Get regression test execution history"""
        
        history = self.execution_history.copy()
        
        if test_suite_id:
            history = [r for r in history if r.test_suite_id == test_suite_id]
        
        # Sort by start time (newest first)
        history.sort(key=lambda x: x.start_time, reverse=True)
        
        return history[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get regression testing statistics"""
        
        total_executions = len(self.execution_history)
        if total_executions == 0:
            return {
                "total_executions": 0,
                "total_baselines": len(self.baseline_manager.baselines),
                "regression_rate": 0.0,
                "average_regressions_per_run": 0.0
            }
        
        executions_with_regressions = len([
            r for r in self.execution_history 
            if r.status == RegressionStatus.REGRESSIONS_DETECTED
        ])
        
        total_regressions = sum(r.regressions_found for r in self.execution_history)
        
        return {
            "total_executions": total_executions,
            "total_baselines": len(self.baseline_manager.baselines),
            "executions_with_regressions": executions_with_regressions,
            "regression_rate": (executions_with_regressions / total_executions) * 100.0,
            "total_regressions_detected": total_regressions,
            "average_regressions_per_run": total_regressions / total_executions
        }


# Global instance
_regression_engine: Optional[RegressionTestingEngine] = None


def get_regression_engine() -> RegressionTestingEngine:
    """Get the global regression testing engine instance"""
    global _regression_engine
    if _regression_engine is None:
        _regression_engine = RegressionTestingEngine()
    return _regression_engine
