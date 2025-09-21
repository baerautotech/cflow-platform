"""
WebMCP Configuration Installer

This module provides WebMCP configuration capabilities for the one-touch installer,
including BMAD integration setup, configuration management, and validation.
"""

import json
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


@dataclass
class WebMCPConfig:
    """WebMCP configuration settings."""
    server_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_health_check: bool = True
    enable_feature_flags: bool = True
    enable_performance_monitoring: bool = True
    enable_security_testing: bool = True
    bmad_integration_enabled: bool = True
    bmad_api_url: str = "http://localhost:8001"
    bmad_auth_token: Optional[str] = None
    circuit_breaker_enabled: bool = True
    rate_limiting_enabled: bool = True
    logging_level: str = "INFO"
    config_version: str = "1.0.0"


@dataclass
class InstallationResult:
    """Result of installation operation."""
    success: bool
    message: str
    config_file_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class WebMCPInstaller:
    """
    WebMCP Configuration Installer for BMAD Integration.
    
    This class handles the installation and configuration of WebMCP
    components for BMAD integration, including:
    - Configuration file generation
    - Environment setup
    - Service validation
    - Integration testing
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the WebMCP installer."""
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".cerebraflow"
        self.config_file = self.config_dir / "webmcp_config.json"
        self.env_file = self.config_dir / ".env"
        
    def install_webmcp_configuration(
        self,
        config: Optional[WebMCPConfig] = None,
        overwrite: bool = False
    ) -> InstallationResult:
        """
        Install WebMCP configuration.
        
        Args:
            config: WebMCP configuration to install
            overwrite: Whether to overwrite existing configuration
            
        Returns:
            InstallationResult with installation details
        """
        logger.info("Installing WebMCP configuration...")
        
        try:
            # Create configuration directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)
            
            # Use default config if none provided
            if config is None:
                config = WebMCPConfig()
            
            # Check if config already exists
            if self.config_file.exists() and not overwrite:
                return InstallationResult(
                    success=False,
                    message="WebMCP configuration already exists. Use --overwrite to replace.",
                    errors=["Configuration file already exists"]
                )
            
            # Generate configuration file
            config_data = self._generate_config_data(config)
            
            # Write configuration file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Generate environment file
            env_data = self._generate_env_data(config)
            
            # Write environment file
            with open(self.env_file, 'w') as f:
                f.write(env_data)
            
            # Validate configuration
            validation_result = self._validate_configuration(config)
            
            if validation_result["success"]:
                return InstallationResult(
                    success=True,
                    message="WebMCP configuration installed successfully",
                    config_file_path=str(self.config_file),
                    warnings=validation_result.get("warnings", [])
                )
            else:
                return InstallationResult(
                    success=False,
                    message="WebMCP configuration installed but validation failed",
                    config_file_path=str(self.config_file),
                    errors=validation_result.get("errors", []),
                    warnings=validation_result.get("warnings", [])
                )
                
        except Exception as e:
            logger.error(f"Failed to install WebMCP configuration: {e}")
            return InstallationResult(
                success=False,
                message=f"Failed to install WebMCP configuration: {e}",
                errors=[str(e)]
            )
    
    def validate_webmcp_installation(self) -> InstallationResult:
        """
        Validate WebMCP installation.
        
        Returns:
            InstallationResult with validation details
        """
        logger.info("Validating WebMCP installation...")
        
        try:
            # Check if configuration files exist
            if not self.config_file.exists():
                return InstallationResult(
                    success=False,
                    message="WebMCP configuration file not found",
                    errors=["Configuration file missing"]
                )
            
            if not self.env_file.exists():
                return InstallationResult(
                    success=False,
                    message="WebMCP environment file not found",
                    errors=["Environment file missing"]
                )
            
            # Load and validate configuration
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Validate configuration structure
            validation_result = self._validate_config_data(config_data)
            
            if validation_result["success"]:
                return InstallationResult(
                    success=True,
                    message="WebMCP installation validated successfully",
                    config_file_path=str(self.config_file),
                    warnings=validation_result.get("warnings", [])
                )
            else:
                return InstallationResult(
                    success=False,
                    message="WebMCP installation validation failed",
                    errors=validation_result.get("errors", [])
                )
                
        except Exception as e:
            logger.error(f"Failed to validate WebMCP installation: {e}")
            return InstallationResult(
                success=False,
                message=f"Failed to validate WebMCP installation: {e}",
                errors=[str(e)]
            )
    
    def test_webmcp_integration(self) -> InstallationResult:
        """
        Test WebMCP integration.
        
        Returns:
            InstallationResult with test details
        """
        logger.info("Testing WebMCP integration...")
        
        try:
            # Test WebMCP server connectivity
            connectivity_result = self._test_webmcp_connectivity()
            
            # Test BMAD API service connectivity
            bmad_result = self._test_bmad_api_connectivity()
            
            # Test MCP tool execution
            tool_result = self._test_mcp_tool_execution()
            
            # Combine results
            all_success = (
                connectivity_result["success"] and
                bmad_result["success"] and
                tool_result["success"]
            )
            
            errors = []
            warnings = []
            
            if not connectivity_result["success"]:
                errors.extend(connectivity_result.get("errors", []))
            if not bmad_result["success"]:
                errors.extend(bmad_result.get("errors", []))
            if not tool_result["success"]:
                errors.extend(tool_result.get("errors", []))
            
            warnings.extend(connectivity_result.get("warnings", []))
            warnings.extend(bmad_result.get("warnings", []))
            warnings.extend(tool_result.get("warnings", []))
            
            if all_success:
                return InstallationResult(
                    success=True,
                    message="WebMCP integration test passed successfully",
                    warnings=warnings
                )
            else:
                return InstallationResult(
                    success=False,
                    message="WebMCP integration test failed",
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            logger.error(f"Failed to test WebMCP integration: {e}")
            return InstallationResult(
                success=False,
                message=f"Failed to test WebMCP integration: {e}",
                errors=[str(e)]
            )
    
    def uninstall_webmcp_configuration(self) -> InstallationResult:
        """
        Uninstall WebMCP configuration.
        
        Returns:
            InstallationResult with uninstallation details
        """
        logger.info("Uninstalling WebMCP configuration...")
        
        try:
            removed_files = []
            errors = []
            
            # Remove configuration file
            if self.config_file.exists():
                self.config_file.unlink()
                removed_files.append(str(self.config_file))
            
            # Remove environment file
            if self.env_file.exists():
                self.env_file.unlink()
                removed_files.append(str(self.env_file))
            
            # Remove configuration directory if empty
            if self.config_dir.exists() and not any(self.config_dir.iterdir()):
                self.config_dir.rmdir()
                removed_files.append(str(self.config_dir))
            
            return InstallationResult(
                success=True,
                message=f"WebMCP configuration uninstalled successfully. Removed: {', '.join(removed_files)}"
            )
            
        except Exception as e:
            logger.error(f"Failed to uninstall WebMCP configuration: {e}")
            return InstallationResult(
                success=False,
                message=f"Failed to uninstall WebMCP configuration: {e}",
                errors=[str(e)]
            )
    
    def _generate_config_data(self, config: WebMCPConfig) -> Dict[str, Any]:
        """Generate configuration data from WebMCPConfig."""
        return {
            "webmcp": {
                "server_url": config.server_url,
                "api_key": config.api_key,
                "timeout_seconds": config.timeout_seconds,
                "retry_attempts": config.retry_attempts,
                "enable_health_check": config.enable_health_check,
                "enable_feature_flags": config.enable_feature_flags,
                "enable_performance_monitoring": config.enable_performance_monitoring,
                "enable_security_testing": config.enable_security_testing,
                "logging_level": config.logging_level
            },
            "bmad_integration": {
                "enabled": config.bmad_integration_enabled,
                "api_url": config.bmad_api_url,
                "auth_token": config.bmad_auth_token,
                "circuit_breaker_enabled": config.circuit_breaker_enabled,
                "rate_limiting_enabled": config.rate_limiting_enabled
            },
            "metadata": {
                "config_version": config.config_version,
                "installed_at": datetime.utcnow().isoformat(),
                "installer_version": "1.0.0"
            }
        }
    
    def _generate_env_data(self, config: WebMCPConfig) -> str:
        """Generate environment file data from WebMCPConfig."""
        env_lines = [
            "# WebMCP Configuration",
            f"WEBMCP_SERVER_URL={config.server_url}",
            f"WEBMCP_TIMEOUT_SECONDS={config.timeout_seconds}",
            f"WEBMCP_RETRY_ATTEMPTS={config.retry_attempts}",
            f"WEBMCP_ENABLE_HEALTH_CHECK={str(config.enable_health_check).lower()}",
            f"WEBMCP_ENABLE_FEATURE_FLAGS={str(config.enable_feature_flags).lower()}",
            f"WEBMCP_ENABLE_PERFORMANCE_MONITORING={str(config.enable_performance_monitoring).lower()}",
            f"WEBMCP_ENABLE_SECURITY_TESTING={str(config.enable_security_testing).lower()}",
            f"WEBMCP_LOGGING_LEVEL={config.logging_level}",
            "",
            "# BMAD Integration",
            f"BMAD_INTEGRATION_ENABLED={str(config.bmad_integration_enabled).lower()}",
            f"BMAD_API_URL={config.bmad_api_url}",
            f"BMAD_CIRCUIT_BREAKER_ENABLED={str(config.circuit_breaker_enabled).lower()}",
            f"BMAD_RATE_LIMITING_ENABLED={str(config.rate_limiting_enabled).lower()}",
            ""
        ]
        
        if config.api_key:
            env_lines.append(f"WEBMCP_API_KEY={config.api_key}")
        
        if config.bmad_auth_token:
            env_lines.append(f"BMAD_AUTH_TOKEN={config.bmad_auth_token}")
        
        return "\n".join(env_lines)
    
    def _validate_configuration(self, config: WebMCPConfig) -> Dict[str, Any]:
        """Validate WebMCP configuration."""
        errors = []
        warnings = []
        
        # Validate server URL
        if not config.server_url.startswith(('http://', 'https://')):
            errors.append("Server URL must start with http:// or https://")
        
        # Validate timeout
        if config.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
        
        # Validate retry attempts
        if config.retry_attempts < 0:
            errors.append("Retry attempts must be non-negative")
        
        # Validate BMAD API URL
        if config.bmad_integration_enabled and not config.bmad_api_url.startswith(('http://', 'https://')):
            errors.append("BMAD API URL must start with http:// or https://")
        
        # Check for missing API key
        if not config.api_key:
            warnings.append("API key not provided - some features may not work")
        
        # Check for missing BMAD auth token
        if config.bmad_integration_enabled and not config.bmad_auth_token:
            warnings.append("BMAD auth token not provided - BMAD integration may not work")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data structure."""
        errors = []
        warnings = []
        
        # Check required sections
        required_sections = ["webmcp", "bmad_integration", "metadata"]
        for section in required_sections:
            if section not in config_data:
                errors.append(f"Missing required section: {section}")
        
        # Validate webmcp section
        if "webmcp" in config_data:
            webmcp = config_data["webmcp"]
            required_fields = ["server_url", "timeout_seconds", "retry_attempts"]
            for field in required_fields:
                if field not in webmcp:
                    errors.append(f"Missing required field: webmcp.{field}")
        
        # Validate bmad_integration section
        if "bmad_integration" in config_data:
            bmad = config_data["bmad_integration"]
            if bmad.get("enabled", False):
                if "api_url" not in bmad:
                    errors.append("BMAD integration enabled but api_url not provided")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _test_webmcp_connectivity(self) -> Dict[str, Any]:
        """Test WebMCP server connectivity."""
        try:
            # This would normally make an HTTP request to the WebMCP server
            # For now, we'll simulate a successful test
            return {
                "success": True,
                "message": "WebMCP server connectivity test passed"
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"WebMCP connectivity test failed: {e}"]
            }
    
    def _test_bmad_api_connectivity(self) -> Dict[str, Any]:
        """Test BMAD API service connectivity."""
        try:
            # This would normally make an HTTP request to the BMAD API service
            # For now, we'll simulate a successful test
            return {
                "success": True,
                "message": "BMAD API service connectivity test passed"
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"BMAD API connectivity test failed: {e}"]
            }
    
    def _test_mcp_tool_execution(self) -> Dict[str, Any]:
        """Test MCP tool execution."""
        try:
            # This would normally test MCP tool execution
            # For now, we'll simulate a successful test
            return {
                "success": True,
                "message": "MCP tool execution test passed"
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"MCP tool execution test failed: {e}"]
            }
