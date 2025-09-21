"""
WebMCP Installer Handlers

This module provides MCP handlers for WebMCP installer functionality,
including configuration management, installation, validation, and testing.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from cflow_platform.core.webmcp_installer import (
    WebMCPInstaller,
    WebMCPConfig,
    InstallationResult
)

logger = logging.getLogger(__name__)


async def bmad_webmcp_install_config(
    server_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    timeout_seconds: int = 30,
    retry_attempts: int = 3,
    enable_health_check: bool = True,
    enable_feature_flags: bool = True,
    enable_performance_monitoring: bool = True,
    enable_security_testing: bool = True,
    bmad_integration_enabled: bool = True,
    bmad_api_url: str = "http://localhost:8001",
    bmad_auth_token: Optional[str] = None,
    circuit_breaker_enabled: bool = True,
    rate_limiting_enabled: bool = True,
    logging_level: str = "INFO",
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Install WebMCP configuration.
    
    Args:
        server_url: WebMCP server URL
        api_key: API key for authentication
        timeout_seconds: Request timeout in seconds
        retry_attempts: Number of retry attempts
        enable_health_check: Enable health checking
        enable_feature_flags: Enable feature flags
        enable_performance_monitoring: Enable performance monitoring
        enable_security_testing: Enable security testing
        bmad_integration_enabled: Enable BMAD integration
        bmad_api_url: BMAD API service URL
        bmad_auth_token: BMAD authentication token
        circuit_breaker_enabled: Enable circuit breaker
        rate_limiting_enabled: Enable rate limiting
        logging_level: Logging level
        overwrite: Whether to overwrite existing configuration
        
    Returns:
        Dictionary with installation result
    """
    try:
        logger.info("Installing WebMCP configuration...")
        
        # Create WebMCP configuration
        config = WebMCPConfig(
            server_url=server_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            enable_health_check=enable_health_check,
            enable_feature_flags=enable_feature_flags,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_security_testing=enable_security_testing,
            bmad_integration_enabled=bmad_integration_enabled,
            bmad_api_url=bmad_api_url,
            bmad_auth_token=bmad_auth_token,
            circuit_breaker_enabled=circuit_breaker_enabled,
            rate_limiting_enabled=rate_limiting_enabled,
            logging_level=logging_level
        )
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Install configuration
        result = installer.install_webmcp_configuration(config, overwrite=overwrite)
        
        return {
            "success": result.success,
            "message": result.message,
            "config_file_path": result.config_file_path,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to install WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_validate_installation() -> Dict[str, Any]:
    """
    Validate WebMCP installation.
    
    Returns:
        Dictionary with validation result
    """
    try:
        logger.info("Validating WebMCP installation...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Validate installation
        result = installer.validate_webmcp_installation()
        
        return {
            "success": result.success,
            "message": result.message,
            "config_file_path": result.config_file_path,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate WebMCP installation: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_test_integration() -> Dict[str, Any]:
    """
    Test WebMCP integration.
    
    Returns:
        Dictionary with test result
    """
    try:
        logger.info("Testing WebMCP integration...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Test integration
        result = installer.test_webmcp_integration()
        
        return {
            "success": result.success,
            "message": result.message,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test WebMCP integration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_uninstall_config() -> Dict[str, Any]:
    """
    Uninstall WebMCP configuration.
    
    Returns:
        Dictionary with uninstallation result
    """
    try:
        logger.info("Uninstalling WebMCP configuration...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Uninstall configuration
        result = installer.uninstall_webmcp_configuration()
        
        return {
            "success": result.success,
            "message": result.message,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to uninstall WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_get_config() -> Dict[str, Any]:
    """
    Get current WebMCP configuration.
    
    Returns:
        Dictionary with current configuration
    """
    try:
        logger.info("Retrieving WebMCP configuration...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Check if configuration exists
        if not installer.config_file.exists():
            return {
                "success": False,
                "error": "WebMCP configuration not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Load configuration
        with open(installer.config_file, 'r') as f:
            config_data = json.load(f)
        
        return {
            "success": True,
            "configuration": config_data,
            "config_file_path": str(installer.config_file),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_update_config(
    config_updates: str
) -> Dict[str, Any]:
    """
    Update WebMCP configuration.
    
    Args:
        config_updates: JSON string with configuration updates
        
    Returns:
        Dictionary with update result
    """
    try:
        logger.info("Updating WebMCP configuration...")
        
        # Parse configuration updates
        try:
            updates = json.loads(config_updates)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in config_updates: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Check if configuration exists
        if not installer.config_file.exists():
            return {
                "success": False,
                "error": "WebMCP configuration not found. Please install first.",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Load current configuration
        with open(installer.config_file, 'r') as f:
            current_config = json.load(f)
        
        # Apply updates
        def update_nested_dict(d, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and key in d and isinstance(d[key], dict):
                    update_nested_dict(d[key], value)
                else:
                    d[key] = value
        
        update_nested_dict(current_config, updates)
        
        # Add metadata
        if "metadata" not in current_config:
            current_config["metadata"] = {}
        current_config["metadata"]["updated_at"] = datetime.utcnow().isoformat()
        
        # Write updated configuration
        with open(installer.config_file, 'w') as f:
            json.dump(current_config, f, indent=2)
        
        return {
            "success": True,
            "message": "WebMCP configuration updated successfully",
            "config_file_path": str(installer.config_file),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_backup_config() -> Dict[str, Any]:
    """
    Backup WebMCP configuration.
    
    Returns:
        Dictionary with backup result
    """
    try:
        logger.info("Backing up WebMCP configuration...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Check if configuration exists
        if not installer.config_file.exists():
            return {
                "success": False,
                "error": "WebMCP configuration not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create backup file
        backup_file = installer.config_file.with_suffix(f".backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        
        # Copy configuration to backup
        import shutil
        shutil.copy2(installer.config_file, backup_file)
        
        return {
            "success": True,
            "message": "WebMCP configuration backed up successfully",
            "backup_file_path": str(backup_file),
            "original_file_path": str(installer.config_file),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to backup WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def bmad_webmcp_restore_config(
    backup_file_path: str
) -> Dict[str, Any]:
    """
    Restore WebMCP configuration from backup.
    
    Args:
        backup_file_path: Path to backup file
        
    Returns:
        Dictionary with restore result
    """
    try:
        logger.info(f"Restoring WebMCP configuration from {backup_file_path}...")
        
        # Create installer
        installer = WebMCPInstaller()
        
        # Check if backup file exists
        backup_path = Path(backup_file_path)
        if not backup_path.exists():
            return {
                "success": False,
                "error": f"Backup file not found: {backup_file_path}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create backup of current configuration if it exists
        if installer.config_file.exists():
            current_backup = installer.config_file.with_suffix(f".backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            import shutil
            shutil.copy2(installer.config_file, current_backup)
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, installer.config_file)
        
        return {
            "success": True,
            "message": "WebMCP configuration restored successfully",
            "config_file_path": str(installer.config_file),
            "backup_file_path": backup_file_path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to restore WebMCP configuration: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
