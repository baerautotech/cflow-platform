"""
Caching and Performance Optimization for WebMCP

This module provides intelligent caching, connection pooling, batch processing,
and memory optimization for the WebMCP server.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
import aiohttp
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl_seconds: int = 300  # 5 minutes default
    max_size: int = 10000
    strategy: CacheStrategy = CacheStrategy.TTL
    enable_compression: bool = True
    enable_serialization: bool = True


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[float] = None


class PerformanceCache:
    """High-performance caching system with multiple strategies"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.redis_client = None
        self.compression_enabled = config.enable_compression
        self.serialization_enabled = config.enable_serialization
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "total_size": 0
        }
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the cache with Redis backend"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Cache initialized with Redis backend")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            # Try Redis first if available
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    return self._deserialize(value)
            
            # Fallback to in-memory cache
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl and time.time() - entry.created_at > entry.ttl:
                    await self.delete(key)
                    self.stats["misses"] += 1
                    return None
                
                # Update access metadata
                entry.accessed_at = time.time()
                entry.access_count += 1
                self._update_access_order(key)
                
                self.stats["hits"] += 1
                return entry.value
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.config.ttl_seconds
            serialized_value = self._serialize(value)
            
            # Set in Redis if available
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
            
            # Set in in-memory cache
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                ttl=ttl
            )
            
            self.cache[key] = entry
            self._update_access_order(key)
            
            # Check size limits
            if len(self.cache) > self.config.max_size:
                await self._evict_entries()
            
            self.stats["sets"] += 1
            self.stats["total_size"] = len(self.cache)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            # Delete from Redis if available
            if self.redis_client:
                await self.redis_client.delete(key)
            
            # Delete from in-memory cache
            if key in self.cache:
                del self.cache[key]
                self.access_order.remove(key)
                self.stats["deletes"] += 1
                self.stats["total_size"] = len(self.cache)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def _evict_entries(self):
        """Evict entries based on strategy"""
        if self.config.strategy == CacheStrategy.LRU:
            # Remove least recently used
            while len(self.cache) > self.config.max_size:
                if self.access_order:
                    oldest_key = self.access_order[0]
                    await self.delete(oldest_key)
                    self.stats["evictions"] += 1
        
        elif self.config.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            while len(self.cache) > self.config.max_size:
                if self.cache:
                    least_used_key = min(
                        self.cache.keys(),
                        key=lambda k: self.cache[k].access_count
                    )
                    await self.delete(least_used_key)
                    self.stats["evictions"] += 1
    
    def _update_access_order(self, key: str):
        """Update access order for LRU strategy"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for storage"""
        if self.serialization_enabled:
            return json.dumps(value, default=str)
        return str(value)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage"""
        if self.serialization_enabled:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "cache_size": len(self.cache),
            "max_size": self.config.max_size,
            "utilization_percent": (len(self.cache) / self.config.max_size * 100)
        }


class ConnectionPoolManager:
    """Connection pool manager for external services"""
    
    def __init__(self):
        self.http_pools: Dict[str, aiohttp.ClientSession] = {}
        self.redis_pools: Dict[str, redis.ConnectionPool] = {}
        self.pool_configs = {
            "default": {
                "max_connections": 100,
                "max_connections_per_host": 50,
                "ttl_dns_cache": 300
            }
        }
    
    async def get_http_session(self, name: str = "default") -> aiohttp.ClientSession:
        """Get HTTP session with connection pooling"""
        if name not in self.http_pools:
            config = self.pool_configs.get(name, self.pool_configs["default"])
            
            connector = aiohttp.TCPConnector(
                limit=config["max_connections"],
                limit_per_host=config["max_connections_per_host"],
                ttl_dns_cache=config["ttl_dns_cache"],
                use_dns_cache=True
            )
            
            self.http_pools[name] = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        
        return self.http_pools[name]
    
    async def get_redis_pool(self, name: str = "default", **kwargs) -> redis.ConnectionPool:
        """Get Redis connection pool"""
        if name not in self.redis_pools:
            self.redis_pools[name] = redis.ConnectionPool(
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 6379),
                db=kwargs.get("db", 0),
                max_connections=kwargs.get("max_connections", 100),
                decode_responses=True
            )
        
        return self.redis_pools[name]
    
    async def close_all(self):
        """Close all connection pools"""
        for session in self.http_pools.values():
            await session.close()
        
        for pool in self.redis_pools.values():
            await pool.disconnect()


class BatchProcessor:
    """Batch processing for multiple tool calls"""
    
    def __init__(self, max_batch_size: int = 100, batch_timeout: float = 0.1):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.batch_task = None
    
    async def add_request(self, request: Dict[str, Any]) -> Any:
        """Add request to batch processing"""
        async with self.batch_lock:
            self.pending_requests.append(request)
            
            # Start batch processing if not already running
            if not self.batch_task or self.batch_task.done():
                self.batch_task = asyncio.create_task(self._process_batch())
            
            # Wait for batch to complete
            return await self._wait_for_result(request.get("request_id"))
    
    async def _process_batch(self):
        """Process pending requests in batch"""
        await asyncio.sleep(self.batch_timeout)
        
        async with self.batch_lock:
            if not self.pending_requests:
                return
            
            batch = self.pending_requests[:self.max_batch_size]
            self.pending_requests = self.pending_requests[self.max_batch_size:]
        
        # Process batch
        results = await self._execute_batch(batch)
        
        # Store results for retrieval
        for result in results:
            await self._store_result(result)
    
    async def _execute_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute batch of requests"""
        # This is a simplified implementation
        # In practice, you'd want to group requests by tool type
        # and execute them efficiently
        
        results = []
        for request in batch:
            try:
                # Simulate batch execution
                result = {
                    "request_id": request.get("request_id"),
                    "result": {"status": "batch_executed", "data": request.get("data")},
                    "success": True
                }
                results.append(result)
            except Exception as e:
                result = {
                    "request_id": request.get("request_id"),
                    "error": str(e),
                    "success": False
                }
                results.append(result)
        
        return results
    
    async def _store_result(self, result: Dict[str, Any]):
        """Store result for retrieval"""
        # In practice, you'd store this in a shared cache or database
        pass
    
    async def _wait_for_result(self, request_id: str) -> Any:
        """Wait for batch result"""
        # Simplified implementation
        await asyncio.sleep(0.1)
        return {"status": "batch_completed", "request_id": request_id}


class MemoryOptimizer:
    """Memory optimization and monitoring"""
    
    def __init__(self, max_memory_mb: int = 512):
        self.max_memory_mb = max_memory_mb
        self.current_usage_mb = 0.0
        self.cleanup_threshold = 0.8  # 80% of max memory
        self.cleanup_lock = asyncio.Lock()
    
    async def allocate_memory(self, size_mb: float) -> bool:
        """Allocate memory and check limits"""
        async with self.cleanup_lock:
            if self.current_usage_mb + size_mb > self.max_memory_mb:
                # Try to cleanup memory
                await self._cleanup_memory()
                
                if self.current_usage_mb + size_mb > self.max_memory_mb:
                    return False
            
            self.current_usage_mb += size_mb
            return True
    
    async def release_memory(self, size_mb: float):
        """Release allocated memory"""
        async with self.cleanup_lock:
            self.current_usage_mb = max(0.0, self.current_usage_mb - size_mb)
    
    async def _cleanup_memory(self):
        """Cleanup memory when approaching limits"""
        if self.current_usage_mb > self.max_memory_mb * self.cleanup_threshold:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Log memory cleanup
            logger.info(f"Memory cleanup performed. Usage: {self.current_usage_mb:.2f}MB")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "current_usage_mb": self.current_usage_mb,
            "max_memory_mb": self.max_memory_mb,
            "utilization_percent": (self.current_usage_mb / self.max_memory_mb * 100),
            "available_mb": self.max_memory_mb - self.current_usage_mb
        }


class PerformanceMetrics:
    """Performance metrics collection"""
    
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "throughput": 0,
            "error_rate": 0.0,
            "cache_hit_rate": 0.0,
            "memory_usage": 0.0,
            "active_connections": 0
        }
        self.start_time = time.time()
    
    def record_response_time(self, response_time: float):
        """Record response time"""
        self.metrics["response_times"].append(response_time)
        
        # Keep only last 1000 measurements
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def record_throughput(self, requests_per_second: float):
        """Record throughput"""
        self.metrics["throughput"] = requests_per_second
    
    def record_error_rate(self, error_rate: float):
        """Record error rate"""
        self.metrics["error_rate"] = error_rate
    
    def record_cache_hit_rate(self, hit_rate: float):
        """Record cache hit rate"""
        self.metrics["cache_hit_rate"] = hit_rate
    
    def record_memory_usage(self, usage_mb: float):
        """Record memory usage"""
        self.metrics["memory_usage"] = usage_mb
    
    def record_active_connections(self, connections: int):
        """Record active connections"""
        self.metrics["active_connections"] = connections
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        response_times = self.metrics["response_times"]
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
            "throughput_rps": self.metrics["throughput"],
            "error_rate_percent": self.metrics["error_rate"],
            "cache_hit_rate_percent": self.metrics["cache_hit_rate"],
            "memory_usage_mb": self.metrics["memory_usage"],
            "active_connections": self.metrics["active_connections"]
        }
