"""
BMAD API Performance Optimizer

This module provides performance optimization features including:
- Response caching
- Rate limiting
- Connection pooling
- Request deduplication
- Circuit breaker pattern
"""

import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import weakref
from functools import wraps
import httpx
from enum import Enum

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types."""
    LRU = "lru"
    TTL = "ttl"
    LFU = "lfu"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl)


@dataclass
class RateLimitRule:
    """Rate limiting rule."""
    max_requests: int
    time_window: int  # seconds
    burst_limit: Optional[int] = None
    key_func: Optional[callable] = None


@dataclass
class RateLimitState:
    """Rate limiting state for a key."""
    requests: deque = field(default_factory=deque)
    burst_count: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class PerformanceOptimizer:
    """
    Performance optimization manager for BMAD API.
    
    Provides caching, rate limiting, connection pooling,
    and other performance optimizations.
    """
    
    def __init__(self, 
                 cache_size: int = 1000,
                 cache_strategy: CacheStrategy = CacheStrategy.LRU,
                 default_ttl: int = 300,
                 rate_limit_rules: Optional[Dict[str, RateLimitRule]] = None,
                 connection_pool_size: int = 100,
                 circuit_breaker_threshold: int = 5,
                 circuit_breaker_timeout: int = 60):
        """Initialize the performance optimizer."""
        self.cache_size = cache_size
        self.cache_strategy = cache_strategy
        self.default_ttl = default_ttl
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: deque = deque()
        
        # Rate limiting
        self.rate_limit_rules = rate_limit_rules or {}
        self._rate_limit_states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        
        # Connection pooling
        self._connection_pools: Dict[str, httpx.AsyncClient] = {}
        self.connection_pool_size = connection_pool_size
        
        # Circuit breaker
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self._circuit_breaker_states: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'failures': 0,
            'last_failure': None,
            'state': 'closed'  # closed, open, half-open
        })
        
        # Statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_hits': 0,
            'circuit_breaker_trips': 0,
            'total_requests': 0,
            'avg_response_time': 0.0
        }
        
        # Start cleanup tasks
        self._start_cleanup_tasks()
    
    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call."""
        # Create a deterministic key from function name and arguments
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            self._stats['cache_misses'] += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry.is_expired():
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._stats['cache_misses'] += 1
            return None
        
        # Update access metadata
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        
        # Update access order for LRU
        if self.cache_strategy == CacheStrategy.LRU:
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
        
        self._stats['cache_hits'] += 1
        return entry.value
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        # Remove oldest entries if cache is full
        while len(self._cache) >= self.cache_size:
            self._evict_oldest()
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            ttl=ttl or self.default_ttl
        )
        
        self._cache[key] = entry
        
        # Update access order
        if self.cache_strategy == CacheStrategy.LRU:
            self._access_order.append(key)
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entry based on strategy."""
        if not self._cache:
            return
        
        if self.cache_strategy == CacheStrategy.LRU:
            # Remove least recently used
            if self._access_order:
                oldest_key = self._access_order.popleft()
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
        elif self.cache_strategy == CacheStrategy.LFU:
            # Remove least frequently used
            oldest_key = min(self._cache.keys(), 
                           key=lambda k: self._cache[k].access_count)
            del self._cache[oldest_key]
        else:
            # Remove first entry (FIFO)
            oldest_key = next(iter(self._cache.keys()))
            del self._cache[oldest_key]
    
    def check_rate_limit(self, key: str, rule_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""
        if rule_name not in self.rate_limit_rules:
            return True, {}
        
        rule = self.rate_limit_rules[rule_name]
        state = self._rate_limit_states[key]
        now = datetime.utcnow()
        
        # Clean old requests outside time window
        cutoff_time = now - timedelta(seconds=rule.time_window)
        while state.requests and state.requests[0] < cutoff_time:
            state.requests.popleft()
        
        # Check burst limit
        if rule.burst_limit and state.burst_count >= rule.burst_limit:
            self._stats['rate_limit_hits'] += 1
            return False, {
                'error': 'Burst limit exceeded',
                'burst_limit': rule.burst_limit,
                'current_burst': state.burst_count
            }
        
        # Check rate limit
        if len(state.requests) >= rule.max_requests:
            self._stats['rate_limit_hits'] += 1
            return False, {
                'error': 'Rate limit exceeded',
                'max_requests': rule.max_requests,
                'time_window': rule.time_window,
                'current_requests': len(state.requests)
            }
        
        # Add current request
        state.requests.append(now)
        state.burst_count += 1
        
        # Reset burst count after time window
        if now - state.last_reset > timedelta(seconds=rule.time_window):
            state.burst_count = 1
            state.last_reset = now
        
        return True, {}
    
    def get_connection_pool(self, base_url: str) -> httpx.AsyncClient:
        """Get or create connection pool for base URL."""
        if base_url not in self._connection_pools:
            self._connection_pools[base_url] = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=self.connection_pool_size,
                    max_connections=self.connection_pool_size
                ),
                timeout=httpx.Timeout(30.0)
            )
        return self._connection_pools[base_url]
    
    def check_circuit_breaker(self, service_name: str) -> Tuple[bool, str]:
        """Check circuit breaker state for service."""
        state = self._circuit_breaker_states[service_name]
        now = datetime.utcnow()
        
        if state['state'] == 'open':
            # Check if timeout has passed
            if state['last_failure'] and \
               (now - state['last_failure']).total_seconds() > self.circuit_breaker_timeout:
                state['state'] = 'half-open'
                return True, 'half-open'
            return False, 'open'
        
        return True, state['state']
    
    def record_circuit_breaker_success(self, service_name: str) -> None:
        """Record successful request for circuit breaker."""
        state = self._circuit_breaker_states[service_name]
        if state['state'] == 'half-open':
            state['state'] = 'closed'
            state['failures'] = 0
    
    def record_circuit_breaker_failure(self, service_name: str) -> None:
        """Record failed request for circuit breaker."""
        state = self._circuit_breaker_states[service_name]
        state['failures'] += 1
        state['last_failure'] = datetime.utcnow()
        
        if state['failures'] >= self.circuit_breaker_threshold:
            state['state'] = 'open'
            self._stats['circuit_breaker_trips'] += 1
    
    def _start_cleanup_tasks(self) -> None:
        """Start background cleanup tasks."""
        async def cleanup_cache():
            while True:
                try:
                    # Remove expired entries
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if entry.is_expired()
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                        if key in self._access_order:
                            self._access_order.remove(key)
                    
                    await asyncio.sleep(60)  # Cleanup every minute
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
                    await asyncio.sleep(60)
        
        async def cleanup_rate_limits():
            while True:
                try:
                    # Clean up old rate limit states
                    cutoff_time = datetime.utcnow() - timedelta(hours=1)
                    keys_to_remove = []
                    
                    for key, state in self._rate_limit_states.items():
                        if state.last_reset < cutoff_time and not state.requests:
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del self._rate_limit_states[key]
                    
                    await asyncio.sleep(300)  # Cleanup every 5 minutes
                except Exception as e:
                    logger.error(f"Rate limit cleanup error: {e}")
                    await asyncio.sleep(300)
        
        # Start cleanup tasks
        asyncio.create_task(cleanup_cache())
        asyncio.create_task(cleanup_rate_limits())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        cache_hit_rate = 0.0
        total_cache_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        if total_cache_requests > 0:
            cache_hit_rate = self._stats['cache_hits'] / total_cache_requests
        
        return {
            'cache': {
                'size': len(self._cache),
                'max_size': self.cache_size,
                'hit_rate': cache_hit_rate,
                'hits': self._stats['cache_hits'],
                'misses': self._stats['cache_misses']
            },
            'rate_limiting': {
                'hits': self._stats['rate_limit_hits'],
                'active_keys': len(self._rate_limit_states)
            },
            'circuit_breaker': {
                'trips': self._stats['circuit_breaker_trips'],
                'active_services': len(self._circuit_breaker_states)
            },
            'connection_pools': {
                'active_pools': len(self._connection_pools)
            },
            'requests': {
                'total': self._stats['total_requests'],
                'avg_response_time': self._stats['avg_response_time']
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown the performance optimizer."""
        # Close all connection pools
        for pool in self._connection_pools.values():
            await pool.aclose()
        self._connection_pools.clear()


# Decorator functions for easy integration
def cached(ttl: Optional[int] = None, key_func: Optional[callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = getattr(wrapper, '_optimizer', None)
            if not optimizer:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = optimizer.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = optimizer.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            optimizer.set_cache(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def rate_limited(rule_name: str, key_func: Optional[callable] = None):
    """Decorator for rate limiting function calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = getattr(wrapper, '_optimizer', None)
            if not optimizer:
                return await func(*args, **kwargs)
            
            # Generate rate limit key
            if key_func:
                rate_key = key_func(*args, **kwargs)
            else:
                rate_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check rate limit
            allowed, error_info = optimizer.check_rate_limit(rate_key, rule_name)
            if not allowed:
                raise Exception(f"Rate limit exceeded: {error_info}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def circuit_breaker(service_name: str):
    """Decorator for circuit breaker pattern."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = getattr(wrapper, '_optimizer', None)
            if not optimizer:
                return await func(*args, **kwargs)
            
            # Check circuit breaker
            allowed, state = optimizer.check_circuit_breaker(service_name)
            if not allowed:
                raise Exception(f"Circuit breaker is open for service: {service_name}")
            
            try:
                result = await func(*args, **kwargs)
                optimizer.record_circuit_breaker_success(service_name)
                return result
            except Exception as e:
                optimizer.record_circuit_breaker_failure(service_name)
                raise
        
        return wrapper
    return decorator


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer(
    cache_size=2000,
    cache_strategy=CacheStrategy.LRU,
    default_ttl=600,  # 10 minutes
    rate_limit_rules={
        'api_requests': RateLimitRule(max_requests=100, time_window=60),
        'workflow_execution': RateLimitRule(max_requests=10, time_window=60),
        'provider_requests': RateLimitRule(max_requests=50, time_window=60, burst_limit=5)
    },
    connection_pool_size=200,
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=120
)
