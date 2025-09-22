from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class WebMCPConfig:
    """Configuration for WebMCP server connection."""
    server_url: str
    api_key: Optional[str] = None
    bmad_api_url: Optional[str] = None
    bmad_auth_token: Optional[str] = None
    timeout: int = 30


@dataclass
class WebMCPInstallResult:
    """Result of WebMCP configuration installation."""
    success: bool
    message: str
    config_file_path: Optional[str] = None
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class WebMCPInstaller:
    """Installer for WebMCP configuration and cluster deployment."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".cerebraflow" / "webmcp"
        self.config_file = self.config_dir / "config.json"
        self.cluster_endpoints = {
            "webmcp": "https://webmcp-bmad.dev.cerebral.baerautotech.com",
            "bmad_api": "https://bmad-api.dev.cerebral.baerautotech.com",
            "bmad_method": "https://bmad-method.dev.cerebral.baerautotech.com"
        }
    
    def install_webmcp_configuration(self, config: WebMCPConfig, overwrite: bool = False) -> WebMCPInstallResult:
        """Install WebMCP configuration for cluster deployment."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if config already exists
            if self.config_file.exists() and not overwrite:
                return WebMCPInstallResult(
                    success=False,
                    message="Configuration already exists. Use --overwrite-config to replace it.",
                    errors=["Configuration file already exists"]
                )
            
            # Detect cluster vs local deployment
            is_cluster_deployment = self._detect_cluster_deployment(config.server_url)
            
            if is_cluster_deployment:
                # Use cluster endpoints
                cluster_config = self._create_cluster_config(config)
                config_data = cluster_config
                warnings = ["Using cluster deployment endpoints"]
            else:
                # Use local endpoints
                config_data = self._create_local_config(config)
                warnings = ["Using local deployment endpoints"]
            
            # Write configuration file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Test connection
            connection_test = self._test_connection(config_data)
            if not connection_test.success:
                return WebMCPInstallResult(
                    success=False,
                    message=f"Configuration saved but connection test failed: {connection_test.message}",
                    config_file_path=str(self.config_file),
                    warnings=warnings,
                    errors=connection_test.errors
                )
            
            return WebMCPInstallResult(
                success=True,
                message="WebMCP configuration installed successfully",
                config_file_path=str(self.config_file),
                warnings=warnings + connection_test.warnings
            )
            
        except Exception as e:
            return WebMCPInstallResult(
                success=False,
                message=f"Failed to install WebMCP configuration: {str(e)}",
                errors=[str(e)]
            )
    
    def _detect_cluster_deployment(self, server_url: str) -> bool:
        """Detect if this is a cluster deployment based on URL."""
        cluster_indicators = [
            "cerebral.baerautotech.com",
            "dev.cerebral.baerautotech.com",
            "webmcp-bmad.dev.cerebral.baerautotech.com"
        ]
        return any(indicator in server_url for indicator in cluster_indicators)
    
    def _create_cluster_config(self, config: WebMCPConfig) -> Dict[str, Any]:
        """Create configuration for cluster deployment."""
        return {
            "deployment_type": "cluster",
            "webmcp": {
                "server_url": self.cluster_endpoints["webmcp"],
                "api_key": config.api_key,
                "timeout": config.timeout,
                "health_endpoint": f"{self.cluster_endpoints['webmcp']}/health",
                "tools_endpoint": f"{self.cluster_endpoints['webmcp']}/mcp/tools",
                "call_endpoint": f"{self.cluster_endpoints['webmcp']}/mcp/tools/call"
            },
            "bmad_api": {
                "server_url": self.cluster_endpoints["bmad_api"],
                "auth_token": config.bmad_auth_token,
                "timeout": config.timeout,
                "health_endpoint": f"{self.cluster_endpoints['bmad_api']}/health",
                "project_type_endpoint": f"{self.cluster_endpoints['bmad_api']}/bmad/project-type/detect",
                "prd_create_endpoint": f"{self.cluster_endpoints['bmad_api']}/bmad/greenfield/prd-create"
            },
            "bmad_method": {
                "server_url": self.cluster_endpoints["bmad_method"],
                "timeout": config.timeout,
                "health_endpoint": f"{self.cluster_endpoints['bmad_method']}/health",
                "agents_endpoint": f"{self.cluster_endpoints['bmad_method']}/bmad/agents",
                "workflows_endpoint": f"{self.cluster_endpoints['bmad_method']}/bmad/workflows"
            },
            "cluster_info": {
                "dns_resolution": "cerebral.baerautotech.com",
                "certificates": "Let's Encrypt via cert-manager",
                "authentication": "Dex OIDC",
                "load_balancer": "MetalLB"
            }
        }
    
    def _create_local_config(self, config: WebMCPConfig) -> Dict[str, Any]:
        """Create configuration for local deployment."""
        return {
            "deployment_type": "local",
            "webmcp": {
                "server_url": config.server_url,
                "api_key": config.api_key,
                "timeout": config.timeout,
                "health_endpoint": f"{config.server_url}/health",
                "tools_endpoint": f"{config.server_url}/mcp/tools",
                "call_endpoint": f"{config.server_url}/mcp/tools/call"
            },
            "bmad_api": {
                "server_url": config.bmad_api_url or "http://localhost:8001",
                "auth_token": config.bmad_auth_token,
                "timeout": config.timeout,
                "health_endpoint": f"{config.bmad_api_url or 'http://localhost:8001'}/health"
            },
            "bmad_method": {
                "server_url": "http://localhost:8080",
                "timeout": config.timeout,
                "health_endpoint": "http://localhost:8080/health"
            }
        }
    
    def _test_connection(self, config_data: Dict[str, Any]) -> WebMCPInstallResult:
        """Test connection to WebMCP server."""
        try:
            webmcp_config = config_data["webmcp"]
            server_url = webmcp_config["server_url"]
            health_endpoint = webmcp_config["health_endpoint"]
            
            # Test health endpoint
            with httpx.Client(timeout=config_data["webmcp"]["timeout"]) as client:
                response = client.get(health_endpoint)
                response.raise_for_status()
                
                health_data = response.json()
                if health_data.get("status") != "healthy":
                    return WebMCPInstallResult(
                        success=False,
                        message="WebMCP server is not healthy",
                        errors=["Server health check failed"]
                    )
                
                # Test tools endpoint
                tools_response = client.get(webmcp_config["tools_endpoint"])
                tools_response.raise_for_status()
                
                tools_data = tools_response.json()
                tool_count = len(tools_data.get("tools", []))
                
                warnings = []
                if tool_count < 10:
                    warnings.append(f"Only {tool_count} tools available (expected 10+)")
                
                return WebMCPInstallResult(
                    success=True,
                    message=f"Connection successful. {tool_count} tools available.",
                    warnings=warnings
                )
                
        except httpx.ConnectError:
            return WebMCPInstallResult(
                success=False,
                message="Cannot connect to WebMCP server",
                errors=["Connection refused or server unavailable"]
            )
        except httpx.HTTPStatusError as e:
            return WebMCPInstallResult(
                success=False,
                message=f"HTTP error: {e.response.status_code}",
                errors=[f"HTTP {e.response.status_code}: {e.response.text}"]
            )
        except Exception as e:
            return WebMCPInstallResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                errors=[str(e)]
            )
    
    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """Get current WebMCP configuration."""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def validate_cluster_deployment(self) -> WebMCPInstallResult:
        """Validate cluster deployment endpoints."""
        try:
            results = []
            warnings = []
            errors = []
            
            for service, url in self.cluster_endpoints.items():
                try:
                    with httpx.Client(timeout=10) as client:
                        response = client.get(f"{url}/health")
                        response.raise_for_status()
                        results.append(f"✓ {service}: {url}")
                except Exception as e:
                    errors.append(f"✗ {service}: {url} - {str(e)}")
            
            if errors:
                return WebMCPInstallResult(
                    success=False,
                    message="Some cluster services are not accessible",
                    errors=errors,
                    warnings=warnings
                )
            
            return WebMCPInstallResult(
                success=True,
                message="All cluster services are accessible",
                warnings=warnings
            )
            
        except Exception as e:
            return WebMCPInstallResult(
                success=False,
                message=f"Cluster validation failed: {str(e)}",
                errors=[str(e)]
            )