"""
Intelligent Response Caching System for WebMCP Performance Enhancement

This module provides sophisticated caching capabilities including:
- Configurable TTL with intelligent expiration
- Cache compression and storage optimization
- Cache invalidation and refresh mechanisms
- Tool-specific caching strategies
- Memory-efficient storage with cleanup
"""

import asyncio
import hashlib
import json
import logging
import time
import zlib
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
from enum import Enum
import pickle
import threading

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types for different tool categories"""
    NO_CACHE = "no_cache"           # Never cache
    SHORT_TERM = "short_term"       # 5-15 minutes
    MEDIUM_TERM = "medium_term"     # 1-4 hours
    LONG_TERM = "long_term"         # 4-24 hours
    PERSISTENT = "persistent"       # Until manually invalidated
    INTELLIGENT = "intelligent"     # Dynamic TTL based on usage patterns


@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl_seconds: float = 300.0  # 5 minutes default
    strategy: CacheStrategy = CacheStrategy.SHORT_TERM
    compressed: bool = False
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    compression_ratio: float = 0.0
    average_access_time: float = 0.0
    hit_rate: float = 0.0


class IntelligentCache:
    """
    High-performance intelligent caching system with advanced features.
    
    Features:
    - Multiple caching strategies
    - Automatic compression for large entries
    - LRU eviction with size-based policies
    - Tag-based invalidation
    - Dependency tracking
    - Usage pattern analysis
    - Memory-efficient storage
    """
    
    def __init__(
        self,
        max_size_mb: int = 100,
        max_entries: int = 10000,
        compression_threshold_kb: int = 10,
        enable_compression: bool = True,
        cleanup_interval_seconds: float = 300.0
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.compression_threshold_bytes = compression_threshold_kb * 1024
        self.enable_compression = enable_compression
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._tag_index: Dict[str, set] = defaultdict(set)
        self._dependency_index: Dict[str, set] = defaultdict(set)
        
        # Statistics
        self._stats = CacheStats()
        self._access_times: List[float] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats_task: Optional[asyncio.Task] = None
        
        # Tool-specific cache strategies
        self._tool_strategies = self._initialize_tool_strategies()
        
        # Usage pattern analysis
        self._access_patterns: Dict[str, List[float]] = defaultdict(list)
        self._pattern_analysis_interval = 3600.0  # 1 hour
        
    def _initialize_tool_strategies(self) -> Dict[str, CacheStrategy]:
        """Initialize cache strategies for different tool types"""
        return {
            # System tools - short term
            "sys_test": CacheStrategy.SHORT_TERM,
            "sys_stats": CacheStrategy.SHORT_TERM,
            "sys_debug": CacheStrategy.SHORT_TERM,
            "sys_version": CacheStrategy.PERSISTENT,
            
            # Task tools - medium term
            "task_list": CacheStrategy.SHORT_TERM,
            "task_get": CacheStrategy.MEDIUM_TERM,
            "task_next": CacheStrategy.SHORT_TERM,
            "task_add": CacheStrategy.NO_CACHE,
            "task_update": CacheStrategy.NO_CACHE,
            
            # Research tools - medium term
            "doc_research": CacheStrategy.MEDIUM_TERM,
            "research": CacheStrategy.MEDIUM_TERM,
            
            # Linting tools - short term
            "lint_full": CacheStrategy.SHORT_TERM,
            "lint_bg": CacheStrategy.SHORT_TERM,
            "lint_status": CacheStrategy.SHORT_TERM,
            
            # Memory tools - medium term
            "memory_search": CacheStrategy.MEDIUM_TERM,
            "memory_stats": CacheStrategy.SHORT_TERM,
            
            # BMAD tools - intelligent caching
            "bmad_prd_get": CacheStrategy.LONG_TERM,
            "bmad_arch_get": CacheStrategy.LONG_TERM,
            "bmad_story_get": CacheStrategy.LONG_TERM,
            "bmad_doc_list": CacheStrategy.SHORT_TERM,
            "bmad_workflow_list": CacheStrategy.MEDIUM_TERM,
            "bmad_workflow_get": CacheStrategy.LONG_TERM,
            
            # Code intelligence - medium term
            "code.search_functions": CacheStrategy.MEDIUM_TERM,
            "code.index_functions": CacheStrategy.LONG_TERM,
            "code.call_paths": CacheStrategy.MEDIUM_TERM,
            
            # Default strategy
            "default": CacheStrategy.INTELLIGENT
        }
    
    async def start(self):
        """Start background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._stats_task = asyncio.create_task(self._stats_loop())
        logger.info("IntelligentCache started")
    
    async def stop(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._stats_task:
            self._stats_task.cancel()
        logger.info("IntelligentCache stopped")
    
    def _generate_cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate a cache key for tool execution"""
        # Sort arguments for consistent key generation
        sorted_args = json.dumps(arguments, sort_keys=True, default=str)
        
        # Create hash of tool name and arguments
        key_data = f"{tool_name}:{sorted_args}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_tool_strategy(self, tool_name: str) -> CacheStrategy:
        """Get cache strategy for a tool"""
        return self._tool_strategies.get(tool_name, self._tool_strategies["default"])
    
    def _calculate_ttl(self, tool_name: str, strategy: CacheStrategy) -> float:
        """Calculate TTL based on strategy and usage patterns"""
        if strategy == CacheStrategy.NO_CACHE:
            return 0.0
        elif strategy == CacheStrategy.SHORT_TERM:
            return 300.0  # 5 minutes
        elif strategy == CacheStrategy.MEDIUM_TERM:
            return 1800.0  # 30 minutes
        elif strategy == CacheStrategy.LONG_TERM:
            return 7200.0  # 2 hours
        elif strategy == CacheStrategy.PERSISTENT:
            return float('inf')
        elif strategy == CacheStrategy.INTELLIGENT:
            return self._calculate_intelligent_ttl(tool_name)
        else:
            return 300.0
    
    def _calculate_intelligent_ttl(self, tool_name: str) -> float:
        """Calculate intelligent TTL based on usage patterns"""
        if tool_name not in self._access_patterns:
            return 300.0  # Default 5 minutes
        
        patterns = self._access_patterns[tool_name]
        if len(patterns) < 2:
            return 300.0
        
        # Calculate average access interval
        intervals = [patterns[i+1] - patterns[i] for i in range(len(patterns)-1)]
        avg_interval = sum(intervals) / len(intervals)
        
        # TTL is 2x the average interval, with min/max bounds
        ttl = max(60.0, min(3600.0, avg_interval * 2))
        return ttl
    
    def _compress_value(self, value: Any) -> Tuple[Any, bool]:
        """Compress value if beneficial"""
        if not self.enable_compression:
            return value, False
        
        try:
            # Serialize to bytes
            serialized = pickle.dumps(value)
            
            if len(serialized) < self.compression_threshold_bytes:
                return value, False
            
            # Compress
            compressed = zlib.compress(serialized, level=6)
            
            # Only use compression if it saves significant space
            if len(compressed) < len(serialized) * 0.8:
                return compressed, True
            
            return value, False
            
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return value, False
    
    def _decompress_value(self, value: Any, compressed: bool) -> Any:
        """Decompress value if needed"""
        if not compressed:
            return value
        
        try:
            decompressed = zlib.decompress(value)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return None
    
    def _calculate_size(self, entry: CacheEntry) -> int:
        """Calculate size of cache entry"""
        try:
            if entry.compressed:
                return len(entry.value)
            else:
                return len(pickle.dumps(entry.value))
        except Exception:
            return 0
    
    def _should_evict(self) -> bool:
        """Check if eviction is needed"""
        return (
            len(self._cache) >= self.max_entries or
            self._stats.total_size_bytes >= self.max_size_bytes
        )
    
    def _evict_entries(self, target_size: int = 0):
        """Evict entries using LRU policy"""
        evicted_count = 0
        
        while self._should_evict():
            if not self._cache:
                break
            
            # Remove least recently used entry
            key, entry = self._cache.popitem(last=False)
            
            # Update statistics
            self._stats.eviction_count += 1
            self._stats.total_entries -= 1
            self._stats.total_size_bytes -= entry.size_bytes
            
            # Remove from indexes
            for tag in entry.tags:
                self._tag_index[tag].discard(key)
            
            for dep in entry.dependencies:
                self._dependency_index[dep].discard(key)
            
            evicted_count += 1
            
            if target_size > 0 and self._stats.total_size_bytes <= target_size:
                break
        
        if evicted_count > 0:
            logger.debug(f"Evicted {evicted_count} cache entries")
    
    async def get(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """Get cached result for tool execution"""
        start_time = time.time()
        
        with self._lock:
            key = self._generate_cache_key(tool_name, arguments)
            
            if key not in self._cache:
                self._stats.miss_count += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() - entry.created_at > entry.ttl_seconds:
                del self._cache[key]
                self._stats.miss_count += 1
                self._stats.total_entries -= 1
                self._stats.total_size_bytes -= entry.size_bytes
                return None
            
            # Update access statistics
            entry.last_accessed = time.time()
            entry.access_count += 1
            self._stats.hit_count += 1
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            # Record access pattern
            self._access_patterns[tool_name].append(time.time())
            
            # Decompress if needed
            value = self._decompress_value(entry.value, entry.compressed)
            
            # Update access time statistics
            access_time = time.time() - start_time
            self._access_times.append(access_time)
            if len(self._access_times) > 1000:
                self._access_times.pop(0)
            
            return value
    
    async def set(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        ttl_seconds: Optional[float] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """Cache tool execution result"""
        with self._lock:
            key = self._generate_cache_key(tool_name, arguments)
            
            # Get cache strategy
            strategy = self._get_tool_strategy(tool_name)
            if strategy == CacheStrategy.NO_CACHE:
                return False
            
            # Calculate TTL
            if ttl_seconds is None:
                ttl_seconds = self._calculate_ttl(tool_name, strategy)
            
            # Compress if beneficial
            compressed_value, is_compressed = self._compress_value(result)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=compressed_value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl_seconds=ttl_seconds,
                strategy=strategy,
                compressed=is_compressed,
                tags=tags or [],
                dependencies=dependencies or []
            )
            
            # Calculate size
            entry.size_bytes = self._calculate_size(entry)
            
            # Check if we need to evict
            if self._should_evict():
                self._evict_entries()
            
            # Add to cache
            self._cache[key] = entry
            self._stats.total_entries += 1
            self._stats.total_size_bytes += entry.size_bytes
            
            # Update indexes
            for tag in entry.tags:
                self._tag_index[tag].add(key)
            
            for dep in entry.dependencies:
                self._dependency_index[dep].add(key)
            
            # Update compression ratio
            if is_compressed:
                original_size = len(pickle.dumps(result))
                self._stats.compression_ratio = (
                    (self._stats.compression_ratio * (self._stats.total_entries - 1) + 
                     (original_size - entry.size_bytes) / original_size) / 
                    self._stats.total_entries
                )
            
            return True
    
    async def invalidate(self, pattern: str = None, tags: List[str] = None, dependencies: List[str] = None):
        """Invalidate cache entries"""
        with self._lock:
            keys_to_remove = set()
            
            if pattern:
                # Pattern-based invalidation
                for key in self._cache:
                    if pattern in key:
                        keys_to_remove.add(key)
            
            if tags:
                # Tag-based invalidation
                for tag in tags:
                    keys_to_remove.update(self._tag_index.get(tag, set()))
            
            if dependencies:
                # Dependency-based invalidation
                for dep in dependencies:
                    keys_to_remove.update(self._dependency_index.get(dep, set()))
            
            # Remove entries
            for key in keys_to_remove:
                if key in self._cache:
                    entry = self._cache[key]
                    del self._cache[key]
                    
                    self._stats.total_entries -= 1
                    self._stats.total_size_bytes -= entry.size_bytes
                    
                    # Remove from indexes
                    for tag in entry.tags:
                        self._tag_index[tag].discard(key)
                    
                    for dep in entry.dependencies:
                        self._dependency_index[dep].discard(key)
            
            if keys_to_remove:
                logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    async def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._tag_index.clear()
            self._dependency_index.clear()
            self._stats.total_entries = 0
            self._stats.total_size_bytes = 0
            logger.info("Cache cleared")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            # Calculate hit rate
            total_requests = self._stats.hit_count + self._stats.miss_count
            self._stats.hit_rate = (
                self._stats.hit_count / total_requests if total_requests > 0 else 0.0
            )
            
            # Calculate average access time
            if self._access_times:
                self._stats.average_access_time = sum(self._access_times) / len(self._access_times)
            
            return self._stats
    
    async def _cleanup_loop(self):
        """Background task for cache cleanup"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time - entry.created_at > entry.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                entry = self._cache[key]
                del self._cache[key]
                
                self._stats.total_entries -= 1
                self._stats.total_size_bytes -= entry.size_bytes
                
                # Remove from indexes
                for tag in entry.tags:
                    self._tag_index[tag].discard(key)
                
                for dep in entry.dependencies:
                    self._dependency_index[dep].discard(key)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _stats_loop(self):
        """Background task for statistics updates"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Update every minute
                
                # Clean up old access patterns
                current_time = time.time()
                for tool_name in list(self._access_patterns.keys()):
                    patterns = self._access_patterns[tool_name]
                    # Keep only patterns from the last hour
                    self._access_patterns[tool_name] = [
                        t for t in patterns if current_time - t < self._pattern_analysis_interval
                    ]
                    
                    if not self._access_patterns[tool_name]:
                        del self._access_patterns[tool_name]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats update error: {e}")


# Global cache instance
_cache: Optional[IntelligentCache] = None


async def get_cache() -> IntelligentCache:
    """Get the global intelligent cache instance"""
    global _cache
    if _cache is None:
        _cache = IntelligentCache()
        await _cache.start()
    return _cache


async def cache_tool_result(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any,
    ttl_seconds: Optional[float] = None,
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None
) -> bool:
    """Cache a tool execution result"""
    cache = await get_cache()
    return await cache.set(tool_name, arguments, result, ttl_seconds, tags, dependencies)


async def get_cached_result(
    tool_name: str,
    arguments: Dict[str, Any]
) -> Optional[Any]:
    """Get cached tool execution result"""
    cache = await get_cache()
    return await cache.get(tool_name, arguments)


async def invalidate_cache(
    pattern: str = None,
    tags: List[str] = None,
    dependencies: List[str] = None
):
    """Invalidate cache entries"""
    cache = await get_cache()
    await cache.invalidate(pattern, tags, dependencies)


async def get_cache_stats() -> CacheStats:
    """Get cache statistics"""
    cache = await get_cache()
    return cache.get_stats()
