"""
Vendor BMAD Integration for BMAD API Service

This module provides integration with vendor BMAD workflows,
handling workflow execution and result processing.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class VendorBMADIntegration:
    """
    Integration with vendor BMAD workflows.
    
    This class handles execution of vendor BMAD workflows
    and processing of results.
    """
    
    def __init__(self):
        """Initialize the vendor BMAD integration."""
        self.vendor_bmad_path = os.getenv("VENDOR_BMAD_PATH", "/app/vendor/bmad")
        self.workflow_engine_path = os.path.join(self.vendor_bmad_path, "bmad-core", "workflows")
        self.template_path = os.path.join(self.vendor_bmad_path, "templates")
        self.expansion_pack_path = os.path.join(self.vendor_bmad_path, "expansion-packs")
        
        self._stats = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "total_execution_time": 0.0
        }
    
    async def execute_workflow(self, workflow_path: str, arguments: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a vendor BMAD workflow.
        
        Args:
            workflow_path: Path to the workflow YAML file
            arguments: Workflow arguments
            user_context: User context for execution
            
        Returns:
            Workflow execution result
            
        Raises:
            Exception: If workflow execution fails
        """
        try:
            logger.info(f"Executing vendor BMAD workflow: {workflow_path}")
            
            # Resolve workflow path
            full_workflow_path = self._resolve_workflow_path(workflow_path)
            
            # Validate workflow exists
            if not os.path.exists(full_workflow_path):
                raise Exception(f"Workflow not found: {full_workflow_path}")
            
            # Load workflow definition
            workflow_def = self._load_workflow_definition(full_workflow_path)
            
            # Prepare execution context
            execution_context = {
                "workflow_path": full_workflow_path,
                "arguments": arguments,
                "user_context": user_context,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Execute workflow
            result = await self._execute_workflow_definition(workflow_def, execution_context)
            
            # Update statistics
            self._stats["workflows_executed"] += 1
            self._stats["workflows_successful"] += 1
            
            logger.info(f"Vendor BMAD workflow executed successfully: {workflow_path}")
            return result
            
        except Exception as e:
            self._stats["workflows_executed"] += 1
            self._stats["workflows_failed"] += 1
            
            logger.error(f"Vendor BMAD workflow execution failed: {workflow_path} - {e}")
            raise
    
    def _resolve_workflow_path(self, workflow_path: str) -> str:
        """
        Resolve workflow path to full file path.
        
        Args:
            workflow_path: Relative workflow path
            
        Returns:
            Full file path
        """
        if workflow_path.startswith("vendor/bmad/"):
            # Remove vendor/bmad/ prefix and resolve
            relative_path = workflow_path[12:]  # Remove "vendor/bmad/"
            return os.path.join(self.vendor_bmad_path, relative_path)
        else:
            # Assume it's already a full path
            return workflow_path
    
    def _load_workflow_definition(self, workflow_path: str) -> Dict[str, Any]:
        """
        Load workflow definition from YAML file.
        
        Args:
            workflow_path: Path to workflow YAML file
            
        Returns:
            Workflow definition dictionary
        """
        try:
            with open(workflow_path, 'r') as f:
                workflow_def = yaml.safe_load(f)
            
            logger.debug(f"Loaded workflow definition from: {workflow_path}")
            return workflow_def
            
        except Exception as e:
            logger.error(f"Failed to load workflow definition: {workflow_path} - {e}")
            raise
    
    async def _execute_workflow_definition(self, workflow_def: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow definition.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            Workflow execution result
        """
        try:
            # For now, simulate workflow execution
            # In a real implementation, this would execute the actual BMAD workflow
            
            workflow_name = workflow_def.get("name", "Unknown Workflow")
            workflow_version = workflow_def.get("version", "1.0.0")
            
            # Simulate workflow execution
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Generate mock result based on workflow type
            result = self._generate_mock_result(workflow_def, execution_context)
            
            return {
                "workflow_name": workflow_name,
                "workflow_version": workflow_version,
                "execution_context": execution_context,
                "result": result,
                "success": True,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Workflow definition execution failed: {e}")
            raise
    
    def _generate_mock_result(self, workflow_def: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock result for workflow execution.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            Mock result dictionary
        """
        workflow_name = workflow_def.get("name", "Unknown Workflow")
        arguments = execution_context.get("arguments", {})
        
        # Generate different results based on workflow type
        if "prd" in workflow_name.lower():
            return {
                "document_type": "PRD",
                "document_id": f"prd_{asyncio.get_event_loop().time()}",
                "content": f"Generated PRD for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed"
            }
        elif "arch" in workflow_name.lower():
            return {
                "document_type": "Architecture",
                "document_id": f"arch_{asyncio.get_event_loop().time()}",
                "content": f"Generated Architecture for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed"
            }
        elif "story" in workflow_name.lower():
            return {
                "document_type": "Story",
                "document_id": f"story_{asyncio.get_event_loop().time()}",
                "content": f"Generated Story for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed"
            }
        elif "test" in workflow_name.lower():
            return {
                "test_type": "Workflow Test",
                "test_id": f"test_{asyncio.get_event_loop().time()}",
                "results": {
                    "passed": 5,
                    "failed": 0,
                    "skipped": 0,
                    "total": 5
                },
                "status": "completed"
            }
        else:
            return {
                "workflow_type": "Generic",
                "workflow_id": f"workflow_{asyncio.get_event_loop().time()}",
                "message": f"Executed workflow: {workflow_name}",
                "status": "completed"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of vendor BMAD integration.
        
        Returns:
            Health check result
        """
        try:
            # Check if vendor BMAD path exists
            vendor_path_exists = os.path.exists(self.vendor_bmad_path)
            workflow_path_exists = os.path.exists(self.workflow_engine_path)
            template_path_exists = os.path.exists(self.template_path)
            
            # Check if we can list workflows
            workflows_available = 0
            if workflow_path_exists:
                try:
                    workflow_files = [f for f in os.listdir(self.workflow_engine_path) if f.endswith('.yaml')]
                    workflows_available = len(workflow_files)
                except Exception:
                    workflows_available = 0
            
            return {
                "healthy": vendor_path_exists and workflow_path_exists,
                "vendor_bmad_path": self.vendor_bmad_path,
                "vendor_path_exists": vendor_path_exists,
                "workflow_path_exists": workflow_path_exists,
                "template_path_exists": template_path_exists,
                "workflows_available": workflows_available,
                "stats": self.get_stats()
            }
            
        except Exception as e:
            logger.error(f"Vendor BMAD health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "vendor_bmad_path": self.vendor_bmad_path
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vendor BMAD integration statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self._stats.copy()
        
        if stats["workflows_executed"] > 0:
            stats["success_rate"] = stats["workflows_successful"] / stats["workflows_executed"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["workflows_executed"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset vendor BMAD integration statistics."""
        self._stats = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "total_execution_time": 0.0
        }
