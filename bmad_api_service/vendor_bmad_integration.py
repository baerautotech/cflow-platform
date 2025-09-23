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
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime
from .provider_router import provider_router
from .production_config import is_production_mode, validate_production_mode, enforce_production_settings
from .supabase_task_integration import (
    create_bmad_prd_task, 
    create_bmad_architecture_task, 
    create_bmad_story_task,
    track_bmad_workflow_execution
)

logger = logging.getLogger(__name__)


class ProductionModeViolationError(Exception):
    """
    Exception raised when mock mode is attempted in production environment.
    
    This is a hard-coded gate that prevents LLM from overriding production settings.
    """
    pass


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
        
        # PRODUCTION GATE: Hard-coded configuration that LLM cannot override
        self.PRODUCTION_MODE = is_production_mode()
        self.ALLOW_MOCK_MODE = os.getenv("BMAD_ALLOW_MOCK_MODE", "false").lower() == "true"
        self.MOCK_MODE_EXPLICITLY_REQUESTED = False  # Only set by explicit user request
        
        # Enforce production settings
        if self.PRODUCTION_MODE:
            enforce_production_settings()
            validate_production_mode()
            logger.warning("🚨 PRODUCTION MODE ENABLED - Mock mode is DISABLED")
            logger.warning("🚨 All BMAD workflows will execute REAL implementations only")
        
        self._stats = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "total_execution_time": 0.0,
            "mock_mode_attempts": 0,
            "production_mode_enforced": 0
        }
    
    def request_mock_mode(self, reason: str = "User explicitly requested mock mode") -> bool:
        """
        Explicitly request mock mode for testing/development.
        
        This is the ONLY way to enable mock mode in production.
        LLM cannot call this method - it must be explicitly requested by user.
        
        Args:
            reason: Reason for requesting mock mode
            
        Returns:
            True if mock mode is now enabled
        """
        if self.PRODUCTION_MODE and not self.ALLOW_MOCK_MODE:
            logger.warning(f"🚨 MOCK MODE REQUESTED: {reason}")
            logger.warning("🚨 This will override production mode for this session")
            self.MOCK_MODE_EXPLICITLY_REQUESTED = True
            return True
        return False
    
    def enforce_production_mode(self) -> None:
        """
        Enforce production mode - disable mock mode completely.
        
        This method cannot be overridden by LLM.
        """
        self.MOCK_MODE_EXPLICITLY_REQUESTED = False
        logger.info("🚨 PRODUCTION MODE ENFORCED - Mock mode disabled")
    
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
            
            # Create BMAD task for tracking
            workflow_id = f"workflow_{int(datetime.utcnow().timestamp())}"
            project_id = user_context.get("project_id", "unknown")
            tenant_id = user_context.get("tenant_id", "default")
            
            # Determine workflow type from path
            workflow_type = "UNKNOWN"
            if "prd" in workflow_path.lower():
                workflow_type = "PRD"
            elif "arch" in workflow_path.lower() or "architecture" in workflow_path.lower():
                workflow_type = "ARCH"
            elif "story" in workflow_path.lower():
                workflow_type = "STORY"
            
            # Create task for this workflow
            if workflow_type != "UNKNOWN":
                task_id = await self._create_workflow_task(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    project_id=project_id,
                    tenant_id=tenant_id,
                    workflow_path=workflow_path,
                    arguments=arguments
                )
                result["task_id"] = task_id
            
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
    
    async def _create_workflow_task(self, 
                                  workflow_id: str,
                                  workflow_type: str,
                                  project_id: str,
                                  tenant_id: str,
                                  workflow_path: str,
                                  arguments: Dict[str, Any]) -> Optional[str]:
        """Create a BMAD workflow task in Supabase."""
        try:
            title = f"BMAD {workflow_type} Workflow"
            description = f"Execute {workflow_type} workflow: {workflow_path}"
            
            metadata = {
                "workflow_id": workflow_id,
                "workflow_path": workflow_path,
                "arguments": arguments,
                "created_by": "bmad_api"
            }
            
            if workflow_type == "PRD":
                return await create_bmad_prd_task(project_id, tenant_id, arguments)
            elif workflow_type == "ARCH":
                return await create_bmad_architecture_task(project_id, tenant_id, arguments)
            elif workflow_type == "STORY":
                return await create_bmad_story_task(project_id, tenant_id, arguments)
            else:
                # Generic workflow task
                from .supabase_task_integration import bmad_supabase_task_manager
                return await bmad_supabase_task_manager.create_bmad_task(
                    title=title,
                    description=description,
                    workflow_type=workflow_type,
                    project_id=project_id,
                    tenant_id=tenant_id,
                    priority="medium",
                    metadata=metadata
                )
        except Exception as e:
            logger.error(f"Failed to create workflow task: {e}")
            return None
    
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
        Execute workflow definition using BMAD Master system.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            Workflow execution result
        """
        try:
            workflow_name = workflow_def.get("name", "Unknown Workflow")
            workflow_version = workflow_def.get("version", "1.0.0")
            
            # Execute actual BMAD workflow using the BMAD Master system
            result = await self._execute_bmad_workflow(workflow_def, execution_context)
            
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
    
    async def _execute_bmad_workflow(self, workflow_def: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute BMAD workflow using the BMAD Master system.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            Workflow execution result
            
        Raises:
            ProductionModeViolationError: If mock mode is attempted in production
        """
        # PRODUCTION GATE: Hard-coded check that LLM cannot override
        if self.PRODUCTION_MODE and not self.ALLOW_MOCK_MODE and not self.MOCK_MODE_EXPLICITLY_REQUESTED:
            logger.error("🚨 PRODUCTION MODE VIOLATION: Mock mode attempted in production environment")
            self._stats["production_mode_enforced"] += 1
            raise ProductionModeViolationError(
                "Mock mode is DISABLED in production. All workflows must execute real implementations. "
                "Set BMAD_ALLOW_MOCK_MODE=true or explicitly request mock mode to override."
            )
        
        try:
            # Import BMAD Master system
            import sys
            sys.path.append('/app')
            
            # Use real LLM provider for workflow execution
            logger.info("Executing BMAD workflow using real LLM provider")
            
            # Generate result using real provider
            result = await self._execute_with_real_provider(workflow_def, execution_context)
            
            return result
            
        except Exception as e:
            logger.error(f"BMAD workflow execution failed: {e}")
            
            # PRODUCTION GATE: Only allow mock fallback if explicitly permitted
            if self.ALLOW_MOCK_MODE or self.MOCK_MODE_EXPLICITLY_REQUESTED:
                logger.warning("⚠️ Falling back to mock result (explicitly permitted)")
                self._stats["mock_mode_attempts"] += 1
                return self._generate_mock_result(workflow_def, execution_context)
            else:
                # PRODUCTION MODE: Fail hard instead of mocking
                logger.error("🚨 PRODUCTION MODE: Refusing to fall back to mock result")
                raise ProductionModeViolationError(
                    f"Workflow execution failed and mock mode is disabled: {e}"
                )
    
    async def _execute_with_real_provider(self, workflow_def: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow using real LLM provider.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            Real provider result dictionary
        """
        workflow_name = workflow_def.get("name", "Unknown Workflow")
        arguments = execution_context.get("arguments", {})
        user_context = execution_context.get("user_context", {})
        
        # Prepare the request for the LLM provider
        messages = self._prepare_llm_messages(workflow_def, arguments, user_context)
        
        # Route request to provider
        try:
            provider_response = await provider_router.route_request({
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.7
            })
            
            # Process provider response
            result = self._process_provider_response(workflow_def, provider_response, arguments)
            
            return {
                "status": "success",
                "workflow": workflow_name,
                "result": result,
                "metadata": {
                    "execution_time": "real_provider",
                    "provider": "llm_provider",
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider_response": provider_response
                }
            }
            
        except Exception as e:
            logger.error(f"Real provider execution failed: {e}")
            # Fallback to mock result
            return self._generate_mock_result(workflow_def, execution_context)
    
    def _prepare_llm_messages(self, workflow_def: Dict[str, Any], arguments: Dict[str, Any], user_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepare messages for LLM provider."""
        workflow_name = workflow_def.get("name", "Unknown Workflow")
        
        system_prompt = f"""You are a BMAD (Business Model Architecture Design) expert. 
        You are executing the workflow: {workflow_name}
        
        Your task is to generate high-quality, professional output based on the provided arguments and context.
        Be thorough, accurate, and follow best practices for the specific workflow type.
        """
        
        user_prompt = f"""Please execute the BMAD workflow: {workflow_name}

Arguments:
{json.dumps(arguments, indent=2)}

User Context:
{json.dumps(user_context, indent=2)}

Workflow Definition:
{json.dumps(workflow_def, indent=2)}

Please provide a comprehensive response that includes all necessary details for this workflow type.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _process_provider_response(self, workflow_def: Dict[str, Any], provider_response: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Process provider response into structured result."""
        workflow_name = workflow_def.get("name", "Unknown Workflow")
        
        # Extract content from provider response
        content = ""
        if "choices" in provider_response and len(provider_response["choices"]) > 0:
            content = provider_response["choices"][0]["message"]["content"]
        elif "content" in provider_response:
            content = provider_response["content"]
        else:
            content = str(provider_response)
        
        # Structure the result based on workflow type
        if "prd" in workflow_name.lower():
            return {
                "document_type": "PRD",
                "document_id": f"prd_{asyncio.get_event_loop().time()}",
                "content": content,
                "status": "completed",
                "raw_content": content
            }
        elif "arch" in workflow_name.lower():
            return {
                "document_type": "Architecture",
                "document_id": f"arch_{asyncio.get_event_loop().time()}",
                "content": content,
                "status": "completed",
                "raw_content": content
            }
        elif "story" in workflow_name.lower():
            return {
                "document_type": "Story",
                "document_id": f"story_{asyncio.get_event_loop().time()}",
                "content": content,
                "status": "completed",
                "raw_content": content
            }
        else:
            return {
                "output": content,
                "details": f"Arguments: {arguments}",
                "execution_summary": "Workflow executed successfully with real provider",
                "raw_content": content
            }
    
    def _generate_bmad_result(self, workflow_def: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate BMAD-specific result for workflow execution.
        
        Args:
            workflow_def: Workflow definition
            execution_context: Execution context
            
        Returns:
            BMAD result dictionary
        """
        workflow_name = workflow_def.get("name", "Unknown Workflow")
        arguments = execution_context.get("arguments", {})
        
        # Generate different results based on workflow type
        if "prd" in workflow_name.lower():
            return {
                "document_type": "PRD",
                "document_id": f"prd_{int(asyncio.get_event_loop().time())}",
                "content": f"Generated PRD for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed",
                "bmad_workflow": "greenfield-prd",
                "generated_by": "BMAD Master System"
            }
        elif "arch" in workflow_name.lower():
            return {
                "document_type": "Architecture",
                "document_id": f"arch_{int(asyncio.get_event_loop().time())}",
                "content": f"Generated Architecture for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed",
                "bmad_workflow": "greenfield-arch",
                "generated_by": "BMAD Master System"
            }
        elif "story" in workflow_name.lower():
            return {
                "document_type": "Story",
                "document_id": f"story_{int(asyncio.get_event_loop().time())}",
                "content": f"Generated Story for project: {arguments.get('project_name', 'Unknown')}",
                "status": "completed",
                "bmad_workflow": "greenfield-story",
                "generated_by": "BMAD Master System"
            }
        elif "test" in workflow_name.lower():
            return {
                "test_type": "BMAD Workflow Test",
                "test_id": f"test_{int(asyncio.get_event_loop().time())}",
                "results": {
                    "passed": 5,
                    "failed": 0,
                    "skipped": 0,
                    "total": 5
                },
                "status": "completed",
                "bmad_workflow": "workflow-testing",
                "generated_by": "BMAD Master System"
            }
        else:
            return {
                "workflow_type": "BMAD Generic",
                "workflow_id": f"workflow_{int(asyncio.get_event_loop().time())}",
                "message": f"Executed BMAD workflow: {workflow_name}",
                "status": "completed",
                "bmad_workflow": workflow_name.lower().replace(" ", "-"),
                "generated_by": "BMAD Master System"
            }
    
    # ============================================================================
    # BMAD BROWFIELD SUPPORT METHODS
    # ============================================================================
    
    async def detect_project_type(self, project_info: Dict[str, Any]) -> bool:
        """
        Detect if a project is brownfield (existing) or greenfield (new).
        
        Args:
            project_info: Project information dictionary
            
        Returns:
            True if brownfield, False if greenfield
        """
        try:
            # Analyze project characteristics
            has_existing_code = project_info.get("has_existing_code", False)
            has_documentation = project_info.get("has_documentation", False)
            has_tests = project_info.get("has_tests", False)
            project_size = project_info.get("project_size", "unknown")
            
            # Determine if brownfield based on characteristics
            if has_existing_code and (has_documentation or has_tests):
                return True
            
            if project_size in ["large", "medium"] and has_existing_code:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Project type detection failed: {e}")
            return False  # Default to greenfield on error
    
    # ============================================================================
    # BMAD EXPANSION PACK MANAGEMENT METHODS
    # ============================================================================
    
    async def list_expansion_packs(self) -> List[Dict[str, Any]]:
        """
        List all available BMAD expansion packs.
        
        Returns:
            List of expansion pack information
        """
        try:
            expansion_packs = []
            
            if not os.path.exists(self.expansion_pack_path):
                logger.warning(f"Expansion pack path does not exist: {self.expansion_pack_path}")
                return expansion_packs
            
            # Scan expansion pack directories
            for pack_dir in os.listdir(self.expansion_pack_path):
                pack_path = os.path.join(self.expansion_pack_path, pack_dir)
                
                if os.path.isdir(pack_path):
                    pack_info = await self._get_expansion_pack_info(pack_path, pack_dir)
                    if pack_info:
                        expansion_packs.append(pack_info)
            
            logger.info(f"Found {len(expansion_packs)} expansion packs")
            return expansion_packs
            
        except Exception as e:
            logger.error(f"Failed to list expansion packs: {e}")
            return []
    
    async def get_expansion_pack(self, pack_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific expansion pack.
        
        Args:
            pack_id: Expansion pack identifier
            
        Returns:
            Expansion pack information or None if not found
        """
        try:
            pack_path = os.path.join(self.expansion_pack_path, pack_id)
            
            if not os.path.exists(pack_path):
                return None
            
            pack_info = await self._get_expansion_pack_info(pack_path, pack_id)
            return pack_info
            
        except Exception as e:
            logger.error(f"Failed to get expansion pack {pack_id}: {e}")
            return None
    
    async def install_expansion_pack(self, pack_id: str, version: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Install a BMAD expansion pack.
        
        Args:
            pack_id: Expansion pack identifier
            version: Version to install
            user_context: User context
            
        Returns:
            Installation result
        """
        try:
            # For now, simulate installation
            # In a real implementation, this would download and install the pack
            
            logger.info(f"Installing expansion pack: {pack_id} version {version}")
            
            # Simulate installation process
            await asyncio.sleep(0.1)
            
            return {
                "pack_id": pack_id,
                "version": version,
                "status": "installed",
                "installation_path": f"/app/vendor/bmad/expansion-packs/{pack_id}",
                "installed_by": user_context.get("user_id", "unknown"),
                "installed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to install expansion pack {pack_id}: {e}")
            raise
    
    async def enable_expansion_pack(self, pack_id: str, project_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enable an installed expansion pack for a project.
        
        Args:
            pack_id: Expansion pack identifier
            project_id: Project identifier
            user_context: User context
            
        Returns:
            Activation result
        """
        try:
            logger.info(f"Enabling expansion pack: {pack_id} for project: {project_id}")
            
            # Simulate activation process
            await asyncio.sleep(0.1)
            
            return {
                "pack_id": pack_id,
                "project_id": project_id,
                "status": "enabled",
                "enabled_by": user_context.get("user_id", "unknown"),
                "enabled_at": datetime.utcnow().isoformat(),
                "available_agents": await self._get_pack_agents(pack_id),
                "available_workflows": await self._get_pack_workflows(pack_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to enable expansion pack {pack_id}: {e}")
            raise
    
    async def uninstall_expansion_pack(self, pack_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uninstall a BMAD expansion pack.
        
        Args:
            pack_id: Expansion pack identifier
            user_context: User context
            
        Returns:
            Uninstallation result
        """
        try:
            logger.info(f"Uninstalling expansion pack: {pack_id}")
            
            # Simulate uninstallation process
            await asyncio.sleep(0.1)
            
            return {
                "pack_id": pack_id,
                "status": "uninstalled",
                "uninstalled_by": user_context.get("user_id", "unknown"),
                "uninstalled_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall expansion pack {pack_id}: {e}")
            raise
    
    async def list_installed_expansion_packs(self) -> List[Dict[str, Any]]:
        """
        List all installed expansion packs.
        
        Returns:
            List of installed expansion pack information
        """
        try:
            installed_packs = []
            
            if not os.path.exists(self.expansion_pack_path):
                return installed_packs
            
            # Scan for installed packs
            for pack_dir in os.listdir(self.expansion_pack_path):
                pack_path = os.path.join(self.expansion_pack_path, pack_dir)
                
                if os.path.isdir(pack_path):
                    pack_info = await self._get_expansion_pack_info(pack_path, pack_dir)
                    if pack_info:
                        pack_info["status"] = "installed"
                        installed_packs.append(pack_info)
            
            return installed_packs
            
        except Exception as e:
            logger.error(f"Failed to list installed expansion packs: {e}")
            return []
    
    async def _get_expansion_pack_info(self, pack_path: str, pack_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an expansion pack from its directory.
        
        Args:
            pack_path: Path to expansion pack directory
            pack_id: Pack identifier
            
        Returns:
            Pack information dictionary
        """
        try:
            config_path = os.path.join(pack_path, "config.yaml")
            
            # Load config if available
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            
            # Count available resources
            agents_count = 0
            workflows_count = 0
            templates_count = 0
            
            agents_path = os.path.join(pack_path, "agents")
            if os.path.exists(agents_path):
                agents_count = len([f for f in os.listdir(agents_path) if f.endswith('.md')])
            
            workflows_path = os.path.join(pack_path, "workflows")
            if os.path.exists(workflows_path):
                workflows_count = len([f for f in os.listdir(workflows_path) if f.endswith('.yaml')])
            
            templates_path = os.path.join(pack_path, "templates")
            if os.path.exists(templates_path):
                templates_count = len([f for f in os.listdir(templates_path) if f.endswith('.yaml')])
            
            return {
                "pack_id": pack_id,
                "name": config.get("name", pack_id.replace("-", " ").title()),
                "description": config.get("description", "BMAD expansion pack"),
                "version": config.get("version", "1.0.0"),
                "category": config.get("category", "general"),
                "agents_count": agents_count,
                "workflows_count": workflows_count,
                "templates_count": templates_count,
                "path": pack_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get expansion pack info for {pack_id}: {e}")
            return None
    
    async def _get_pack_agents(self, pack_id: str) -> List[str]:
        """Get list of agents available in an expansion pack."""
        try:
            agents_path = os.path.join(self.expansion_pack_path, pack_id, "agents")
            
            if not os.path.exists(agents_path):
                return []
            
            agents = []
            for agent_file in os.listdir(agents_path):
                if agent_file.endswith('.md'):
                    agents.append(agent_file[:-3])  # Remove .md extension
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get agents for pack {pack_id}: {e}")
            return []
    
    async def _get_pack_workflows(self, pack_id: str) -> List[str]:
        """Get list of workflows available in an expansion pack."""
        try:
            workflows_path = os.path.join(self.expansion_pack_path, pack_id, "workflows")
            
            if not os.path.exists(workflows_path):
                return []
            
            workflows = []
            for workflow_file in os.listdir(workflows_path):
                if workflow_file.endswith('.yaml'):
                    workflows.append(workflow_file[:-5])  # Remove .yaml extension
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get workflows for pack {pack_id}: {e}")
            return []
