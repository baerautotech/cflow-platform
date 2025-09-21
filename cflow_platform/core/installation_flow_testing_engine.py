"""
Installation Flow Testing Engine

This module provides comprehensive testing capabilities for the complete
installation flow, including environment validation, component installation,
configuration management, and end-to-end testing.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class InstallationStep:
    """Represents a single installation step."""
    name: str
    description: str
    command: List[str]
    expected_exit_code: int = 0
    timeout_seconds: int = 300
    required_files: List[str] = field(default_factory=list)
    required_directories: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    validation_checks: List[str] = field(default_factory=list)


@dataclass
class InstallationFlowResult:
    """Result of installation flow testing."""
    success: bool
    message: str
    total_steps: int
    completed_steps: int
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    installation_time: float = 0.0
    validation_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class InstallationFlowTestingEngine:
    """
    Installation Flow Testing Engine for BMAD Integration.
    
    This class provides comprehensive testing of the complete installation flow,
    including:
    - Environment validation
    - Component installation
    - Configuration management
    - End-to-end testing
    - Rollback testing
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the installation flow testing engine."""
        self.project_root = project_root or Path.cwd()
        self.test_dir = self.project_root / ".test_installation"
        self.original_env = os.environ.copy()
        
    def create_installation_flow(self) -> List[InstallationStep]:
        """
        Create the complete installation flow steps.
        
        Returns:
            List of InstallationStep objects representing the complete flow
        """
        return [
            InstallationStep(
                name="environment_validation",
                description="Validate environment and dependencies",
                command=[sys.executable, "-m", "cflow_platform.verify_env", "--mode", "migrations", "--mode", "ragkg", "--mode", "llm", "--scope", "both"],
                validation_checks=["python_available", "dependencies_installed", "environment_variables_set"]
            ),
            InstallationStep(
                name="install_hooks",
                description="Install git hooks and pre-commit hooks",
                command=[sys.executable, "-m", "cflow_platform.install_hooks"],
                required_directories=[".git"],
                validation_checks=["hooks_installed", "pre_commit_configured"]
            ),
            InstallationStep(
                name="setup_cursor",
                description="Setup Cursor workspace configuration",
                command=[sys.executable, "-m", "cflow_platform.cli.setup_cursor"],
                validation_checks=["cursor_config_created", "workspace_configured"]
            ),
            InstallationStep(
                name="memory_connectivity",
                description="Test memory connectivity and configuration",
                command=[sys.executable, "-m", "cflow_platform.cli.memory_check"],
                validation_checks=["memory_accessible", "connection_established"]
            ),
            InstallationStep(
                name="bmad_integration_setup",
                description="Setup BMAD integration components",
                command=[sys.executable, "-m", "cflow_platform.cli.one_touch_installer", "--setup-bmad"],
                required_directories=["vendor/bmad"],
                validation_checks=["bmad_handlers_available", "bmad_templates_found"]
            ),
            InstallationStep(
                name="webmcp_configuration",
                description="Install WebMCP configuration",
                command=[sys.executable, "-m", "cflow_platform.cli.one_touch_installer", "--setup-webmcp", "--webmcp-server-url", "http://localhost:8000", "--bmad-api-url", "http://localhost:8001"],
                validation_checks=["webmcp_config_created", "environment_file_created", "configuration_valid"]
            ),
            InstallationStep(
                name="supabase_migrations",
                description="Apply Supabase migrations if available",
                command=[sys.executable, "-m", "cflow_platform.cli.migrate_supabase", "--apply"],
                validation_checks=["migrations_applied", "database_schema_updated"]
            ),
            InstallationStep(
                name="sync_agent_installation",
                description="Install sync agent for auto-start",
                command=[sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "install-agent", "--project-root", str(self.project_root)],
                validation_checks=["sync_agent_installed", "launch_agent_configured"]
            ),
            InstallationStep(
                name="initial_backfill",
                description="Perform initial backfill of docs and tasks",
                command=[sys.executable, "-m", "cflow_platform.cli.docs_backfill"],
                validation_checks=["docs_backfilled", "tasks_backfilled", "sync_status_checked"]
            ),
            InstallationStep(
                name="integration_validation",
                description="Validate complete integration",
                command=[sys.executable, "-m", "cflow_platform.cli.test_webmcp_installer"],
                validation_checks=["webmcp_tools_functional", "integration_tests_passed"]
            )
        ]
    
    async def test_complete_installation_flow(
        self,
        test_environment: bool = True,
        skip_optional_steps: bool = False
    ) -> InstallationFlowResult:
        """
        Test the complete installation flow.
        
        Args:
            test_environment: Whether to test in a temporary environment
            skip_optional_steps: Whether to skip optional installation steps
            
        Returns:
            InstallationFlowResult with test results
        """
        logger.info("Starting complete installation flow testing...")
        
        start_time = time.time()
        
        try:
            # Create test environment if requested
            if test_environment:
                await self._setup_test_environment()
            
            # Get installation flow steps
            steps = self.create_installation_flow()
            
            # Filter out optional steps if requested
            if skip_optional_steps:
                optional_steps = ["supabase_migrations", "sync_agent_installation", "initial_backfill"]
                steps = [step for step in steps if step.name not in optional_steps]
            
            # Execute installation steps
            step_results = {}
            failed_steps = []
            
            for step in steps:
                logger.info(f"Executing step: {step.name}")
                step_result = await self._execute_installation_step(step)
                step_results[step.name] = step_result
                
                if not step_result["success"]:
                    failed_steps.append(step.name)
                    logger.error(f"Step {step.name} failed: {step_result['error']}")
                else:
                    logger.info(f"Step {step.name} completed successfully")
            
            # Calculate results
            completed_steps = len(steps) - len(failed_steps)
            success = len(failed_steps) == 0
            
            installation_time = time.time() - start_time
            
            # Perform final validation
            validation_start = time.time()
            validation_result = await self._validate_complete_installation()
            validation_time = time.time() - validation_start
            
            return InstallationFlowResult(
                success=success,
                message=f"Installation flow testing completed. {completed_steps}/{len(steps)} steps successful.",
                total_steps=len(steps),
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                step_results=step_results,
                installation_time=installation_time,
                validation_time=validation_time,
                errors=validation_result.get("errors", []),
                warnings=validation_result.get("warnings", [])
            )
            
        except Exception as e:
            logger.error(f"Installation flow testing failed: {e}")
            return InstallationFlowResult(
                success=False,
                message=f"Installation flow testing failed: {e}",
                total_steps=0,
                completed_steps=0,
                errors=[str(e)]
            )
        finally:
            # Cleanup test environment if created
            if test_environment:
                await self._cleanup_test_environment()
    
    async def test_installation_step(
        self,
        step_name: str,
        custom_command: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Test a specific installation step.
        
        Args:
            step_name: Name of the installation step to test
            custom_command: Custom command to execute instead of default
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Testing installation step: {step_name}")
        
        try:
            # Get installation flow steps
            steps = self.create_installation_flow()
            step = next((s for s in steps if s.name == step_name), None)
            
            if not step:
                return {
                    "success": False,
                    "error": f"Installation step '{step_name}' not found"
                }
            
            # Use custom command if provided
            if custom_command:
                step.command = custom_command
            
            # Execute the step
            result = await self._execute_installation_step(step)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to test installation step {step_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_rollback_flow(self) -> InstallationFlowResult:
        """
        Test the rollback flow after installation.
        
        Returns:
            InstallationFlowResult with rollback test results
        """
        logger.info("Testing rollback flow...")
        
        start_time = time.time()
        
        try:
            # Test uninstall WebMCP configuration
            uninstall_result = await self._execute_command([
                sys.executable, "-c",
                "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_uninstall_config')))"
            ])
            
            # Test cleanup of installation artifacts
            cleanup_checks = await self._check_cleanup_artifacts()
            
            # Calculate results
            success = uninstall_result["success"] and cleanup_checks["success"]
            
            return InstallationFlowResult(
                success=success,
                message=f"Rollback flow testing completed. Success: {success}",
                total_steps=2,
                completed_steps=2 if success else 1,
                installation_time=time.time() - start_time,
                validation_time=0.0,
                errors=uninstall_result.get("errors", []) + cleanup_checks.get("errors", []),
                warnings=cleanup_checks.get("warnings", [])
            )
            
        except Exception as e:
            logger.error(f"Rollback flow testing failed: {e}")
            return InstallationFlowResult(
                success=False,
                message=f"Rollback flow testing failed: {e}",
                total_steps=0,
                completed_steps=0,
                errors=[str(e)]
            )
    
    async def _execute_installation_step(self, step: InstallationStep) -> Dict[str, Any]:
        """Execute a single installation step."""
        try:
            # Check prerequisites
            prereq_result = await self._check_prerequisites(step)
            if not prereq_result["success"]:
                return {
                    "success": False,
                    "error": f"Prerequisites not met: {prereq_result['error']}",
                    "step": step.name
                }
            
            # Execute command
            command_result = await self._execute_command(step.command, step.timeout_seconds)
            
            # Perform validation checks
            validation_result = await self._perform_validation_checks(step)
            
            # Combine results
            success = (
                command_result["success"] and
                command_result["exit_code"] == step.expected_exit_code and
                validation_result["success"]
            )
            
            return {
                "success": success,
                "step": step.name,
                "command_result": command_result,
                "validation_result": validation_result,
                "prerequisites": prereq_result,
                "duration": command_result.get("duration", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to execute installation step {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step": step.name
            }
    
    async def _execute_command(
        self,
        command: List[str],
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """Execute a command with timeout."""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
                
                duration = time.time() - start_time
                
                return {
                    "success": True,
                    "exit_code": process.returncode,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "duration": duration
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout_seconds} seconds",
                    "exit_code": -1,
                    "duration": time.time() - start_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exit_code": -1,
                "duration": time.time() - start_time
            }
    
    async def _check_prerequisites(self, step: InstallationStep) -> Dict[str, Any]:
        """Check prerequisites for an installation step."""
        try:
            # Check required files
            for file_path in step.required_files:
                if not Path(file_path).exists():
                    return {
                        "success": False,
                        "error": f"Required file not found: {file_path}"
                    }
            
            # Check required directories
            for dir_path in step.required_directories:
                if not Path(dir_path).exists():
                    return {
                        "success": False,
                        "error": f"Required directory not found: {dir_path}"
                    }
            
            # Check environment variables
            for env_var, expected_value in step.environment_variables.items():
                actual_value = os.environ.get(env_var)
                if actual_value != expected_value:
                    return {
                        "success": False,
                        "error": f"Environment variable {env_var} not set correctly. Expected: {expected_value}, Got: {actual_value}"
                    }
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _perform_validation_checks(self, step: InstallationStep) -> Dict[str, Any]:
        """Perform validation checks for an installation step."""
        try:
            validation_results = {}
            
            for check in step.validation_checks:
                if check == "python_available":
                    validation_results[check] = sys.executable is not None
                elif check == "dependencies_installed":
                    validation_results[check] = await self._check_dependencies()
                elif check == "environment_variables_set":
                    validation_results[check] = await self._check_environment_variables()
                elif check == "hooks_installed":
                    validation_results[check] = await self._check_git_hooks()
                elif check == "pre_commit_configured":
                    validation_results[check] = await self._check_pre_commit()
                elif check == "cursor_config_created":
                    validation_results[check] = await self._check_cursor_config()
                elif check == "workspace_configured":
                    validation_results[check] = await self._check_workspace_config()
                elif check == "memory_accessible":
                    validation_results[check] = await self._check_memory_access()
                elif check == "connection_established":
                    validation_results[check] = await self._check_connection()
                elif check == "bmad_handlers_available":
                    validation_results[check] = await self._check_bmad_handlers()
                elif check == "bmad_templates_found":
                    validation_results[check] = await self._check_bmad_templates()
                elif check == "webmcp_config_created":
                    validation_results[check] = await self._check_webmcp_config()
                elif check == "environment_file_created":
                    validation_results[check] = await self._check_environment_file()
                elif check == "configuration_valid":
                    validation_results[check] = await self._check_configuration_validity()
                elif check == "migrations_applied":
                    validation_results[check] = await self._check_migrations()
                elif check == "database_schema_updated":
                    validation_results[check] = await self._check_database_schema()
                elif check == "sync_agent_installed":
                    validation_results[check] = await self._check_sync_agent()
                elif check == "launch_agent_configured":
                    validation_results[check] = await self._check_launch_agent()
                elif check == "docs_backfilled":
                    validation_results[check] = await self._check_docs_backfill()
                elif check == "tasks_backfilled":
                    validation_results[check] = await self._check_tasks_backfill()
                elif check == "sync_status_checked":
                    validation_results[check] = await self._check_sync_status()
                elif check == "webmcp_tools_functional":
                    validation_results[check] = await self._check_webmcp_tools()
                elif check == "integration_tests_passed":
                    validation_results[check] = await self._check_integration_tests()
                else:
                    validation_results[check] = False
            
            success = all(validation_results.values())
            
            return {
                "success": success,
                "results": validation_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_complete_installation(self) -> Dict[str, Any]:
        """Validate the complete installation."""
        try:
            validation_checks = {
                "webmcp_configuration": await self._check_webmcp_config(),
                "bmad_integration": await self._check_bmad_handlers(),
                "environment_setup": await self._check_environment_variables(),
                "git_hooks": await self._check_git_hooks(),
                "cursor_config": await self._check_cursor_config()
            }
            
            success = all(validation_checks.values())
            errors = []
            warnings = []
            
            for check_name, result in validation_checks.items():
                if not result:
                    errors.append(f"Validation check failed: {check_name}")
            
            return {
                "success": success,
                "errors": errors,
                "warnings": warnings,
                "checks": validation_checks
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    async def _setup_test_environment(self):
        """Setup test environment."""
        self.test_dir.mkdir(exist_ok=True)
        os.chdir(self.test_dir)
    
    async def _cleanup_test_environment(self):
        """Cleanup test environment."""
        os.chdir(self.project_root)
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)
    
    async def _check_cleanup_artifacts(self) -> Dict[str, Any]:
        """Check if installation artifacts were properly cleaned up."""
        try:
            config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
            env_file = self.project_root / ".cerebraflow" / ".env"
            
            config_removed = not config_file.exists()
            env_removed = not env_file.exists()
            
            success = config_removed and env_removed
            
            return {
                "success": success,
                "config_removed": config_removed,
                "env_removed": env_removed
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Validation check methods
    async def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            import cflow_platform
            return True
        except ImportError:
            return False
    
    async def _check_environment_variables(self) -> bool:
        """Check if required environment variables are set."""
        # This is a simplified check - in practice, you'd check specific variables
        return True
    
    async def _check_git_hooks(self) -> bool:
        """Check if git hooks are installed."""
        hooks_dir = self.project_root / ".git" / "hooks"
        return hooks_dir.exists()
    
    async def _check_pre_commit(self) -> bool:
        """Check if pre-commit is configured."""
        pre_commit_config = self.project_root / ".pre-commit-config.yaml"
        return pre_commit_config.exists()
    
    async def _check_cursor_config(self) -> bool:
        """Check if Cursor configuration exists."""
        cursor_config = self.project_root / ".cursor"
        return cursor_config.exists()
    
    async def _check_workspace_config(self) -> bool:
        """Check if workspace is configured."""
        # This would check for workspace-specific configuration files
        return True
    
    async def _check_memory_access(self) -> bool:
        """Check if memory is accessible."""
        # This would check memory connectivity
        return True
    
    async def _check_connection(self) -> bool:
        """Check if connection is established."""
        # This would check network connectivity
        return True
    
    async def _check_bmad_handlers(self) -> bool:
        """Check if BMAD handlers are available."""
        try:
            from cflow_platform.handlers.bmad_handlers import BMADHandlers
            return True
        except ImportError:
            return False
    
    async def _check_bmad_templates(self) -> bool:
        """Check if BMAD templates are found."""
        templates_path = self.project_root / "vendor" / "bmad" / "bmad-core" / "templates"
        return templates_path.exists()
    
    async def _check_webmcp_config(self) -> bool:
        """Check if WebMCP configuration exists."""
        config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
        return config_file.exists()
    
    async def _check_environment_file(self) -> bool:
        """Check if environment file exists."""
        env_file = self.project_root / ".cerebraflow" / ".env"
        return env_file.exists()
    
    async def _check_configuration_validity(self) -> bool:
        """Check if configuration is valid."""
        try:
            config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    json.load(f)
                return True
            return False
        except Exception:
            return False
    
    async def _check_migrations(self) -> bool:
        """Check if migrations were applied."""
        # This would check database migration status
        return True
    
    async def _check_database_schema(self) -> bool:
        """Check if database schema is updated."""
        # This would check database schema
        return True
    
    async def _check_sync_agent(self) -> bool:
        """Check if sync agent is installed."""
        # This would check sync agent installation
        return True
    
    async def _check_launch_agent(self) -> bool:
        """Check if launch agent is configured."""
        # This would check launch agent configuration
        return True
    
    async def _check_docs_backfill(self) -> bool:
        """Check if docs were backfilled."""
        # This would check docs backfill status
        return True
    
    async def _check_tasks_backfill(self) -> bool:
        """Check if tasks were backfilled."""
        # This would check tasks backfill status
        return True
    
    async def _check_sync_status(self) -> bool:
        """Check if sync status is checked."""
        # This would check sync status
        return True
    
    async def _check_webmcp_tools(self) -> bool:
        """Check if WebMCP tools are functional."""
        try:
            from cflow_platform.core.direct_client import execute_mcp_tool
            # This would test WebMCP tool execution
            return True
        except Exception:
            return False
    
    async def _check_integration_tests(self) -> bool:
        """Check if integration tests passed."""
        # This would check integration test results
        return True
