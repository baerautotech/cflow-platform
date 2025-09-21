"""
Git Workflow Manager for Automated Testing & Validation Framework

This module provides automated git operations (commit/push) integrated with
the testing framework to ensure all changes are properly tracked and versioned.
"""

import asyncio
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .git_ops import attempt_auto_commit

logger = logging.getLogger(__name__)


class GitWorkflowStatus(Enum):
    """Git workflow status"""
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class GitWorkflowResult:
    """Result of git workflow operation"""
    status: GitWorkflowStatus
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    message: Optional[str] = None
    push_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class CommitTemplate:
    """Template for commit messages"""
    test_type: str
    template: str
    variables: List[str]


class CommitTemplateManager:
    """Manages commit message templates for different test types"""
    
    def __init__(self):
        self.templates = {
            "workflow_testing": CommitTemplate(
                test_type="workflow_testing",
                template="""test(workflow): Complete workflow testing execution

✅ Tests: {successful_tests}/{total_tests} passed
📊 Score: {overall_score:.1f}%
🎯 Status: {status}

Automated commit from workflow testing framework.""",
                variables=["successful_tests", "total_tests", "overall_score", "status"]
            ),
            "scenario_testing": CommitTemplate(
                test_type="scenario_testing",
                template="""test(scenario): Execute scenario-based testing

🎭 Scenarios: {scenarios_executed} executed
📈 Success Rate: {success_rate:.1f}%
🏷️ Priority: {priority_level}

Automated commit from scenario testing framework.""",
                variables=["scenarios_executed", "success_rate", "priority_level"]
            ),
            "regression_testing": CommitTemplate(
                test_type="regression_testing",
                template="""test(regression): Regression testing execution

🔍 Tests Run: {tests_run}
⚠️ Regressions Found: {regressions_found}
✅ Status: {status}

Automated commit from regression testing framework.""",
                variables=["tests_run", "regressions_found", "status"]
            ),
            "integration_testing": CommitTemplate(
                test_type="integration_testing",
                template="""test(integration): Integration testing execution

🔗 Components: {components_tested}
📊 Coverage: {coverage:.1f}%
🎯 Status: {status}

Automated commit from integration testing framework.""",
                variables=["components_tested", "coverage", "status"]
            ),
            "baseline_establishment": CommitTemplate(
                test_type="baseline_establishment",
                template="""test(baseline): Establish new regression baseline

📋 Baseline ID: {baseline_id}
📝 Description: {description}
🧪 Test Count: {test_count}

Automated commit from regression testing framework.""",
                variables=["baseline_id", "description", "test_count"]
            )
        }
    
    def generate_message(self, test_type: str, test_results: Dict[str, Any]) -> str:
        """Generate commit message based on test type and results"""
        
        template = self.templates.get(test_type)
        if not template:
            # Fallback to default template
            return self._default_template(test_results)
        
        try:
            # Extract variables from test results
            variables = {}
            for var in template.variables:
                variables[var] = test_results.get(var, "unknown")
            
            # Format template with variables
            return template.template.format(**variables)
            
        except Exception as e:
            logger.warning(f"Failed to format commit template: {e}")
            return self._default_template(test_results)
    
    def _default_template(self, test_results: Dict[str, Any]) -> str:
        """Default commit message template"""
        
        test_type = test_results.get("test_type", "testing")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""test({test_type}): Automated testing execution

🕒 Timestamp: {timestamp}
📊 Results: {test_results.get('summary', 'See details')}

Automated commit from testing framework."""


class PushHandler:
    """Handles automated git push operations with retry logic"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5.0
        self.conflict_resolver = ConflictResolver()
    
    async def push_changes(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Push changes to remote repository with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                result = await self._attempt_push(branch)
                
                if result["success"]:
                    return result
                
                if result.get("conflict"):
                    # Try to resolve conflicts
                    resolution_result = await self.conflict_resolver.resolve_conflicts()
                    if resolution_result["success"]:
                        continue
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                return {
                    "success": False,
                    "error": f"Push failed after {self.max_retries} attempts: {result.get('error')}"
                }
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                return {
                    "success": False,
                    "error": f"Push failed with exception: {str(e)}"
                }
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def _attempt_push(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to push changes"""
        
        try:
            # Get current branch if not specified
            if not branch:
                branch_result = await self._run_git_command(["branch", "--show-current"])
                if not branch_result["success"]:
                    return {"success": False, "error": "Could not determine current branch"}
                branch = branch_result["output"].strip()
            
            # Push to remote
            push_command = ["push", "origin", branch]
            push_result = await self._run_git_command(push_command)
            
            if push_result["success"]:
                return {
                    "success": True,
                    "branch": branch,
                    "output": push_result["output"]
                }
            else:
                # Check for specific error types
                error_output = push_result["error"]
                
                if "conflict" in error_output.lower() or "diverged" in error_output.lower():
                    return {
                        "success": False,
                        "conflict": True,
                        "error": error_output
                    }
                else:
                    return {
                        "success": False,
                        "conflict": False,
                        "error": error_output
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "conflict": False,
                "error": f"Push attempt failed: {str(e)}"
            }
    
    async def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Run git command and return result"""
        
        try:
            full_command = ["git"] + command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30.0
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Git command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Git command failed: {str(e)}"
            }


class ConflictResolver:
    """Resolves git conflicts automatically"""
    
    def __init__(self):
        self.strategies = [
            self._strategy_rebase,
            self._strategy_merge,
            self._strategy_reset
        ]
    
    async def resolve_conflicts(self) -> Dict[str, Any]:
        """Attempt to resolve git conflicts using various strategies"""
        
        for strategy in self.strategies:
            try:
                result = await strategy()
                if result["success"]:
                    return result
            except Exception as e:
                logger.warning(f"Conflict resolution strategy failed: {e}")
                continue
        
        return {
            "success": False,
            "error": "All conflict resolution strategies failed"
        }
    
    async def _strategy_rebase(self) -> Dict[str, Any]:
        """Try rebase strategy"""
        
        try:
            # Fetch latest changes
            fetch_result = await self._run_git_command(["fetch", "origin"])
            if not fetch_result["success"]:
                return {"success": False, "error": "Fetch failed"}
            
            # Try rebase
            rebase_result = await self._run_git_command(["rebase", "origin/main"])
            if rebase_result["success"]:
                return {"success": True, "strategy": "rebase"}
            else:
                # Abort rebase if it failed
                await self._run_git_command(["rebase", "--abort"])
                return {"success": False, "error": "Rebase failed"}
                
        except Exception as e:
            return {"success": False, "error": f"Rebase strategy failed: {e}"}
    
    async def _strategy_merge(self) -> Dict[str, Any]:
        """Try merge strategy"""
        
        try:
            # Try merge
            merge_result = await self._run_git_command(["merge", "origin/main"])
            if merge_result["success"]:
                return {"success": True, "strategy": "merge"}
            else:
                # Abort merge if it failed
                await self._run_git_command(["merge", "--abort"])
                return {"success": False, "error": "Merge failed"}
                
        except Exception as e:
            return {"success": False, "error": f"Merge strategy failed: {e}"}
    
    async def _strategy_reset(self) -> Dict[str, Any]:
        """Try reset strategy (last resort)"""
        
        try:
            # Reset to origin/main
            reset_result = await self._run_git_command(["reset", "--hard", "origin/main"])
            if reset_result["success"]:
                return {
                    "success": True, 
                    "strategy": "reset",
                    "warning": "Reset to origin/main - local changes may be lost"
                }
            else:
                return {"success": False, "error": "Reset failed"}
                
        except Exception as e:
            return {"success": False, "error": f"Reset strategy failed: {e}"}
    
    async def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Run git command and return result"""
        
        try:
            full_command = ["git"] + command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30.0
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Git command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Git command failed: {str(e)}"
            }


class GitConfigManager:
    """Manages git workflow configuration"""
    
    def __init__(self):
        self.config = {
            "auto_push_enabled": True,
            "commit_message_max_length": 300,
            "push_retry_count": 3,
            "push_retry_delay": 5.0,
            "conflict_resolution_enabled": True,
            "branch_protection_enabled": False
        }
    
    def auto_push_enabled(self) -> bool:
        """Check if auto-push is enabled"""
        return self.config.get("auto_push_enabled", True)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration"""
        self.config.update(updates)
        logger.info(f"Git workflow configuration updated: {updates}")


class GitWorkflowManager:
    """Main manager for automated git operations in testing framework"""
    
    def __init__(self):
        self.commit_template_manager = CommitTemplateManager()
        self.push_handler = PushHandler()
        self.config_manager = GitConfigManager()
        self.git_ops = GitOperations()
    
    async def auto_commit_and_push(
        self,
        test_type: str,
        test_results: Dict[str, Any],
        include_untracked: bool = True,
        custom_message: Optional[str] = None
    ) -> GitWorkflowResult:
        """Automatically commit and push changes after testing"""
        
        start_time = time.time()
        
        try:
            # Check for changes
            if not self.git_ops.has_changes():
                return GitWorkflowResult(
                    status=GitWorkflowStatus.SKIPPED,
                    error="No changes to commit",
                    duration_seconds=time.time() - start_time
                )
            
            # Generate commit message
            if custom_message:
                commit_message = custom_message
            else:
                commit_message = self.commit_template_manager.generate_message(
                    test_type=test_type,
                    test_results=test_results
                )
            
            # Commit changes
            commit_result = await self.git_ops.commit_changes(
                message=commit_message,
                include_untracked=include_untracked
            )
            
            if not commit_result["success"]:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.ERROR,
                    error=commit_result["error"],
                    duration_seconds=time.time() - start_time
                )
            
            # Push changes (if enabled)
            push_result = None
            if self.config_manager.auto_push_enabled():
                push_result = await self.push_handler.push_changes()
                
                if push_result["success"]:
                    return GitWorkflowResult(
                        status=GitWorkflowStatus.SUCCESS,
                        commit_hash=commit_result["commit_hash"],
                        branch=commit_result["branch"],
                        message=commit_message,
                        push_result=push_result,
                        duration_seconds=time.time() - start_time
                    )
                else:
                    return GitWorkflowResult(
                        status=GitWorkflowStatus.PARTIAL,
                        commit_hash=commit_result["commit_hash"],
                        branch=commit_result["branch"],
                        message=commit_message,
                        push_result=push_result,
                        error=f"Commit successful but push failed: {push_result.get('error')}",
                        duration_seconds=time.time() - start_time
                    )
            else:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.SUCCESS,
                    commit_hash=commit_result["commit_hash"],
                    branch=commit_result["branch"],
                    message=commit_message,
                    push_result=None,
                    duration_seconds=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Git workflow failed: {e}")
            return GitWorkflowResult(
                status=GitWorkflowStatus.ERROR,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def commit_only(
        self,
        test_type: str,
        test_results: Dict[str, Any],
        include_untracked: bool = True,
        custom_message: Optional[str] = None
    ) -> GitWorkflowResult:
        """Commit changes without pushing"""
        
        start_time = time.time()
        
        try:
            # Generate commit message
            if custom_message:
                commit_message = custom_message
            else:
                commit_message = self.commit_template_manager.generate_message(
                    test_type=test_type,
                    test_results=test_results
                )
            
            # Commit changes
            commit_result = await self.git_ops.commit_changes(
                message=commit_message,
                include_untracked=include_untracked
            )
            
            if commit_result["success"]:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.SUCCESS,
                    commit_hash=commit_result["commit_hash"],
                    branch=commit_result["branch"],
                    message=commit_message,
                    duration_seconds=time.time() - start_time
                )
            else:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.ERROR,
                    error=commit_result["error"],
                    duration_seconds=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Commit operation failed: {e}")
            return GitWorkflowResult(
                status=GitWorkflowStatus.ERROR,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def push_only(self, branch: Optional[str] = None) -> GitWorkflowResult:
        """Push existing commits without committing new changes"""
        
        start_time = time.time()
        
        try:
            push_result = await self.push_handler.push_changes(branch)
            
            if push_result["success"]:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.SUCCESS,
                    push_result=push_result,
                    duration_seconds=time.time() - start_time
                )
            else:
                return GitWorkflowResult(
                    status=GitWorkflowStatus.ERROR,
                    error=push_result.get("error"),
                    duration_seconds=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Push operation failed: {e}")
            return GitWorkflowResult(
                status=GitWorkflowStatus.ERROR,
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current git workflow status"""
        
        return {
            "config": self.config_manager.get_config(),
            "has_changes": self.git_ops.has_changes(),
            "current_branch": self.git_ops.get_current_branch(),
            "last_commit": self.git_ops.get_last_commit_hash()
        }


class GitOperations:
    """Wrapper around existing git_ops functionality"""
    
    def __init__(self):
        self.repo_root = self._find_repo_root()
    
    def has_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        
        if not self.repo_root:
            return False
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10.0
            )
            
            return len(result.stdout.strip()) > 0
            
        except Exception:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        
        if not self.repo_root:
            return None
        
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10.0
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
        except Exception:
            pass
        
        return None
    
    def get_last_commit_hash(self) -> Optional[str]:
        """Get last commit hash"""
        
        if not self.repo_root:
            return None
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10.0
            )
            
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # Short hash
            
        except Exception:
            pass
        
        return None
    
    async def commit_changes(
        self,
        message: str,
        include_untracked: bool = True
    ) -> Dict[str, Any]:
        """Commit changes using existing git_ops functionality"""
        
        if not self.repo_root:
            return {
                "success": False,
                "error": "Not in a git repository"
            }
        
        try:
            # Use existing attempt_auto_commit function
            result = attempt_auto_commit(
                message=message,
                include_untracked=include_untracked
            )
            
            if result["status"] == "success":
                return {
                    "success": True,
                    "commit_hash": result["commit"],
                    "branch": result["branch"],
                    "message": result["message"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Commit failed")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Commit operation failed: {str(e)}"
            }
    
    def _find_repo_root(self) -> Optional[Path]:
        """Find git repository root"""
        
        current_path = Path.cwd()
        
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return current_path
            current_path = current_path.parent
        
        return None


# Global instance
_git_workflow_manager: Optional[GitWorkflowManager] = None


def get_git_workflow_manager() -> GitWorkflowManager:
    """Get the global git workflow manager instance"""
    global _git_workflow_manager
    if _git_workflow_manager is None:
        _git_workflow_manager = GitWorkflowManager()
    return _git_workflow_manager
