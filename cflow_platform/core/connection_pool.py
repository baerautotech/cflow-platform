"""
Connection Pooling System for WebMCP Performance Enhancement

This module provides connection pooling for Redis, HTTP clients, and other external services
to improve resource utilization and reduce connection overhead.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass
import time
import weakref
from collections import defaultdict

import httpx
import redis.asyncio as redis
from supabase import create_client, Client as SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pools"""
    max_connections: int = 20
    min_connections: int = 5
    max_idle_time: float = 300.0  # 5 minutes
    connection_timeout: float = 10.0
    read_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


class HTTPConnectionPool:
    """Async HTTP connection pool with keep-alive and retry logic"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._last_used = time.time()
        self._request_count = 0
        
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=self.config.max_connections,
                        max_connections=self.config.max_connections,
                        keepalive_expiry=self.config.max_idle_time
                    ),
                    timeout=httpx.Timeout(
                        connect=self.config.connection_timeout,
                        read=self.config.read_timeout
                    ),
                    retries=self.config.retry_attempts
                )
                logger.info(f"Created HTTP client with {self.config.max_connections} max connections")
            
            self._last_used = time.time()
            self._request_count += 1
            return self._client
    
    async def close(self):
        """Close the HTTP client and cleanup resources"""
        async with self._lock:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
                self._client = None
                logger.info("HTTP client closed")


class RedisConnectionPool:
    """Async Redis connection pool with automatic reconnection"""
    
    def __init__(self, config: PoolConfig, redis_url: str):
        self.config = config
        self.redis_url = redis_url
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._last_used = time.time()
        self._connection_count = 0
        
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client with connection pooling"""
        async with self._lock:
            if self._client is None or not await self._is_connected():
                self._pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.config.max_connections,
                    retry_on_timeout=True,
                    socket_connect_timeout=self.config.connection_timeout,
                    socket_timeout=self.config.read_timeout
                )
                
                self._client = redis.Redis(
                    connection_pool=self._pool,
                    decode_responses=True
                )
                
                # Test connection
                await self._client.ping()
                logger.info(f"Created Redis client with {self.config.max_connections} max connections")
            
            self._last_used = time.time()
            self._connection_count += 1
            return self._client
    
    async def _is_connected(self) -> bool:
        """Check if Redis connection is alive"""
        try:
            if self._client:
                await self._client.ping()
                return True
        except Exception:
            pass
        return False
    
    async def close(self):
        """Close Redis connections and cleanup resources"""
        async with self._lock:
            if self._client:
                await self._client.aclose()
                self._client = None
            if self._pool:
                await self._pool.aclose()
                self._pool = None
            logger.info("Redis client closed")


class SupabaseConnectionPool:
    """Supabase client with connection management"""
    
    def __init__(self, config: PoolConfig, supabase_url: str, supabase_key: str):
        self.config = config
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self._client: Optional[SupabaseClient] = None
        self._lock = asyncio.Lock()
        self._last_used = time.time()
        self._request_count = 0
        
    async def get_client(self) -> SupabaseClient:
        """Get or create Supabase client"""
        async with self._lock:
            if self._client is None:
                self._client = create_client(
                    self.supabase_url,
                    self.supabase_key,
                    options={
                        "postgrest": {
                            "timeout": self.config.read_timeout
                        }
                    }
                )
                logger.info("Created Supabase client")
            
            self._last_used = time.time()
            self._request_count += 1
            return self._client
    
    async def close(self):
        """Close Supabase client"""
        async with self._lock:
            # Supabase client doesn't have explicit close method
            # but we can clear the reference
            self._client = None
            logger.info("Supabase client closed")


class ConnectionPoolManager:
    """
    Centralized connection pool manager for all external services.
    
    Provides:
    - HTTP connection pooling
    - Redis connection pooling  
    - Supabase client management
    - Automatic cleanup and monitoring
    """
    
    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self._pools: Dict[str, Any] = {}
        self._pool_metrics = defaultdict(lambda: {
            "requests": 0,
            "errors": 0,
            "avg_response_time": 0.0,
            "last_used": 0.0
        })
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the connection pool manager and background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_connections())
        self._monitoring_task = asyncio.create_task(self._monitor_pools())
        logger.info("ConnectionPoolManager started")
    
    async def stop(self):
        """Stop the connection pool manager and cleanup all connections"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        # Close all pools
        for pool in self._pools.values():
            if hasattr(pool, 'close'):
                await pool.close()
        
        logger.info("ConnectionPoolManager stopped")
    
    def get_http_pool(self, name: str = "default") -> HTTPConnectionPool:
        """Get HTTP connection pool"""
        if name not in self._pools:
            self._pools[name] = HTTPConnectionPool(self.config)
        return self._pools[name]
    
    def get_redis_pool(self, name: str = "default", redis_url: Optional[str] = None) -> RedisConnectionPool:
        """Get Redis connection pool"""
        if name not in self._pools:
            if redis_url is None:
                redis_url = "redis://localhost:6379"
            self._pools[name] = RedisConnectionPool(self.config, redis_url)
        return self._pools[name]
    
    def get_supabase_pool(
        self, 
        name: str = "default", 
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ) -> SupabaseConnectionPool:
        """Get Supabase connection pool"""
        if name not in self._pools:
            if supabase_url is None:
                supabase_url = os.environ.get("SUPABASE_URL", "")
            if supabase_key is None:
                supabase_key = os.environ.get("SUPABASE_KEY", "")
            
            self._pools[name] = SupabaseConnectionPool(
                self.config, supabase_url, supabase_key
            )
        return self._pools[name]
    
    async def _cleanup_idle_connections(self):
        """Background task to cleanup idle connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = time.time()
                idle_threshold = self.config.max_idle_time
                
                for name, pool in list(self._pools.items()):
                    if hasattr(pool, '_last_used'):
                        if current_time - pool._last_used > idle_threshold:
                            logger.info(f"Cleaning up idle connection pool: {name}")
                            await pool.close()
                            del self._pools[name]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
    
    async def _monitor_pools(self):
        """Background task to monitor pool health and metrics"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                for name, pool in self._pools.items():
                    metrics = self._pool_metrics[name]
                    
                    # Update last used time
                    if hasattr(pool, '_last_used'):
                        metrics["last_used"] = pool._last_used
                    
                    # Log pool status
                    if hasattr(pool, '_client') and pool._client:
                        if isinstance(pool, HTTPConnectionPool):
                            logger.debug(f"HTTP pool {name}: {pool._request_count} requests")
                        elif isinstance(pool, RedisConnectionPool):
                            logger.debug(f"Redis pool {name}: {pool._connection_count} connections")
                        elif isinstance(pool, SupabaseConnectionPool):
                            logger.debug(f"Supabase pool {name}: {pool._request_count} requests")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        return {
            "active_pools": len(self._pools),
            "pool_names": list(self._pools.keys()),
            "pool_metrics": dict(self._pool_metrics),
            "config": {
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "max_idle_time": self.config.max_idle_time
            }
        }


# Global connection pool manager
_pool_manager: Optional[ConnectionPoolManager] = None


async def get_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
        await _pool_manager.start()
    return _pool_manager


async def get_http_client(name: str = "default") -> httpx.AsyncClient:
    """Get HTTP client from pool"""
    manager = await get_pool_manager()
    pool = manager.get_http_pool(name)
    return await pool.get_client()


async def get_redis_client(name: str = "default", redis_url: Optional[str] = None) -> redis.Redis:
    """Get Redis client from pool"""
    manager = await get_pool_manager()
    pool = manager.get_redis_pool(name, redis_url)
    return await pool.get_client()


async def get_supabase_client(
    name: str = "default",
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None
) -> SupabaseClient:
    """Get Supabase client from pool"""
    manager = await get_pool_manager()
    pool = manager.get_supabase_pool(name, supabase_url, supabase_key)
    return await pool.get_client()


async def get_connection_metrics() -> Dict[str, Any]:
    """Get connection pool metrics"""
    manager = await get_pool_manager()
    return manager.get_metrics()
