"""
Async Master Tool Base Classes for BMAD

This module provides the foundation for master tools with async execution,
operation support, registry system, and migration adapter for backward compatibility.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Master tool operation types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    EXECUTE = "execute"
    VALIDATE = "validate"
    APPROVE = "approve"
    REJECT = "reject"


class OperationStatus(Enum):
    """Operation execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Operation:
    """Master tool operation definition"""
    name: str
    operation_type: OperationType
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Optional[Callable] = None
    timeout: float = 30.0
    requires_auth: bool = False
    cache_ttl: Optional[int] = None
    priority: int = 100


@dataclass
class OperationRequest:
    """Request for master tool operation"""
    operation_name: str
    arguments: Dict[str, Any]
    request_id: str
    client_info: Dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    timeout: float = 30.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class OperationResult:
    """Result of master tool operation"""
    request_id: str
    operation_name: str
    result: Any
    success: bool
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class AsyncMasterTool(ABC):
    """Abstract base class for async master tools"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.operations: Dict[str, Operation] = {}
        self.cache = None
        self.circuit_breaker = None
        self.metrics = None
        self.status = "initialized"
        self.created_at = time.time()
        self.last_used = time.time()
        
        # Performance tracking
        self.operation_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Initialize operations
        self._initialize_operations()
    
    @abstractmethod
    def _initialize_operations(self):
        """Initialize tool operations - must be implemented by subclasses"""
        pass
    
    def register_operation(self, operation: Operation):
        """Register an operation"""
        self.operations[operation.name] = operation
        logger.info(f"Registered operation {operation.name} for master tool {self.name}")
    
    def get_operation(self, operation_name: str) -> Optional[Operation]:
        """Get operation by name"""
        return self.operations.get(operation_name)
    
    def list_operations(self) -> List[str]:
        """List all available operations"""
        return list(self.operations.keys())
    
    def get_operation_schema(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get operation input schema"""
        operation = self.get_operation(operation_name)
        if operation:
            return {
                "name": operation.name,
                "description": operation.description,
                "inputSchema": operation.input_schema,
                "outputSchema": operation.output_schema,
                "timeout": operation.timeout,
                "requires_auth": operation.requires_auth,
                "cache_ttl": operation.cache_ttl,
                "priority": operation.priority
            }
        return None
    
    async def execute_operation(self, request: OperationRequest) -> OperationResult:
        """Execute a master tool operation"""
        start_time = time.time()
        
        try:
            # Validate operation exists
            operation = self.get_operation(request.operation_name)
            if not operation:
                raise ValueError(f"Operation {request.operation_name} not found")
            
            # Update last used timestamp
            self.last_used = time.time()
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                self.operation_stats["cache_hits"] += 1
                return cached_result
            
            self.operation_stats["cache_misses"] += 1
            
            # Execute operation with circuit breaker
            if self.circuit_breaker:
                result = await self.circuit_breaker.call(
                    self._execute_operation_handler, operation, request
                )
            else:
                result = await self._execute_operation_handler(operation, request)
            
            execution_time = time.time() - start_time
            
            # Create operation result
            operation_result = OperationResult(
                request_id=request.request_id,
                operation_name=request.operation_name,
                result=result,
                success=True,
                execution_time=execution_time,
                metadata={
                    "tool_name": self.name,
                    "tool_version": self.version,
                    "operation_type": operation.operation_type.value,
                    "cache_hit": False
                }
            )
            
            # Cache result if configured
            if operation.cache_ttl:
                await self._cache_result(cache_key, operation_result, operation.cache_ttl)
            
            # Update statistics
            self._update_stats(True, execution_time)
            
            # Record metrics
            if self.metrics:
                self.metrics.record_execution(request.operation_name, operation_result)
            
            return operation_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Operation execution failed: {request.operation_name}, error: {e}")
            
            # Update statistics
            self._update_stats(False, execution_time)
            
            return OperationResult(
                request_id=request.request_id,
                operation_name=request.operation_name,
                result=None,
                success=False,
                execution_time=execution_time,
                error=str(e),
                metadata={
                    "tool_name": self.name,
                    "tool_version": self.version,
                    "error_type": type(e).__name__
                }
            )
    
    async def _execute_operation_handler(self, operation: Operation, request: OperationRequest) -> Any:
        """Execute the operation handler"""
        if operation.handler:
            if asyncio.iscoroutinefunction(operation.handler):
                return await operation.handler(request.arguments)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                with asyncio.ThreadPoolExecutor() as executor:
                    return await loop.run_in_executor(
                        executor, operation.handler, request.arguments
                    )
        else:
            # Default handler - delegate to subclass
            return await self._handle_operation(operation, request.arguments)
    
    async def _handle_operation(self, operation: Operation, arguments: Dict[str, Any]) -> Any:
        """Handle operation - can be overridden by subclasses"""
        raise NotImplementedError(f"Operation {operation.name} not implemented")
    
    def _generate_cache_key(self, request: OperationRequest) -> str:
        """Generate cache key for request"""
        key_data = {
            "tool": self.name,
            "operation": request.operation_name,
            "args": request.arguments
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_result(self, cache_key: str) -> Optional[OperationResult]:
        """Get cached result"""
        if self.cache:
            try:
                return await self.cache.get(cache_key)
            except Exception as e:
                logger.error(f"Cache get error: {e}")
        return None
    
    async def _cache_result(self, cache_key: str, result: OperationResult, ttl: int):
        """Cache operation result"""
        if self.cache:
            try:
                await self.cache.set(cache_key, result, ttl)
            except Exception as e:
                logger.error(f"Cache set error: {e}")
    
    def _update_stats(self, success: bool, execution_time: float):
        """Update operation statistics"""
        self.operation_stats["total_executions"] += 1
        
        if success:
            self.operation_stats["successful_executions"] += 1
        else:
            self.operation_stats["failed_executions"] += 1
        
        # Update average execution time
        total_time = (self.operation_stats["average_execution_time"] * 
                     (self.operation_stats["total_executions"] - 1) + 
                     execution_time)
        self.operation_stats["average_execution_time"] = (
            total_time / self.operation_stats["total_executions"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get master tool statistics"""
        total_executions = self.operation_stats["total_executions"]
        success_rate = (self.operation_stats["successful_executions"] / 
                       total_executions * 100) if total_executions > 0 else 0
        
        cache_hits = self.operation_stats["cache_hits"]
        cache_misses = self.operation_stats["cache_misses"]
        cache_hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0
        
        return {
            "tool_name": self.name,
            "tool_version": self.version,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "operations_count": len(self.operations),
            "operations": list(self.operations.keys()),
            "statistics": {
                **self.operation_stats,
                "success_rate_percent": success_rate,
                "cache_hit_rate_percent": cache_hit_rate
            }
        }
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get complete tool schema for MCP"""
        operations_schemas = {}
        for op_name, operation in self.operations.items():
            operations_schemas[op_name] = self.get_operation_schema(op_name)
        
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "operations": operations_schemas,
            "metadata": {
                "tool_type": "master_tool",
                "async_enabled": True,
                "cache_enabled": self.cache is not None,
                "circuit_breaker_enabled": self.circuit_breaker is not None,
                "metrics_enabled": self.metrics is not None
            }
        }


class MasterToolRegistry:
    """Registry for master tools"""
    
    def __init__(self):
        self.tools: Dict[str, AsyncMasterTool] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.operation_index: Dict[str, str] = {}  # operation_name -> tool_name
        
    def register_tool(self, tool: AsyncMasterTool):
        """Register a master tool"""
        self.tools[tool.name] = tool
        
        # Index operations
        for operation_name in tool.list_operations():
            self.operation_index[operation_name] = tool.name
        
        # Store metadata
        self.tool_metadata[tool.name] = tool.get_tool_schema()
        
        logger.info(f"Registered master tool: {tool.name} with {len(tool.list_operations())} operations")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a master tool"""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            
            # Remove from operation index
            for operation_name in tool.list_operations():
                self.operation_index.pop(operation_name, None)
            
            # Remove tool
            del self.tools[tool_name]
            del self.tool_metadata[tool_name]
            
            logger.info(f"Unregistered master tool: {tool_name}")
            return True
        
        return False
    
    def get_tool(self, tool_name: str) -> Optional[AsyncMasterTool]:
        """Get master tool by name"""
        return self.tools.get(tool_name)
    
    def get_tool_for_operation(self, operation_name: str) -> Optional[AsyncMasterTool]:
        """Get master tool that handles an operation"""
        tool_name = self.operation_index.get(operation_name)
        if tool_name:
            return self.tools.get(tool_name)
        return None
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())
    
    def list_operations(self) -> List[str]:
        """List all available operations"""
        return list(self.operation_index.keys())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_operations = len(self.operation_index)
        total_tools = len(self.tools)
        
        return {
            "total_tools": total_tools,
            "total_operations": total_operations,
            "tools": list(self.tools.keys()),
            "operations": list(self.operation_index.keys()),
            "tool_metadata": self.tool_metadata.copy()
        }


class ToolMigrationAdapter:
    """Adapter for migrating legacy tools to master tools"""
    
    def __init__(self, master_tool_registry: MasterToolRegistry):
        self.master_tool_registry = master_tool_registry
        self.legacy_tool_mappings: Dict[str, Dict[str, str]] = {}  # legacy_tool -> {operation: master_tool}
        self.migration_stats = {
            "migrations_attempted": 0,
            "migrations_successful": 0,
            "migrations_failed": 0
        }
    
    def add_legacy_mapping(self, legacy_tool_name: str, master_tool_name: str, 
                          operation_mappings: Dict[str, str]):
        """Add mapping from legacy tool to master tool operations"""
        self.legacy_tool_mappings[legacy_tool_name] = {
            "master_tool": master_tool_name,
            "operations": operation_mappings
        }
        logger.info(f"Added legacy mapping: {legacy_tool_name} -> {master_tool_name}")
    
    async def migrate_legacy_request(self, legacy_tool_name: str, operation_name: str, 
                                   arguments: Dict[str, Any]) -> OperationResult:
        """Migrate legacy tool request to master tool"""
        self.migration_stats["migrations_attempted"] += 1
        
        try:
            # Get mapping
            mapping = self.legacy_tool_mappings.get(legacy_tool_name)
            if not mapping:
                raise ValueError(f"No migration mapping found for {legacy_tool_name}")
            
            master_tool_name = mapping["master_tool"]
            operation_mappings = mapping["operations"]
            
            # Get master tool operation
            master_operation = operation_mappings.get(operation_name)
            if not master_operation:
                raise ValueError(f"No master operation mapping for {legacy_tool_name}.{operation_name}")
            
            # Get master tool
            master_tool = self.master_tool_registry.get_tool(master_tool_name)
            if not master_tool:
                raise ValueError(f"Master tool {master_tool_name} not found")
            
            # Create request
            request = OperationRequest(
                operation_name=master_operation,
                arguments=arguments,
                request_id=f"migration_{int(time.time() * 1000)}",
                client_info={"legacy_tool": legacy_tool_name, "original_operation": operation_name}
            )
            
            # Execute master tool operation
            result = await master_tool.execute_operation(request)
            
            # Update migration metadata
            result.metadata.update({
                "migrated_from": legacy_tool_name,
                "original_operation": operation_name,
                "master_tool": master_tool_name,
                "master_operation": master_operation
            })
            
            self.migration_stats["migrations_successful"] += 1
            return result
            
        except Exception as e:
            self.migration_stats["migrations_failed"] += 1
            logger.error(f"Migration failed: {legacy_tool_name}.{operation_name} -> {e}")
            
            return OperationResult(
                request_id=f"migration_failed_{int(time.time() * 1000)}",
                operation_name=operation_name,
                result=None,
                success=False,
                execution_time=0.0,
                error=f"Migration failed: {e}",
                metadata={
                    "legacy_tool": legacy_tool_name,
                    "migration_error": str(e)
                }
            )
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """Get migration statistics"""
        total_attempts = self.migration_stats["migrations_attempted"]
        success_rate = (self.migration_stats["migrations_successful"] / 
                       total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            **self.migration_stats,
            "success_rate_percent": success_rate,
            "legacy_mappings": len(self.legacy_tool_mappings),
            "mappings": self.legacy_tool_mappings.copy()
        }
    
    def list_legacy_tools(self) -> List[str]:
        """List all legacy tools with mappings"""
        return list(self.legacy_tool_mappings.keys())


class MasterToolManager:
    """Main manager for master tools"""
    
    def __init__(self):
        self.registry = MasterToolRegistry()
        self.migration_adapter = ToolMigrationAdapter(self.registry)
        self.status = "initialized"
        
        # Performance components (will be injected)
        self.cache = None
        self.circuit_breaker = None
        self.metrics = None
    
    def inject_performance_components(self, cache=None, circuit_breaker=None, metrics=None):
        """Inject performance components"""
        self.cache = cache
        self.circuit_breaker = circuit_breaker
        self.metrics = metrics
        
        # Inject into all registered tools
        for tool in self.registry.tools.values():
            tool.cache = cache
            tool.circuit_breaker = circuit_breaker
            tool.metrics = metrics
        
        logger.info("Performance components injected into master tools")
    
    def register_tool(self, tool: AsyncMasterTool):
        """Register a master tool"""
        # Inject performance components
        tool.cache = self.cache
        tool.circuit_breaker = self.circuit_breaker
        tool.metrics = self.metrics
        
        self.registry.register_tool(tool)
    
    async def execute_operation(self, tool_name: str, operation_name: str, 
                              arguments: Dict[str, Any], request_id: str = None) -> OperationResult:
        """Execute operation on master tool"""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Master tool {tool_name} not found")
        
        request = OperationRequest(
            operation_name=operation_name,
            arguments=arguments,
            request_id=request_id or f"{tool_name}_{operation_name}_{int(time.time() * 1000)}"
        )
        
        return await tool.execute_operation(request)
    
    async def migrate_legacy_request(self, legacy_tool_name: str, operation_name: str, 
                                   arguments: Dict[str, Any]) -> OperationResult:
        """Migrate legacy tool request"""
        return await self.migration_adapter.migrate_legacy_request(
            legacy_tool_name, operation_name, arguments
        )
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            "status": self.status,
            "registry": self.registry.get_registry_stats(),
            "migration": self.migration_adapter.get_migration_stats(),
            "performance_components": {
                "cache_enabled": self.cache is not None,
                "circuit_breaker_enabled": self.circuit_breaker is not None,
                "metrics_enabled": self.metrics is not None
            }
        }
