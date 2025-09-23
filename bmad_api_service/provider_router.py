"""
BMAD Provider Router

This module provides real LLM provider routing for BMAD workflows,
replacing the mock implementation with actual provider integration.
"""

import asyncio
import logging
import os
import httpx
import json
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Enumeration of supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 300  # 5 minutes


@dataclass
class ProviderHealth:
    """Health status of a provider."""
    provider_id: str
    is_healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0


class ProviderRouter:
    """
    Routes BMAD workflow requests to appropriate LLM providers.
    
    This class manages multiple LLM providers, handles failover,
    and provides health monitoring.
    """
    
    def __init__(self):
        """Initialize the provider router."""
        self.providers: Dict[str, ProviderConfig] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self.default_provider: Optional[str] = None
        self.failover_order: List[str] = []
        
        # Initialize providers from environment
        self._initialize_providers()
        
        # Start health monitoring
        self._health_monitor_task = None
        self._start_health_monitoring()
    
    def _initialize_providers(self):
        """Initialize providers from environment variables."""
        # OpenAI Provider
        if os.getenv("OPENAI_API_KEY"):
            provider_id = "openai-primary"
            self.providers[provider_id] = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            )
            self.health_status[provider_id] = ProviderHealth(
                provider_id=provider_id,
                is_healthy=True,
                last_check=datetime.utcnow()
            )
            if not self.default_provider:
                self.default_provider = provider_id
        
        # Anthropic Provider
        if os.getenv("ANTHROPIC_API_KEY"):
            provider_id = "anthropic-primary"
            self.providers[provider_id] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))
            )
            self.health_status[provider_id] = ProviderHealth(
                provider_id=provider_id,
                is_healthy=True,
                last_check=datetime.utcnow()
            )
            if not self.default_provider:
                self.default_provider = provider_id
        
        # Azure OpenAI Provider
        if os.getenv("AZURE_OPENAI_API_KEY"):
            provider_id = "azure-openai-primary"
            self.providers[provider_id] = ProviderConfig(
                provider_type=ProviderType.AZURE_OPENAI,
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                max_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7"))
            )
            self.health_status[provider_id] = ProviderHealth(
                provider_id=provider_id,
                is_healthy=True,
                last_check=datetime.utcnow()
            )
            if not self.default_provider:
                self.default_provider = provider_id
        
        # Set failover order
        self.failover_order = list(self.providers.keys())
        
        logger.info(f"Initialized {len(self.providers)} providers: {list(self.providers.keys())}")
        logger.info(f"Default provider: {self.default_provider}")
    
    async def route_request(self, request: Dict[str, Any], provider_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Route a request to an appropriate provider.
        
        Args:
            request: The request to route
            provider_id: Specific provider to use (optional)
            
        Returns:
            Provider response
            
        Raises:
            Exception: If all providers fail
        """
        if not self.providers:
            raise Exception("No providers configured")
        
        # Determine which providers to try
        if provider_id:
            providers_to_try = [provider_id] if provider_id in self.providers else []
        else:
            providers_to_try = self._get_healthy_providers()
        
        if not providers_to_try:
            raise Exception("No healthy providers available")
        
        last_error = None
        
        for provider_id in providers_to_try:
            try:
                logger.info(f"Routing request to provider: {provider_id}")
                result = await self._execute_request(provider_id, request)
                
                # Update health status on success
                self._update_provider_health(provider_id, True)
                
                logger.info(f"Request successfully routed to provider: {provider_id}")
                return result
                
            except Exception as e:
                logger.warning(f"Provider {provider_id} failed: {e}")
                self._update_provider_health(provider_id, False, str(e))
                last_error = e
                continue
        
        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def _execute_request(self, provider_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a request using a specific provider."""
        provider = self.providers[provider_id]
        
        if provider.provider_type == ProviderType.OPENAI:
            return await self._execute_openai_request(provider, request)
        elif provider.provider_type == ProviderType.ANTHROPIC:
            return await self._execute_anthropic_request(provider, request)
        elif provider.provider_type == ProviderType.AZURE_OPENAI:
            return await self._execute_azure_openai_request(provider, request)
        else:
            raise Exception(f"Unsupported provider type: {provider.provider_type}")
    
    async def _execute_openai_request(self, provider: ProviderConfig, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a request using OpenAI API."""
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider.model,
            "messages": request.get("messages", []),
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature
        }
        
        async with httpx.AsyncClient(timeout=provider.timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def _execute_anthropic_request(self, provider: ProviderConfig, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a request using Anthropic API."""
        headers = {
            "x-api-key": provider.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": provider.model,
            "messages": request.get("messages", []),
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature
        }
        
        async with httpx.AsyncClient(timeout=provider.timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def _execute_azure_openai_request(self, provider: ProviderConfig, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a request using Azure OpenAI API."""
        headers = {
            "api-key": provider.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": request.get("messages", []),
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature
        }
        
        url = f"{provider.base_url}/openai/deployments/{provider.model}/chat/completions?api-version=2023-12-01-preview"
        
        async with httpx.AsyncClient(timeout=provider.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    def _get_healthy_providers(self) -> List[str]:
        """Get list of healthy providers in failover order."""
        healthy_providers = []
        for provider_id in self.failover_order:
            if provider_id in self.health_status and self.health_status[provider_id].is_healthy:
                healthy_providers.append(provider_id)
        return healthy_providers
    
    def _update_provider_health(self, provider_id: str, is_healthy: bool, error_message: Optional[str] = None):
        """Update provider health status."""
        if provider_id not in self.health_status:
            self.health_status[provider_id] = ProviderHealth(
                provider_id=provider_id,
                is_healthy=is_healthy,
                last_check=datetime.utcnow()
            )
        
        health = self.health_status[provider_id]
        health.last_check = datetime.utcnow()
        
        if is_healthy:
            health.is_healthy = True
            health.consecutive_failures = 0
            health.error_message = None
        else:
            health.consecutive_failures += 1
            health.error_message = error_message
            
            # Mark as unhealthy after 3 consecutive failures
            if health.consecutive_failures >= 3:
                health.is_healthy = False
    
    async def _health_check_provider(self, provider_id: str) -> bool:
        """Perform health check on a provider."""
        try:
            provider = self.providers[provider_id]
            
            # Simple health check request
            test_request = {
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            start_time = datetime.utcnow()
            await self._execute_request(provider_id, test_request)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            self.health_status[provider_id].response_time_ms = response_time
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for provider {provider_id}: {e}")
            return False
    
    def _start_health_monitoring(self):
        """Start background health monitoring."""
        async def health_monitor():
            while True:
                try:
                    for provider_id in self.providers.keys():
                        is_healthy = await self._health_check_provider(provider_id)
                        self._update_provider_health(provider_id, is_healthy)
                    
                    await asyncio.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        self._health_monitor_task = asyncio.create_task(health_monitor())
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            "providers": {
                provider_id: {
                    "config": {
                        "provider_type": provider.provider_type.value,
                        "model": provider.model,
                        "max_tokens": provider.max_tokens,
                        "temperature": provider.temperature
                    },
                    "health": {
                        "is_healthy": self.health_status[provider_id].is_healthy,
                        "last_check": self.health_status[provider_id].last_check.isoformat(),
                        "response_time_ms": self.health_status[provider_id].response_time_ms,
                        "consecutive_failures": self.health_status[provider_id].consecutive_failures,
                        "error_message": self.health_status[provider_id].error_message
                    }
                }
                for provider_id, provider in self.providers.items()
            },
            "default_provider": self.default_provider,
            "failover_order": self.failover_order
        }
    
    async def shutdown(self):
        """Shutdown the provider router."""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass


# Global provider router instance
provider_router = ProviderRouter()
