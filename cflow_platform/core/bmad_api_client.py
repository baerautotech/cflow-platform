"""
BMAD API Client for WebMCP Server

This module provides a client for communicating with the BMAD API service,
including authentication, connection pooling, and retry logic.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import ClientTimeout, ClientError
import json

logger = logging.getLogger(__name__)


class BMADAPIClient:
    """
    Client for communicating with the BMAD API service.
    
    This class handles HTTP communication with the BMAD API service,
    including authentication, connection pooling, and retry logic.
    """
    
    def __init__(self):
        """Initialize the BMAD API client."""
        self.base_url = os.getenv("BMAD_API_URL", "https://bmad-api.cerebral.baerautotech.com")
        self.jwt_token = os.getenv("BMAD_JWT_TOKEN", "")
        self.timeout = ClientTimeout(total=30, connect=10)
        self.max_retries = 3
        self.retry_delay = 1.0
        self._session: Optional[aiohttp.ClientSession] = None
        self._connection_pool_size = 10
        self._stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "retries_attempted": 0,
            "total_execution_time": 0.0
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp session with connection pooling.
        
        Returns:
            aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self._connection_pool_size,
                limit_per_host=self._connection_pool_size,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WebMCP-BMAD-Client/1.0"
                }
            )
        return self._session
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a BMAD tool via the BMAD API service.
        
        Args:
            tool_name: Name of the BMAD tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If tool execution fails
        """
        logger.info(f"Executing BMAD tool via API: {tool_name}")
        start_time = time.time()
        
        # Prepare request
        url = f"{self.base_url}/bmad/tools/{tool_name}/execute"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "arguments": arguments,
            "timestamp": time.time(),
            "client": "webmcp"
        }
        
        # Execute with retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self._stats["requests_sent"] += 1
                
                session = await self._get_session()
                async with session.post(url, json=payload, headers=headers) as response:
                    execution_time = time.time() - start_time
                    self._stats["total_execution_time"] += execution_time
                    
                    if response.status == 200:
                        result = await response.json()
                        self._stats["requests_successful"] += 1
                        logger.info(f"BMAD tool execution successful: {tool_name} (took {execution_time:.2f}s)")
                        return result
                    else:
                        error_text = await response.text()
                        error_msg = f"HTTP {response.status}: {error_text}"
                        logger.error(f"BMAD API error for {tool_name}: {error_msg}")
                        raise Exception(error_msg)
                        
            except ClientError as e:
                last_exception = e
                logger.warning(f"BMAD API client error for {tool_name} (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries:
                    self._stats["retries_attempted"] += 1
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self._stats["requests_failed"] += 1
                    logger.error(f"BMAD API execution failed after {self.max_retries + 1} attempts: {e}")
                    raise Exception(f"BMAD API execution failed: {e}")
            
            except Exception as e:
                last_exception = e
                logger.error(f"BMAD API execution error for {tool_name}: {e}")
                self._stats["requests_failed"] += 1
                raise
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise Exception("BMAD API execution failed for unknown reason")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the BMAD API service.
        
        Returns:
            Health check result
        """
        try:
            url = f"{self.base_url}/bmad/health"
            session = await self._get_session()
            
            async with session.get(url, timeout=ClientTimeout(total=5)) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "healthy": True,
                        "status": "ok",
                        "response": result
                    }
                else:
                    return {
                        "healthy": False,
                        "status": f"http_{response.status}",
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.warning(f"BMAD API health check failed: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """
        List available BMAD tools from the API service.
        
        Returns:
            List of available tools
        """
        try:
            url = f"{self.base_url}/bmad/tools"
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            
            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Failed to list BMAD tools: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with client statistics
        """
        stats = self._stats.copy()
        if stats["requests_sent"] > 0:
            stats["success_rate"] = stats["requests_successful"] / stats["requests_sent"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["requests_successful"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset client statistics."""
        self._stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "retries_attempted": 0,
            "total_execution_time": 0.0
        }
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            # Note: This is not ideal for async cleanup, but it's a fallback
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except Exception:
                pass
