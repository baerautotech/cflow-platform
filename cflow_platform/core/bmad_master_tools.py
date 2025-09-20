"""
Core BMAD Master Tools with Caching

This module implements the core BMAD master tools for task, plan, document,
and workflow management with operation-level caching.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from .master_tool_base import AsyncMasterTool, Operation, OperationType, OperationRequest, OperationResult
from .performance_cache import PerformanceCache, CacheConfig

logger = logging.getLogger(__name__)


class BMADTaskMasterTool(AsyncMasterTool):
    """Master tool for task management operations"""
    
    def __init__(self):
        super().__init__(
            name="bmad_task",
            description="BMAD Task Management Master Tool - handles all task operations",
            version="1.0.0"
        )
    
    def _initialize_operations(self):
        """Initialize task operations"""
        # Create task
        self.register_operation(Operation(
            name="create",
            operation_type=OperationType.CREATE,
            description="Create a new task",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "assignee": {"type": "string", "description": "Task assignee"},
                    "due_date": {"type": "string", "format": "date", "description": "Task due date"},
                    "project_id": {"type": "string", "description": "Project ID"}
                },
                "required": ["title", "description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cache_ttl=300,  # 5 minutes
            priority=100
        ))
        
        # Get task
        self.register_operation(Operation(
            name="get",
            operation_type=OperationType.READ,
            description="Get task details",
            input_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"}
                },
                "required": ["task_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "string"},
                    "assignee": {"type": "string"},
                    "due_date": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=600,  # 10 minutes
            priority=100
        ))
        
        # Update task
        self.register_operation(Operation(
            name="update",
            operation_type=OperationType.UPDATE,
            description="Update task details",
            input_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "title": {"type": "string", "description": "Updated title"},
                    "description": {"type": "string", "description": "Updated description"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "assignee": {"type": "string", "description": "Updated assignee"},
                    "due_date": {"type": "string", "format": "date", "description": "Updated due date"}
                },
                "required": ["task_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "status": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=300,  # 5 minutes
            priority=100
        ))
        
        # Delete task
        self.register_operation(Operation(
            name="delete",
            operation_type=OperationType.DELETE,
            description="Delete a task",
            input_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"}
                },
                "required": ["task_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "deleted": {"type": "boolean"},
                    "deleted_at": {"type": "string"}
                }
            },
            cache_ttl=60,  # 1 minute
            priority=100
        ))
        
        # List tasks
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List tasks with filtering",
            input_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Filter by project ID"},
                    "assignee": {"type": "string", "description": "Filter by assignee"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "limit": {"type": "integer", "default": 50, "description": "Maximum number of tasks to return"},
                    "offset": {"type": "integer", "default": 0, "description": "Number of tasks to skip"}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,  # 5 minutes
            priority=100
        ))
        
        # Search tasks
        self.register_operation(Operation(
            name="search",
            operation_type=OperationType.SEARCH,
            description="Search tasks by text",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "project_id": {"type": "string", "description": "Filter by project ID"},
                    "limit": {"type": "integer", "default": 20, "description": "Maximum number of results"}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "total_count": {"type": "integer"},
                    "query": {"type": "string"}
                }
            },
            cache_ttl=600,  # 10 minutes
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle task operations"""
        if operation.name == "create":
            return await self._create_task(arguments)
        elif operation.name == "get":
            return await self._get_task(arguments)
        elif operation.name == "update":
            return await self._update_task(arguments)
        elif operation.name == "delete":
            return await self._delete_task(arguments)
        elif operation.name == "list":
            return await self._list_tasks(arguments)
        elif operation.name == "search":
            return await self._search_tasks(arguments)
        else:
            raise ValueError(f"Unknown operation: {operation.name}")
    
    async def _create_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        # Simulate task creation
        task_id = f"task_{int(time.time() * 1000)}"
        return {
            "task_id": task_id,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get task details"""
        task_id = arguments["task_id"]
        # Simulate task retrieval
        return {
            "task_id": task_id,
            "title": f"Sample Task {task_id}",
            "description": "Sample task description",
            "status": "pending",
            "priority": "medium",
            "assignee": "user@example.com",
            "due_date": "2025-01-15",
            "created_at": "2025-01-09 10:00:00",
            "updated_at": "2025-01-09 10:00:00"
        }
    
    async def _update_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update task details"""
        task_id = arguments["task_id"]
        return {
            "task_id": task_id,
            "status": "updated",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _delete_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task"""
        task_id = arguments["task_id"]
        return {
            "task_id": task_id,
            "deleted": True,
            "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks with filtering"""
        # Simulate task listing
        tasks = [
            {
                "task_id": f"task_{i}",
                "title": f"Task {i}",
                "status": "pending",
                "priority": "medium"
            }
            for i in range(1, 11)
        ]
        
        return {
            "tasks": tasks,
            "total_count": len(tasks),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
    
    async def _search_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search tasks by text"""
        query = arguments["query"]
        # Simulate search results
        results = [
            {
                "task_id": f"task_{i}",
                "title": f"Task matching {query}",
                "description": f"Description containing {query}",
                "score": 0.9 - (i * 0.1)
            }
            for i in range(1, 6)
        ]
        
        return {
            "results": results,
            "total_count": len(results),
            "query": query
        }


class BMADPlanMasterTool(AsyncMasterTool):
    """Master tool for plan management operations"""
    
    def __init__(self):
        super().__init__(
            name="bmad_plan",
            description="BMAD Plan Management Master Tool - handles all plan operations",
            version="1.0.0"
        )
    
    def _initialize_operations(self):
        """Initialize plan operations"""
        # Create plan
        self.register_operation(Operation(
            name="create",
            operation_type=OperationType.CREATE,
            description="Create a new plan",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Plan name"},
                    "description": {"type": "string", "description": "Plan description"},
                    "project_type": {"type": "string", "enum": ["greenfield", "brownfield"], "default": "greenfield"},
                    "estimated_duration": {"type": "integer", "description": "Estimated duration in weeks"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                },
                "required": ["name", "description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get plan
        self.register_operation(Operation(
            name="get",
            operation_type=OperationType.READ,
            description="Get plan details",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "Plan ID"}
                },
                "required": ["plan_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "project_type": {"type": "string"},
                    "status": {"type": "string"},
                    "estimated_duration": {"type": "integer"},
                    "priority": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=600,
            priority=100
        ))
        
        # Update plan
        self.register_operation(Operation(
            name="update",
            operation_type=OperationType.UPDATE,
            description="Update plan details",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "Plan ID"},
                    "name": {"type": "string", "description": "Updated name"},
                    "description": {"type": "string", "description": "Updated description"},
                    "status": {"type": "string", "enum": ["draft", "active", "completed", "cancelled"]},
                    "estimated_duration": {"type": "integer", "description": "Updated duration"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                },
                "required": ["plan_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "status": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # List plans
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List plans with filtering",
            input_schema={
                "type": "object",
                "properties": {
                    "project_type": {"type": "string", "enum": ["greenfield", "brownfield"]},
                    "status": {"type": "string", "enum": ["draft", "active", "completed", "cancelled"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plans": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Execute plan
        self.register_operation(Operation(
            name="execute",
            operation_type=OperationType.EXECUTE,
            description="Execute a plan",
            input_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "Plan ID"},
                    "execution_mode": {"type": "string", "enum": ["dry_run", "live"], "default": "dry_run"}
                },
                "required": ["plan_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string"},
                    "execution_id": {"type": "string"},
                    "status": {"type": "string"},
                    "started_at": {"type": "string"}
                }
            },
            cache_ttl=60,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle plan operations"""
        if operation.name == "create":
            return await self._create_plan(arguments)
        elif operation.name == "get":
            return await self._get_plan(arguments)
        elif operation.name == "update":
            return await self._update_plan(arguments)
        elif operation.name == "list":
            return await self._list_plans(arguments)
        elif operation.name == "execute":
            return await self._execute_plan(arguments)
        else:
            raise ValueError(f"Unknown operation: {operation.name}")
    
    async def _create_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new plan"""
        plan_id = f"plan_{int(time.time() * 1000)}"
        return {
            "plan_id": plan_id,
            "status": "draft",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get plan details"""
        plan_id = arguments["plan_id"]
        return {
            "plan_id": plan_id,
            "name": f"Sample Plan {plan_id}",
            "description": "Sample plan description",
            "project_type": "greenfield",
            "status": "draft",
            "estimated_duration": 4,
            "priority": "medium",
            "created_at": "2025-01-09 10:00:00",
            "updated_at": "2025-01-09 10:00:00"
        }
    
    async def _update_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update plan details"""
        plan_id = arguments["plan_id"]
        return {
            "plan_id": plan_id,
            "status": "updated",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_plans(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List plans with filtering"""
        plans = [
            {
                "plan_id": f"plan_{i}",
                "name": f"Plan {i}",
                "status": "draft",
                "project_type": "greenfield"
            }
            for i in range(1, 11)
        ]
        
        return {
            "plans": plans,
            "total_count": len(plans),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
    
    async def _execute_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plan"""
        plan_id = arguments["plan_id"]
        execution_id = f"exec_{int(time.time() * 1000)}"
        return {
            "plan_id": plan_id,
            "execution_id": execution_id,
            "status": "running",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }


class BMADDocMasterTool(AsyncMasterTool):
    """Master tool for document management operations"""
    
    def __init__(self):
        super().__init__(
            name="bmad_doc",
            description="BMAD Document Management Master Tool - handles all document operations",
            version="1.0.0"
        )
    
    def _initialize_operations(self):
        """Initialize document operations"""
        # Create document
        self.register_operation(Operation(
            name="create",
            operation_type=OperationType.CREATE,
            description="Create a new document",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document content"},
                    "document_type": {"type": "string", "enum": ["prd", "arch", "story", "spec"], "description": "Document type"},
                    "project_id": {"type": "string", "description": "Project ID"},
                    "template": {"type": "string", "description": "Template to use"}
                },
                "required": ["title", "content", "document_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Get document
        self.register_operation(Operation(
            name="get",
            operation_type=OperationType.READ,
            description="Get document details",
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID"}
                },
                "required": ["document_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "document_type": {"type": "string"},
                    "status": {"type": "string"},
                    "version": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=600,
            priority=100
        ))
        
        # Update document
        self.register_operation(Operation(
            name="update",
            operation_type=OperationType.UPDATE,
            description="Update document content",
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID"},
                    "title": {"type": "string", "description": "Updated title"},
                    "content": {"type": "string", "description": "Updated content"},
                    "version": {"type": "string", "description": "New version"}
                },
                "required": ["document_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "version": {"type": "string"},
                    "status": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Approve document
        self.register_operation(Operation(
            name="approve",
            operation_type=OperationType.APPROVE,
            description="Approve a document",
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID"},
                    "approver": {"type": "string", "description": "Approver name"},
                    "comments": {"type": "string", "description": "Approval comments"}
                },
                "required": ["document_id", "approver"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "status": {"type": "string"},
                    "approved_by": {"type": "string"},
                    "approved_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # List documents
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List documents with filtering",
            input_schema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "enum": ["prd", "arch", "story", "spec"]},
                    "project_id": {"type": "string", "description": "Project ID"},
                    "status": {"type": "string", "enum": ["draft", "review", "approved", "published"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "documents": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle document operations"""
        if operation.name == "create":
            return await self._create_document(arguments)
        elif operation.name == "get":
            return await self._get_document(arguments)
        elif operation.name == "update":
            return await self._update_document(arguments)
        elif operation.name == "approve":
            return await self._approve_document(arguments)
        elif operation.name == "list":
            return await self._list_documents(arguments)
        else:
            raise ValueError(f"Unknown operation: {operation.name}")
    
    async def _create_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document"""
        document_id = f"doc_{int(time.time() * 1000)}"
        return {
            "document_id": document_id,
            "status": "draft",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get document details"""
        document_id = arguments["document_id"]
        return {
            "document_id": document_id,
            "title": f"Sample Document {document_id}",
            "content": "Sample document content",
            "document_type": "prd",
            "status": "draft",
            "version": "1.0",
            "created_at": "2025-01-09 10:00:00",
            "updated_at": "2025-01-09 10:00:00"
        }
    
    async def _update_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update document content"""
        document_id = arguments["document_id"]
        return {
            "document_id": document_id,
            "version": "1.1",
            "status": "updated",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _approve_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a document"""
        document_id = arguments["document_id"]
        approver = arguments["approver"]
        return {
            "document_id": document_id,
            "status": "approved",
            "approved_by": approver,
            "approved_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List documents with filtering"""
        documents = [
            {
                "document_id": f"doc_{i}",
                "title": f"Document {i}",
                "document_type": "prd",
                "status": "draft"
            }
            for i in range(1, 11)
        ]
        
        return {
            "documents": documents,
            "total_count": len(documents),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }


class BMADWorkflowMasterTool(AsyncMasterTool):
    """Master tool for workflow management operations"""
    
    def __init__(self):
        super().__init__(
            name="bmad_workflow",
            description="BMAD Workflow Management Master Tool - handles all workflow operations",
            version="1.0.0"
        )
    
    def _initialize_operations(self):
        """Initialize workflow operations"""
        # Create workflow
        self.register_operation(Operation(
            name="create",
            operation_type=OperationType.CREATE,
            description="Create a new workflow",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Workflow name"},
                    "description": {"type": "string", "description": "Workflow description"},
                    "steps": {"type": "array", "items": {"type": "object"}, "description": "Workflow steps"},
                    "project_type": {"type": "string", "enum": ["greenfield", "brownfield"], "default": "greenfield"}
                },
                "required": ["name", "description", "steps"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
        
        # Execute workflow
        self.register_operation(Operation(
            name="execute",
            operation_type=OperationType.EXECUTE,
            description="Execute a workflow",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "parameters": {"type": "object", "description": "Execution parameters"},
                    "execution_mode": {"type": "string", "enum": ["dry_run", "live"], "default": "dry_run"}
                },
                "required": ["workflow_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "execution_id": {"type": "string"},
                    "status": {"type": "string"},
                    "started_at": {"type": "string"}
                }
            },
            cache_ttl=60,
            priority=100
        ))
        
        # Get workflow status
        self.register_operation(Operation(
            name="status",
            operation_type=OperationType.READ,
            description="Get workflow execution status",
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
                    "workflow_id": {"type": "string"},
                    "status": {"type": "string"},
                    "current_step": {"type": "string"},
                    "progress": {"type": "number"},
                    "started_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            },
            cache_ttl=30,
            priority=100
        ))
        
        # List workflows
        self.register_operation(Operation(
            name="list",
            operation_type=OperationType.LIST,
            description="List workflows",
            input_schema={
                "type": "object",
                "properties": {
                    "project_type": {"type": "string", "enum": ["greenfield", "brownfield"]},
                    "status": {"type": "string", "enum": ["active", "inactive", "archived"]},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "workflows": {"type": "array", "items": {"type": "object"}},
                    "total_count": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                }
            },
            cache_ttl=300,
            priority=100
        ))
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle workflow operations"""
        if operation.name == "create":
            return await self._create_workflow(arguments)
        elif operation.name == "execute":
            return await self._execute_workflow(arguments)
        elif operation.name == "status":
            return await self._get_workflow_status(arguments)
        elif operation.name == "list":
            return await self._list_workflows(arguments)
        else:
            raise ValueError(f"Unknown operation: {operation.name}")
    
    async def _create_workflow(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow"""
        workflow_id = f"workflow_{int(time.time() * 1000)}"
        return {
            "workflow_id": workflow_id,
            "status": "active",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _execute_workflow(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        workflow_id = arguments["workflow_id"]
        execution_id = f"exec_{int(time.time() * 1000)}"
        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": "running",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_workflow_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow execution status"""
        execution_id = arguments["execution_id"]
        return {
            "execution_id": execution_id,
            "workflow_id": f"workflow_{execution_id}",
            "status": "running",
            "current_step": "step_2",
            "progress": 0.5,
            "started_at": "2025-01-09 10:00:00",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _list_workflows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List workflows"""
        workflows = [
            {
                "workflow_id": f"workflow_{i}",
                "name": f"Workflow {i}",
                "status": "active",
                "project_type": "greenfield"
            }
            for i in range(1, 11)
        ]
        
        return {
            "workflows": workflows,
            "total_count": len(workflows),
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0)
        }
