"""
BMAD Tool Router for WebMCP Server

This module provides routing logic for BMAD tools, directing them to either
the BMAD API service or local handlers based on configuration and health status.
"""

import logging
from typing import Dict, Any, Optional
from .bmad_api_client import BMADAPIClient
from .feature_flags import FeatureFlags
from .health_checker import HealthChecker
from .direct_client import execute_mcp_tool

logger = logging.getLogger(__name__)


class BMADToolRouter:
    """
    Routes BMAD tools to either cluster execution or local handlers.
    
    This class implements the core routing logic for BMAD tools, providing
    fallback capabilities and health checking.
    """
    
    def __init__(self):
        """Initialize the BMAD tool router."""
        self.bmad_api_client = BMADAPIClient()
        self.feature_flags = FeatureFlags()
        self.health_checker = HealthChecker()
        self._routing_stats = {
            "cluster_executions": 0,
            "local_executions": 0,
            "fallback_executions": 0,
            "errors": 0
        }
    
    async def route_bmad_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a BMAD tool to either cluster or local execution.
        
        Args:
            tool_name: Name of the BMAD tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If tool execution fails
        """
        logger.info(f"Routing BMAD tool: {tool_name}")
        
        # Check if cluster execution is enabled
        if not self.feature_flags.is_enabled("bmad_cluster_execution"):
            logger.info(f"Cluster execution disabled, routing {tool_name} to local")
            return await self._route_to_local(tool_name, arguments, "feature_disabled")
        
        # Check BMAD API health
        if not await self.health_checker.is_bmad_api_healthy():
            logger.warning(f"BMAD API unhealthy, routing {tool_name} to local")
            return await self._route_to_local(tool_name, arguments, "api_unhealthy")
        
        # Route to cluster execution
        try:
            logger.info(f"Routing {tool_name} to cluster execution")
            result = await self.bmad_api_client.execute_tool(tool_name, arguments)
            self._routing_stats["cluster_executions"] += 1
            logger.info(f"Cluster execution successful for {tool_name}")
            return result
        except Exception as e:
            logger.error(f"Cluster execution failed for {tool_name}: {e}")
            self._routing_stats["errors"] += 1
            
            # Fallback to local execution
            logger.info(f"Falling back to local execution for {tool_name}")
            return await self._route_to_local(tool_name, arguments, "cluster_error")
    
    async def _route_to_local(self, tool_name: str, arguments: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """
        Route tool to local execution.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            reason: Reason for local routing
            
        Returns:
            Tool execution result
        """
        logger.info(f"Routing {tool_name} to local execution (reason: {reason})")
        
        try:
            result = await execute_mcp_tool(tool_name, **arguments)
            
            if reason == "cluster_error":
                self._routing_stats["fallback_executions"] += 1
            else:
                self._routing_stats["local_executions"] += 1
            
            logger.info(f"Local execution successful for {tool_name}")
            return result
        except Exception as e:
            logger.error(f"Local execution failed for {tool_name}: {e}")
            self._routing_stats["errors"] += 1
            raise
    
    def get_routing_stats(self) -> Dict[str, int]:
        """
        Get routing statistics.
        
        Returns:
            Dictionary with routing statistics
        """
        return self._routing_stats.copy()
    
    def reset_routing_stats(self) -> None:
        """Reset routing statistics."""
        self._routing_stats = {
            "cluster_executions": 0,
            "local_executions": 0,
            "fallback_executions": 0,
            "errors": 0
        }
    
    def is_bmad_tool(self, tool_name: str) -> bool:
        """
        Check if a tool name is a BMAD tool.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if the tool is a BMAD tool
        """
        return tool_name.startswith("bmad_")
    
    async def get_routing_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get routing information for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with routing information
        """
        cluster_enabled = self.feature_flags.is_enabled("bmad_cluster_execution")
        api_healthy = await self.health_checker.is_bmad_api_healthy()
        
        return {
            "tool_name": tool_name,
            "is_bmad_tool": self.is_bmad_tool(tool_name),
            "cluster_execution_enabled": cluster_enabled,
            "bmad_api_healthy": api_healthy,
            "will_route_to_cluster": cluster_enabled and api_healthy,
            "routing_stats": self.get_routing_stats()
        }
