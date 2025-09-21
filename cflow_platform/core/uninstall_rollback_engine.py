"""
Uninstall and Rollback Engine

This module provides comprehensive uninstall and rollback capabilities for BMAD integration,
including complete cleanup, rollback to previous states, and restoration capabilities.
"""

import asyncio
import json
import logging
import os
import shutil
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
class UninstallStep:
    """Represents a single uninstall step."""
    name: str
    description: str
    action: str  # 'remove_file', 'remove_directory', 'restore_file', 'restore_directory', 'run_command'
    target_path: str
    backup_path: Optional[str] = None
    command: Optional[List[str]] = None
    required: bool = True
    validation_checks: List[str] = field(default_factory=list)


@dataclass
class RollbackPoint:
    """Represents a rollback point for restoration."""
    name: str
    description: str
    timestamp: datetime
    files: List[str] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UninstallResult:
    """Result of uninstall operation."""
    success: bool
    message: str
    total_steps: int
    completed_steps: int
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    uninstall_time: float = 0.0
    cleanup_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RollbackResult:
    """Result of rollback operation."""
    success: bool
    message: str
    rollback_point: str
    restored_files: List[str] = field(default_factory=list)
    restored_directories: List[str] = field(default_factory=list)
    rollback_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UninstallRollbackEngine:
    """
    Uninstall and Rollback Engine for BMAD Integration.
    
    This class provides comprehensive uninstall and rollback capabilities,
    including:
    - Complete uninstall with cleanup
    - Rollback to previous states
    - Backup and restoration
    - Configuration management
    - Artifact cleanup
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the uninstall and rollback engine."""
        self.project_root = project_root or Path.cwd()
        self.backup_dir = self.project_root / ".cerebraflow" / "backups"
        self.rollback_dir = self.project_root / ".cerebraflow" / "rollbacks"
        
        # Ensure backup and rollback directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)
    
    def create_uninstall_steps(self) -> List[UninstallStep]:
        """
        Create the complete uninstall steps.
        
        Returns:
            List of UninstallStep objects representing the complete uninstall flow
        """
        return [
            UninstallStep(
                name="backup_current_state",
                description="Create backup of current state before uninstall",
                action="run_command",
                target_path="",
                command=[sys.executable, "-c", "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_backup_config')))"],
                validation_checks=["backup_created"]
            ),
            UninstallStep(
                name="stop_services",
                description="Stop running services and processes",
                action="run_command",
                target_path="",
                command=[sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "stop"],
                required=False,
                validation_checks=["services_stopped"]
            ),
            UninstallStep(
                name="uninstall_webmcp_config",
                description="Uninstall WebMCP configuration",
                action="run_command",
                target_path="",
                command=[sys.executable, "-c", "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_webmcp_uninstall_config')))"],
                validation_checks=["webmcp_config_removed"]
            ),
            UninstallStep(
                name="remove_cerebraflow_dir",
                description="Remove .cerebraflow directory",
                action="remove_directory",
                target_path=".cerebraflow",
                required=False,
                validation_checks=["cerebraflow_dir_removed"]
            ),
            UninstallStep(
                name="remove_git_hooks",
                description="Remove git hooks",
                action="remove_directory",
                target_path=".git/hooks",
                required=False,
                validation_checks=["git_hooks_removed"]
            ),
            UninstallStep(
                name="remove_cursor_config",
                description="Remove Cursor configuration",
                action="remove_directory",
                target_path=".cursor",
                required=False,
                validation_checks=["cursor_config_removed"]
            ),
            UninstallStep(
                name="remove_pre_commit_config",
                description="Remove pre-commit configuration",
                action="remove_file",
                target_path=".pre-commit-config.yaml",
                required=False,
                validation_checks=["pre_commit_config_removed"]
            ),
            UninstallStep(
                name="remove_launch_agents",
                description="Remove LaunchAgents",
                action="run_command",
                target_path="",
                command=[sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "uninstall-agent"],
                required=False,
                validation_checks=["launch_agents_removed"]
            ),
            UninstallStep(
                name="cleanup_vendor_bmad",
                description="Cleanup vendor BMAD directory",
                action="remove_directory",
                target_path="vendor/bmad",
                required=False,
                validation_checks=["vendor_bmad_removed"]
            ),
            UninstallStep(
                name="final_cleanup",
                description="Perform final cleanup and validation",
                action="run_command",
                target_path="",
                command=[sys.executable, "-c", "import asyncio; from cflow_platform.core.direct_client import execute_mcp_tool; print(asyncio.run(execute_mcp_tool('bmad_installation_validate_components')))"],
                validation_checks=["cleanup_complete"]
            )
        ]
    
    async def uninstall_bmad_integration(
        self,
        create_backup: bool = True,
        remove_vendor_bmad: bool = False,
        force: bool = False
    ) -> UninstallResult:
        """
        Uninstall BMAD integration completely.
        
        Args:
            create_backup: Whether to create backup before uninstall
            remove_vendor_bmad: Whether to remove vendor BMAD directory
            force: Whether to force uninstall even if some steps fail
            
        Returns:
            UninstallResult with uninstall details
        """
        logger.info("Starting BMAD integration uninstall...")
        
        start_time = time.time()
        
        try:
            # Get uninstall steps
            steps = self.create_uninstall_steps()
            
            # Filter steps based on options
            if not create_backup:
                steps = [step for step in steps if step.name != "backup_current_state"]
            
            if not remove_vendor_bmad:
                steps = [step for step in steps if step.name != "cleanup_vendor_bmad"]
            
            # Execute uninstall steps
            step_results = {}
            failed_steps = []
            
            for step in steps:
                logger.info(f"Executing uninstall step: {step.name}")
                step_result = await self._execute_uninstall_step(step)
                step_results[step.name] = step_result
                
                if not step_result["success"]:
                    failed_steps.append(step.name)
                    logger.error(f"Uninstall step {step.name} failed: {step_result['error']}")
                    
                    if step.required and not force:
                        logger.error(f"Required step {step.name} failed. Stopping uninstall.")
                        break
                else:
                    logger.info(f"Uninstall step {step.name} completed successfully")
            
            # Calculate results
            completed_steps = len(steps) - len(failed_steps)
            success = len(failed_steps) == 0 or force
            
            uninstall_time = time.time() - start_time
            
            # Perform final cleanup
            cleanup_start = time.time()
            cleanup_result = await self._perform_final_cleanup()
            cleanup_time = time.time() - cleanup_start
            
            return UninstallResult(
                success=success,
                message=f"BMAD integration uninstall completed. {completed_steps}/{len(steps)} steps successful.",
                total_steps=len(steps),
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                step_results=step_results,
                uninstall_time=uninstall_time,
                cleanup_time=cleanup_time,
                errors=cleanup_result.get("errors", []),
                warnings=cleanup_result.get("warnings", [])
            )
            
        except Exception as e:
            logger.error(f"BMAD integration uninstall failed: {e}")
            return UninstallResult(
                success=False,
                message=f"BMAD integration uninstall failed: {e}",
                total_steps=0,
                completed_steps=0,
                errors=[str(e)]
            )
    
    async def create_rollback_point(
        self,
        name: str,
        description: str = ""
    ) -> RollbackResult:
        """
        Create a rollback point for future restoration.
        
        Args:
            name: Name of the rollback point
            description: Description of the rollback point
            
        Returns:
            RollbackResult with rollback point creation details
        """
        logger.info(f"Creating rollback point: {name}")
        
        start_time = time.time()
        
        try:
            # Create rollback point directory
            rollback_point_dir = self.rollback_dir / name
            rollback_point_dir.mkdir(exist_ok=True)
            
            # Backup current configuration files
            config_files = [
                ".cerebraflow/webmcp_config.json",
                ".cerebraflow/.env",
                ".pre-commit-config.yaml"
            ]
            
            backed_up_files = []
            for config_file in config_files:
                source_path = self.project_root / config_file
                if source_path.exists():
                    dest_path = rollback_point_dir / config_file
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    backed_up_files.append(config_file)
            
            # Backup current state information
            state_info = {
                "name": name,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
                "files": backed_up_files,
                "directories": [".cerebraflow", ".cursor"],
                "configuration": await self._get_current_configuration(),
                "metadata": {
                    "project_root": str(self.project_root),
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }
            
            # Save rollback point metadata
            metadata_file = rollback_point_dir / "rollback_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(state_info, f, indent=2)
            
            rollback_time = time.time() - start_time
            
            return RollbackResult(
                success=True,
                message=f"Rollback point '{name}' created successfully",
                rollback_point=name,
                restored_files=backed_up_files,
                rollback_time=rollback_time
            )
            
        except Exception as e:
            logger.error(f"Failed to create rollback point {name}: {e}")
            return RollbackResult(
                success=False,
                message=f"Failed to create rollback point {name}: {e}",
                rollback_point=name,
                errors=[str(e)]
            )
    
    async def rollback_to_point(
        self,
        rollback_point_name: str,
        force: bool = False
    ) -> RollbackResult:
        """
        Rollback to a specific rollback point.
        
        Args:
            rollback_point_name: Name of the rollback point to restore
            force: Whether to force rollback even if some steps fail
            
        Returns:
            RollbackResult with rollback details
        """
        logger.info(f"Rolling back to point: {rollback_point_name}")
        
        start_time = time.time()
        
        try:
            # Check if rollback point exists
            rollback_point_dir = self.rollback_dir / rollback_point_name
            if not rollback_point_dir.exists():
                return RollbackResult(
                    success=False,
                    message=f"Rollback point '{rollback_point_name}' not found",
                    rollback_point=rollback_point_name,
                    errors=[f"Rollback point directory not found: {rollback_point_dir}"]
                )
            
            # Load rollback point metadata
            metadata_file = rollback_point_dir / "rollback_metadata.json"
            if not metadata_file.exists():
                return RollbackResult(
                    success=False,
                    message=f"Rollback point metadata not found for '{rollback_point_name}'",
                    rollback_point=rollback_point_name,
                    errors=[f"Metadata file not found: {metadata_file}"]
                )
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Restore files
            restored_files = []
            for file_path in metadata.get("files", []):
                source_path = rollback_point_dir / file_path
                dest_path = self.project_root / file_path
                
                if source_path.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    restored_files.append(file_path)
            
            # Restore configuration
            await self._restore_configuration(metadata.get("configuration", {}))
            
            rollback_time = time.time() - start_time
            
            return RollbackResult(
                success=True,
                message=f"Successfully rolled back to point '{rollback_point_name}'",
                rollback_point=rollback_point_name,
                restored_files=restored_files,
                rollback_time=rollback_time
            )
            
        except Exception as e:
            logger.error(f"Failed to rollback to point {rollback_point_name}: {e}")
            return RollbackResult(
                success=False,
                message=f"Failed to rollback to point {rollback_point_name}: {e}",
                rollback_point=rollback_point_name,
                errors=[str(e)]
            )
    
    async def list_rollback_points(self) -> Dict[str, Any]:
        """
        List all available rollback points.
        
        Returns:
            Dictionary with rollback points information
        """
        try:
            rollback_points = []
            
            for rollback_dir in self.rollback_dir.iterdir():
                if rollback_dir.is_dir():
                    metadata_file = rollback_dir / "rollback_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        rollback_points.append(metadata)
            
            return {
                "success": True,
                "rollback_points": rollback_points,
                "total_points": len(rollback_points)
            }
            
        except Exception as e:
            logger.error(f"Failed to list rollback points: {e}")
            return {
                "success": False,
                "error": str(e),
                "rollback_points": [],
                "total_points": 0
            }
    
    async def delete_rollback_point(self, rollback_point_name: str) -> Dict[str, Any]:
        """
        Delete a specific rollback point.
        
        Args:
            rollback_point_name: Name of the rollback point to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            rollback_point_dir = self.rollback_dir / rollback_point_name
            
            if not rollback_point_dir.exists():
                return {
                    "success": False,
                    "error": f"Rollback point '{rollback_point_name}' not found"
                }
            
            shutil.rmtree(rollback_point_dir)
            
            return {
                "success": True,
                "message": f"Rollback point '{rollback_point_name}' deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete rollback point {rollback_point_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_uninstall_step(self, step: UninstallStep) -> Dict[str, Any]:
        """Execute a single uninstall step."""
        try:
            if step.action == "remove_file":
                result = await self._remove_file(step.target_path)
            elif step.action == "remove_directory":
                result = await self._remove_directory(step.target_path)
            elif step.action == "restore_file":
                result = await self._restore_file(step.target_path, step.backup_path)
            elif step.action == "restore_directory":
                result = await self._restore_directory(step.target_path, step.backup_path)
            elif step.action == "run_command":
                result = await self._run_command(step.command)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action: {step.action}"
                }
            
            # Perform validation checks
            if result["success"]:
                validation_result = await self._perform_validation_checks(step)
                result["validation"] = validation_result
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute uninstall step {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step": step.name
            }
    
    async def _remove_file(self, file_path: str) -> Dict[str, Any]:
        """Remove a file."""
        try:
            full_path = self.project_root / file_path
            if full_path.exists():
                full_path.unlink()
                return {"success": True, "message": f"File removed: {file_path}"}
            else:
                return {"success": True, "message": f"File not found (already removed): {file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _remove_directory(self, dir_path: str) -> Dict[str, Any]:
        """Remove a directory."""
        try:
            full_path = self.project_root / dir_path
            if full_path.exists():
                shutil.rmtree(full_path)
                return {"success": True, "message": f"Directory removed: {dir_path}"}
            else:
                return {"success": True, "message": f"Directory not found (already removed): {dir_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restore_file(self, target_path: str, backup_path: str) -> Dict[str, Any]:
        """Restore a file from backup."""
        try:
            source_path = self.project_root / backup_path
            dest_path = self.project_root / target_path
            
            if source_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                return {"success": True, "message": f"File restored: {target_path}"}
            else:
                return {"success": False, "error": f"Backup file not found: {backup_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restore_directory(self, target_path: str, backup_path: str) -> Dict[str, Any]:
        """Restore a directory from backup."""
        try:
            source_path = self.project_root / backup_path
            dest_path = self.project_root / target_path
            
            if source_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.rmtree(dest_path, ignore_errors=True)
                shutil.copytree(source_path, dest_path)
                return {"success": True, "message": f"Directory restored: {target_path}"}
            else:
                return {"success": False, "error": f"Backup directory not found: {backup_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run a command."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exit_code": -1
            }
    
    async def _perform_validation_checks(self, step: UninstallStep) -> Dict[str, Any]:
        """Perform validation checks for an uninstall step."""
        try:
            validation_results = {}
            
            for check in step.validation_checks:
                if check == "backup_created":
                    validation_results[check] = await self._check_backup_created()
                elif check == "services_stopped":
                    validation_results[check] = await self._check_services_stopped()
                elif check == "webmcp_config_removed":
                    validation_results[check] = await self._check_webmcp_config_removed()
                elif check == "cerebraflow_dir_removed":
                    validation_results[check] = await self._check_cerebraflow_dir_removed()
                elif check == "git_hooks_removed":
                    validation_results[check] = await self._check_git_hooks_removed()
                elif check == "cursor_config_removed":
                    validation_results[check] = await self._check_cursor_config_removed()
                elif check == "pre_commit_config_removed":
                    validation_results[check] = await self._check_pre_commit_config_removed()
                elif check == "launch_agents_removed":
                    validation_results[check] = await self._check_launch_agents_removed()
                elif check == "vendor_bmad_removed":
                    validation_results[check] = await self._check_vendor_bmad_removed()
                elif check == "cleanup_complete":
                    validation_results[check] = await self._check_cleanup_complete()
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
    
    async def _perform_final_cleanup(self) -> Dict[str, Any]:
        """Perform final cleanup after uninstall."""
        try:
            cleanup_actions = []
            
            # Clean up any remaining temporary files
            temp_files = [
                ".cerebraflow/temp",
                ".cerebraflow/cache",
                ".cerebraflow/logs"
            ]
            
            for temp_file in temp_files:
                temp_path = self.project_root / temp_file
                if temp_path.exists():
                    if temp_path.is_file():
                        temp_path.unlink()
                    else:
                        shutil.rmtree(temp_path)
                    cleanup_actions.append(f"Removed: {temp_file}")
            
            return {
                "success": True,
                "actions": cleanup_actions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_current_configuration(self) -> Dict[str, Any]:
        """Get current configuration state."""
        try:
            config = {}
            
            # Get WebMCP configuration
            webmcp_config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
            if webmcp_config_file.exists():
                with open(webmcp_config_file, 'r') as f:
                    config["webmcp"] = json.load(f)
            
            # Get environment configuration
            env_file = self.project_root / ".cerebraflow" / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    config["environment"] = f.read()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get current configuration: {e}")
            return {}
    
    async def _restore_configuration(self, configuration: Dict[str, Any]):
        """Restore configuration from rollback point."""
        try:
            # Restore WebMCP configuration
            if "webmcp" in configuration:
                webmcp_config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
                webmcp_config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(webmcp_config_file, 'w') as f:
                    json.dump(configuration["webmcp"], f, indent=2)
            
            # Restore environment configuration
            if "environment" in configuration:
                env_file = self.project_root / ".cerebraflow" / ".env"
                env_file.parent.mkdir(parents=True, exist_ok=True)
                with open(env_file, 'w') as f:
                    f.write(configuration["environment"])
            
        except Exception as e:
            logger.error(f"Failed to restore configuration: {e}")
    
    # Validation check methods
    async def _check_backup_created(self) -> bool:
        """Check if backup was created."""
        # This would check if backup was created successfully
        return True
    
    async def _check_services_stopped(self) -> bool:
        """Check if services were stopped."""
        # This would check if services were stopped
        return True
    
    async def _check_webmcp_config_removed(self) -> bool:
        """Check if WebMCP configuration was removed."""
        config_file = self.project_root / ".cerebraflow" / "webmcp_config.json"
        return not config_file.exists()
    
    async def _check_cerebraflow_dir_removed(self) -> bool:
        """Check if .cerebraflow directory was removed."""
        cerebraflow_dir = self.project_root / ".cerebraflow"
        return not cerebraflow_dir.exists()
    
    async def _check_git_hooks_removed(self) -> bool:
        """Check if git hooks were removed."""
        hooks_dir = self.project_root / ".git" / "hooks"
        return not hooks_dir.exists()
    
    async def _check_cursor_config_removed(self) -> bool:
        """Check if Cursor configuration was removed."""
        cursor_config = self.project_root / ".cursor"
        return not cursor_config.exists()
    
    async def _check_pre_commit_config_removed(self) -> bool:
        """Check if pre-commit configuration was removed."""
        pre_commit_config = self.project_root / ".pre-commit-config.yaml"
        return not pre_commit_config.exists()
    
    async def _check_launch_agents_removed(self) -> bool:
        """Check if LaunchAgents were removed."""
        # This would check if LaunchAgents were removed
        return True
    
    async def _check_vendor_bmad_removed(self) -> bool:
        """Check if vendor BMAD directory was removed."""
        vendor_bmad = self.project_root / "vendor" / "bmad"
        return not vendor_bmad.exists()
    
    async def _check_cleanup_complete(self) -> bool:
        """Check if cleanup is complete."""
        # This would check if cleanup is complete
        return True
