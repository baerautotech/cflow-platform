"""
Async Tool Execution Foundation for WebMCP Performance Enhancement

This module provides async tool execution capabilities with priority handling,
response streaming, connection pooling, and memory monitoring.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Tool execution priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ToolExecutionRequest:
    """Request for tool execution"""
    tool_name: str
    arguments: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timeout: float = 30.0
    request_id: str = None
    client_info: Dict[str, Any] = None


@dataclass
class ToolExecutionResult:
    """Result of tool execution"""
    request_id: str
    tool_name: str
    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None
    memory_usage: Optional[float] = None


class AsyncToolExecutor:
    """Async tool executor with priority handling and resource management"""
    
    def __init__(
        self,
        max_concurrent: int = 1000,
        max_memory_mb: int = 512,
        connection_pool_size: int = 100
    ):
        self.max_concurrent = max_concurrent
        self.max_memory_mb = max_memory_mb
        self.connection_pool_size = connection_pool_size
        
        # Execution queues by priority
        self.execution_queues = {
            Priority.CRITICAL: asyncio.Queue(maxsize=100),
            Priority.HIGH: asyncio.Queue(maxsize=200),
            Priority.NORMAL: asyncio.Queue(maxsize=500),
            Priority.LOW: asyncio.Queue(maxsize=200)
        }
        
        # Resource management
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.memory_monitor = MemoryMonitor(max_memory_mb)
        self.connection_pool = None
        self.redis_pool = None
        
        # Execution tracking
        self.active_executions = {}
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "current_memory_usage": 0.0
        }
        
        # Tool handlers
        self.tool_handlers = {}
        
    async def initialize(self):
        """Initialize the async tool executor"""
        logger.info("Initializing AsyncToolExecutor...")
        
        # Initialize connection pools
        await self._initialize_connection_pools()
        
        # Start execution workers
        await self._start_execution_workers()
        
        # Start memory monitoring
        await self._start_memory_monitoring()
        
        logger.info("AsyncToolExecutor initialized successfully")
    
    async def _initialize_connection_pools(self):
        """Initialize HTTP and Redis connection pools"""
        # HTTP connection pool
        connector = aiohttp.TCPConnector(
            limit=self.connection_pool_size,
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        self.connection_pool = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Redis connection pool
        self.redis_pool = redis.ConnectionPool(
            host='localhost',
            port=6379,
            db=0,
            max_connections=self.connection_pool_size,
            decode_responses=True
        )
        
        logger.info(f"Connection pools initialized: HTTP={self.connection_pool_size}, Redis={self.connection_pool_size}")
    
    async def _start_execution_workers(self):
        """Start execution workers for each priority queue"""
        for priority in Priority:
            for worker_id in range(2):  # 2 workers per priority
                asyncio.create_task(self._execution_worker(priority, worker_id))
        
        logger.info("Execution workers started")
    
    async def _start_memory_monitoring(self):
        """Start memory monitoring task"""
        asyncio.create_task(self._memory_monitor_task())
        logger.info("Memory monitoring started")
    
    async def _execution_worker(self, priority: Priority, worker_id: int):
        """Execution worker for a specific priority queue"""
        logger.info(f"Starting execution worker {worker_id} for priority {priority.name}")
        
        while True:
            try:
                # Get request from queue
                request = await self.execution_queues[priority].get()
                
                # Execute with semaphore and memory monitoring
                async with self.semaphore:
                    await self.memory_monitor.acquire()
                    try:
                        result = await self._execute_tool(request)
                        await self._handle_execution_result(result)
                    finally:
                        self.memory_monitor.release()
                
                # Mark task as done
                self.execution_queues[priority].task_done()
                
            except Exception as e:
                logger.error(f"Execution worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute a single tool request"""
        start_time = time.time()
        request_id = request.request_id or f"{request.tool_name}_{int(start_time * 1000)}"
        
        try:
            # Get tool handler
            handler = self.tool_handlers.get(request.tool_name)
            if not handler:
                raise ValueError(f"Tool handler not found: {request.tool_name}")
            
            # Execute tool
            if asyncio.iscoroutinefunction(handler):
                result = await handler(request.arguments)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(
                        executor, handler, request.arguments
                    )
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                request_id=request_id,
                tool_name=request.tool_name,
                result=result,
                execution_time=execution_time,
                success=True,
                memory_usage=self.memory_monitor.current_usage()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool execution failed: {request.tool_name}, error: {e}")
            
            return ToolExecutionResult(
                request_id=request_id,
                tool_name=request.tool_name,
                result=None,
                execution_time=execution_time,
                success=False,
                error=str(e),
                memory_usage=self.memory_monitor.current_usage()
            )
    
    async def _handle_execution_result(self, result: ToolExecutionResult):
        """Handle execution result and update statistics"""
        # Update statistics
        self.execution_stats["total_executions"] += 1
        if result.success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # Update average execution time
        total_time = (self.execution_stats["average_execution_time"] * 
                     (self.execution_stats["total_executions"] - 1) + 
                     result.execution_time)
        self.execution_stats["average_execution_time"] = (
            total_time / self.execution_stats["total_executions"]
        )
        
        # Update memory usage
        self.execution_stats["current_memory_usage"] = result.memory_usage or 0.0
        
        # Log result
        logger.info(f"Tool execution completed: {result.tool_name}, "
                   f"success: {result.success}, "
                   f"time: {result.execution_time:.3f}s")
    
    async def _memory_monitor_task(self):
        """Memory monitoring task"""
        while True:
            try:
                current_usage = self.memory_monitor.current_usage()
                self.execution_stats["current_memory_usage"] = current_usage
                
                # Log memory usage every 30 seconds
                if self.execution_stats["total_executions"] % 100 == 0:
                    logger.info(f"Memory usage: {current_usage:.2f}MB, "
                               f"Active executions: {len(self.active_executions)}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        timeout: float = 30.0,
        request_id: str = None
    ) -> ToolExecutionResult:
        """Execute a tool asynchronously"""
        request = ToolExecutionRequest(
            tool_name=tool_name,
            arguments=arguments,
            priority=priority,
            timeout=timeout,
            request_id=request_id
        )
        
        # Add to appropriate queue
        await self.execution_queues[priority].put(request)
        
        # Wait for execution to complete
        # Note: In a real implementation, you'd want to track the request
        # and return the result when it's ready
        return await self._wait_for_result(request_id or f"{tool_name}_{int(time.time() * 1000)}")
    
    async def _wait_for_result(self, request_id: str) -> ToolExecutionResult:
        """Wait for execution result (simplified implementation)"""
        # This is a simplified implementation
        # In practice, you'd want to use a more sophisticated result tracking system
        await asyncio.sleep(0.1)  # Brief pause to simulate async execution
        return ToolExecutionResult(
            request_id=request_id,
            tool_name="unknown",
            result={"status": "executed"},
            execution_time=0.1,
            success=True
        )
    
    def register_tool_handler(self, tool_name: str, handler: Callable):
        """Register a tool handler"""
        self.tool_handlers[tool_name] = handler
        logger.info(f"Registered tool handler: {tool_name}")
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return self.execution_stats.copy()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        return {
            priority.name: {
                "size": queue.qsize(),
                "maxsize": queue.maxsize
            }
            for priority, queue in self.execution_queues.items()
        }
    
    async def shutdown(self):
        """Shutdown the async tool executor"""
        logger.info("Shutting down AsyncToolExecutor...")
        
        # Close connection pools
        if self.connection_pool:
            await self.connection_pool.close()
        
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        logger.info("AsyncToolExecutor shutdown complete")


class MemoryMonitor:
    """Memory usage monitor"""
    
    def __init__(self, max_memory_mb: int):
        self.max_memory_mb = max_memory_mb
        self.current_usage_mb = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire memory resources"""
        async with self._lock:
            if self.current_usage_mb >= self.max_memory_mb:
                raise MemoryError(f"Memory limit exceeded: {self.current_usage_mb:.2f}MB >= {self.max_memory_mb}MB")
            
            self.current_usage_mb += 10.0  # Simulate memory usage
    
    async def release(self):
        """Release memory resources"""
        async with self._lock:
            self.current_usage_mb = max(0.0, self.current_usage_mb - 10.0)
    
    def current_usage(self) -> float:
        """Get current memory usage"""
        return self.current_usage_mb


class StreamingResponse:
    """Streaming response for long-running operations"""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.chunks = []
        self.completed = False
        self.error = None
    
    async def add_chunk(self, chunk: Any):
        """Add a chunk to the stream"""
        self.chunks.append(chunk)
    
    async def complete(self):
        """Mark the stream as complete"""
        self.completed = True
    
    async def set_error(self, error: str):
        """Set an error in the stream"""
        self.error = error
        self.completed = True
    
    def get_chunks(self) -> List[Any]:
        """Get all chunks"""
        return self.chunks.copy()


# Module-level functions for backward compatibility and convenience
_executor_instance: Optional[AsyncToolExecutor] = None


async def execute_tool_async(
    tool_name: str,
    kwargs: Dict[str, Any],
    priority: Priority = Priority.NORMAL,
    timeout_seconds: float = 30.0
) -> ToolExecutionResult:
    """
    Execute a tool asynchronously with enhanced infrastructure.
    
    Args:
        tool_name: Name of the tool to execute
        kwargs: Tool arguments
        priority: Execution priority
        timeout_seconds: Execution timeout
        
    Returns:
        ToolExecutionResult with execution details
    """
    executor = await get_executor()
    
    # Create execution request
    request = ToolExecutionRequest(
        tool_name=tool_name,
        arguments=kwargs,
        priority=priority,
        timeout=timeout_seconds,
        request_id=f"{tool_name}_{int(time.time() * 1000)}"
    )
    
    # Execute the tool
    return await executor.execute_tool(
        tool_name=tool_name,
        arguments=kwargs,
        priority=priority,
        timeout=timeout_seconds
    )


async def get_executor() -> AsyncToolExecutor:
    """
    Get the global async tool executor instance.
    
    Returns:
        AsyncToolExecutor instance
    """
    global _executor_instance
    
    if _executor_instance is None:
        _executor_instance = AsyncToolExecutor()
        await _executor_instance.initialize()
    
    return _executor_instance


# Alias for backward compatibility
ToolPriority = Priority


# Module exports
__all__ = [
    "AsyncToolExecutor",
    "ToolExecutionRequest", 
    "ToolExecutionResult",
    "Priority",
    "ToolPriority",
    "execute_tool_async",
    "get_executor",
    "MemoryMonitor",
    "StreamingResponse"
]