"""
Health Checker for BMAD API Service

This module provides health checking functionality for the BMAD API service,
including caching and fallback logic.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Health checker for BMAD API service.
    
    This class provides health checking functionality with caching
    and fallback logic for the BMAD API service.
    """
    
    def __init__(self):
        """Initialize the health checker."""
        self.bmad_api_url = os.getenv("BMAD_API_URL", "https://bmad-api.cerebral.baerautotech.com")
        self.check_interval = 30.0  # seconds
        self.timeout = 5.0  # seconds
        self.cache_duration = 10.0  # seconds
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_check_time = 0.0
        self._last_health_status = False
        self._health_cache: Dict[str, Any] = {}
        self._stats = {
            "checks_performed": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "cache_hits": 0,
            "last_check_duration": 0.0
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp session.
        
        Returns:
            aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def is_bmad_api_healthy(self) -> bool:
        """
        Check if the BMAD API service is healthy.
        
        Returns:
            True if the API service is healthy
        """
        current_time = time.time()
        
        # Check cache first
        if (current_time - self._last_check_time) < self.cache_duration:
            self._stats["cache_hits"] += 1
            logger.debug("Using cached health status")
            return self._last_health_status
        
        # Perform health check
        try:
            start_time = time.time()
            health_result = await self._perform_health_check()
            check_duration = time.time() - start_time
            
            self._last_check_time = current_time
            self._last_health_status = health_result["healthy"]
            self._health_cache = health_result
            self._stats["checks_performed"] += 1
            self._stats["last_check_duration"] = check_duration
            
            if health_result["healthy"]:
                self._stats["successful_checks"] += 1
                logger.debug(f"BMAD API health check successful (took {check_duration:.2f}s)")
            else:
                self._stats["failed_checks"] += 1
                logger.warning(f"BMAD API health check failed: {health_result.get('error', 'Unknown error')}")
            
            return self._last_health_status
            
        except Exception as e:
            self._stats["checks_performed"] += 1
            self._stats["failed_checks"] += 1
            self._last_check_time = current_time
            self._last_health_status = False
            
            logger.error(f"BMAD API health check error: {e}")
            return False
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform the actual health check.
        
        Returns:
            Dictionary with health check result
        """
        try:
            url = f"{self.bmad_api_url}/bmad/health"
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "healthy": True,
                        "status": "ok",
                        "response": result,
                        "timestamp": time.time()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "healthy": False,
                        "status": f"http_{response.status}",
                        "error": f"HTTP {response.status}: {error_text}",
                        "timestamp": time.time()
                    }
        except asyncio.TimeoutError:
            return {
                "healthy": False,
                "status": "timeout",
                "error": f"Health check timeout after {self.timeout}s",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """
        Get detailed health information.
        
        Returns:
            Dictionary with detailed health information
        """
        # Force a fresh health check
        health_result = await self._perform_health_check()
        
        return {
            "bmad_api_url": self.bmad_api_url,
            "health_status": health_result,
            "cache_info": {
                "last_check_time": self._last_check_time,
                "cache_duration": self.cache_duration,
                "cached_status": self._last_health_status
            },
            "stats": self.get_stats()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get health checker statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self._stats.copy()
        
        if stats["checks_performed"] > 0:
            stats["success_rate"] = stats["successful_checks"] / stats["checks_performed"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset health checker statistics."""
        self._stats = {
            "checks_performed": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "cache_hits": 0,
            "last_check_duration": 0.0
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information.
        
        Returns:
            Dictionary with cache information
        """
        current_time = time.time()
        time_since_last_check = current_time - self._last_check_time
        
        return {
            "last_check_time": self._last_check_time,
            "time_since_last_check": time_since_last_check,
            "cache_duration": self.cache_duration,
            "cache_valid": time_since_last_check < self.cache_duration,
            "cached_status": self._last_health_status,
            "health_cache": self._health_cache
        }
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except Exception:
                pass
