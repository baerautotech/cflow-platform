"""
Batch Processing System for WebMCP Performance Enhancement

This module provides efficient batch processing capabilities for multiple tool calls,
including dependency resolution, parallel execution, and result aggregation.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class BatchExecutionMode(Enum):
    """Batch execution modes"""
    PARALLEL = "parallel"           # Execute all tools in parallel
    SEQUENTIAL = "sequential"       # Execute tools one by one
    DEPENDENCY_ORDERED = "dependency_ordered"  # Execute based on dependencies
    HYBRID = "hybrid"               # Mix of parallel and sequential


class BatchFailureMode(Enum):
    """How to handle failures in batch execution"""
    FAIL_FAST = "fail_fast"         # Stop on first failure
    CONTINUE_ON_ERROR = "continue_on_error"  # Continue despite failures
    RETRY_FAILURES = "retry_failures"        # Retry failed executions


@dataclass
class BatchToolRequest:
    """Individual tool request in a batch"""
    tool_name: str
    arguments: Dict[str, Any]
    request_id: str = ""
    priority: int = 0
    timeout_seconds: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    cache_key: Optional[str] = None


@dataclass
class BatchToolResult:
    """Result of individual tool execution in batch"""
    request_id: str
    tool_name: str
    result: Any
    success: bool
    execution_time: float
    error: Optional[str] = None
    retry_count: int = 0
    cached: bool = False


@dataclass
class BatchExecutionResult:
    """Complete batch execution result"""
    batch_id: str
    results: List[BatchToolResult]
    total_execution_time: float
    success_count: int
    failure_count: int
    cached_count: int
    retry_count: int
    execution_mode: BatchExecutionMode
    failure_mode: BatchFailureMode
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor:
    """
    High-performance batch processor for tool execution.
    
    Features:
    - Multiple execution modes (parallel, sequential, dependency-ordered)
    - Dependency resolution and ordering
    - Failure handling strategies
    - Result caching and deduplication
    - Performance optimization
    - Resource management
    """
    
    def __init__(
        self,
        max_concurrent: int = 50,
        max_batch_size: int = 100,
        default_timeout: float = 30.0,
        enable_caching: bool = True,
        enable_deduplication: bool = True
    ):
        self.max_concurrent = max_concurrent
        self.max_batch_size = max_batch_size
        self.default_timeout = default_timeout
        self.enable_caching = enable_caching
        self.enable_deduplication = enable_deduplication
        
        # Execution tracking
        self._active_batches: Dict[str, asyncio.Task] = {}
        self._batch_results: Dict[str, BatchExecutionResult] = {}
        
        # Deduplication
        self._request_signatures: Dict[str, str] = {}
        
        # Performance tracking
        self._execution_stats = {
            "total_batches": 0,
            "total_tools": 0,
            "successful_tools": 0,
            "failed_tools": 0,
            "cached_tools": 0,
            "average_execution_time": 0.0,
            "average_batch_size": 0.0
        }
    
    async def execute_batch(
        self,
        requests: List[BatchToolRequest],
        execution_mode: BatchExecutionMode = BatchExecutionMode.HYBRID,
        failure_mode: BatchFailureMode = BatchFailureMode.CONTINUE_ON_ERROR,
        batch_id: Optional[str] = None
    ) -> BatchExecutionResult:
        """
        Execute a batch of tool requests.
        
        Args:
            requests: List of tool requests to execute
            execution_mode: How to execute the batch
            failure_mode: How to handle failures
            batch_id: Optional batch identifier
            
        Returns:
            BatchExecutionResult with all execution results
        """
        if not requests:
            return BatchExecutionResult(
                batch_id=batch_id or "empty",
                results=[],
                total_execution_time=0.0,
                success_count=0,
                failure_count=0,
                cached_count=0,
                retry_count=0,
                execution_mode=execution_mode,
                failure_mode=failure_mode
            )
        
        # Validate batch size
        if len(requests) > self.max_batch_size:
            raise ValueError(f"Batch size {len(requests)} exceeds maximum {self.max_batch_size}")
        
        batch_id = batch_id or f"batch_{int(time.time() * 1000)}"
        start_time = time.time()
        
        logger.info(f"Starting batch {batch_id} with {len(requests)} tools in {execution_mode.value} mode")
        
        # Deduplicate requests if enabled
        if self.enable_deduplication:
            requests = self._deduplicate_requests(requests)
            logger.debug(f"After deduplication: {len(requests)} unique requests")
        
        # Execute based on mode
        if execution_mode == BatchExecutionMode.PARALLEL:
            results = await self._execute_parallel(requests, failure_mode)
        elif execution_mode == BatchExecutionMode.SEQUENTIAL:
            results = await self._execute_sequential(requests, failure_mode)
        elif execution_mode == BatchExecutionMode.DEPENDENCY_ORDERED:
            results = await self._execute_dependency_ordered(requests, failure_mode)
        elif execution_mode == BatchExecutionMode.HYBRID:
            results = await self._execute_hybrid(requests, failure_mode)
        else:
            raise ValueError(f"Unknown execution mode: {execution_mode}")
        
        # Calculate statistics
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        cached_count = sum(1 for r in results if r.cached)
        retry_count = sum(r.retry_count for r in results)
        
        # Create result
        batch_result = BatchExecutionResult(
            batch_id=batch_id,
            results=results,
            total_execution_time=total_time,
            success_count=success_count,
            failure_count=failure_count,
            cached_count=cached_count,
            retry_count=retry_count,
            execution_mode=execution_mode,
            failure_mode=failure_mode,
            metadata={
                "start_time": start_time,
                "end_time": time.time(),
                "original_count": len(requests),
                "deduplicated": self.enable_deduplication
            }
        )
        
        # Store result
        self._batch_results[batch_id] = batch_result
        
        # Update statistics
        self._update_stats(batch_result)
        
        logger.info(
            f"Completed batch {batch_id}: {success_count} successful, "
            f"{failure_count} failed, {cached_count} cached in {total_time:.2f}s"
        )
        
        return batch_result
    
    def _deduplicate_requests(self, requests: List[BatchToolRequest]) -> List[BatchToolRequest]:
        """Remove duplicate requests based on tool name and arguments"""
        seen = set()
        unique_requests = []
        
        for request in requests:
            # Create signature
            signature = self._create_request_signature(request)
            
            if signature not in seen:
                seen.add(signature)
                unique_requests.append(request)
                self._request_signatures[request.request_id] = signature
            else:
                logger.debug(f"Deduplicated request: {request.tool_name}")
        
        return unique_requests
    
    def _create_request_signature(self, request: BatchToolRequest) -> str:
        """Create a unique signature for a request"""
        return f"{request.tool_name}:{json.dumps(request.arguments, sort_keys=True)}"
    
    async def _execute_parallel(
        self,
        requests: List[BatchToolRequest],
        failure_mode: BatchFailureMode
    ) -> List[BatchToolResult]:
        """Execute requests in parallel with concurrency control"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []
        
        async def execute_single(request: BatchToolRequest) -> BatchToolResult:
            async with semaphore:
                return await self._execute_single_request(request, failure_mode)
        
        # Execute all requests
        tasks = [execute_single(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(BatchToolResult(
                    request_id=requests[i].request_id,
                    tool_name=requests[i].tool_name,
                    result=None,
                    success=False,
                    execution_time=0.0,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_sequential(
        self,
        requests: List[BatchToolRequest],
        failure_mode: BatchFailureMode
    ) -> List[BatchToolResult]:
        """Execute requests sequentially"""
        results = []
        
        for request in requests:
            result = await self._execute_single_request(request, failure_mode)
            results.append(result)
            
            # Check failure mode
            if failure_mode == BatchFailureMode.FAIL_FAST and not result.success:
                logger.info(f"Stopping batch execution due to failure: {result.error}")
                break
        
        return results
    
    async def _execute_dependency_ordered(
        self,
        requests: List[BatchToolRequest],
        failure_mode: BatchFailureMode
    ) -> List[BatchToolResult]:
        """Execute requests in dependency order"""
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(requests)
        
        # Topological sort
        execution_order = self._topological_sort(dependency_graph)
        
        # Execute in dependency order
        results = []
        completed_results = {}
        
        for request_id in execution_order:
            request = next(req for req in requests if req.request_id == request_id)
            
            # Check if dependencies are satisfied
            if not self._dependencies_satisfied(request, completed_results):
                result = BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    result=None,
                    success=False,
                    execution_time=0.0,
                    error="Dependencies not satisfied"
                )
                results.append(result)
                continue
            
            # Execute request
            result = await self._execute_single_request(request, failure_mode)
            results.append(result)
            completed_results[request_id] = result
            
            # Check failure mode
            if failure_mode == BatchFailureMode.FAIL_FAST and not result.success:
                logger.info(f"Stopping batch execution due to failure: {result.error}")
                break
        
        return results
    
    async def _execute_hybrid(
        self,
        requests: List[BatchToolRequest],
        failure_mode: BatchFailureMode
    ) -> List[BatchToolResult]:
        """Execute requests using hybrid approach (dependency groups in parallel)"""
        # Group requests by dependency level
        dependency_groups = self._group_by_dependency_level(requests)
        
        results = []
        
        # Execute each group in parallel
        for group in dependency_groups:
            if not group:
                continue
            
            # Execute group in parallel
            group_results = await self._execute_parallel(group, failure_mode)
            results.extend(group_results)
            
            # Check if we should stop due to failures
            if failure_mode == BatchFailureMode.FAIL_FAST:
                has_failures = any(not r.success for r in group_results)
                if has_failures:
                    logger.info("Stopping batch execution due to failure in group")
                    break
        
        return results
    
    def _build_dependency_graph(self, requests: List[BatchToolRequest]) -> Dict[str, Set[str]]:
        """Build dependency graph from requests"""
        graph = defaultdict(set)
        
        # Create request ID mapping
        request_map = {req.request_id: req for req in requests}
        
        for request in requests:
            graph[request.request_id] = set()
            
            for dep_id in request.dependencies:
                if dep_id in request_map:
                    graph[request.request_id].add(dep_id)
        
        return dict(graph)
    
    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Perform topological sort on dependency graph"""
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for node in graph:
            in_degree[node] = 0
        
        for node, deps in graph.items():
            for dep in deps:
                in_degree[node] += 1
        
        # Kahn's algorithm
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Update in-degrees
            for neighbor, deps in graph.items():
                if node in deps:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        return result
    
    def _group_by_dependency_level(self, requests: List[BatchToolRequest]) -> List[List[BatchToolRequest]]:
        """Group requests by dependency level"""
        graph = self._build_dependency_graph(requests)
        levels = defaultdict(list)
        
        # Calculate dependency levels
        for request in requests:
            level = self._calculate_dependency_level(request.request_id, graph)
            levels[level].append(request)
        
        # Return groups in level order
        return [levels[level] for level in sorted(levels.keys())]
    
    def _calculate_dependency_level(self, node: str, graph: Dict[str, Set[str]], visited: Set[str] = None) -> int:
        """Calculate dependency level for a node"""
        if visited is None:
            visited = set()
        
        if node in visited:
            return 0  # Cycle detected
        
        visited.add(node)
        
        max_dep_level = 0
        for dep in graph.get(node, set()):
            dep_level = self._calculate_dependency_level(dep, graph, visited.copy())
            max_dep_level = max(max_dep_level, dep_level)
        
        return max_dep_level + 1
    
    def _dependencies_satisfied(
        self,
        request: BatchToolRequest,
        completed_results: Dict[str, BatchToolResult]
    ) -> bool:
        """Check if all dependencies are satisfied"""
        for dep_id in request.dependencies:
            if dep_id not in completed_results or not completed_results[dep_id].success:
                return False
        return True
    
    async def _execute_single_request(
        self,
        request: BatchToolRequest,
        failure_mode: BatchFailureMode
    ) -> BatchToolResult:
        """Execute a single tool request"""
        start_time = time.time()
        
        # Check cache first
        if self.enable_caching:
            cached_result = await self._get_cached_result(request)
            if cached_result is not None:
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    result=cached_result,
                    success=True,
                    execution_time=time.time() - start_time,
                    cached=True
                )
        
        # Execute tool
        retry_count = 0
        last_error = None
        
        while retry_count <= request.max_retries:
            try:
                # Import the enhanced tool executor
                from .async_tool_executor import execute_tool_async, ToolPriority
                
                # Determine priority
                priority = ToolPriority.HIGH if request.priority > 0 else ToolPriority.NORMAL
                
                # Execute with timeout
                timeout = request.timeout_seconds or self.default_timeout
                result = await asyncio.wait_for(
                    execute_tool_async(
                        tool_name=request.tool_name,
                        kwargs=request.arguments,
                        priority=priority,
                        timeout_seconds=timeout
                    ),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                # Cache result if successful
                if self.enable_caching and result.success:
                    await self._cache_result(request, result.result)
                
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    result=result.result,
                    success=result.success,
                    execution_time=execution_time,
                    error=result.error,
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if retry_count <= request.max_retries:
                    logger.warning(f"Request {request.request_id} failed, retrying ({retry_count}/{request.max_retries}): {e}")
                    await asyncio.sleep(min(2 ** retry_count, 10))  # Exponential backoff
                else:
                    logger.error(f"Request {request.request_id} failed after {retry_count} attempts: {e}")
        
        # All retries failed
        return BatchToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            result=None,
            success=False,
            execution_time=time.time() - start_time,
            error=last_error,
            retry_count=retry_count
        )
    
    async def _get_cached_result(self, request: BatchToolRequest) -> Optional[Any]:
        """Get cached result for request"""
        try:
            from .intelligent_cache import get_cached_result
            return await get_cached_result(request.tool_name, request.arguments)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            return None
    
    async def _cache_result(self, request: BatchToolRequest, result: Any):
        """Cache result for request"""
        try:
            from .intelligent_cache import cache_tool_result
            await cache_tool_result(
                tool_name=request.tool_name,
                arguments=request.arguments,
                result=result,
                tags=request.tags
            )
        except Exception as e:
            logger.warning(f"Caching failed: {e}")
    
    def _update_stats(self, batch_result: BatchExecutionResult):
        """Update execution statistics"""
        self._execution_stats["total_batches"] += 1
        self._execution_stats["total_tools"] += len(batch_result.results)
        self._execution_stats["successful_tools"] += batch_result.success_count
        self._execution_stats["failed_tools"] += batch_result.failure_count
        self._execution_stats["cached_tools"] += batch_result.cached_count
        
        # Update averages
        total_batches = self._execution_stats["total_batches"]
        self._execution_stats["average_execution_time"] = (
            (self._execution_stats["average_execution_time"] * (total_batches - 1) + 
             batch_result.total_execution_time) / total_batches
        )
        
        self._execution_stats["average_batch_size"] = (
            (self._execution_stats["average_batch_size"] * (total_batches - 1) + 
             len(batch_result.results)) / total_batches
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processor statistics"""
        return {
            **self._execution_stats,
            "active_batches": len(self._active_batches),
            "completed_batches": len(self._batch_results)
        }
    
    def get_batch_result(self, batch_id: str) -> Optional[BatchExecutionResult]:
        """Get result for a specific batch"""
        return self._batch_results.get(batch_id)


# Global batch processor
_batch_processor: Optional[BatchProcessor] = None


async def get_batch_processor() -> BatchProcessor:
    """Get the global batch processor"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor


async def execute_tool_batch(
    requests: List[BatchToolRequest],
    execution_mode: BatchExecutionMode = BatchExecutionMode.HYBRID,
    failure_mode: BatchFailureMode = BatchFailureMode.CONTINUE_ON_ERROR,
    batch_id: Optional[str] = None
) -> BatchExecutionResult:
    """Execute a batch of tool requests"""
    processor = await get_batch_processor()
    return await processor.execute_batch(requests, execution_mode, failure_mode, batch_id)


async def get_batch_stats() -> Dict[str, Any]:
    """Get batch processor statistics"""
    processor = await get_batch_processor()
    return processor.get_stats()
