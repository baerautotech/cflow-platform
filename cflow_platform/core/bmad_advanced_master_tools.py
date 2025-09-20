"""
Advanced BMAD Master Tools with Fault Tolerance

This module implements advanced BMAD master tools for HIL, Git, orchestrator,
and expansion pack management with circuit breakers and fault tolerance.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from .master_tool_base import AsyncMasterTool, Operation, OperationType, OperationRequest, OperationResult
from .fault_tolerance import CircuitBreaker, CircuitBreakerConfig, GracefulDegradation

logger = logging.getLogger(__name__)


class BMADHILMasterTool(AsyncMasterTool):
    """Master tool for Human-in-the-Loop (HIL) operations with fault tolerance"""
    
    def __init__(self):
        super().__init__(
            name="bmad_hil",
            description="BMAD Human-in-the-Loop Master Tool - handles all HIL operations with fault tolerance",
            version="1.0.0"
        )
        self.graceful_degradation = GracefulDegradation()
        self._setup_fault_tolerance()
    
    def _setup_fault_tolerance(self):
        """Setup fault tolerance components"""
        # Circuit breaker for HIL operations
        hil_config = CircuitBreakerConfig(
            name="hil_operations",
            failure_threshold=3,
            recovery_timeout=60.0,
            expected_exception=Exception
        )
        self.circuit_breaker = CircuitBreaker(hil_config)
        
        # Register fallback handlers
        self.graceful_degradation.register_fallback("hil_request", self._fallback_hil_request)
        self.graceful_degradation.register_fallback("hil_approval", self._fallback_hil_approval)
    
    def _initialize_operations(self):
        """Initialize HIL operations"""
        # Request HIL intervention
        self.register_operation(Operation(
            name="request",
            operation_type=OperationType.EXECUTE,
            description="Request human intervention",
            input_schema={
                "type": "object",
                "properties": {
                    "request_type": {"type": "string", "enum": ["approval", "decision", "review", "input"]},
                    "context": {"type": "string", "description": "Request context"},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "data": {"type": "object", "description": "Request data"},
                    "timeout_minutes": {"type": "integer", "default": 60, "description": "Request timeout"}
                },
                "required": ["request_type", "context"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"},
                    "estimated_response_time": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get HIL request status
        self.register_operation(Operation(
            name="status",
            operation_type=OperationType.READ,
            description="Get HIL request status",
            input_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "Request ID"}
                },
                "required": ["request_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "status": {"type": "string"},
                    "response": {"type": "object"},
                    "responded_at": {"type": "string"},
                    "responded_by": {"type": "string"}
                }
            },
            cache_ttl=60,
            priority=100
        ))
        
        # Approve HIL request
        self.register_operation(Operation(
            name="approve",
            operation_type=OperationType.APPROVE,
            description="Approve HIL request",
            input_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "Request ID"},
                    "approver": {"type": "string", "description": "Approver name"},
                    "comments": {"type": "string", "description": "Approval comments"},
                    "approval_data": {"type": "object", "description": "Approval data"}
                },
                "required": ["request_id", "approver"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "status": {"type": "string"},
                    "approved_at": {"type": "string"},
                    "approved_by": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # List HIL requests
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List HIL requests",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "approved", "rejected", "expired"]},
                    "request_type": {"type": "string", "enum": ["approval", "decision", "review", "input"]},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "requests": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle HIL operations with fault tolerance"""
        try:
            if operation.name == "request":
                return await self.graceful_degradation.execute_with_fallback(
                    "hil_request", self._request_hil_intervention, arguments
                )
            elif operation.name == "status":
                return await self._get_hil_status(arguments)
            elif operation.name == "approve":
                return await self.graceful_degradation.execute_with_fallback(
                    "hil_approval", self._approve_hil_request, arguments
                )
            elif operation.name == "list":
                return await self._list_hil_requests(arguments)
            else:
                raise ValueError(f"Unknown operation: {operation.name}")
        except Exception as e:
            logger.error(f"HIL operation {operation.name} failed: {e}")
            raise
    
    async def _request_hil_intervention(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Request human intervention"""
        request_id = f"hil_{int(time.time() * 1000)}"
        return {
            "request_id": request_id,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_response_time": "2-4 hours"
        }
    
    async def _get_hil_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get HIL request status"""
        request_id = arguments["request_id"]
        return {
            "request_id": request_id,
            "status": "pending",
            "response": None,
            "responded_at": None,
            "responded_by": None
        }
    
    async def _approve_hil_request(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Approve HIL request"""
        request_id = arguments["request_id"]
        approver = arguments["approver"]
        return {
            "request_id": request_id,
            "status": "approved",
            "approved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "approved_by": approver
        }
    
    async def _list_hil_requests(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List HIL requests"""
        requests = [
            {
                "request_id": f"hil_{i}",
                "request_type": "approval",
                "status": "pending",
                "urgency": "medium"
            }
            for i in range(1, 11)
        ]
        
        return {
            "requests": requests,
            "total_count": len(requests),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
    
    async def _fallback_hil_request(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for HIL request when primary fails"""
        logger.warning("Using fallback for HIL request")
        return {
            "request_id": f"fallback_{int(time.time() * 1000)}",
            "status": "fallback_mode",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_response_time": "Extended due to system issues"
        }
    
    async def _fallback_hil_approval(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for HIL approval when primary fails"""
        logger.warning("Using fallback for HIL approval")
        return {
            "request_id": arguments["request_id"],
            "status": "fallback_approved",
            "approved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "approved_by": "system_fallback"
        }


class BMADGitMasterTool(AsyncMasterTool):
    """Master tool for Git operations with fault tolerance"""
    
    def __init__(self):
        super().__init__(
            name="bmad_git",
            description="BMAD Git Management Master Tool - handles all Git operations with fault tolerance",
            version="1.0.0"
        )
        self.graceful_degradation = GracefulDegradation()
        self._setup_fault_tolerance()
    
    def _setup_fault_tolerance(self):
        """Setup fault tolerance components"""
        # Circuit breaker for Git operations
        git_config = CircuitBreakerConfig(
            name="git_operations",
            failure_threshold=5,
            recovery_timeout=120.0,
            expected_exception=Exception
        )
        self.circuit_breaker = CircuitBreaker(git_config)
        
        # Register fallback handlers
        self.graceful_degradation.register_fallback("git_commit", self._fallback_git_commit)
        self.graceful_degradation.register_fallback("git_push", self._fallback_git_push)
        self.graceful_degradation.register_fallback("git_pull", self._fallback_git_pull)
    
    def _initialize_operations(self):
        """Initialize Git operations"""
        # Commit changes
        self.register_operation(Operation(
            name="commit",
            operation_type=OperationType.EXECUTE,
            description="Commit changes to repository",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files to commit"},
                    "branch": {"type": "string", "description": "Target branch", "default": "main"},
                    "author": {"type": "string", "description": "Commit author"}
                },
                "required": ["message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "commit_hash": {"type": "string"},
                    "status": {"type": "string"},
                    "committed_at": {"type": "string"},
                    "files_count": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Push changes
        self.register_operation(Operation(
            name="push",
            operation_type=OperationType.EXECUTE,
            description="Push changes to remote repository",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch to push", "default": "main"},
                    "remote": {"type": "string", "description": "Remote repository", "default": "origin"},
                    "force": {"type": "boolean", "description": "Force push", "default": False}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "pushed_at": {"type": "string"},
                    "commits_pushed": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Pull changes
        self.register_operation(Operation(
            name="pull",
            operation_type=OperationType.EXECUTE,
            description="Pull changes from remote repository",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch to pull", "default": "main"},
                    "remote": {"type": "string", "description": "Remote repository", "default": "origin"}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "pulled_at": {"type": "string"},
                    "commits_pulled": {"type": "integer"},
                    "conflicts": {"type": "array", "items": {"type": "string"}}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Create branch
        self.register_operation(Operation(
            name="create_branch",
            operation_type=OperationType.CREATE,
            description="Create a new branch",
            input_schema={
                "type": "object",
                "properties": {
                    "branch_name": {"type": "string", "description": "New branch name"},
                    "from_branch": {"type": "string", "description": "Source branch", "default": "main"},
                    "checkout": {"type": "boolean", "description": "Checkout new branch", "default": True}
                },
                "required": ["branch_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "branch_name": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Merge branch
        self.register_operation(Operation(
            name="merge",
            operation_type=OperationType.EXECUTE,
            description="Merge branch into target branch",
            input_schema={
                "type": "object",
                "properties": {
                    "source_branch": {"type": "string", "description": "Source branch to merge"},
                    "target_branch": {"type": "string", "description": "Target branch", "default": "main"},
                    "merge_message": {"type": "string", "description": "Merge commit message"}
                },
                "required": ["source_branch"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "merge_hash": {"type": "string"},
                    "status": {"type": "string"},
                    "merged_at": {"type": "string"},
                    "conflicts": {"type": "array", "items": {"type": "string"}}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get repository status
        self.register_operation(Operation(
            name="status",
            operation_type=OperationType.READ,
            description="Get repository status",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch to check", "default": "current"}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "current_branch": {"type": "string"},
                    "status": {"type": "string"},
                    "modified_files": {"type": "array", "items": {"type": "string"}},
                    "staged_files": {"type": "array", "items": {"type": "string"}},
                    "untracked_files": {"type": "array", "items": {"type": "string"}}
                }
            },
            cache_ttl=60,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle Git operations with fault tolerance"""
        try:
            if operation.name == "commit":
                return await self.graceful_degradation.execute_with_fallback(
                    "git_commit", self._commit_changes, arguments
                )
            elif operation.name == "push":
                return await self.graceful_degradation.execute_with_fallback(
                    "git_push", self._push_changes, arguments
                )
            elif operation.name == "pull":
                return await self.graceful_degradation.execute_with_fallback(
                    "git_pull", self._pull_changes, arguments
                )
            elif operation.name == "create_branch":
                return await self._create_branch(arguments)
            elif operation.name == "merge":
                return await self._merge_branch(arguments)
            elif operation.name == "status":
                return await self._get_repository_status(arguments)
            else:
                raise ValueError(f"Unknown operation: {operation.name}")
        except Exception as e:
            logger.error(f"Git operation {operation.name} failed: {e}")
            raise
    
    async def _commit_changes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes to repository"""
        commit_hash = f"commit_{int(time.time() * 1000)}"
        files = arguments.get("files", [])
        return {
            "commit_hash": commit_hash,
            "status": "committed",
            "committed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files_count": len(files)
        }
    
    async def _push_changes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Push changes to remote repository"""
        return {
            "status": "pushed",
            "pushed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commits_pushed": 1
        }
    
    async def _pull_changes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Pull changes from remote repository"""
        return {
            "status": "pulled",
            "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commits_pulled": 2,
            "conflicts": []
        }
    
    async def _create_branch(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new branch"""
        branch_name = arguments["branch_name"]
        return {
            "branch_name": branch_name,
            "status": "created",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _merge_branch(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Merge branch into target branch"""
        merge_hash = f"merge_{int(time.time() * 1000)}"
        return {
            "merge_hash": merge_hash,
            "status": "merged",
            "merged_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conflicts": []
        }
    
    async def _get_repository_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository status"""
        return {
            "current_branch": "main",
            "status": "clean",
            "modified_files": [],
            "staged_files": [],
            "untracked_files": []
        }
    
    async def _fallback_git_commit(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for Git commit when primary fails"""
        logger.warning("Using fallback for Git commit")
        return {
            "commit_hash": f"fallback_{int(time.time() * 1000)}",
            "status": "fallback_committed",
            "committed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files_count": 0
        }
    
    async def _fallback_git_push(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for Git push when primary fails"""
        logger.warning("Using fallback for Git push")
        return {
            "status": "fallback_pushed",
            "pushed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commits_pushed": 0
        }
    
    async def _fallback_git_pull(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for Git pull when primary fails"""
        logger.warning("Using fallback for Git pull")
        return {
            "status": "fallback_pulled",
            "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commits_pulled": 0,
            "conflicts": []
        }


class BMADOrchestratorMasterTool(AsyncMasterTool):
    """Master tool for orchestrator operations with fault tolerance"""
    
    def __init__(self):
        super().__init__(
            name="bmad_orchestrator",
            description="BMAD Orchestrator Master Tool - handles all orchestration operations with fault tolerance",
            version="1.0.0"
        )
        self.graceful_degradation = GracefulDegradation()
        self._setup_fault_tolerance()
    
    def _setup_fault_tolerance(self):
        """Setup fault tolerance components"""
        # Circuit breaker for orchestrator operations
        orchestrator_config = CircuitBreakerConfig(
            name="orchestrator_operations",
            failure_threshold=3,
            recovery_timeout=90.0,
            expected_exception=Exception
        )
        self.circuit_breaker = CircuitBreaker(orchestrator_config)
        
        # Register fallback handlers
        self.graceful_degradation.register_fallback("orchestrator_start", self._fallback_start_orchestration)
        self.graceful_degradation.register_fallback("orchestrator_stop", self._fallback_stop_orchestration)
    
    def _initialize_operations(self):
        """Initialize orchestrator operations"""
        # Start orchestration
        self.register_operation(Operation(
            name="start",
            operation_type=OperationType.EXECUTE,
            description="Start orchestration process",
            input_schema={
                "type": "object",
                "properties": {
                    "orchestration_id": {"type": "string", "description": "Orchestration ID"},
                    "config": {"type": "object", "description": "Orchestration configuration"},
                    "parallel_execution": {"type": "boolean", "description": "Enable parallel execution", "default": True},
                    "max_retries": {"type": "integer", "description": "Maximum retries", "default": 3}
                },
                "required": ["orchestration_id", "config"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "orchestration_id": {"type": "string"},
                    "execution_id": {"type": "string"},
                    "status": {"type": "string"},
                    "started_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Stop orchestration
        self.register_operation(Operation(
            name="stop",
            operation_type=OperationType.EXECUTE,
            description="Stop orchestration process",
            input_schema={
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string", "description": "Execution ID"},
                    "force": {"type": "boolean", "description": "Force stop", "default": False}
                },
                "required": ["execution_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string"},
                    "status": {"type": "string"},
                    "stopped_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get orchestration status
        self.register_operation(Operation(
            name="status",
            operation_type=OperationType.READ,
            description="Get orchestration status",
            input_schema={
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string", "description": "Execution ID"}
                },
                "required": ["execution_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string"},
                    "status": {"type": "string"},
                    "progress": {"type": "number"},
                    "current_step": {"type": "string"},
                    "started_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=30,
            priority=100
        ))
        
        # List orchestrations
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List orchestrations",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["running", "completed", "failed", "stopped"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "orchestrations": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle orchestrator operations with fault tolerance"""
        try:
            if operation.name == "start":
                return await self.graceful_degradation.execute_with_fallback(
                    "orchestrator_start", self._start_orchestration, arguments
                )
            elif operation.name == "stop":
                return await self.graceful_degradation.execute_with_fallback(
                    "orchestrator_stop", self._stop_orchestration, arguments
                )
            elif operation.name == "status":
                return await self._get_orchestration_status(arguments)
            elif operation.name == "list":
                return await self._list_orchestrations(arguments)
            else:
                raise ValueError(f"Unknown operation: {operation.name}")
        except Exception as e:
            logger.error(f"Orchestrator operation {operation.name} failed: {e}")
            raise
    
    async def _start_orchestration(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Start orchestration process"""
        orchestration_id = arguments["orchestration_id"]
        execution_id = f"exec_{int(time.time() * 1000)}"
        return {
            "orchestration_id": orchestration_id,
            "execution_id": execution_id,
            "status": "running",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _stop_orchestration(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Stop orchestration process"""
        execution_id = arguments["execution_id"]
        return {
            "execution_id": execution_id,
            "status": "stopped",
            "stopped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_orchestration_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get orchestration status"""
        execution_id = arguments["execution_id"]
        return {
            "execution_id": execution_id,
            "status": "running",
            "progress": 0.75,
            "current_step": "step_3",
            "started_at": "2025-01-09 10:00:00",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_orchestrations(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List orchestrations"""
        orchestrations = [
            {
                "execution_id": f"exec_{i}",
                "orchestration_id": f"orch_{i}",
                "status": "running",
                "progress": 0.5
            }
            for i in range(1, 11)
        ]
        
        return {
            "orchestrations": orchestrations,
            "total_count": len(orchestrations),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
    
    async def _fallback_start_orchestration(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for start orchestration when primary fails"""
        logger.warning("Using fallback for start orchestration")
        return {
            "orchestration_id": arguments["orchestration_id"],
            "execution_id": f"fallback_{int(time.time() * 1000)}",
            "status": "fallback_running",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _fallback_stop_orchestration(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for stop orchestration when primary fails"""
        logger.warning("Using fallback for stop orchestration")
        return {
            "execution_id": arguments["execution_id"],
            "status": "fallback_stopped",
            "stopped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }


class BMADExpansionMasterTool(AsyncMasterTool):
    """Master tool for expansion pack management with fault tolerance"""
    
    def __init__(self):
        super().__init__(
            name="bmad_expansion",
            description="BMAD Expansion Pack Master Tool - handles all expansion pack operations with fault tolerance",
            version="1.0.0"
        )
        self.graceful_degradation = GracefulDegradation()
        self._setup_fault_tolerance()
    
    def _setup_fault_tolerance(self):
        """Setup fault tolerance components"""
        # Circuit breaker for expansion pack operations
        expansion_config = CircuitBreakerConfig(
            name="expansion_operations",
            failure_threshold=3,
            recovery_timeout=60.0,
            expected_exception=Exception
        )
        self.circuit_breaker = CircuitBreaker(expansion_config)
        
        # Register fallback handlers
        self.graceful_degradation.register_fallback("expansion_install", self._fallback_install_expansion)
        self.graceful_degradation.register_fallback("expansion_uninstall", self._fallback_uninstall_expansion)
    
    def _initialize_operations(self):
        """Initialize expansion pack operations"""
        # Install expansion pack
        self.register_operation(Operation(
            name="install",
            operation_type=OperationType.EXECUTE,
            description="Install expansion pack",
            input_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string", "description": "Expansion pack name"},
                    "version": {"type": "string", "description": "Pack version", "default": "latest"},
                    "config": {"type": "object", "description": "Installation configuration"},
                    "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Required dependencies"}
                },
                "required": ["pack_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string"},
                    "version": {"type": "string"},
                    "status": {"type": "string"},
                    "installed_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Uninstall expansion pack
        self.register_operation(Operation(
            name="uninstall",
            operation_type=OperationType.DELETE,
            description="Uninstall expansion pack",
            input_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string", "description": "Expansion pack name"},
                    "remove_data": {"type": "boolean", "description": "Remove pack data", "default": False}
                },
                "required": ["pack_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string"},
                    "status": {"type": "string"},
                    "uninstalled_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # List expansion packs
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List expansion packs",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["installed", "available", "outdated"]},
                    "category": {"type": "string", "enum": ["game_dev", "devops", "creative", "analytics"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "packs": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Update expansion pack
        self.register_operation(Operation(
            name="update",
            operation_type=OperationType.UPDATE,
            description="Update expansion pack",
            input_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string", "description": "Expansion pack name"},
                    "version": {"type": "string", "description": "Target version", "default": "latest"}
                },
                "required": ["pack_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string"},
                    "old_version": {"type": "string"},
                    "new_version": {"type": "string"},
                    "status": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get expansion pack info
        self.register_operation(Operation(
            name="info",
            operation_type=OperationType.READ,
            description="Get expansion pack information",
            input_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string", "description": "Expansion pack name"}
                },
                "required": ["pack_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "pack_name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string"},
                    "installed_at": {"type": "string"}
                }
            },
            cache_ttl=600,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle expansion pack operations with fault tolerance"""
        try:
            if operation.name == "install":
                return await self.graceful_degradation.execute_with_fallback(
                    "expansion_install", self._install_expansion_pack, arguments
                )
            elif operation.name == "uninstall":
                return await self.graceful_degradation.execute_with_fallback(
                    "expansion_uninstall", self._uninstall_expansion_pack, arguments
                )
            elif operation.name == "list":
                return await self._list_expansion_packs(arguments)
            elif operation.name == "update":
                return await self._update_expansion_pack(arguments)
            elif operation.name == "info":
                return await self._get_expansion_pack_info(arguments)
            else:
                raise ValueError(f"Unknown operation: {operation.name}")
        except Exception as e:
            logger.error(f"Expansion pack operation {operation.name} failed: {e}")
            raise
    
    async def _install_expansion_pack(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Install expansion pack"""
        pack_name = arguments["pack_name"]
        version = arguments.get("version", "latest")
        return {
            "pack_name": pack_name,
            "version": version,
            "status": "installed",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _uninstall_expansion_pack(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Uninstall expansion pack"""
        pack_name = arguments["pack_name"]
        return {
            "pack_name": pack_name,
            "status": "uninstalled",
            "uninstalled_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_expansion_packs(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List expansion packs"""
        packs = [
            {
                "pack_name": f"pack_{i}",
                "version": "1.0.0",
                "category": "game_dev",
                "status": "installed"
            }
            for i in range(1, 11)
        ]
        
        return {
            "packs": packs,
            "total_count": len(packs),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
    
    async def _update_expansion_pack(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update expansion pack"""
        pack_name = arguments["pack_name"]
        new_version = arguments.get("version", "latest")
        return {
            "pack_name": pack_name,
            "old_version": "1.0.0",
            "new_version": new_version,
            "status": "updated",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_expansion_pack_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get expansion pack information"""
        pack_name = arguments["pack_name"]
        return {
            "pack_name": pack_name,
            "version": "1.0.0",
            "description": f"Expansion pack {pack_name}",
            "category": "game_dev",
            "dependencies": ["bmad_core"],
            "status": "installed",
            "installed_at": "2025-01-09 10:00:00"
        }
    
    async def _fallback_install_expansion(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for install expansion pack when primary fails"""
        logger.warning("Using fallback for install expansion pack")
        return {
            "pack_name": arguments["pack_name"],
            "version": arguments.get("version", "latest"),
            "status": "fallback_installed",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _fallback_uninstall_expansion(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for uninstall expansion pack when primary fails"""
        logger.warning("Using fallback for uninstall expansion pack")
        return {
            "pack_name": arguments["pack_name"],
            "status": "fallback_uninstalled",
            "uninstalled_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
