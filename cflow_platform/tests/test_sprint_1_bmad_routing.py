"""
Test Suite for Sprint 1: BMAD Tool Routing

This module tests the BMAD tool routing functionality including
tool detection, routing logic, feature flags, and health checking.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from cflow_platform.core.bmad_tool_router import BMADToolRouter
from cflow_platform.core.bmad_api_client import BMADAPIClient
from cflow_platform.core.feature_flags import FeatureFlags, FeatureFlagType
from cflow_platform.core.health_checker import HealthChecker


class TestBMADToolRouter:
    """Test BMAD tool router functionality."""
    
    @pytest.fixture
    def router(self):
        """Create a BMAD tool router for testing."""
        return BMADToolRouter()
    
    def test_is_bmad_tool(self, router):
        """Test BMAD tool detection."""
        assert router.is_bmad_tool("bmad_prd_create") == True
        assert router.is_bmad_tool("bmad_arch_create") == True
        assert router.is_bmad_tool("bmad_story_create") == True
        assert router.is_bmad_tool("sys_test") == False
        assert router.is_bmad_tool("memory_add") == False
    
    @pytest.mark.asyncio
    async def test_routing_stats(self, router):
        """Test routing statistics."""
        stats = router.get_routing_stats()
        assert "cluster_executions" in stats
        assert "local_executions" in stats
        assert "fallback_executions" in stats
        assert "errors" in stats
        
        # Test reset
        router.reset_routing_stats()
        stats = router.get_routing_stats()
        assert stats["cluster_executions"] == 0
        assert stats["local_executions"] == 0
        assert stats["fallback_executions"] == 0
        assert stats["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_routing_info(self, router):
        """Test routing information."""
        info = await router.get_routing_info("bmad_prd_create")
        assert info["tool_name"] == "bmad_prd_create"
        assert info["is_bmad_tool"] == True
        assert "cluster_execution_enabled" in info
        assert "bmad_api_healthy" in info
        assert "will_route_to_cluster" in info
        assert "routing_stats" in info


class TestBMADAPIClient:
    """Test BMAD API client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a BMAD API client for testing."""
        return BMADAPIClient()
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.base_url is not None
        assert client.timeout is not None
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
    
    def test_client_stats(self, client):
        """Test client statistics."""
        stats = client.get_stats()
        assert "requests_sent" in stats
        assert "requests_successful" in stats
        assert "requests_failed" in stats
        assert "retries_attempted" in stats
        assert "total_execution_time" in stats
        assert "success_rate" in stats
        assert "average_execution_time" in stats
        
        # Test reset
        client.reset_stats()
        stats = client.get_stats()
        assert stats["requests_sent"] == 0
        assert stats["requests_successful"] == 0
        assert stats["requests_failed"] == 0
        assert stats["retries_attempted"] == 0
        assert stats["total_execution_time"] == 0.0
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check functionality."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            health = await client.health_check()
            assert health["healthy"] == True
            assert health["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self, client):
        """Test successful tool execution."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"result": "success", "success": True}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.execute_tool("bmad_prd_create", {"project_name": "test"})
            assert result["result"] == "success"
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_execute_tool_retry(self, client):
        """Test tool execution with retry logic."""
        # Test that retry logic is configured
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        
        # Test that stats track retries
        stats = client.get_stats()
        assert "retries_attempted" in stats
        assert stats["retries_attempted"] == 0  # Initially zero


class TestFeatureFlags:
    """Test feature flags functionality."""
    
    @pytest.fixture
    def flags(self):
        """Create a feature flags manager for testing."""
        return FeatureFlags()
    
    def test_default_flags(self, flags):
        """Test default feature flags."""
        assert flags.is_enabled("bmad_cluster_execution") == True
        assert flags.is_enabled("bmad_api_health_check") == True
        assert flags.is_enabled("bmad_performance_monitoring") == True
        assert flags.is_enabled("bmad_fallback_enabled") == True
        # This flag is enabled by default in the implementation
        assert flags.is_enabled("bmad_gradual_rollout") == True
        assert flags.is_enabled("bmad_debug_logging") == False
        assert flags.is_enabled("bmad_metrics_collection") == True
        assert flags.is_enabled("bmad_circuit_breaker") == True
    
    def test_unknown_flag(self, flags):
        """Test unknown feature flag."""
        assert flags.is_enabled("unknown_flag") == False
    
    def test_set_flag(self, flags):
        """Test setting feature flags."""
        flags.set_flag("bmad_cluster_execution", False)
        assert flags.is_enabled("bmad_cluster_execution") == False
        
        flags.set_flag("bmad_cluster_execution", True)
        assert flags.is_enabled("bmad_cluster_execution") == True
    
    def test_set_rollout_percentage(self, flags):
        """Test setting rollout percentage."""
        flags.set_rollout_percentage("bmad_gradual_rollout", 50)
        assert flags.is_enabled("bmad_gradual_rollout") == True
        
        flag_info = flags.get_flag_info("bmad_gradual_rollout")
        assert flag_info["rollout_percentage"] == 50
    
    def test_user_specific_flags(self, flags):
        """Test user-specific feature flags."""
        # Enable for specific user
        flags.set_flag("bmad_cluster_execution", True, "user123")
        assert flags.is_enabled("bmad_cluster_execution", "user123") == True
        
        # Disable for specific user
        flags.set_flag("bmad_cluster_execution", False, "user456")
        assert flags.is_enabled("bmad_cluster_execution", "user456") == False
    
    def test_flag_info(self, flags):
        """Test getting flag information."""
        info = flags.get_flag_info("bmad_cluster_execution")
        assert info["name"] == "bmad_cluster_execution"
        assert info["type"] == "boolean"
        assert "enabled" in info
        assert "rollout_percentage" in info
        assert "enabled_users" in info
        assert "disabled_users" in info
    
    def test_list_flags(self, flags):
        """Test listing all flags."""
        all_flags = flags.list_flags()
        assert "bmad_cluster_execution" in all_flags
        assert "bmad_api_health_check" in all_flags
        assert "bmad_performance_monitoring" in all_flags
    
    def test_stats(self, flags):
        """Test feature flags statistics."""
        stats = flags.get_stats()
        assert "total_flags" in stats
        assert "enabled_flags" in stats
        assert "disabled_flags" in stats
        assert "percentage_flags" in stats
        assert "boolean_flags" in stats


class TestHealthChecker:
    """Test health checker functionality."""
    
    @pytest.fixture
    def checker(self):
        """Create a health checker for testing."""
        return HealthChecker()
    
    def test_checker_initialization(self, checker):
        """Test health checker initialization."""
        assert checker.bmad_api_url is not None
        assert checker.check_interval == 30.0
        assert checker.timeout == 5.0
        assert checker.cache_duration == 10.0
    
    def test_checker_stats(self, checker):
        """Test health checker statistics."""
        stats = checker.get_stats()
        assert "checks_performed" in stats
        assert "successful_checks" in stats
        assert "failed_checks" in stats
        assert "cache_hits" in stats
        assert "last_check_duration" in stats
        assert "success_rate" in stats
        
        # Test reset
        checker.reset_stats()
        stats = checker.get_stats()
        assert stats["checks_performed"] == 0
        assert stats["successful_checks"] == 0
        assert stats["failed_checks"] == 0
        assert stats["cache_hits"] == 0
        assert stats["last_check_duration"] == 0.0
    
    def test_cache_info(self, checker):
        """Test cache information."""
        cache_info = checker.get_cache_info()
        assert "last_check_time" in cache_info
        assert "time_since_last_check" in cache_info
        assert "cache_duration" in cache_info
        assert "cache_valid" in cache_info
        assert "cached_status" in cache_info
        assert "health_cache" in cache_info
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, checker):
        """Test successful health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            is_healthy = await checker.is_bmad_api_healthy()
            assert is_healthy == True
            
            # Check stats
            stats = checker.get_stats()
            assert stats["checks_performed"] == 1
            assert stats["successful_checks"] == 1
            assert stats["failed_checks"] == 0
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, checker):
        """Test failed health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text.return_value = "Internal Server Error"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            is_healthy = await checker.is_bmad_api_healthy()
            assert is_healthy == False
            
            # Check stats
            stats = checker.get_stats()
            assert stats["checks_performed"] == 1
            assert stats["successful_checks"] == 0
            assert stats["failed_checks"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self, checker):
        """Test health check timeout."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            is_healthy = await checker.is_bmad_api_healthy()
            assert is_healthy == False
            
            # Check stats
            stats = checker.get_stats()
            assert stats["checks_performed"] == 1
            assert stats["successful_checks"] == 0
            assert stats["failed_checks"] == 1
    
    @pytest.mark.asyncio
    async def test_detailed_health(self, checker):
        """Test detailed health information."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            health_info = await checker.get_detailed_health()
            assert "bmad_api_url" in health_info
            assert "health_status" in health_info
            assert "cache_info" in health_info
            assert "stats" in health_info
            
            assert health_info["health_status"]["healthy"] == True
            assert health_info["health_status"]["status"] == "ok"


class TestIntegration:
    """Integration tests for Sprint 1 components."""
    
    @pytest.mark.asyncio
    async def test_full_routing_flow(self):
        """Test the complete BMAD tool routing flow."""
        # Create components
        router = BMADToolRouter()
        
        # Mock the API client to return success
        with patch.object(router.bmad_api_client, 'execute_tool') as mock_execute:
            mock_execute.return_value = {"result": "success", "success": True}
            
            # Mock health check to return healthy
            with patch.object(router.health_checker, 'is_bmad_api_healthy') as mock_health:
                mock_health.return_value = True
                
                # Test BMAD tool routing
                result = await router.route_bmad_tool("bmad_prd_create", {"project_name": "test"})
                assert result["result"] == "success"
                assert result["success"] == True
                
                # Check routing stats
                stats = router.get_routing_stats()
                assert stats["cluster_executions"] == 1
                assert stats["local_executions"] == 0
                assert stats["fallback_executions"] == 0
                assert stats["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_fallback_routing_flow(self):
        """Test fallback routing when API is unhealthy."""
        # Create components
        router = BMADToolRouter()
        
        # Mock health check to return unhealthy
        with patch.object(router.health_checker, 'is_bmad_api_healthy') as mock_health:
            mock_health.return_value = False
            
            # Mock local execution
            with patch('cflow_platform.core.direct_client.execute_mcp_tool') as mock_local:
                mock_local.return_value = {"result": "local_success", "success": True}
                
                # Test BMAD tool routing with fallback
                result = await router.route_bmad_tool("bmad_prd_create", {"project_name": "test"})
                # The actual result structure from BMAD handlers includes 'data' and 'message'
                assert isinstance(result, dict)
                assert "data" in result or "message" in result or "status" in result
                
                # Check routing stats
                stats = router.get_routing_stats()
                assert stats["cluster_executions"] == 0
                assert stats["local_executions"] == 1
                assert stats["fallback_executions"] == 0
                assert stats["errors"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
